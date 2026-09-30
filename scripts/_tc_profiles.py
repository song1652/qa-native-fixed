"""작성 프로필 — 생성 규칙 묶음 (PRD F3). state/tc_library/_profiles.json"""
from __future__ import annotations

import _paths
from _state import read_state, update_state
from _tc_library import LibraryError
from _tc_model import now_iso

DEFAULT_PROFILE = {
    "name": "기본",
    "coverage": {"positive": 0, "negative": 0, "validation_if_input": 0},
    "rules": [
        "제공한 정보에 명시된 기능·조건·기대 결과를 기준으로 작성한다. 문서에 없는 동작은 추측하지 않는다",
        "TC 하나에는 하나의 검증 목적을 담고, 중복 케이스는 합친다",
        "조건에 따라 결과가 달라진다고 명시된 경우에만 케이스를 나눈다",
        "Step은 한 줄에 한 동작, Expected는 확인 가능한 결과와 원문 화면 문구로 작성한다",
    ],
    "banned_phrases": ["정상 동작", "정상적으로 노출"],
    "examples": 8,
}
_FIELDS = ("coverage", "rules", "banned_phrases", "examples")


def _path():
    return _paths.TC_LIBRARY_DIR / "_profiles.json"


def list_profiles() -> list[dict]:
    saved = read_state(_path()).get("profiles", [])
    names = {p["name"] for p in saved}
    return ([dict(DEFAULT_PROFILE)] if DEFAULT_PROFILE["name"] not in names else []) + saved


def get_profile(name: str) -> dict:
    for profile in list_profiles():
        if profile["name"] == name:
            return profile
    raise LibraryError(f"작성 프로필이 없습니다: {name}", "PROFILE_NOT_FOUND", 404)


def save_profile(name: str, fields: dict) -> dict:
    name = (name or "").strip()
    if not name or len(name) > 40:
        raise LibraryError("프로필 이름은 1~40자여야 합니다", "INVALID_PROFILE")
    rules = fields.get("rules", DEFAULT_PROFILE["rules"])
    if not isinstance(rules, list) or not all(isinstance(r, str) and r.strip() for r in rules):
        raise LibraryError("규칙은 비어 있지 않은 문자열 목록이어야 합니다", "INVALID_PROFILE")
    profile = {"name": name, **{k: fields.get(k, DEFAULT_PROFILE[k]) for k in _FIELDS},
               "updated_at": now_iso()}

    def mutate(data: dict) -> dict:
        profiles = [p for p in data.get("profiles", []) if p["name"] != name]
        return {"profiles": profiles + [profile]}

    update_state(_path(), mutate)
    return profile
