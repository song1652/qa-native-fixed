"""Durable Import Studio run, commit, and rollback operations.

The HTTP handler intentionally delegates filesystem mutation here so preview
state, stale-input checks, journaling, and recovery share one implementation.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import shutil
import tempfile
import time
import unicodedata
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from _excel_import import file_sha256, parse_sheet
from _import_validator import classify_row, load_existing_testcases


STATUSES = ("added", "updated", "conflict", "error", "same")


class ImportRunError(RuntimeError):
    def __init__(self, message: str, code: str = "IMPORT_ERROR"):
        super().__init__(message)
        self.code = code


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        Path(tmp).replace(path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    if root.exists():
        for path in sorted(root.rglob("tc_*.md")):
            if not path.is_file():
                continue
            digest.update(path.relative_to(root).as_posix().encode())
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def _safe_child(root: Path, relative: str) -> Path:
    target = (root.resolve() / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ImportRunError("허용되지 않은 경로입니다", "INVALID_PATH")
    return target


def _resolve_file(import_dir: Path, file_id: str) -> Path:
    for path in import_dir.glob("*.xlsx"):
        candidate_id = hashlib.sha256(path.name.encode()).hexdigest()[:8]
        if candidate_id == file_id or path.name == file_id:
            return path
    raise ImportRunError(f"file_id '{file_id}'에 해당하는 파일 없음", "FILE_NOT_FOUND")


def _normalize_sources(body: dict) -> list[dict]:
    if isinstance(body.get("sources"), list):
        return body["sources"]
    if isinstance(body.get("files"), list):
        sources = []
        for item in body["files"]:
            for sheet in item.get("sheets", []):
                if isinstance(sheet, str):
                    sheet = {"sheet_name": sheet}
                sources.append({
                    "file_id": item.get("file_id") or item.get("id"),
                    "sheet_name": sheet.get("sheet_name") or sheet.get("name"),
                    "mappings": sheet.get("mappings") or item.get("mappings", {}),
                    "header_row": sheet.get("header_row") or item.get("header_row"),
                })
        return sources
    return [{
        "file_id": body.get("file_id"),
        "sheet_name": body.get("sheet_name"),
        "mappings": body.get("mappings", {}),
        "header_row": body.get("header_row"),
    }]


def create_preview(body: dict, import_dir: Path, testcases_dir: Path, runs_dir: Path) -> dict:
    sources = _normalize_sources(body)
    if not sources or any(not s.get("file_id") or not s.get("sheet_name") for s in sources):
        raise ImportRunError("file_id와 sheet_name이 필요합니다", "INVALID_REQUEST")

    required = ("tc_id", "title", "precondition", "steps", "expected")
    existing = load_existing_testcases(testcases_dir)
    rows: list[dict] = []
    source_records: list[dict] = []
    seen: dict[str, dict] = {}
    for source in sources:
        mappings = source.get("mappings") or {}
        missing = [field for field in required if not mappings.get(field)]
        if missing:
            raise ImportRunError(f"필수 매핑 누락: {', '.join(missing)}", "MISSING_MAPPING")
        file_path = _resolve_file(import_dir, str(source["file_id"]))
        parsed = parse_sheet(
            file_path,
            str(source["sheet_name"]),
            mappings,
            header_row=source.get("header_row"),
        )
        source_records.append({
            "file_id": source["file_id"],
            "file_name": file_path.name,
            "file_sha256": file_sha256(file_path),
            "sheet_name": source["sheet_name"],
            "mappings": mappings,
            "header_row": source.get("header_row"),
        })
        for row in parsed:
            result = {**row, **classify_row(row, existing)}
            result["_source_file_id"] = source["file_id"]
            tc_id = str(row.get("tc_id", "")).strip()
            if tc_id and tc_id in seen:
                result.update(status="conflict", reason="선택한 Excel 범위 안에서 tc_id 중복",
                              reason_code="DUPLICATE_SOURCE_TC_ID")
                first = seen[tc_id]
                first.update(status="conflict", reason="선택한 Excel 범위 안에서 tc_id 중복",
                             reason_code="DUPLICATE_SOURCE_TC_ID",
                             excluded=body.get("conflict_policy") == "exclude",
                             decision="exclude" if body.get("conflict_policy") == "exclude" else "pending")
            elif tc_id:
                seen[tc_id] = result
            current = existing.get(tc_id)
            result["before"] = ({
                field: current.get(field)
                for field in ("title", "precondition", "steps", "expected", "priority", "tags", "group", "hash")
            } | {"file_name": current["path"].name} if current else None)
            result["after"] = {field: result.get(field) for field in
                               ("tc_id", "title", "precondition", "steps", "expected", "priority", "tags", "group")}
            if result.get("status") == "conflict":
                excluded = body.get("conflict_policy") == "exclude"
                result["excluded"] = excluded
                result["decision"] = "exclude" if excluded else "pending"
            else:
                result["excluded"] = result.get("status") not in {"added", "updated"}
                result["decision"] = "automatic"
            rows.append(result)

    summary = {status: sum(row.get("status") == status for row in rows) for status in STATUSES}
    run_id = f"run_{datetime.now().strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:8]}"
    run = {
        "run_id": run_id,
        "session_id": run_id,
        "status": "preview_ready",
        "created_at": _now(),
        "sources": source_records,
        "testcases_sha256": _tree_hash(testcases_dir),
        "summary": summary,
        "rows": rows,
    }
    _atomic_json(runs_dir / f"{run_id}.json", run)
    return run


def load_run(runs_dir: Path, run_id: str) -> dict:
    if not re.fullmatch(r"run_[A-Za-z0-9_-]+|sess_[A-Za-z0-9_-]+", run_id):
        raise ImportRunError("invalid run_id", "INVALID_RUN_ID")
    path = _safe_child(runs_dir, f"{run_id}.json")
    if not path.exists():
        raise ImportRunError(f"run '{run_id}' 없음", "RUN_NOT_FOUND")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ImportRunError(f"run 상태를 읽을 수 없음: {exc}", "RUN_CORRUPT") from exc


def _render(row: dict) -> str:
    tags = row.get("tags") or ["general"]
    if not isinstance(tags, list):
        raise ImportRunError("tags는 문자열 배열이어야 합니다", "INVALID_TAGS")
    tags_text = json.dumps([str(tag) for tag in tags], ensure_ascii=False)
    priority = str(row.get("priority") or "medium").lower()
    if priority not in {"high", "medium", "low"}:
        priority = "medium"
    precondition = str(row.get("precondition") or "").strip()
    precondition_section = f"## 사전 조건\n{precondition}\n\n" if precondition else ""
    return (
        f"---\nid: {json.dumps(str(row['tc_id']), ensure_ascii=False)}\ndata_key: null\n"
        f"priority: {json.dumps(priority)}\ntags: {tags_text}\ntype: structured\n---\n"
        f"# {row['title']}\n\n{precondition_section}"
        f"## Steps\n{row['steps']}\n\n"
        f"## Expected\n{row['expected']}\n"
    )


def _target_for(row: dict, testcases_dir: Path) -> Path:
    group = str(row["group"])
    if not re.fullmatch(r"[A-Za-z0-9가-힣_-]+", group):
        raise ImportRunError(f"잘못된 group: {group}", "INVALID_GROUP")
    slug = re.sub(r"[^A-Za-z0-9가-힣_-]+", "_", str(row["title"]).lower()).strip("_")[:40] or "case"
    return _safe_child(testcases_dir, f"{group}/tc_{row['tc_id']}_{slug}.md")


def _apply_conflict_decisions(run: dict, decisions: list[dict],
                              policy: str = "skip-conflict") -> None:
    conflicts = [row for row in run.get("rows", []) if row.get("status") == "conflict"]
    if not conflicts and decisions:
        raise ImportRunError("결정 대상 conflict 행이 없습니다", "INVALID_DECISIONS")
    matched: set[int] = set()
    for decision in decisions:
        if not isinstance(decision, dict) or decision.get("action") != "exclude":
            raise ImportRunError("decision action은 exclude만 허용됩니다", "INVALID_DECISIONS")
        try:
            decision_row = int(decision.get("source_row", -1))
        except (TypeError, ValueError) as exc:
            raise ImportRunError("decision source_row 형식 오류", "INVALID_DECISIONS") from exc
        candidates = []
        for index, row in enumerate(conflicts):
            file_matches = (
                decision.get("file_id") == row.get("_source_file_id")
                if decision.get("file_id") is not None
                else decision.get("file_name") == row.get("_source_file")
            )
            if (file_matches and decision.get("sheet_name") == row.get("_source_sheet")
                    and decision_row == int(row.get("_row", -2))
                    and decision.get("tc_id") == row.get("tc_id")):
                candidates.append(index)
        if len(candidates) != 1 or candidates[0] in matched:
            raise ImportRunError("unknown 또는 duplicate conflict decision", "INVALID_DECISIONS")
        matched.add(candidates[0])
        conflicts[candidates[0]].update(excluded=True, decision="exclude")
    # Apply policy to any remaining unresolved conflict rows
    for row in conflicts:
        if row.get("decision") not in {"exclude", "overwrite"}:
            if policy == "overwrite":
                row.update(excluded=False, decision="overwrite")
            else:
                # "skip-conflict" (default) and "replace-with-snapshot" both skip
                row.update(excluded=True, decision="exclude")


def _canonical_decisions(decisions: list[dict] | None) -> list[dict]:
    """Normalize the semantic decision fields for stable request identity.

    Decision array order, mapping key order, ignored extension fields, and a
    numeric ``source_row`` represented as a string do not change the request.
    Validation remains the responsibility of ``_apply_conflict_decisions``.
    """
    if decisions is None:
        return []
    if not isinstance(decisions, list):
        raise ImportRunError("decisions must be an array", "INVALID_DECISIONS")
    canonical: list[dict] = []
    for decision in decisions:
        if not isinstance(decision, dict):
            raise ImportRunError("decision 형식 오류", "INVALID_DECISIONS")
        source_row = decision.get("source_row")
        try:
            source_row = int(source_row) if source_row is not None else None
        except (TypeError, ValueError):
            # Preserve invalid input deterministically. A first commit will
            # still reject it during decision validation; a replay with the
            # same key will compare it safely without mutating state.
            source_row = str(source_row)
        normalized = {
            "action": decision.get("action"),
            "sheet_name": decision.get("sheet_name"),
            "source_row": source_row,
            "tc_id": decision.get("tc_id"),
        }
        if decision.get("file_id") is not None:
            normalized["file_id"] = decision.get("file_id")
        else:
            normalized["file_name"] = decision.get("file_name")
        canonical.append(normalized)
    return sorted(canonical, key=lambda item: json.dumps(
        item, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ))


def _decisions_fingerprint(decisions: list[dict] | None) -> tuple[list[dict], str]:
    canonical = _canonical_decisions(decisions)
    payload = json.dumps(canonical, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return canonical, hashlib.sha256(payload).hexdigest()


def _replace_file(temp_path: Path, target: Path) -> None:
    """Atomic replace seam kept separate for deterministic recovery tests."""
    temp_path.replace(target)


def _pid_is_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _lock_is_abandoned(lock: Path, stale_seconds: int = 300) -> bool:
    try:
        metadata = json.loads(lock.read_text(encoding="utf-8"))
        pid = int(metadata.get("pid", 0))
        return not _pid_is_alive(pid)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        try:
            return time.time() - lock.stat().st_mtime > stale_seconds
        except OSError:
            return False


@contextmanager
def _commit_lock(runs_dir: Path, run_id: str):
    runs_dir.mkdir(parents=True, exist_ok=True)
    lock = runs_dir / ".commit.lock"
    for attempt in range(2):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump({"pid": os.getpid(), "created_at": _now(), "run_id": run_id}, stream)
                stream.flush()
                os.fsync(stream.fileno())
            break
        except FileExistsError as exc:
            if attempt == 0 and _lock_is_abandoned(lock):
                lock.unlink(missing_ok=True)
                continue
            raise ImportRunError("다른 Import 커밋이 진행 중입니다", "COMMIT_LOCKED") from exc
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def _path_state(path: Path) -> tuple[bool, str | None]:
    exists = path.exists()
    if exists and not path.is_file():
        raise ImportRunError(f"파일이어야 하는 경로: {path}", "SNAPSHOT_CORRUPT")
    return exists, hashlib.sha256(path.read_bytes()).hexdigest() if exists else None


def _preflight_restore_manifest(manifest: dict, project_root: Path, snapshot_dir: Path) -> list[dict]:
    """Resolve and validate the complete restore plan before any mutation."""
    resolved: list[dict] = []
    seen_targets: set[Path] = set()
    entries = manifest.get("entries")
    if not isinstance(entries, list):
        raise ImportRunError("snapshot entries 형식 오류", "SNAPSHOT_CORRUPT")
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("target"), str):
            raise ImportRunError("snapshot entry 형식 오류", "SNAPSHOT_CORRUPT")
        target = _safe_child(project_root, entry["target"])
        if target in seen_targets:
            raise ImportRunError(f"snapshot target 중복: {entry['target']}", "SNAPSHOT_CORRUPT")
        seen_targets.add(target)
        temp = _safe_child(project_root, entry["temp"]) if entry.get("temp") else None
        backup = None
        if entry.get("before_exists"):
            if not isinstance(entry.get("backup"), str) or not entry.get("before_sha256"):
                raise ImportRunError(f"snapshot backup 메타데이터 누락: {entry['target']}",
                                     "SNAPSHOT_CORRUPT")
            backup = _safe_child(snapshot_dir, entry["backup"])
            if not backup.is_file():
                raise ImportRunError(f"snapshot backup 없음: {entry['target']}", "SNAPSHOT_CORRUPT")
            backup_hash = hashlib.sha256(backup.read_bytes()).hexdigest()
            if backup_hash != entry["before_sha256"]:
                raise ImportRunError(f"snapshot backup SHA256 불일치: {entry['target']}",
                                     "SNAPSHOT_CORRUPT")
        resolved.append({"entry": entry, "target": target, "temp": temp, "backup": backup})
    return resolved


def _restore_manifest(manifest: dict, project_root: Path, snapshot_dir: Path) -> dict:
    resolved = _preflight_restore_manifest(manifest, project_root, snapshot_dir)
    restored = deleted = 0
    for item in reversed(resolved):
        entry, target = item["entry"], item["target"]
        if item["temp"]:
            item["temp"].unlink(missing_ok=True)
        if entry.get("before_exists"):
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item["backup"], target)
            restored += 1
        elif target.exists():
            target.unlink()
            deleted += 1
    return {"restored": restored, "deleted": deleted}


def _preflight_interrupted_recovery(manifest: dict, project_root: Path,
                                    snapshot_dir: Path) -> None:
    """Reject recovery if any target is neither its before nor transaction state."""
    for item in _preflight_restore_manifest(manifest, project_root, snapshot_dir):
        entry, target = item["entry"], item["target"]
        current = _path_state(target)
        before = (bool(entry.get("before_exists")), entry.get("before_sha256"))
        applying = (bool(entry.get("after_exists")), entry.get("after_sha256"))
        if "after_exists" not in entry or (entry.get("after_exists") and not entry.get("after_sha256")):
            raise ImportRunError(f"복구 예상 상태 누락: {entry['target']}", "RECOVERY_CONFLICT")
        if current not in {before, applying}:
            raise ImportRunError(f"중단 후 외부 변경 감지: {entry['target']}", "RECOVERY_CONFLICT")


def _recover_interrupted_commits(snapshots_dir: Path, project_root: Path, runs_dir: Path) -> None:
    """Recover a process that stopped after its journal entered applying state."""
    if not snapshots_dir.exists():
        return
    for manifest_path in snapshots_dir.glob("*/manifest.json"):
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        run_id = str(manifest.get("run_id", ""))
        run_path = runs_dir / f"{run_id}.json"
        run = json.loads(run_path.read_text(encoding="utf-8")) if run_path.exists() else None
        if manifest.get("status") == "recovery_conflict":
            raise ImportRunError(
                f"수동 확인이 필요한 중단 복구 충돌: {manifest.get('snapshot_id', manifest_path.parent.name)}",
                "RECOVERY_CONFLICT",
            )
        if manifest.get("status") == "applying":
            try:
                _preflight_interrupted_recovery(manifest, project_root, manifest_path.parent)
                result = _restore_manifest(manifest, project_root, manifest_path.parent)
            except ImportRunError as exc:
                manifest.update(status="recovery_conflict", recovery_failed_at=_now(),
                                error=str(exc), error_code=exc.code)
                _atomic_json(manifest_path, manifest)
                if run is not None:
                    run.update(status="recovery_conflict", last_recovery={
                        "snapshot_id": manifest.get("snapshot_id"), "error": str(exc),
                        "error_code": exc.code,
                    })
                    _atomic_json(run_path, run)
                raise
            manifest.update(status="recovered", recovered_at=_now(), recovery=result,
                            error="이전 프로세스의 중단된 커밋 자동 복구")
            _atomic_json(manifest_path, manifest)
            if run is not None:
                run.update(status="preview_ready", last_recovery={"snapshot_id": manifest.get("snapshot_id"), **result})
                _atomic_json(run_path, run)
        elif manifest.get("status") == "committed" and run is not None and run.get("status") != "committed":
            # Crash after durable filesystem commit but before the run record.
            run.update(status="committed", committed_at=manifest.get("committed_at", _now()),
                       snapshot_id=manifest.get("snapshot_id"),
                       idempotency_key=manifest.get("idempotency_key"),
                       request_fingerprint=manifest.get("request_fingerprint"),
                       decisions=manifest.get("decisions", []),
                       result=manifest.get("result", {}),
                       committed_testcases_sha256=manifest.get("committed_testcases_sha256"))
            _atomic_json(run_path, run)
        elif manifest.get("status") == "rolling_back" and run is not None:
            try:
                # A crashed rollback may leave each target either in its
                # committed state or already restored to its pre-commit state.
                # Anything else is a post-crash external edit and must never
                # be overwritten by automatic recovery.
                _preflight_interrupted_recovery(manifest, project_root, manifest_path.parent)
                result = _restore_manifest(manifest, project_root, manifest_path.parent)
            except ImportRunError as exc:
                manifest.update(status="recovery_conflict", recovery_failed_at=_now(),
                                recovery_operation="rollback", error=str(exc),
                                error_code=exc.code)
                run.update(status="recovery_conflict", last_recovery={
                    "snapshot_id": manifest.get("snapshot_id"), "operation": "rollback",
                    "error": str(exc), "error_code": exc.code,
                })
                _atomic_json(manifest_path, manifest)
                _atomic_json(run_path, run)
                raise
            actual_hash = _tree_hash(project_root / "testcases")
            expected_hash = run.get("testcases_sha256")
            if actual_hash == expected_hash:
                result["verified"] = True
                manifest.update(status="rolled_back", rolled_back_at=_now(), rollback_result=result)
                run.update(status="rolled_back", rolled_back_at=_now(), rollback_result=result)
            else:
                manifest.update(status="rollback_verification_failed", actual_sha256=actual_hash,
                                expected_sha256=expected_hash, rollback_result=result)
                run.update(status="rollback_verification_failed", rollback_result=result,
                           rollback_actual_sha256=actual_hash, rollback_expected_sha256=expected_hash)
            _atomic_json(manifest_path, manifest)
            _atomic_json(run_path, run)


def commit_run(run_id: str, import_dir: Path, testcases_dir: Path, runs_dir: Path, snapshots_dir: Path,
               project_root: Path, idempotency_key: str = "", decisions: list[dict] | None = None,
               policy: str = "skip-conflict") -> dict:
    with _commit_lock(runs_dir, run_id):
        _recover_interrupted_commits(snapshots_dir, project_root, runs_dir)
        run = load_run(runs_dir, run_id)
        canonical_decisions, request_fingerprint = _decisions_fingerprint(decisions)
        if run.get("status") == "committed" and idempotency_key and run.get("idempotency_key") == idempotency_key:
            if run.get("request_fingerprint") != request_fingerprint:
                raise ImportRunError(
                    "같은 idempotency_key가 다른 commit 결정과 함께 사용되었습니다",
                    "IDEMPOTENCY_CONFLICT",
                )
            return {"run_id": run_id, "status": "committed", "snapshot_id": run["snapshot_id"],
                    **run["result"], "replayed": True}
        if run.get("status") == "committed":
            raise ImportRunError("이미 커밋된 run", "ALREADY_COMMITTED")
        if run.get("status") not in {"preview", "preview_ready"}:
            raise ImportRunError("커밋할 수 없는 run 상태", "INVALID_RUN_STATE")
        _apply_conflict_decisions(run, decisions or [], policy=policy)
        run["decisions"] = canonical_decisions
        run["request_fingerprint"] = request_fingerprint
        _atomic_json(runs_dir / f"{run_id}.json", run)
        for source in run.get("sources", []):
            path = _resolve_file(import_dir, source["file_id"])
            if file_sha256(path) != source["file_sha256"]:
                raise ImportRunError(f"Preview 이후 원본 Excel 변경: {path.name}", "SOURCE_CHANGED")
        if _tree_hash(testcases_dir) != run.get("testcases_sha256"):
            raise ImportRunError("Preview 이후 테스트케이스가 변경됨", "TARGET_CHANGED")

        existing = load_existing_testcases(testcases_dir)
        rows = [r for r in run.get("rows", [])
                if r.get("status") in {"added", "updated"}
                or (r.get("status") == "conflict" and r.get("decision") == "overwrite")]
        created = sum(row.get("status") == "added" for row in rows)
        updated = sum(row.get("status") == "updated" for row in rows)
        snap_id = f"snap_{run_id.removeprefix('run_')}_{uuid.uuid4().hex[:6]}"
        snapshot_dir = _safe_child(snapshots_dir, snap_id)
        backup_dir = snapshot_dir / "backup"
        snapshot_dir.mkdir(parents=True, exist_ok=False)
        manifest = {"snapshot_id": snap_id, "run_id": run_id, "created_at": _now(), "status": "prepared", "entries": []}

        # Record every path that can change, including old paths removed by rename.
        planned: list[tuple[dict, Path, str]] = []
        affected: dict[str, Path] = {}
        for row in rows:
            target = _target_for(row, testcases_dir)
            planned.append((row, target, _render(row)))
            affected[str(target)] = target
            old = existing.get(str(row["tc_id"]), {}).get("path")
            if old is not None and Path(old).resolve() != target.resolve():
                affected[str(Path(old).resolve())] = Path(old).resolve()
        for target in affected.values():
            rel = target.resolve().relative_to(project_root.resolve()).as_posix()
            entry = {"target": rel, "before_exists": target.exists()}
            if any(planned_target.resolve() == target.resolve() for _, planned_target, _ in planned):
                temp_name = f".{target.name}.{run_id}.tmp"
                entry["temp"] = target.with_name(temp_name).relative_to(project_root).as_posix()
            if target.exists():
                backup_rel = rel
                backup = backup_dir / backup_rel
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
                entry.update(backup=f"backup/{backup_rel}", before_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
            manifest["entries"].append(entry)

        rendered_by_target = {
            target.resolve(): content.encode("utf-8") for _, target, content in planned
        }
        for entry in manifest["entries"]:
            target = _safe_child(project_root, entry["target"])
            rendered = rendered_by_target.get(target.resolve())
            entry["after_exists"] = rendered is not None
            entry["after_sha256"] = hashlib.sha256(rendered).hexdigest() if rendered is not None else None
        _atomic_json(snapshot_dir / "manifest.json", manifest)

        try:
            # Write-ahead journal transition must be durable before the first
            # testcase mutation so a process crash is recoverable on re-entry.
            manifest["status"] = "applying"
            _atomic_json(snapshot_dir / "manifest.json", manifest)
            for row, target, content in planned:
                manifest["next_target"] = target.relative_to(project_root).as_posix()
                _atomic_json(snapshot_dir / "manifest.json", manifest)
                target.parent.mkdir(parents=True, exist_ok=True)
                entry = next(item for item in manifest["entries"] if item["target"] == target.relative_to(project_root).as_posix())
                tmp_path = _safe_child(project_root, entry["temp"])
                fd = os.open(tmp_path, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as stream:
                        stream.write(content)
                        stream.flush()
                        os.fsync(stream.fileno())
                    _replace_file(tmp_path, target)
                finally:
                    tmp_path.unlink(missing_ok=True)
                old = existing.get(str(row["tc_id"]), {}).get("path")
                if old is not None and Path(old).resolve() != target.resolve():
                    Path(old).unlink(missing_ok=True)
                manifest["last_target"] = target.relative_to(project_root).as_posix()
                _atomic_json(snapshot_dir / "manifest.json", manifest)
        except Exception as exc:
            try:
                _preflight_interrupted_recovery(manifest, project_root, snapshot_dir)
                recovery = _restore_manifest(manifest, project_root, snapshot_dir)
            except ImportRunError as recovery_exc:
                manifest.update(status="recovery_conflict", error=str(recovery_exc),
                                error_code=recovery_exc.code)
                _atomic_json(snapshot_dir / "manifest.json", manifest)
                raise recovery_exc from exc
            manifest.update(status="recovered", error=str(exc), recovery=recovery)
            _atomic_json(snapshot_dir / "manifest.json", manifest)
            raise ImportRunError(f"커밋 실패 후 자동 복구됨: {exc}", "COMMIT_RECOVERED") from exc

        committed_hash = _tree_hash(testcases_dir)
        for entry in manifest["entries"]:
            target = _safe_child(project_root, entry["target"])
            entry["after_exists"] = target.exists()
            entry["after_sha256"] = (hashlib.sha256(target.read_bytes()).hexdigest()
                                      if target.exists() else None)
        result = {"committed": len(rows), "created": created, "updated": updated,
                  "skipped": len(run.get("rows", [])) - len(rows)}
        manifest.update(status="committed", committed_at=_now(), result=result,
                        idempotency_key=idempotency_key or None, decisions=canonical_decisions,
                        request_fingerprint=request_fingerprint,
                        committed_testcases_sha256=committed_hash)
        manifest.pop("last_target", None)
        manifest.pop("next_target", None)
        _atomic_json(snapshot_dir / "manifest.json", manifest)
        run.update(status="committed", committed_at=_now(), snapshot_id=snap_id,
                   idempotency_key=idempotency_key or None,
                   request_fingerprint=request_fingerprint,
                   committed_testcases_sha256=committed_hash, result=result)
        _atomic_json(runs_dir / f"{run_id}.json", run)
        return {"run_id": run_id, "status": "committed", "snapshot_id": snap_id, **run["result"]}


def rollback_run(run_id: str, runs_dir: Path, snapshots_dir: Path, project_root: Path,
                 testcases_dir: Path | None = None) -> dict:
    with _commit_lock(runs_dir, run_id):
        _recover_interrupted_commits(snapshots_dir, project_root, runs_dir)
        run = load_run(runs_dir, run_id)
        if run.get("status") == "rolled_back":
            return {"run_id": run_id, "status": "rolled_back", "already_rolled_back": True,
                    **run.get("rollback_result", {})}
        if run.get("status") != "committed" or not run.get("snapshot_id"):
            raise ImportRunError("롤백할 수 없는 run 상태", "INVALID_RUN_STATE")
        snapshot_dir = _safe_child(snapshots_dir, run["snapshot_id"])
        manifest_path = snapshot_dir / "manifest.json"
        if not manifest_path.exists():
            raise ImportRunError("스냅샷 manifest 없음", "SNAPSHOT_NOT_FOUND")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        testcase_root = testcases_dir or (project_root / "testcases")
        if _tree_hash(testcase_root) != run.get("committed_testcases_sha256"):
            raise ImportRunError("Commit 이후 테스트케이스가 외부에서 변경됨", "ROLLBACK_CONFLICT")
        _preflight_restore_manifest(manifest, project_root, snapshot_dir)
        for entry in manifest.get("entries", []):
            target = _safe_child(project_root, entry["target"])
            exists = target.exists()
            current_hash = hashlib.sha256(target.read_bytes()).hexdigest() if exists else None
            if exists != entry.get("after_exists") or current_hash != entry.get("after_sha256"):
                raise ImportRunError(f"Rollback 대상 외부 변경: {entry['target']}", "ROLLBACK_CONFLICT")
        manifest.update(status="rolling_back", rollback_started_at=_now())
        _atomic_json(manifest_path, manifest)
        result = _restore_manifest(manifest, project_root, snapshot_dir)
        actual_hash = _tree_hash(testcase_root)
        expected_hash = run.get("testcases_sha256")
        if actual_hash != expected_hash:
            manifest.update(status="rollback_verification_failed", rollback_attempted_at=_now(),
                            expected_sha256=expected_hash, actual_sha256=actual_hash,
                            rollback_result=result)
            _atomic_json(manifest_path, manifest)
            run.update(status="rollback_verification_failed", rollback_result=result,
                       rollback_expected_sha256=expected_hash, rollback_actual_sha256=actual_hash)
            _atomic_json(runs_dir / f"{run_id}.json", run)
            raise ImportRunError("롤백 후 테스트케이스 tree SHA256 불일치",
                                 "ROLLBACK_VERIFICATION_FAILED")
        result["verified"] = True
        manifest.update(status="rolled_back", rolled_back_at=_now(), rollback_result=result)
        _atomic_json(manifest_path, manifest)
        run.update(status="rolled_back", rolled_back_at=_now(), rollback_result=result)
        _atomic_json(runs_dir / f"{run_id}.json", run)
        return {"run_id": run_id, "status": "rolled_back", **result}


def rows_csv(run: dict, skipped_only: bool = False) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([sanitize_csv_cell(value) for value in
                     ["source_file_id", "file", "sheet", "row", "tc_id", "title", "group",
                      "status", "reason_code", "reason"]])
    for row in run.get("rows", []):
        if skipped_only and row.get("status") in {"added", "updated"}:
            continue
        writer.writerow([sanitize_csv_cell(value) for value in
                         [row.get("_source_file_id", ""), row.get("_source_file", ""),
                          row.get("_source_sheet", ""), row.get("_row", ""), row.get("tc_id", ""),
                          row.get("title", ""), row.get("group", ""), row.get("status", ""),
                          row.get("reason_code", ""), row.get("reason", "")]])
    return output.getvalue().encode("utf-8-sig")


def sanitize_csv_cell(value: object) -> str:
    """Neutralize spreadsheet formulas, including whitespace/control prefixes."""
    text = "" if value is None else str(value)
    index = 0
    while index < len(text) and (
        text[index].isspace() or unicodedata.category(text[index]) in {"Cc", "Cf"}
    ):
        index += 1
    candidate = text[index:]
    if candidate.startswith(("=", "+", "-", "@")):
        return "'" + text
    return text
