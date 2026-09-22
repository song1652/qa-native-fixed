"""result_parser.parse_failure_messages 단위 테스트.

05_execute.py/99_merge.py가 group_results[].tests[].error에 저장하는
실패 요약(짧은 마지막 트레이스백 줄) 추출 로직을 검증한다.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from result_parser import parse_failure_messages


def _report(tests: list[dict]) -> dict:
    return {"tests": tests}


class TestParseFailureMessages:
    def test_call_phase_longrepr_first_e_line_extracted(self):
        report = _report([{
            "nodeid": "tests/generated/customer_login/tc_CL_02_x.py::test_wrong_password",
            "outcome": "failed",
            "call": {"longrepr": "Traceback (most recent call last):\n  File x.py, line 10\nE   AssertionError: Locator expected to be visible\n"},
        }])
        result = parse_failure_messages(report)
        assert result == {
            "tests/generated/customer_login/tc_CL_02_x.py::test_wrong_password":
                "E   AssertionError: Locator expected to be visible",
        }

    def test_playwright_expect_failure_ignores_trailing_call_log_and_aria_snapshot(self):
        """실제 데모 실행(tc_01_login_api_error.py)에서 재현된 회귀 케이스.

        Playwright expect().to_be_visible() 실패는 실제 에러 요약 뒤에
        "Actual value:"/"Call log:"/"Aria snapshot:" 같은 부가 정보가
        여러 줄 더 붙는다. 예전 구현(마지막 비공백 줄)은 이 노이즈 중
        하나("E   - button "로그인"")를 요약으로 잘못 골랐다.
        """
        longrepr = (
            'tc_01_login_api_error.py:35: in test_login_shows_error_when_auth_api_fails\n'
            '    expect(page.locator("#error-message")).to_be_visible(timeout=3000)\n'
            'E   AssertionError: Locator expected to be visible\n'
            'E   Actual value: None\n'
            'E   Error: element(s) not found \n'
            'E   Call log:\n'
            'E     - Expect "to_be_visible" with timeout 3000ms\n'
            'E     - waiting for locator("#error-message")\n'
            'E   \n'
            'E   Aria snapshot:\n'
            'E   - heading "고객 로그인" [level=1]\n'
            'E   - textbox "아이디"\n'
            'E   - textbox "비밀번호"\n'
            'E   - button "로그인"'
        )
        report = _report([{
            "nodeid": "tests/generated/api_demo/tc_01_login_api_error.py::test_login_shows_error_when_auth_api_fails",
            "outcome": "failed",
            "call": {"longrepr": longrepr},
        }])
        result = parse_failure_messages(report)
        assert result == {
            "tests/generated/api_demo/tc_01_login_api_error.py::test_login_shows_error_when_auth_api_fails":
                "E   AssertionError: Locator expected to be visible",
        }

    def test_passed_and_skipped_tests_are_ignored(self):
        report = _report([
            {"nodeid": "a::test_a", "outcome": "passed",
             "call": {"longrepr": "should not appear"}},
            {"nodeid": "b::test_b", "outcome": "skipped",
             "call": {"longrepr": "should not appear either"}},
        ])
        assert parse_failure_messages(report) == {}

    def test_unrecognized_outcome_treated_as_failed(self):
        report = _report([{
            "nodeid": "a::test_a", "outcome": "error",
            "call": {"longrepr": "E   Error: boom"},
        }])
        assert parse_failure_messages(report) == {"a::test_a": "E   Error: boom"}

    def test_falls_back_to_setup_phase_when_call_has_no_longrepr(self):
        report = _report([{
            "nodeid": "a::test_a", "outcome": "failed",
            "call": {},
            "setup": {"longrepr": "fixture 'page' failed\nE   RuntimeError: browser closed"},
        }])
        assert parse_failure_messages(report) == {
            "a::test_a": "E   RuntimeError: browser closed",
        }

    def test_failed_test_without_any_longrepr_is_skipped(self):
        report = _report([{"nodeid": "a::test_a", "outcome": "failed", "call": {}}])
        assert parse_failure_messages(report) == {}

    def test_empty_report_returns_empty_dict(self):
        assert parse_failure_messages({}) == {}
        assert parse_failure_messages({"tests": []}) == {}
