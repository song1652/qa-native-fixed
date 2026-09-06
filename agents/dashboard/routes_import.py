"""routes_import.py — ImportRoutesMixin (serve.py Phase-4 분리).

Import Studio 관련 HTTP 핸들러 메서드를 담당하는 Mixin 클래스.
DashboardHandler가 이 Mixin을 상속받아 사용한다.

설계 원칙:
- 이 모듈은 serve.py를 import하지 않는다 (순환 import 방지).
- 경로 상수는 _paths.X 형식으로 참조 (테스트 패치 가능성 보장).
- __init__ 정의 없음 — MRO에서 BaseHTTPRequestHandler.__init__ 사용.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

from _paths import (
    PROJECT_ROOT,
    IMPORT_DIR,
    TESTCASES_DIR,
    IMPORT_SESSIONS_DIR,
    IMPORT_SNAPSHOTS_DIR,
)
from _validators import is_safe_filename
from dash_state import load_json
from dash_excel import _list_excel_sheets, _parse_excel_sheet, _write_tc_files
from dash_http import _read_body, _read_profiles_locked, _update_profiles_locked

# ALLOWED_ORIGIN: serve.py와 동일한 env 소스 — 순환 import 없이 독립 파생
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "http://localhost:8766")


class ImportRoutesMixin:
    """Import Studio GET/POST/DELETE 핸들러 모음.

    DashboardHandler(ImportRoutesMixin, BaseHTTPRequestHandler) 형태로 사용.
    self._serve_bytes / self._serve_json 은 DashboardHandler infra layer가 제공.
    """

    # ── v2 파일·시트 조회 ─────────────────────────────────────────

    def _get_import_files(self):
        """GET /api/import/files — 메타데이터 포함 파일 목록 (S2 확장)."""
        if not IMPORT_DIR.exists():
            # import/ 폴더가 없으면 빈 배열 반환 (FE 오류 방지)
            self._serve_bytes(
                json.dumps({"ok": True, "files": []}, ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8",
            )
            return

        import hashlib as _hashlib
        from _excel_import import get_file_metadata  # type: ignore[import]

        files = []
        for f in sorted(IMPORT_DIR.glob("*.xlsx")):
            file_id = _hashlib.sha256(f.name.encode("utf-8")).hexdigest()[:8]
            try:
                meta = get_file_metadata(f)
            except Exception as exc:
                # 파싱 불가 파일도 목록에는 포함 (sheets 없이)
                meta = {"sheets": [], "size": f.stat().st_size,
                        "modified": "", "error": str(exc)}
            files.append({
                "id":       file_id,
                "name":     f.name,
                "size":     meta.get("size", 0),
                "modified": meta.get("modified", ""),
                "sheets":   meta.get("sheets", []),
                "error":    meta.get("error"),
            })
        self._serve_bytes(
            json.dumps({"ok": True, "files": files}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def _get_import_sheets(self):
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(self.path).query)
        fname = qs.get("file", [""])[0]
        if not is_safe_filename(fname):
            self._serve_bytes(
                b'{"ok":false,"error":"file parameter required"}',
                "application/json; charset=utf-8")
            return
        fpath = IMPORT_DIR / fname
        if not fpath.exists():
            self._serve_bytes(
                json.dumps({"ok": False, "error": f"{fname} not found"},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
            return
        try:
            sheets = _list_excel_sheets(fpath)
            self._serve_bytes(
                json.dumps({"ok": True, "sheets": sheets},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
        except Exception as e:
            self._serve_bytes(
                json.dumps({"ok": False, "error": str(e)},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")

    # ── v1 Excel 변환 (레거시) ────────────────────────────────────

    def _post_import_convert(self):
        import openpyxl
        body = _read_body(self)
        fname = body.get("file", "").strip()
        sheet_names = body.get("sheets", [])
        if not fname or not sheet_names:
            self._serve_bytes(
                b'{"ok":false,"error":"file and sheets required"}',
                "application/json; charset=utf-8")
            return
        if not is_safe_filename(fname):
            self._serve_bytes(
                b'{"ok":false,"error":"invalid file parameter"}',
                "application/json; charset=utf-8")
            return
        fpath = IMPORT_DIR / fname
        if not fpath.exists():
            self._serve_bytes(
                json.dumps({"ok": False, "error": f"{fname} not found"},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
            return
        try:
            wb = openpyxl.load_workbook(str(fpath), data_only=True)
            results = []
            for sn in sheet_names:
                if sn not in wb.sheetnames:
                    results.append({"sheet": sn, "count": 0, "error": "시트 없음"})
                    continue
                cases = _parse_excel_sheet(wb, sn)
                folder_name = re.sub(r'\s+', '_', sn.strip().lower())
                out_dir = TESTCASES_DIR / folder_name
                # 기존 파일 정리
                if out_dir.exists():
                    for old in out_dir.glob("tc_*.md"):
                        old.unlink()
                count = _write_tc_files(cases, out_dir)
                results.append({"sheet": sn, "count": count,
                                "folder": f"testcases/{folder_name}/"})
            wb.close()
            self._serve_bytes(
                json.dumps({"ok": True, "results": results},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")
        except Exception as e:
            self._serve_bytes(
                json.dumps({"ok": False, "error": str(e)},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8")

    # ── Import Studio run-based API (S5-S8) ──────────────────────

    def _import_error_v2(self, exc, default_status: int = 400):
        code = getattr(exc, "code", "IMPORT_ERROR")
        status = {
            "FILE_NOT_FOUND": 404,
            "RUN_NOT_FOUND": 404,
            "SNAPSHOT_NOT_FOUND": 404,
            "ALREADY_COMMITTED": 409,
            "IDEMPOTENCY_CONFLICT": 409,
            "COMMIT_LOCKED": 409,
            "SOURCE_CHANGED": 409,
            "TARGET_CHANGED": 409,
            "UNRESOLVED_CONFLICT": 409,
            "ROLLBACK_CONFLICT": 409,
            "RECOVERY_CONFLICT": 409,
            "PROFILE_NOT_FOUND": 404,
            "PROFILE_EXISTS": 409,
            "PROFILE_STORE_ERROR": 500,
            "RUN_CORRUPT": 500,
            "SNAPSHOT_CORRUPT": 500,
            "COMMIT_RECOVERED": 500,
            "ROLLBACK_VERIFICATION_FAILED": 500,
        }.get(code, default_status)
        self._serve_bytes(
            json.dumps({"ok": False, "error": str(exc), "code": code},
                       ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8", status=status,
        )

    def _post_import_preview_v2(self):
        from _import_commit import ImportRunError, create_preview  # type: ignore[import]

        try:
            run = create_preview(
                _read_body(self), IMPORT_DIR, TESTCASES_DIR, IMPORT_SESSIONS_DIR,
            )
        except ImportRunError as exc:
            self._import_error_v2(exc)
            return
        except Exception as exc:
            self._import_error_v2(
                ImportRunError(f"Excel 파싱 실패: {exc}", "PARSE_FAILED"), 422
            )
            return

        rows = [{
            "source_file_id": row.get("_source_file_id", ""),
            "file_name": row.get("_source_file", ""),
            "sheet_name": row.get("_source_sheet", ""),
            "source_row": row.get("_row", 0),
            "row": row.get("_row", 0),
            "tc_id": row.get("tc_id", ""),
            "title": row.get("title", ""),
            "group": row.get("group", ""),
            "status": row.get("status", ""),
            "reason_code": row.get("reason_code", ""),
            "reason": row.get("reason", ""),
            "excluded": row.get("excluded", False),
            "decision": row.get("decision", "automatic"),
            "before": row.get("before"),
            "after": row.get("after"),
        } for row in run["rows"]]
        self._serve_bytes(
            json.dumps({
                "ok": True,
                "run_id": run["run_id"],
                "session_id": run["run_id"],
                "status": run["status"],
                "sources": run["sources"],
                "summary": run["summary"],
                "rows": rows,
            }, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def _post_import_commit_v2(self):
        from _import_commit import ImportRunError, commit_run  # type: ignore[import]

        body = _read_body(self)
        run_id = str(body.get("run_id") or body.get("session_id") or "").strip()
        idempotency_key = str(body.get("idempotency_key") or "").strip()
        decisions = body.get("decisions", [])
        policy = str(body.get("policy") or "skip-conflict").strip()
        if policy not in {"skip-conflict", "overwrite", "replace-with-snapshot"}:
            policy = "skip-conflict"
        if not isinstance(decisions, list):
            self._import_error_v2(ImportRunError("decisions must be an array", "INVALID_DECISIONS"))
            return
        if len(idempotency_key) > 128:
            self._import_error_v2(ImportRunError("idempotency_key too long", "INVALID_REQUEST"))
            return
        if not run_id:
            self._import_error_v2(ImportRunError("run_id required", "INVALID_REQUEST"))
            return
        try:
            result = commit_run(
                run_id, IMPORT_DIR, TESTCASES_DIR, IMPORT_SESSIONS_DIR,
                IMPORT_SNAPSHOTS_DIR, PROJECT_ROOT, idempotency_key, decisions, policy,
            )
        except ImportRunError as exc:
            self._import_error_v2(exc)
            return
        self._serve_bytes(
            json.dumps({"ok": True, **result}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def _post_import_rollback_v2(self):
        from _import_commit import ImportRunError, rollback_run  # type: ignore[import]

        body = _read_body(self)
        run_id = str(body.get("run_id") or "").strip()
        # Legacy clients know only snapshot_id; resolve it to its owning run.
        if not run_id and body.get("snapshot_id"):
            snap_id = str(body["snapshot_id"])
            if not is_safe_filename(snap_id):
                self._import_error_v2(ImportRunError("invalid snapshot_id", "INVALID_REQUEST"))
                return
            snaps_root = IMPORT_SNAPSHOTS_DIR.resolve()
            manifest = (snaps_root / snap_id / "manifest.json").resolve()
            if not manifest.is_relative_to(snaps_root):
                self._import_error_v2(ImportRunError("invalid snapshot_id", "INVALID_REQUEST"))
                return
            if manifest.exists():
                run_id = str((load_json(manifest) or {}).get("run_id", ""))
        if not run_id:
            self._import_error_v2(ImportRunError("run_id required", "INVALID_REQUEST"))
            return
        try:
            result = rollback_run(
                run_id, IMPORT_SESSIONS_DIR, IMPORT_SNAPSHOTS_DIR, PROJECT_ROOT,
                TESTCASES_DIR,
            )
        except ImportRunError as exc:
            self._import_error_v2(exc)
            return
        self._serve_bytes(
            json.dumps({"ok": True, **result}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def _post_import_run_rollback_v2(self, path: str):
        from _import_commit import ImportRunError, rollback_run  # type: ignore[import]

        run_id = path.removeprefix("/api/import/runs/").removesuffix("/rollback").strip("/")
        try:
            result = rollback_run(
                run_id, IMPORT_SESSIONS_DIR, IMPORT_SNAPSHOTS_DIR, PROJECT_ROOT,
                TESTCASES_DIR,
            )
        except ImportRunError as exc:
            self._import_error_v2(exc)
            return
        self._serve_bytes(
            json.dumps({"ok": True, **result}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def _get_import_run_v2(self, path: str):
        from _import_commit import ImportRunError, load_run, rows_csv  # type: ignore[import]

        relative = path.removeprefix("/api/import/runs/").strip("/")
        skipped_csv = relative.endswith("/skipped.csv")
        run_id = relative.removesuffix("/skipped.csv") if skipped_csv else relative
        try:
            run = load_run(IMPORT_SESSIONS_DIR, run_id)
        except ImportRunError as exc:
            self._import_error_v2(exc)
            return
        if skipped_csv:
            payload = rows_csv(run, skipped_only=True)
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="import_skipped_{run_id}.csv"')
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        # The durable representation is also the result contract. Internal
        # underscore keys retain provenance without leaking filesystem paths.
        public = {**run, "rows": [{
            **{k: v for k, v in row.items() if not k.startswith("_")},
            "file_name": row.get("_source_file", ""),
            "source_file_id": row.get("_source_file_id", ""),
            "sheet_name": row.get("_source_sheet", ""),
            "source_row": row.get("_row", 0),
        } for row in run.get("rows", [])]}
        self._serve_bytes(
            json.dumps({"ok": True, **public}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    # ── 프로필 CRUD ───────────────────────────────────────────────

    def _delete_import_profile_v2(self, profile_id: str):
        from _paths import IMPORT_PROFILES_PATH
        from _import_commit import ImportRunError

        if not is_safe_filename(profile_id):
            self._serve_bytes(b'{"ok":false,"error":"invalid profile id","code":"INVALID_PROFILE_ID"}',
                              "application/json; charset=utf-8", status=400)
            return
        try:
            def mutate(data):
                profiles = data.get("profiles", [])
                remaining = [p for p in profiles if str(p.get("id")) != profile_id]
                if len(remaining) == len(profiles):
                    raise ImportRunError("profile not found", "PROFILE_NOT_FOUND")
                data["profiles"] = remaining
                return profile_id
            _update_profiles_locked(IMPORT_PROFILES_PATH, mutate)
        except ImportRunError as exc:
            self._import_error_v2(exc, 404)
            return
        self._serve_bytes(
            json.dumps({"ok": True, "deleted": profile_id}).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def _put_import_profile_v2(self, profile_id: str):
        from _paths import IMPORT_PROFILES_PATH
        from _import_commit import ImportRunError

        if not is_safe_filename(profile_id):
            self._serve_bytes(b'{"ok":false,"error":"invalid profile id","code":"INVALID_PROFILE_ID"}',
                              "application/json; charset=utf-8", status=400)
            return
        body = _read_body(self)
        if not set(body).intersection({"name", "mappings"}):
            self._serve_bytes(b'{"ok":false,"error":"name or mappings required","code":"INVALID_PROFILE"}',
                              "application/json; charset=utf-8", status=400)
            return
        if "name" in body:
            name = str(body["name"]).strip()
            if not name or len(name) > 50:
                self._serve_bytes(b'{"ok":false,"error":"invalid name","code":"INVALID_PROFILE"}',
                                  "application/json; charset=utf-8", status=400)
                return
        if "mappings" in body:
            if (not isinstance(body["mappings"], dict) or not body["mappings"]
                    or any(not isinstance(key, str) or not isinstance(value, str)
                           for key, value in body["mappings"].items())):
                self._serve_bytes(b'{"ok":false,"error":"invalid mappings","code":"INVALID_PROFILE"}',
                                  "application/json; charset=utf-8", status=400)
                return
        try:
            def mutate(data):
                profile = next((p for p in data.get("profiles", []) if str(p.get("id")) == profile_id), None)
                if profile is None:
                    raise ImportRunError("profile not found", "PROFILE_NOT_FOUND")
                if "name" in body:
                    name = str(body["name"]).strip()
                    if any(p is not profile and p.get("name") == name for p in data["profiles"]):
                        raise ImportRunError("profile name already exists", "PROFILE_EXISTS")
                    profile["name"] = name
                if "mappings" in body:
                    profile["mappings"] = body["mappings"]
                profile["updated_at"] = datetime.now().isoformat()
                return profile
            profile = _update_profiles_locked(IMPORT_PROFILES_PATH, mutate)
        except ImportRunError as exc:
            self._import_error_v2(exc, 404 if exc.code == "PROFILE_NOT_FOUND" else 409)
            return
        self._serve_bytes(
            json.dumps({"ok": True, "profile": profile}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def _get_import_profiles_v2(self):
        from _import_commit import ImportRunError
        from _paths import IMPORT_PROFILES_PATH
        try:
            data = _read_profiles_locked(IMPORT_PROFILES_PATH)
        except ImportRunError as exc:
            self._import_error_v2(exc, 500)
            return
        self._serve_bytes(
            json.dumps({"ok": True, "profiles": data.get("profiles", [])},
                       ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def _post_import_profiles_v2(self):
        import secrets
        from _paths import IMPORT_PROFILES_PATH
        from _import_commit import ImportRunError

        body = _read_body(self)
        name = str(body.get("name", "")).strip()
        mappings = body.get("mappings")
        if (not name or len(name) > 50 or not isinstance(mappings, dict) or not mappings
                or any(not isinstance(key, str) or not isinstance(value, str)
                       for key, value in mappings.items())):
            self._serve_bytes(b'{"ok":false,"error":"invalid name or mappings","code":"INVALID_PROFILE"}',
                              "application/json; charset=utf-8", status=400)
            return
        try:
            def mutate(data):
                profiles = data.setdefault("profiles", [])
                if any(profile.get("name") == name for profile in profiles):
                    raise ImportRunError("profile name already exists", "PROFILE_EXISTS")
                profile = {"id": f"prof_{secrets.token_hex(4)}", "name": name,
                           "mappings": mappings, "created_at": datetime.now().isoformat()}
                profiles.append(profile)
                return profile
            profile = _update_profiles_locked(IMPORT_PROFILES_PATH, mutate)
        except ImportRunError as exc:
            self._import_error_v2(exc, 409)
            return
        self._serve_bytes(
            json.dumps({"ok": True, "id": profile["id"], "profile": profile},
                       ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8", status=201,
        )

    def _post_import_profiles_update(self):
        """POST /api/import/profiles/update — 프로필 이름 또는 매핑 수정."""
        from _paths import IMPORT_PROFILES_PATH
        from _import_commit import ImportRunError

        body = _read_body(self)
        profile_id = body.get("id", "").strip()
        new_name   = body.get("name", "").strip()
        new_mappings = body.get("mappings")

        if not profile_id:
            self._serve_bytes(
                b'{"ok":false,"error":"id required"}',
                "application/json; charset=utf-8",
                status=400,
            )
            return

        # name 검증
        if new_name and len(new_name) > 50:
            self._serve_bytes(
                b'{"ok":false,"error":"name must be 50 characters or fewer"}',
                "application/json; charset=utf-8",
                status=400,
            )
            return

        # mappings 타입 검증
        if new_mappings is not None:
            if not isinstance(new_mappings, dict) or any(
                not isinstance(v, str) for v in new_mappings.values()
            ):
                self._serve_bytes(
                    b'{"ok":false,"error":"mappings values must be strings"}',
                    "application/json; charset=utf-8",
                    status=400,
                )
                return

        try:
            def mutate(data):
                profiles = data.setdefault("profiles", [])
                target = next((p for p in profiles if p.get("id") == profile_id), None)
                if target is None:
                    raise ImportRunError(f"프로필 '{profile_id}' 없음", "PROFILE_NOT_FOUND")
                if new_name and any(
                    p.get("name") == new_name and p.get("id") != profile_id
                    for p in profiles
                ):
                    raise ImportRunError(f"프로필 이름 '{new_name}' 이미 존재", "PROFILE_EXISTS")
                if new_name:
                    target["name"] = new_name
                if new_mappings is not None:
                    target["mappings"] = new_mappings
                target["updated_at"] = datetime.now().isoformat()
                return dict(target)

            updated = _update_profiles_locked(IMPORT_PROFILES_PATH, mutate)
        except ImportRunError as exc:
            self._import_error_v2(exc, 404 if exc.code == "PROFILE_NOT_FOUND" else 409)
            return

        self._serve_bytes(
            json.dumps({"ok": True, "id": profile_id, "profile": updated},
                       ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    def _post_import_profiles_delete(self):
        """POST /api/import/profiles/delete — 프로필 삭제 (DELETE 대안)."""
        from _paths import IMPORT_PROFILES_PATH
        from _import_commit import ImportRunError

        body = _read_body(self)
        profile_id = body.get("id", "").strip()
        if not profile_id:
            self._serve_bytes(
                b'{"ok":false,"error":"id required"}',
                "application/json; charset=utf-8",
                status=400,
            )
            return

        try:
            def mutate(data):
                profiles = data.setdefault("profiles", [])
                remaining = [p for p in profiles if p.get("id") != profile_id]
                if len(remaining) == len(profiles):
                    raise ImportRunError(f"프로필 '{profile_id}' 없음", "PROFILE_NOT_FOUND")
                data["profiles"] = remaining
                return profile_id

            _update_profiles_locked(IMPORT_PROFILES_PATH, mutate)
        except ImportRunError as exc:
            self._import_error_v2(exc, 404)
            return

        self._serve_bytes(
            json.dumps({"ok": True, "deleted": profile_id}, ensure_ascii=False).encode("utf-8"),
            "application/json; charset=utf-8",
        )

    # ── CSV 미리보기 다운로드 ──────────────────────────────────────

    def _get_import_preview_csv(self):
        """GET /api/import/preview/csv?session_id=... — CSV 다운로드."""
        import csv
        import io
        from _import_commit import sanitize_csv_cell
        from urllib.parse import urlparse, parse_qs

        qs = parse_qs(urlparse(self.path).query)
        session_id = qs.get("session_id", [""])[0]

        if not session_id:
            self._serve_bytes(
                b'{"ok":false,"error":"session_id parameter required"}',
                "application/json; charset=utf-8", status=400)
            return

        if not is_safe_filename(session_id):
            self._serve_bytes(
                json.dumps({"ok": False, "error": "invalid session_id"},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8", status=400)
            return

        # 경로 봉쇄 (P66 패턴)
        _sessions_root = IMPORT_SESSIONS_DIR.resolve()
        session_path = (_sessions_root / f"{session_id}.json").resolve()
        if not session_path.is_relative_to(_sessions_root):
            self._serve_bytes(
                b'{"ok":false,"error":"invalid session_id"}',
                "application/json; charset=utf-8", status=400)
            return

        if not session_path.exists():
            self._serve_bytes(
                json.dumps({"ok": False, "error": f"세션 '{session_id}' 없음 또는 만료"},
                           ensure_ascii=False).encode("utf-8"),
                "application/json; charset=utf-8", status=404)
            return

        session_data = load_json(session_path) or {}
        rows = session_data.get("rows", [])

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["row", "tc_id", "title", "group", "status", "reason"])
        for r in rows:
            writer.writerow([sanitize_csv_cell(value) for value in [
                r.get("_row", r.get("row", "")),
                r.get("tc_id", ""),
                r.get("title", ""),
                r.get("group", ""),
                r.get("status", ""),
                r.get("reason", ""),
            ]])

        csv_bytes = buf.getvalue().encode("utf-8")
        fname = f"import_preview_{session_id}.csv"
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{fname}"')
        self.send_header("Access-Control-Allow-Origin", ALLOWED_ORIGIN)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(csv_bytes)))
        self.end_headers()
        self.wfile.write(csv_bytes)
