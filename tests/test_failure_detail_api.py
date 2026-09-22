"""GET /api/testcase/failure_detail 통합 테스트.

실패한 TC를 파이프라인 화면에서 펼쳤을 때 스크린샷·콘솔로그·네트워크실패·
trace 안내·실패 요약(error)을 한 번에 반환하는 엔드포인트를 검증한다.
tests/import_studio_test_support.dashboard_server로 실제 서버를 격리된
임시 프로젝트 위에서 띄워 실제 HTTP로 확인한다.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from tests.import_studio_test_support import dashboard_server, request_json

GROUP = "customer_login"
NODEID = f"tests/generated/{GROUP}/tc_CL_02_x.py::test_wrong_password"
TEST_FUNC = "test_wrong_password"


@pytest.fixture
def project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    tc_dir = root / "testcases" / GROUP
    tc_dir.mkdir(parents=True)
    (tc_dir / "tc_CL_02_wrong_password.md").write_text(
        '---\nid: "CL_02"\npriority: "medium"\ntags: []\ntype: structured\n---\n'
        "# 잘못된 비밀번호 오류 메시지 검증\n\n"
        "## Steps\n올바른 아이디, 잘못된 비밀번호를 입력한다\n\n"
        "## Expected\n\"비밀번호가 일치하지 않습니다\"가 표시된다\n",
        encoding="utf-8",
    )
    shot_dir = root / "tests" / "screenshots"
    shot_dir.mkdir(parents=True)
    (shot_dir / f"{GROUP}__{TEST_FUNC}.png").write_bytes(b"\x89PNG\r\n")
    (shot_dir / f"{GROUP}__{TEST_FUNC}.meta.json").write_text(json.dumps({
        "url": "https://mall.serveone.co.kr/M3/cmm/login.dev",
        "timestamp": "2026-09-22T14:31:07",
        "trace_path": str(root / "tests" / "traces" / f"{GROUP}__{TEST_FUNC}.zip"),
        "video_path": str(root / "tests" / "videos" / f"{GROUP}__{TEST_FUNC}.webm"),
        "console_errors": [{"type": "error", "text": "Uncaught TypeError: x is null"}],
        "network_failures": [{"url": "/api/auth", "method": "POST", "status": 401, "failure": "HTTP 401"}],
    }), encoding="utf-8")
    # trace_path/video_path가 실제로 존재해야 응답에 반영된다
    (root / "tests" / "traces").mkdir(parents=True)
    (root / "tests" / "traces" / f"{GROUP}__{TEST_FUNC}.zip").write_bytes(b"PK")
    (root / "tests" / "videos").mkdir(parents=True)
    (root / "tests" / "videos" / f"{GROUP}__{TEST_FUNC}.webm").write_bytes(b"\x00")

    state_dir = root / "state"
    state_dir.mkdir(parents=True)
    (state_dir / "pipeline.json").write_text(json.dumps({
        "step": "done",
        "execution_result": {
            "group_results": {
                GROUP: {"passed": 0, "failed": 1, "skipped": 0, "tests": [{
                    "nodeid": NODEID,
                    "name": "test_wrong_password",
                    "passed": False,
                    "outcome": "failed",
                    "error": "E   AssertionError: Locator expected to be visible",
                }]},
            },
        },
    }), encoding="utf-8")
    return root


def test_failure_detail_combines_expected_meta_and_error_summary(project: Path):
    with dashboard_server(project) as base_url:
        status, body = request_json(base_url, "GET", f"/api/testcase/failure_detail?nodeid={NODEID}")

    assert status == 200
    assert body["ok"] is True
    assert body["group"] == GROUP
    assert body["test_name"] == TEST_FUNC
    assert "비밀번호가 일치하지 않습니다" in body["expected"]
    assert "잘못된 비밀번호를 입력한다" in body["steps"]
    assert body["error_summary"] == "E   AssertionError: Locator expected to be visible"
    assert body["screenshot_url"] == f"/screenshots/{GROUP}__{TEST_FUNC}.png"
    assert body["video_url"] == f"/videos/{GROUP}__{TEST_FUNC}.webm"
    assert body["trace_cmd"] and body["trace_cmd"].startswith("npx playwright show-trace ")
    assert body["url"] == "https://mall.serveone.co.kr/M3/cmm/login.dev"
    assert body["console_errors"] == [{"type": "error", "text": "Uncaught TypeError: x is null"}]
    assert body["network_failures"] == [{"url": "/api/auth", "method": "POST", "status": 401, "failure": "HTTP 401"}]


def test_missing_nodeid_param_is_rejected(project: Path):
    with dashboard_server(project) as base_url:
        status, body = request_json(base_url, "GET", "/api/testcase/failure_detail")
    assert status == 200  # 서버는 항상 200 + ok:false로 오류를 표현
    assert body["ok"] is False


def test_get_testcase_still_returns_raw_md_content(project: Path):
    """_get_testcase()는 _resolve_tc_file() 공유 헬퍼로 리팩터링됐다 — 회귀 확인.

    이 엔드포인트는 이전까지 테스트가 전혀 없었으므로, 실패 상세 API와
    같은 nodeid 해석 로직을 공유하게 된 이번 리팩터링이 기존 동작을
    깨지 않았는지 직접 확인한다.
    """
    with dashboard_server(project) as base_url:
        status, body = request_json(base_url, "GET", f"/api/testcase?nodeid={NODEID}")

    assert status == 200
    assert body["ok"] is True
    assert body["file"] == "tc_CL_02_wrong_password.md"
    assert "비밀번호가 일치하지 않습니다" in body["content"]


def test_get_testcase_missing_file_reports_not_found(project: Path):
    nodeid = f"tests/generated/{GROUP}/tc_CL_99_x.py::test_never_ran"
    with dashboard_server(project) as base_url:
        status, body = request_json(base_url, "GET", f"/api/testcase?nodeid={nodeid}")

    assert status == 200
    assert body["ok"] is False
    assert "not found" in body["error"]


def test_unknown_test_returns_graceful_empty_fields(project: Path):
    nodeid = f"tests/generated/{GROUP}/tc_CL_99_x.py::test_never_ran"
    with dashboard_server(project) as base_url:
        status, body = request_json(base_url, "GET", f"/api/testcase/failure_detail?nodeid={nodeid}")

    assert status == 200
    assert body["ok"] is True
    assert body["expected"] == ""  # tc 파일 없음
    assert body["steps"] == ""
    assert body["screenshot_url"] is None
    assert body["video_url"] is None
    assert body["trace_cmd"] is None
    assert body["error_summary"] == ""
    assert body["console_errors"] == []
    assert body["network_failures"] == []
