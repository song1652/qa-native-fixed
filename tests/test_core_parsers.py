"""핵심 파싱 함수 단위 테스트.

테스트 대상:
- 06_heal.py: classify_error, extract_key_lines, parse_failures
- parse_cases.py: load_cases
- 05_execute.py: count_test_functions
"""
import sys
import tempfile
from pathlib import Path

# scripts/ 모듈 import 준비
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


# ── 06_heal.py 함수 테스트 ────────────────────────────────────────


class TestClassifyError:
    """classify_error: traceback → 오류 유형 분류."""

    def setup_method(self):
        from _paths import PROJECT_ROOT  # noqa: F811
        # 06_heal.py에서 함수만 import (main 실행 안 함)
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "heal", str(PROJECT_ROOT / "scripts" / "06_heal.py")
        )
        mod = importlib.util.module_from_spec(spec)
        # main() 실행 방지: if __name__ 블록은 import 시 실행 안 됨
        spec.loader.exec_module(mod)
        self.classify = mod.classify_error
        self.extract = mod.extract_key_lines
        self.parse = mod.parse_failures

    def test_locator_strict_mode(self):
        assert self.classify("strict mode violation: locator resolved to 2 elements") == "Locator"

    def test_locator_element_not_found(self):
        assert self.classify("Error: Element not found") == "Locator"

    def test_locator_getby(self):
        assert self.classify("Error: getByRole('button') not found") == "Locator"

    def test_assertion_expected(self):
        assert self.classify('AssertionError: Expected "Login" to contain "Welcome"') == "Assertion"

    def test_assertion_to_have_text(self):
        # "locator" 키워드가 먼저 매칭되므로 Locator로 분류됨 (classify_error 우선순위 정책)
        assert self.classify("expect(locator).to have text 'hello'") == "Locator"

    def test_assertion_expected_contain(self):
        assert self.classify('Expected "Login page" to contain "Welcome"') == "Assertion"

    def test_timeout(self):
        assert self.classify("TimeoutError: Timeout 30000ms exceeded") == "Timeout"

    def test_url(self):
        assert self.classify("Error: goto navigation failed for url") == "URL"

    def test_unknown(self):
        assert self.classify("SomeRandomError: something happened") == "기타"

    def test_empty(self):
        assert self.classify("") == "기타"


