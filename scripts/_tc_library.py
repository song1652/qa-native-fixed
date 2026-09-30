"""TC 라이브러리 저장소 — state/tc_library/{suite}/ (PRD §5, F5.2~F5.4, F5.11, F6.7).

파일 구성:
  cases.json             {"suite", "sheets": [...], "cases": [...]}  ← update_state 원자 쓰기
  history.jsonl          변경 1건 = 1줄 (append 전용)
  template.xlsx          가져온 원본의 사본 (내보내기 템플릿)
  template_profile.json  시트별 TemplateProfile
"""
from __future__ import annotations

import json
import secrets
import shutil
from pathlib import Path

import _paths
from _state import read_state, update_state
from _tc_model import EDITABLE_FIELDS, next_case_id, now_iso, validate_case
from _tc_template import TemplateProfile
from _validators import is_valid_group_name


class LibraryError(Exception):
    def __init__(self, message: str, code: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


class RevConflict(LibraryError):
    def __init__(self, server_case: dict):
        super().__init__("다른 곳에서 먼저 바뀌었습니다", "REV_CONFLICT", 409)
        self.server_case = server_case


def suite_dir(suite: str) -> Path:
    if not suite or suite.startswith("_") or not is_valid_group_name(suite):
        raise LibraryError(f"스위트 이름이 올바르지 않습니다: {suite!r}", "INVALID_SUITE")
    return _paths.TC_LIBRARY_DIR / suite


def _cases_path(suite: str) -> Path:
    return suite_dir(suite) / "cases.json"


def _history_path(suite: str) -> Path:
    return suite_dir(suite) / "history.jsonl"


def list_suites() -> list[dict]:
    root = _paths.TC_LIBRARY_DIR
    if not root.exists():
        return []
    suites = []
    for d in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")):
        data = read_state(d / "cases.json")
        live = [c for c in data.get("cases", []) if not c.get("deleted")]
        suites.append({"suite": d.name, "sheets": data.get("sheets", []), "count": len(live)})
    return suites


def load_cases(suite: str, *, include_deleted: bool = False) -> list[dict]:
    cases = read_state(_cases_path(suite)).get("cases", [])
    return cases if include_deleted else [c for c in cases if not c.get("deleted")]


def load_profiles(suite: str) -> dict[str, TemplateProfile]:
    path = suite_dir(suite) / "template_profile.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {name: TemplateProfile.from_dict(p) for name, p in raw.items()}


def get_case(suite: str, case_id: str) -> dict:
    for case in load_cases(suite, include_deleted=True):
        if case["case_id"] == case_id:
            return case
    raise LibraryError(f"케이스가 없습니다: {case_id}", "CASE_NOT_FOUND", 404)


def _entry(case_id: str, field: str, before, after, actor: str, kind: str = "edit") -> dict:
    return {"history_id": "h_" + secrets.token_hex(6), "case_id": case_id, "field": field,
            "before": before, "after": after, "actor": actor, "kind": kind, "at": now_iso()}


def _append_history(suite: str, entries: list[dict]) -> None:
    if not entries:
        return
    path = _history_path(suite)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _paths._file_lock(path.with_suffix(".lock"), path):
        with path.open("a", encoding="utf-8") as fh:
            for entry in entries:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _apply(case: dict, changes: dict, actor: str) -> list[dict]:
    entries = []
    for field, value in changes.items():
        if field not in EDITABLE_FIELDS:
            raise LibraryError(f"수정할 수 없는 필드입니다: {field}", "FIELD_NOT_EDITABLE")
        if case.get(field) != value:
            entries.append(_entry(case["case_id"], field, case.get(field), value, actor))
            case[field] = value
    if entries:
        case["rev"] += 1
        case["updated_at"] = now_iso()
    return entries


def _find(data: dict, case_id: str, *, deleted: bool = False) -> dict:
    for case in data.get("cases", []):
        if case["case_id"] == case_id and bool(case.get("deleted")) == deleted:
            return case
    raise LibraryError(f"케이스가 없습니다: {case_id}", "CASE_NOT_FOUND", 404)


def save_template(suite: str, xlsx_path: Path, profiles: dict[str, TemplateProfile]) -> None:
    target = suite_dir(suite)
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(xlsx_path, target / "template.xlsx")
    (target / "template_profile.json").write_text(
        json.dumps({k: v.to_dict() for k, v in profiles.items()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def import_cases(suite: str, sheets: list[str], incoming: list[dict], actor: str) -> dict:
    """case_id가 같으면 갱신, 없으면 추가 (F6.7). 같은 내용이면 건드리지 않는다."""
    summary = {"created": 0, "updated": 0, "unchanged": 0}
    history: list[dict] = []

    def mutate(data: dict) -> dict:
        data.setdefault("suite", suite)
        data["sheets"] = list(dict.fromkeys(data.get("sheets", []) + sheets))
        cases = data.setdefault("cases", [])
        by_id = {c["case_id"]: c for c in cases}
        for new in incoming:
            old = by_id.get(new["case_id"])
            if old is None:
                cases.append(new)
                by_id[new["case_id"]] = new
                history.append(_entry(new["case_id"], "*", None, "import", actor, "create"))
                summary["created"] += 1
                continue
            changes = {f: new[f] for f in EDITABLE_FIELDS if f != "status" and old.get(f) != new[f]}
            if old.get("deleted"):
                old["deleted"] = False
                changes.setdefault("status", old["status"])
            if changes:
                history.extend(_apply(old, changes, actor))
                summary["updated"] += 1
            else:
                summary["unchanged"] += 1
        return data

    update_state(_cases_path(suite), mutate)
    _append_history(suite, history)
    return summary


def patch_case(suite: str, case_id: str, base_rev: int, changes: dict, actor: str) -> dict:
    out: dict = {}

    def mutate(data: dict) -> dict:
        case = _find(data, case_id)
        if case["rev"] != base_rev:
            raise RevConflict(dict(case))
        out["entries"] = _apply(case, changes, actor)
        out["case"] = dict(case)
        return data

    update_state(_cases_path(suite), mutate)
    _append_history(suite, out["entries"])
    return out["case"]


def bulk_patch(suite: str, items: list[dict], changes: dict, actor: str) -> dict:
    """rev가 맞는 케이스만 바꾸고 나머지는 conflicts로 돌려준다 (피드백 #15)."""
    result: dict = {"updated": [], "conflicts": []}
    history: list[dict] = []

    def mutate(data: dict) -> dict:
        for item in items:
            case = _find(data, item["case_id"])
            if case["rev"] != item["rev"]:
                result["conflicts"].append(dict(case))
                continue
            history.extend(_apply(case, changes, actor))
            result["updated"].append(case["case_id"])
        return data

    update_state(_cases_path(suite), mutate)
    _append_history(suite, history)
    return result


def _prefix_for(cases: list[dict], sheet: str) -> str:
    for case in cases:
        if case["sheet"] == sheet and "_" in case["case_id"]:
            return case["case_id"].rsplit("_", 1)[0]
    return "TC"


def create_case(suite: str, fields: dict, actor: str, *, after: str | None = None) -> dict:
    from _tc_model import new_case

    out: dict = {}

    def mutate(data: dict) -> dict:
        cases = data.setdefault("cases", [])
        sheet = fields.get("sheet") or (data.get("sheets") or [""])[0]
        case_id = next_case_id(_prefix_for(cases, sheet), {c["case_id"] for c in cases})
        base = {k: v for k, v in fields.items() if k in EDITABLE_FIELDS or k == "source_refs"}
        base.update(case_id=case_id, sheet=sheet, status="draft")
        case = new_case(**base)
        index = next((i + 1 for i, c in enumerate(cases) if c["case_id"] == after), len(cases))
        cases.insert(index, case)
        out["case"] = dict(case)
        return data

    update_state(_cases_path(suite), mutate)
    _append_history(suite, [_entry(out["case"]["case_id"], "*", None, "create", actor, "create")])
    return out["case"]


def duplicate_case(suite: str, case_id: str, actor: str) -> dict:
    source = get_case(suite, case_id)
    fields = {f: source[f] for f in EDITABLE_FIELDS}
    fields["source_refs"] = list(source.get("source_refs", []))
    created = create_case(suite, fields, actor, after=case_id)
    return created


def delete_cases(suite: str, items: list[dict], actor: str) -> dict:
    result: dict = {"deleted": [], "conflicts": []}
    history: list[dict] = []

    def mutate(data: dict) -> dict:
        for item in items:
            case = _find(data, item["case_id"])
            if case["rev"] != item["rev"]:
                result["conflicts"].append(dict(case))
                continue
            case["deleted"] = True
            case["rev"] += 1
            case["updated_at"] = now_iso()
            history.append(_entry(case["case_id"], "deleted", False, True, actor, "delete"))
            result["deleted"].append(case["case_id"])
        return data

    update_state(_cases_path(suite), mutate)
    _append_history(suite, history)
    return result


def restore_case(suite: str, case_id: str, actor: str) -> dict:
    out: dict = {}

    def mutate(data: dict) -> dict:
        case = _find(data, case_id, deleted=True)
        case["deleted"] = False
        case["rev"] += 1
        case["updated_at"] = now_iso()
        out["case"] = dict(case)
        return data

    update_state(_cases_path(suite), mutate)
    _append_history(suite, [_entry(case_id, "deleted", True, False, actor, "restore")])
    return out["case"]


def history(suite: str, case_id: str) -> list[dict]:
    path = _history_path(suite)
    if not path.exists():
        return []
    entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return [e for e in reversed(entries) if e["case_id"] == case_id]


def revert(suite: str, case_id: str, history_id: str, base_rev: int, actor: str) -> dict:
    entry = next((e for e in history(suite, case_id) if e["history_id"] == history_id), None)
    if entry is None or entry["kind"] != "edit":
        raise LibraryError("되돌릴 수 없는 이력입니다", "HISTORY_NOT_REVERTIBLE")
    return patch_case(suite, case_id, base_rev, {entry["field"]: entry["before"]}, actor)
