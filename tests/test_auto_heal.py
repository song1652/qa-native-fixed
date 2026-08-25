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


class TestBackupCodeRemoved:
    """디스크 백업은 읽는 곳이 없어 제거됐다 (재도입 방지)."""

    def test_no_backup_suffix_constant(self, auto_heal):
        assert not hasattr(auto_heal, "BACKUP_SUFFIX")

    def test_source_has_no_pre_autoheal_reference(self):
        src = (_SCRIPTS_DIR / "06_auto_heal.py").read_text(encoding="utf-8")
        assert "pre_autoheal" not in src