class TestExtractKeyLines:
    def setup_method(self):
        from _paths import PROJECT_ROOT
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "heal2", str(PROJECT_ROOT / "scripts" / "06_heal.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.extract = mod.extract_key_lines

    def test_extracts_error_lines(self):
        tb = """  File "test.py", line 10
    assert page.url == "/secure"
AssertionError: Expected '/login' == '/secure'
"""
        lines = self.extract(tb)
        assert len(lines) >= 1
        assert any("assert" in l.lower() or "Error" in l for l in lines)

    def test_max_3_lines(self):
        tb = "\n".join([f"Error line {i}" for i in range(10)])
        lines = self.extract(tb)
        assert len(lines) <= 3

    def test_empty_traceback(self):
        assert self.extract("") == []


class TestParseFailures:
    def setup_method(self):
        from _paths import PROJECT_ROOT
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "heal3", str(PROJECT_ROOT / "scripts" / "06_heal.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.parse = mod.parse_failures

    def test_single_failure(self):
        output = """
___ test_login ___
    def test_login(page):
>       assert page.url == "/secure"
E       AssertionError
FAILED tests/test_login.py::test_login
"""
        failures = self.parse(output, "tests/test_login.py")
        assert len(failures) == 1
        assert failures[0]["test_name"] == "test_login"
        assert "AssertionError" in failures[0]["traceback"]

    def test_multiple_failures(self):
        output = """
___ test_a ___
Error in test_a
FAILED tests/test.py::test_a
___ test_b ___
Timeout in test_b
FAILED tests/test.py::test_b
"""
        failures = self.parse(output, "tests/test.py")
        assert len(failures) == 2
        names = {f["test_name"] for f in failures}
        assert names == {"test_a", "test_b"}

    def test_no_failures(self):
        output = "1 passed in 2.5s"
        failures = self.parse(output, "tests/test.py")
        assert len(failures) == 0


# ── 05_execute.py count_test_functions 테스트 ─────────────────────


class TestCountTestFunctions:
    def setup_method(self):
        from _paths import PROJECT_ROOT
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "execute", str(PROJECT_ROOT / "scripts" / "05_execute.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.count = mod.count_test_functions

    def test_single_function_file(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("def test_login(page):\n    pass\n")
            f.flush()
            count, has_dep = self.count(f.name)
            assert count == 1
            assert has_dep is False
            Path(f.name).unlink()

    def test_multiple_functions(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("def test_a(page):\n    pass\ndef test_b(page):\n    pass\n")
            f.flush()
            count, has_dep = self.count(f.name)
            assert count == 2
            assert has_dep is True
            Path(f.name).unlink()

    def test_no_test_functions(self):
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
            f.write("def helper():\n    pass\n")
            f.flush()
            count, _ = self.count(f.name)
            assert count == 0
            Path(f.name).unlink()

    def test_directory(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "tc_01_login.py").write_text("def test_x():\n    pass\n")
            (Path(td) / "tc_02_logout.py").write_text("def test_y():\n    pass\n")
            (Path(td) / "__init__.py").write_text("")
            count, has_dep = self.count(td)
            assert count == 2
            assert has_dep is False


# ── parse_cases.py 테스트 ─────────────────────────────────────────


class TestParseCases:
    def setup_method(self):
        import importlib.util
        from _paths import PROJECT_ROOT
        spec = importlib.util.spec_from_file_location(
            "parse_cases", str(PROJECT_ROOT / "scripts" / "parse_cases.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.load_cases = mod.load_cases

    def test_load_structured_case(self):
        with tempfile.TemporaryDirectory() as td:
            case_file = Path(td) / "tc_01_login.md"
            case_file.write_text("""---
id: tc_01
data_key: valid_user
priority: high
tags: [positive, smoke]
type: structured
---
# 정상 로그인

## Precondition
0. 로그인 페이지 접속

## Steps
1. username 입력
2. password 입력
3. Login 클릭

## Expected
- 성공 메시지 표시
""")
            cases = self.load_cases(td)
            assert len(cases) == 1
            c = cases[0]
            assert c["id"] == "tc_01"
            assert c["data_key"] == "valid_user"
            assert c["priority"] == "high"
            assert "structured" in c.get("format", c.get("type", ""))
            assert len(c.get("steps", [])) >= 1

    def test_empty_directory(self):
        with tempfile.TemporaryDirectory() as td:
            cases = self.load_cases(td)
            assert cases == []


# ── _paths.py read_state/write_state 테스트 ───────────────────────


class TestReadWriteState:
    """read_state/write_state: fcntl 파일 잠금 기반 JSON 읽기/쓰기."""

    def setup_method(self):
        from _paths import read_state, write_state
        self.read_state = read_state
        self.write_state = write_state

    def test_write_and_read(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.json"
            data = {"step": "done", "count": 42, "한글": "테스트"}
            self.write_state(p, data)
            assert p.exists()
            result = self.read_state(p)
            assert result == data

    def test_read_nonexistent_returns_empty(self):
        result = self.read_state(Path("/tmp/nonexistent_state_12345.json"))
        assert result == {}

    def test_write_creates_parent_dirs(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "sub" / "deep" / "state.json"
            self.write_state(p, {"ok": True})
            assert p.exists()
            assert self.read_state(p) == {"ok": True}

    def test_overwrite_preserves_new_data(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.json"
            self.write_state(p, {"v": 1})
            self.write_state(p, {"v": 2, "new_key": "hello"})
            result = self.read_state(p)
            assert result == {"v": 2, "new_key": "hello"}

    def test_unicode_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "test.json"
            data = {"패턴": "Locator::셀렉터 불일치", "emoji": "✅"}
            self.write_state(p, data)
            assert self.read_state(p) == data

    def test_concurrent_safety(self):
        """멀티스레드에서 동시 쓰기 시 데이터 손상이 없어야 한다."""
        import threading
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "concurrent.json"
            self.write_state(p, {"count": 0})
            errors = []

            def increment(n):
                try:
                    for _ in range(n):
                        state = self.read_state(p)
                        state["count"] = state.get("count", 0) + 1
                        self.write_state(p, state)
                except Exception as e:
                    errors.append(str(e))

            threads = [threading.Thread(target=increment, args=(10,)) for _ in range(4)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            assert not errors, f"Errors during concurrent access: {errors}"
            result = self.read_state(p)
            # count가 40이 아닐 수 있지만 (잠금은 원자적 R-M-W가 아님) 파일이 손상되지 않아야 함
            assert isinstance(result["count"], int)
            assert result["count"] > 0


# ── serve.py 입력 검증 테스트 ─────────────────────────────────────


class TestDashboardInputValidation:
    """대시보드 serve.py가 실제로 사용하는 scripts/_validators.py 검증 함수 테스트.

    serve.py는 모듈 최상단에서 파일 감시 스레드를 시작하는 부작용이 있어
    직접 import하지 않고, serve.py가 위임하는 _validators 모듈을 그대로
    import해서 실제 검증 정책을 검증한다.
    """

    def setup_method(self):
        from _validators import is_valid_url, is_valid_group_name, is_safe_filename
        self.is_valid_url = is_valid_url
        self.is_valid_group_name = is_valid_group_name
        self.is_safe_filename = is_safe_filename

    def test_valid_url_patterns(self):
        valid = ["http://example.com", "https://example.com/path", "https://the-internet.herokuapp.com/login"]
        for url in valid:
            assert self.is_valid_url(url), f"Valid URL rejected: {url}"

    def test_invalid_url_patterns(self):
        invalid = ["ftp://example.com", "javascript:alert(1)", "/etc/passwd", ""]
        for url in invalid:
            assert not self.is_valid_url(url), f"Invalid URL accepted: {url}"

    def test_valid_group_names(self):
        valid = ["heroku", "login", "my_shop", "test-group", "group123"]
        for name in valid:
            assert self.is_valid_group_name(name), f"Valid group rejected: {name}"

    def test_invalid_group_names(self):
        invalid = ["../etc", "foo bar", "group/sub", "a;rm -rf", ""]
        for name in invalid:
            assert not self.is_valid_group_name(name), f"Invalid group accepted: {name}"

    def test_valid_filenames(self):
        valid = ["report.xlsx", "my-file_2024.xlsx", "a.md"]
        for name in valid:
            assert self.is_safe_filename(name), f"Valid filename rejected: {name}"

    def test_invalid_filenames(self):
        invalid = ["../../etc/passwd", "..\\..\\windows", "..", ""]
        for name in invalid:
            assert not self.is_safe_filename(name), f"Invalid filename accepted: {name}"


# ── classify_error 복합 키워드 우선순위 테스트 ────────────────────


class TestClassifyErrorPriority:
    """오류 분류 우선순위가 올바르게 적용되는지 확인."""

    def setup_method(self):
        from _paths import PROJECT_ROOT
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "heal_priority", str(PROJECT_ROOT / "scripts" / "06_heal.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.classify = mod.classify_error

    def test_locator_beats_timeout(self):
        # "locator"와 "timeout" 둘 다 포함 → Locator 우선
        assert self.classify("locator timeout 30000ms") == "Locator"

    def test_assertion_without_locator(self):
        assert self.classify("AssertionError: expected true") == "Assertion"

    def test_timeout_only(self):
        assert self.classify("page.wait_for_selector: timeout 10000ms exceeded") == "Timeout"

    def test_url_navigation(self):
        assert self.classify("Navigation to url failed") == "URL"

    def test_mixed_assertion_url(self):
        # "assert" + "url" → Assertion이 URL보다 우선
        assert self.classify("AssertionError: expected url to match") == "Assertion"


# ── heal_utils.compare_assertions: strict → weak 대체 감지 테스트 ──


class TestCompareAssertionsStrictWeak:
    """정밀 assertion(STRICT_METHODS)이 느슨한 assertion(WEAK_METHODS)으로
    바꿔치기된 패턴 감지."""

    def setup_method(self):
        from heal_utils import compare_assertions
        self.compare = compare_assertions

    @staticmethod
    def _snap(assertions):
        return {
            "count": len(assertions),
            "playwright_count": len(assertions),
            "python_assert_count": 0,
            "assertions": assertions,
        }

    def _pw(self, method, arg=""):
        return {"line": 1, "type": "playwright", "method": method, "arg": arg, "raw": ""}

    def test_strict_replaced_by_weak_detected(self):
        # pre: to_have_text 2개 → post: to_be_visible 2개 (개수는 동일, 정밀도만 하락)
        pre = {"test_x.py": self._snap([self._pw("to_have_text", "'Hello'"),
                                          self._pw("to_have_text", "'World'")])}
        post = {"test_x.py": self._snap([self._pw("to_be_visible"),
                                           self._pw("to_be_visible")])}
        result = self.compare(pre, post)
        assert result["has_warnings"]
        assert any("정밀 assertion" in w for w in result["warnings"])

    def test_strict_replaced_by_strict_no_warning(self):
        # strict → strict 대체는 정밀도 하락이 아니므로 경고 없음
        pre = {"test_x.py": self._snap([self._pw("to_have_text", "'Hello'")])}
        post = {"test_x.py": self._snap([self._pw("to_have_value", "'Hello'")])}
        result = self.compare(pre, post)
        assert not result["has_warnings"]
