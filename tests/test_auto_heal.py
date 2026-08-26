"""06_auto_heal.py 단위 테스트.

테스트 대상:
- _insert_import            — import 삽입 위치 (__future__ 앞에 끼어들면 SyntaxError)
- fix_to_have_class_regex   — re.compile 변환 + import re 삽입
- _make_heal_context_mutator — heal_context를 fresh 위에 병합
"""
import importlib.util
import sys
from pathlib import Path

import pytest

# scripts/ 모듈 import 준비
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


@pytest.fixture(scope="module")
def auto_heal():
    """숫자 프리픽스 모듈이라 importlib으로 로드 (main() 실행 안 됨)."""
    spec = importlib.util.spec_from_file_location(
        "auto_heal", str(_SCRIPTS_DIR / "06_auto_heal.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


FUTURE_SRC = '''"""모듈 docstring."""
from __future__ import annotations
from playwright.sync_api import expect


def test_x(page):
    expect(page.locator(".a")).to_have_class(r"active", timeout=5000)
'''


class TestInsertImport:
    """import 삽입 위치 — __future__ 앞에 넣으면 파일이 깨진다."""

    def test_inserted_after_future_import(self, auto_heal):
        out = auto_heal._insert_import(FUTURE_SRC, "import re\n")
        lines = out.splitlines()
        assert lines[1].startswith("from __future__ import")
        assert "import re" in lines[2]

    def test_result_compiles(self, auto_heal):
        """compile까지 통과해야 실제로 고쳐진 것 (ast.parse는 이 규칙을 안 본다)."""
        out = auto_heal._insert_import(FUTURE_SRC, "import re\n")
        compile(out, "t.py", "exec")

    def test_naive_prepend_would_break(self, auto_heal):
        """회귀 감지용: 앞에 그냥 붙이면 SyntaxError가 난다는 사실을 고정."""
        with pytest.raises(SyntaxError):
            compile("import re\n" + FUTURE_SRC, "t.py", "exec")

    def test_plain_file_gets_import_at_top(self, auto_heal):
        src = "from playwright.sync_api import expect\n\n\ndef t(p):\n    pass\n"
        out = auto_heal._insert_import(src, "import re\n")
        assert out.splitlines()[0] == "import re"
        compile(out, "t.py", "exec")

    def test_docstring_only_file(self, auto_heal):
        """docstring 앞에 삽입하면 docstring이 아니게 되므로 뒤에 와야 한다."""
        src = '"""doc."""\n\n\ndef t():\n    pass\n'
        out = auto_heal._insert_import(src, "import re\n")
        assert out.splitlines()[0] == '"""doc."""'
        compile(out, "t.py", "exec")

    def test_unparseable_source_falls_back_without_raising(self, auto_heal):
        """문법이 깨진 소스에도 예외 없이 동작해야 한다 (fallback 경로)."""
        src = "from __future__ import annotations\ndef broken(:\n"
        out = auto_heal._insert_import(src, "import re\n")
        assert "import re" in out


class TestFixToHaveClassRegex:
    """to_have_class(r'...') → re.compile 변환."""

    def test_converts_and_adds_import(self, auto_heal):
        out, changed = auto_heal.fix_to_have_class_regex(FUTURE_SRC, "")
        assert changed
        assert "re.compile" in out
        assert "import re" in out

    def test_future_file_still_compiles(self, auto_heal):
        """754bc64가 고친 실제 버그 — 이 조합에서 파일이 깨졌었다."""
        out, _ = auto_heal.fix_to_have_class_regex(FUTURE_SRC, "")
        compile(out, "t.py", "exec")

    def test_no_change_when_pattern_absent(self, auto_heal):
        src = "def t():\n    assert True\n"
        out, changed = auto_heal.fix_to_have_class_regex(src, "")
        assert not changed
        assert out == src

    def test_does_not_duplicate_existing_import(self, auto_heal):
        src = 'import re\n\n\ndef t(p):\n    p.to_have_class(r"a", 1)\n'
        out, _ = auto_heal.fix_to_have_class_regex(src, "")
        assert out.count("import re") == 1


class TestHealContextMutator:
    """fe26599 — heal_context를 fresh 위에 병합 (동시 변경 보존)."""

    def test_merges_onto_fresh_state(self, auto_heal):
        mutator = auto_heal._make_heal_context_mutator([], 3)
        out = mutator({"heal_count": 99, "heal_context": {"other": "keep"}})
        assert out["heal_count"] == 99                 # 다른 필드 보존
        assert out["heal_context"]["other"] == "keep"  # 중첩 키 보존
        assert out["heal_context"]["failures"] == []
        assert out["heal_context"]["failure_count"] == 0
        assert out["heal_context"]["auto_healed"] == 3

    def test_failure_count_tracks_remaining(self, auto_heal):
        remaining = [{"test_id": "a::b"}, {"test_id": "a::c"}]
        out = auto_heal._make_heal_context_mutator(remaining, 5)({})
        assert out["heal_context"]["failure_count"] == 2
        assert out["heal_context"]["failures"] == remaining


class TestAtomicWriteText:
    """#28 — target.write_text()는 비원자적 truncate-write. tempfile+replace로 교체.

    죽은 .pre_autoheal 백업이 제거된 뒤(f9fe4ec) 남은 유일한 안전장치라,
    쓰기 도중 실패해도 원본이 훼손되지 않아야 한다.
    """

    def test_writes_content(self, auto_heal, tmp_path):
        target = tmp_path / "f.py"
        auto_heal._atomic_write_text(target, "print('hi')\n")
        assert target.read_text(encoding="utf-8") == "print('hi')\n"

    def test_overwrites_existing_file(self, auto_heal, tmp_path):
        target = tmp_path / "f.py"
        target.write_text("old\n", encoding="utf-8")
        auto_heal._atomic_write_text(target, "new\n")
        assert target.read_text(encoding="utf-8") == "new\n"

    def test_no_leftover_tmp_files_on_success(self, auto_heal, tmp_path):
        target = tmp_path / "f.py"
        auto_heal._atomic_write_text(target, "x = 1\n")
        leftovers = [p for p in tmp_path.iterdir() if p.suffix == ".tmp"]
        assert leftovers == []

    def test_original_preserved_if_write_fails(self, auto_heal, tmp_path, monkeypatch):
        """쓰기 도중 실패(디스크 오류 등 시뮬레이션)해도 원본이 그대로 남아야 한다."""
        target = tmp_path / "f.py"
        target.write_text("original\n", encoding="utf-8")

        def _boom(*a, **k):
            raise OSError("simulated disk failure")

        monkeypatch.setattr("builtins.open", _boom)
        with pytest.raises(OSError):
            auto_heal._atomic_write_text(target, "new content\n")

        assert target.read_text(encoding="utf-8") == "original\n"
        leftovers = [p for p in tmp_path.iterdir() if p.suffix == ".tmp"]
        assert leftovers == [], "실패 시 임시파일이 청소되지 않고 남음"


class TestRerunOutcome:
    """#24 — pytest ERROR가 섞이면 failed==0이라도 실패인데 크래시 가드가 못 잡았다.

    _rerun_outcome은 "전부 성공"을 passed == expected_count로 판정해야
    ERROR가 섞인 재실행을 성공으로 오판하지 않는다.
    """

    def test_all_passed(self, auto_heal):
        stdout = (
            "tests/t.py::test_a PASSED [ 50%]\n"
            "tests/t.py::test_b PASSED [100%]\n"
            "=== 2 passed in 0.01s ===\n"
        )
        out = auto_heal._rerun_outcome(stdout, 0, expected_count=2)
        assert out == {
            "passed": 2, "failed": 0, "errors": 0,
            "crashed": False, "all_passed": True,
        }

    def test_error_mixed_with_passed_is_not_all_passed(self, auto_heal):
        """실제 회귀 재현: 3개 중 2 PASSED / 1 ERROR — 예전엔 failed==0이라 성공 오판."""
        stdout = (
            "tests/t.py::test_a PASSED [ 33%]\n"
            "tests/t.py::test_b PASSED [ 66%]\n"
            "tests/t.py::test_c ERROR [100%]\n"
            "=== 2 passed, 1 error in 0.01s ===\n"
        )
        out = auto_heal._rerun_outcome(stdout, 1, expected_count=3)
        assert out["passed"] == 2
        assert out["failed"] == 0
        assert out["errors"] == 1
        assert out["crashed"] is False
        assert out["all_passed"] is False

    def test_all_failed(self, auto_heal):
        stdout = (
            "tests/t.py::test_a FAILED [ 50%]\n"
            "tests/t.py::test_b FAILED [100%]\n"
        )
        out = auto_heal._rerun_outcome(stdout, 1, expected_count=2)
        assert out["all_passed"] is False
        assert out["crashed"] is False

    def test_full_crash_no_passed_no_failed(self, auto_heal):
        """수집 실패 등으로 아무 테스트도 안 돌면 crashed=True."""
        stdout = "ImportError while importing test module.\n"
        out = auto_heal._rerun_outcome(stdout, 2, expected_count=1)
        assert out["crashed"] is True
        assert out["all_passed"] is False


class TestBackupCodeRemoved:
    """디스크 백업은 읽는 곳이 없어 제거됐다 (재도입 방지)."""

    def test_no_backup_suffix_constant(self, auto_heal):
        assert not hasattr(auto_heal, "BACKUP_SUFFIX")

    def test_source_has_no_pre_autoheal_reference(self):
        src = (_SCRIPTS_DIR / "06_auto_heal.py").read_text(encoding="utf-8")
        assert "pre_autoheal" not in src
