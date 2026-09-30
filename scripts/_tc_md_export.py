"""TC 라이브러리 → 파이프라인용 testcases/{group}/tc_*.md (PRD F7, 로드맵 M4~M6).

미리보기·커밋·롤백은 Import Studio(_import_commit)를 그대로 쓴다. 이 모듈은 다음만 한다:
- 대상 판정 퍼널: 전체 → AUTO=Y-web → 승인 → 추정 문구·검증 오류 없음 → 그룹 매핑됨
- 라이브러리 가지(시트 › 대분류 › 중분류 › 소분류) → pages.json 그룹 + tc_id 접두어 매핑 (가장 긴 접두 일치)
- case_id → md tc_id 고정 배정 (다시 내보내도 같은 파일을 갱신)
- 드리프트: 마지막으로 내보낸 뒤 testcases/ 파일을 사람이 직접 고쳤으면 충돌(FILE_DRIFT)로 올린다

state/tc_library/{suite}/md_export.json
  {"groups": [{"path": [시트, 대, 중, 소], "group": "yafit_invite", "code": "YFI"}],
   "ids": {case_id: tc_id}, "exported": {tc_id: 파일 sha256}}
"""
from __future__ import annotations

import hashlib
import json
import re

import _paths
from _import_commit import _atomic_json, _target_for, commit_run, create_preview_from_rows, load_run, rollback_run
from _import_validator import load_existing_testcases
from _state import read_state, update_state
from _tc_library import LibraryError, load_cases, suite_dir, with_issues
from _tc_model import format_steps, join_expected
from _tc_review import classify

PRIORITY_MAP = {"P0": "very_high", "P1": "high", "P2": "medium", "P3": "low"}
_GROUP = re.compile(r"[A-Za-z0-9_-]+")
_CODE = re.compile(r"[A-Z][A-Z0-9]{1,7}")


def _config_path(suite: str):
    return suite_dir(suite) / "md_export.json"


def load_config(suite: str) -> dict:
    cfg = read_state(_config_path(suite))
    return {"groups": cfg.get("groups", []), "ids": cfg.get("ids", {}), "exported": cfg.get("exported", {})}


