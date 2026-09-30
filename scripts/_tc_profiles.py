"""작성 프로필 — 생성 규칙 묶음 (PRD F3). state/tc_library/_profiles.json"""
from __future__ import annotations

import _paths
from _state import read_state, update_state
from _tc_library import LibraryError
from _tc_model import now_iso

DEFAULT_PROFILE = {
    "name": "기본",
    "coverage": {"positive": 1, "negative": 1, "validation_if_input": 1},
    "rules": [
        "기능마다 정상 케이스 1개 이상, 예외/부정 케이스 1개 이상을 만든다",
        "입력 필드가 있으면 유효성 케이스를 1개 이상 만든다",
        "코호트·날짜 조건(D+4~D+6 등)은 조건마다 행을 나눈다",
        "P0 핵심 흐름 / P1 주요 기능 / P2 보조 기능 / P3 엣지 케이스",
        "AUTO: 브라우저로 자동화할 수 있으면 Y-web, 앱 자동화가 필요하면 Y-app, 사람만 확인할 수 있으면 N",
        "Step은 한 줄에 한 동작, Expected는 결과 한 문장 + 화면 문구는 '- ' 불릿",
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
