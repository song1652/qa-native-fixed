"""대시보드 serve.py 입력 검증 헬퍼.

serve.py는 모듈 최상단에서 백그라운드 스레드를 시작하는 부작용이 있어
테스트에서 직접 import하기 부적합하다. 검증 로직만 이 모듈로 분리해
serve.py와 테스트 양쪽에서 부작용 없이 재사용한다.
"""
from __future__ import annotations

import re


def is_valid_url(url: str) -> bool:
    """URL이 http(s) 스킴으로 시작하는지 검증."""
    return url.startswith(("http://", "https://"))


def is_valid_group_name(name: str) -> bool:
    """그룹명이 영숫자/언더스코어/하이픈만 포함하는지 검증 (경로 탈출 방지)."""
    return bool(re.match(r'^[\w\-]+$', name))


def is_safe_filename(name: str) -> bool:
    """파일명에 상위 디렉토리 접근 패턴이 없는지 검증 (경로 탈출 방지)."""
    return bool(name) and ".." not in name
