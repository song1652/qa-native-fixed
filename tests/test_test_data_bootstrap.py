"""config/test_data.json 부트스트랩 템플릿 테스트 (#27).

배경: config/test_data.json은 .gitignore 대상인데 .example 템플릿이
없어서, 새로 클론하면 tests/generated/의 생성 테스트 6개가 전부
FileNotFoundError/KeyError로 깨졌다. config/test_data.example.json을
추가했으니, 그 템플릿이 실제로 생성 테스트가 요구하는 키를 전부
채우는지 고정한다.
"""
import json
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_EXAMPLE_PATH = _ROOT / "config" / "test_data.example.json"
_GENERATED_DIR = _ROOT / "tests" / "generated"


def test_example_file_exists():
    assert _EXAMPLE_PATH.exists(), "config/test_data.example.json이 없음"


def test_example_is_valid_json():
    json.loads(_EXAMPLE_PATH.read_text(encoding="utf-8"))


def _extract_data_key_paths(py_source: str) -> list[tuple[str, ...]]:
    """`data["a"]["b"]["c"]` 형태의 체인을 ("a","b","c") 튜플로 뽑는다."""
    paths = []
    for m in re.finditer(r'data((?:\["[^"]+"\])+)', py_source):
        keys = tuple(re.findall(r'\["([^"]+)"\]', m.group(1)))
        if keys not in paths:
            paths.append(keys)
    return paths


def _resolve(data: dict, keys: tuple[str, ...]):
    cur = data
    for k in keys:
        cur = cur[k]  # KeyError면 pytest가 그대로 실패 이유로 보여줌
    return cur


class TestExampleCoversGeneratedTests:
    """tests/generated/ 아래 생성 테스트가 실제로 참조하는 키가 example에 전부 있는지."""

    def test_generated_tests_reference_test_data(self):
        """전제 확인: 이 테스트가 의미 있으려면 실제로 참조하는 파일이 있어야 한다."""
        files_using_test_data = [
            p for p in _GENERATED_DIR.rglob("*.py")
            if "TEST_DATA_PATH" in p.read_text(encoding="utf-8")
        ]
        assert files_using_test_data, (
            "TEST_DATA_PATH를 쓰는 생성 테스트가 하나도 없음 — "
            "이 전제가 깨지면 아래 커버리지 테스트가 공허하게 통과한다."
        )

    def test_all_referenced_keys_resolve_in_example(self):
        example = json.loads(_EXAMPLE_PATH.read_text(encoding="utf-8"))
        checked = 0
        for py_file in sorted(_GENERATED_DIR.rglob("*.py")):
            src = py_file.read_text(encoding="utf-8")
            if "TEST_DATA_PATH" not in src:
                continue
            for keys in _extract_data_key_paths(src):
                checked += 1
                try:
                    _resolve(example, keys)
                except KeyError as e:
                    raise AssertionError(
                        f"{py_file.relative_to(_ROOT)}가 참조하는 "
                        f"data{''.join(f'[{k!r}]' for k in keys)}가 "
                        f"config/test_data.example.json에 없음 (missing: {e})"
                    )
        assert checked > 0


class TestReadmeDocumentsBootstrap:
    """README 셋업 절차에 복사 안내가 실제로 있는지."""

    def test_readme_mentions_copy_command(self):
        readme = (_ROOT / "README.md").read_text(encoding="utf-8")
        assert "cp config/test_data.example.json config/test_data.json" in readme
