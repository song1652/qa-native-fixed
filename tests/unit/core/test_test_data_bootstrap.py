"""test_data/ 부트스트랩 템플릿 테스트 (#27).

배경: 실제 입력값 test_data/{프로덕트}.json은 .gitignore 대상이라 새로 클론하면
없다. 함께 추적되는 test_data/{프로덕트}.example.json 템플릿이 생성 테스트가
요구하는 키를 전부 채우는지 고정한다. (예전 config/test_data.json 단일 파일은 폐지)
"""
import json
import re
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[3]
_TEST_DATA_DIR = _ROOT / "test_data"
_GENERATED_DIR = _ROOT / "tests" / "generated"
_PATH_RE = re.compile(r'TEST_DATA_PATH = .*/ "test_data" / "([^"]+)\.json"')
_LEGACY_RE = re.compile(r'"config" / "test_data\.json"')


def _examples() -> list[Path]:
    return sorted(_TEST_DATA_DIR.glob("*.example.json"))


def test_example_files_exist_and_are_valid_json():
    assert _examples(), "test_data/*.example.json 템플릿이 없음"
    for p in _examples():
        json.loads(p.read_text(encoding="utf-8"))


def _key_chains(src: str) -> list[tuple[str, ...]]:
    """`test_data["a"]["b"]` 체인을 ("a","b") 튜플로 뽑는다."""
    return [tuple(re.findall(r'\["([^"]+)"\]', m.group(1)))
            for m in re.finditer(r'(?<![A-Za-z0-9])test_data((?:\["[^"]+"\])+)', src)]


def test_generated_tests_resolve_in_example():
    checked = 0
    for py in sorted(_GENERATED_DIR.rglob("*.py")):
        src = py.read_text(encoding="utf-8")
        rel = py.relative_to(_ROOT)
        assert not _LEGACY_RE.search(src), f"{rel}가 폐지된 config/test_data.json을 읽음"
        m = _PATH_RE.search(src)
        if not m:
            continue
        example = _TEST_DATA_DIR / f"{m.group(1)}.example.json"
        assert example.exists(), f"{rel}가 읽는 {m.group(1)}.json의 템플릿 {example.name}이 없음"
        data = json.loads(example.read_text(encoding="utf-8"))
        for keys in _key_chains(src):
            cur = data
            for k in keys:
                assert isinstance(cur, dict) and k in cur, f"{rel}의 test_data{list(keys)}가 {example.name}에 없음"
                cur = cur[k]
            checked += 1
    if checked == 0:
        pytest.skip("tests/generated/ 에 test_data 참조가 없음 (P63)")


def test_readme_mentions_copy_command():
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")
    assert "cp test_data/" in readme