def _pages() -> dict:
    try:
        data = json.loads(_paths.PAGES_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {k: v for k, v in data.items() if not k.startswith("_")}


def save_group(suite: str, path: list[str], group: str, code: str) -> dict:
    """가지 → 그룹 매핑 추가·교체. 그룹은 pages.json에 있어야 한다 (URL이 없으면 파이프라인이 못 돈다)."""
    path = [p for p in path if p]
    if len(path) < 2:
        raise LibraryError("시트와 대분류까지 고르세요", "INVALID_MD_GROUP")
    if not _GROUP.fullmatch(group or "") or group not in _pages():
        raise LibraryError(f"config/pages.json에 없는 그룹입니다: {group}. 페이지 URL 관리에서 먼저 추가하세요",
                           "GROUP_NOT_IN_PAGES")
    if not _CODE.fullmatch(code or ""):
        raise LibraryError("tc_id 접두어는 영문 대문자로 시작하는 2~8자입니다", "INVALID_MD_CODE")

    def mutate(cfg: dict) -> dict:
        groups = [g for g in cfg.get("groups", []) if g["path"] != path]
        if any(g["code"] == code and g["group"] != group for g in groups):
            raise LibraryError(f"접두어 {code}는 다른 그룹이 쓰고 있습니다", "INVALID_MD_CODE")
        return {**cfg, "groups": groups + [{"path": path, "group": group, "code": code}]}

    update_state(_config_path(suite), mutate)
    return load_config(suite)


def _keys(case: dict) -> list[str]:
    return [case["sheet"], *[p for p in case["path"] if p]]


def group_for(case: dict, groups: list[dict]) -> dict | None:
    keys = _keys(case)
    hits = [g for g in groups if keys[: len(g["path"])] == g["path"]]
    return max(hits, key=lambda g: len(g["path"])) if hits else None


def eligibility(suite: str) -> dict:
    """퍼널·가지별 매핑 상태·제외 이유·드리프트 파일 (원격 호출 없음)."""
    cfg = load_config(suite)
    cases = [with_issues(c) for c in load_cases(suite)]
    web = [c for c in cases if c["auto"] == "Y-web"]
    approved = [c for c in web if c["status"] == "approved"]
    clean = [c for c in approved if not c["has_error"] and all(b["verified"] for b in c["bullets"])]
    mapped = [c for c in clean if group_for(c, cfg["groups"])]
    excluded = []
    for c in web:
        if c["status"] != "approved":
            excluded.append({"case_id": c["case_id"], "feature": c["feature"], "reason": "미승인"})
        elif c["has_error"]:
            excluded.append({"case_id": c["case_id"], "feature": c["feature"], "reason": "검증 오류"})
        elif not all(b["verified"] for b in c["bullets"]):
            est = next(b["text"] for b in c["bullets"] if not b["verified"])
            excluded.append({"case_id": c["case_id"], "feature": c["feature"], "reason": f'추정 문구 "{est}"'})
        elif not group_for(c, cfg["groups"]):
            excluded.append({"case_id": c["case_id"], "feature": c["feature"], "reason": "그룹 매핑 없음"})
    branches: dict[tuple, dict] = {}
    for c in clean:
        key = tuple(_keys(c)[:3])
        g = group_for(c, cfg["groups"])
        item = branches.setdefault(key, {"path": list(key), "group": g["group"] if g else "",
                                         "code": g["code"] if g else "", "count": 0})
        item["count"] += 1
    return {
        "funnel": [{"label": "라이브러리 전체", "count": len(cases)}, {"label": "AUTO = Y-web", "count": len(web)},
                   {"label": "승인됨", "count": len(approved)}, {"label": "추정 문구·검증 오류 없음", "count": len(clean)},
                   {"label": "pages.json 그룹 매핑됨", "count": len(mapped)}],
        "branches": sorted(branches.values(), key=lambda b: b["path"]),
        "groups": cfg["groups"], "pages": sorted(_pages()), "excluded": excluded,
        "drifted": drifted_files(suite),
    }


def _file_sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def drifted_files(suite: str) -> list[dict]:
    cfg = load_config(suite)
    existing = load_existing_testcases(_paths.TESTCASES_DIR)
    out = []
    for tc_id, sha in cfg["exported"].items():
        entry = existing.get(tc_id)
        if entry and _file_sha(entry["path"]) != sha:
            out.append({"tc_id": tc_id, "file": f"{entry['group']}/{entry['path'].name}"})
    return out


def _allocate_ids(suite: str, cases: list[dict], groups: list[dict]) -> dict[str, str]:
    """case_id → tc_id ("{code}_{NN}"). 한번 배정한 번호는 유지하고, 새 번호는 기존 파일과도 겹치지 않게 한다."""
    existing = set(load_existing_testcases(_paths.TESTCASES_DIR))

    def mutate(cfg: dict) -> dict:
        ids = dict(cfg.get("ids", {}))
        used = set(ids.values()) | existing
        for case in cases:
            if case["case_id"] in ids:
                continue
            code = group_for(case, groups)["code"]
            n = 1 + max([int(m.group(1)) for i in used if (m := re.fullmatch(rf"{code}_(\d+)", i))] + [0])
            ids[case["case_id"]] = f"{code}_{n:02d}"
            used.add(ids[case["case_id"]])
        return {**cfg, "ids": ids}

    return update_state(_config_path(suite), mutate)["ids"]


def build_rows(suite: str) -> list[dict]:
    """대상 케이스 → Import Studio 행 (파일 쓰기 전)."""
    cfg = load_config(suite)
    cases = [c for c in (with_issues(c) for c in load_cases(suite))
             if c["auto"] == "Y-web" and c["status"] == "approved" and not c["has_error"]
             and all(b["verified"] for b in c["bullets"]) and group_for(c, cfg["groups"])]
    ids = _allocate_ids(suite, cases, cfg["groups"])
    rows = []
    for n, case in enumerate(cases, 1):
        tags = [{"positive": "positive", "negative": "negative", "validation": "validation"}[classify(case)]]
        if case["bullets"]:
            tags.append("content")
        rows.append({
            "tc_id": ids[case["case_id"]], "title": case["feature"], "precondition": case["precondition"],
            "steps": format_steps(case["steps"]), "expected": join_expected(case["expected"], case["bullets"]),
            "priority": PRIORITY_MAP.get(case["priority"], "medium"), "tags": tags,
            "group": group_for(case, cfg["groups"])["group"], "source_ref": f"tc-library:{suite}/{case['case_id']}",
            "case_id": case["case_id"], "_source_sheet": "tc_library", "_row": n,
        })
    return rows


def preview(suite: str) -> dict:
    rows = build_rows(suite)
    if not rows:
        raise LibraryError("내보낼 케이스가 없습니다. 대상 조건을 확인하세요", "NOTHING_TO_EXPORT")
    run = create_preview_from_rows(rows, {"kind": "tc_library", "suite": suite},
                                   _paths.TESTCASES_DIR, _paths.IMPORT_SESSIONS_DIR)
    drift = {d["tc_id"] for d in drifted_files(suite)}
    for row in run["rows"]:
        if row["tc_id"] in drift and row.get("status") in ("updated", "same"):
            row.update(status="conflict", reason="마지막 내보내기 이후 파일을 직접 고쳤습니다",
                       reason_code="FILE_DRIFT", excluded=False, decision="pending")
    run["summary"] = {s: sum(r.get("status") == s for r in run["rows"]) for s in run["summary"]}
    run["tc_library_suite"] = suite
    _atomic_json(_paths.IMPORT_SESSIONS_DIR / f"{run['run_id']}.json", run)
    return run


def commit(suite: str, run_id: str, skip_tc_ids: list[str]) -> dict:
    """충돌 중 skip_tc_ids는 건너뛰고 나머지 충돌은 라이브러리 값으로 덮어쓴다."""
    run = load_run(_paths.IMPORT_SESSIONS_DIR, run_id)
    if run.get("tc_library_suite") != suite:
        raise LibraryError("이 스위트의 md 미리보기가 아닙니다", "INVALID_RUN")
    conflicts = {r["tc_id"]: r for r in run["rows"] if r.get("status") == "conflict"}
    decisions = [{"action": "exclude", "file_id": suite, "sheet_name": "tc_library",
                  "source_row": conflicts[t]["_row"], "tc_id": t} for t in skip_tc_ids if t in conflicts]
    before = load_config(suite)["exported"]
    result = commit_run(run_id, _paths.IMPORT_DIR, _paths.TESTCASES_DIR, _paths.IMPORT_SESSIONS_DIR,
                        _paths.IMPORT_SNAPSHOTS_DIR, _paths.PROJECT_ROOT, "", decisions, policy="overwrite")
    written = [r for r in load_run(_paths.IMPORT_SESSIONS_DIR, run_id)["rows"] if not r.get("excluded")
               and (r.get("status") in ("added", "updated") or r.get("decision") == "overwrite")]

    def mutate(cfg: dict) -> dict:
        exported = dict(cfg.get("exported", {}))
        for row in written:
            target = _target_for(row, _paths.TESTCASES_DIR)
            if target.exists():
                exported[row["tc_id"]] = _file_sha(target)
        # 롤백하면 이 커밋 전의 "마지막 내보내기" 상태로 되돌린다
        return {**cfg, "exported": exported, "before_commit": {**cfg.get("before_commit", {}), run_id: before}}

    update_state(_config_path(suite), mutate)
    return result


def rollback(suite: str, run_id: str) -> dict:
    run = load_run(_paths.IMPORT_SESSIONS_DIR, run_id)
    if run.get("tc_library_suite") != suite:
        raise LibraryError("이 스위트의 md 미리보기가 아닙니다", "INVALID_RUN")
    result = rollback_run(run_id, _paths.IMPORT_SESSIONS_DIR, _paths.IMPORT_SNAPSHOTS_DIR,
                          _paths.PROJECT_ROOT, _paths.TESTCASES_DIR)

    def mutate(cfg: dict) -> dict:
        saved = dict(cfg.get("before_commit", {}))
        exported = saved.pop(run_id, cfg.get("exported", {}))
        return {**cfg, "exported": exported, "before_commit": saved}

    update_state(_config_path(suite), mutate)
    return result
