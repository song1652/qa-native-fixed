"""
tc_01_empty_fields_validation.py
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
- 테스트 함수명: test_empty_fields_validation
- 고객 로그인 빈 필드 유효성 검증 (CL-01)
"""
import json
import re
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"

TEST_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "test_data.json"


def load_test_data():
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_empty_fields_validation(page: Page):
    """고객 로그인 빈 필드 유효성 검증: 아이디/비밀번호 미입력 시 에러 메시지 또는 로그인 차단 확인"""
    # 페이지 접속
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 고객 탭은 기본 on 상태 — 클릭 불필요
    # 빈 필드 상태에서 로그인 버튼 클릭
    # alert 핸들러 등록 (브라우저 native alert 대응)
    alert_messages = []

    def handle_dialog(dialog):
        alert_messages.append(dialog.message)
        # conftest가 dialog.accept()를 이미 처리하므로 여기서는 message만 수집

    page.on("dialog", handle_dialog)

    page.locator("#btnCustomerLogin").click()

    # 검증: native alert 또는 페이지 내 에러 메시지 중 하나로 유효성 검증됨
    # networkidle 대기 (동적 에러 메시지 렌더링 대응)
    page.wait_for_load_state("networkidle")

    # 페이지가 로그인 페이지에 머물고 있음을 확인
    assert "login" in page.url.lower() or "cmm" in page.url.lower(), (
        f"로그인 페이지를 이탈했습니다: {page.url}"
    )

    # native alert이 발생했으면 메시지 확인
    if alert_messages:
        msg = alert_messages[0]
        assert any(keyword in msg for keyword in ["아이디", "비밀번호", "입력", "id", "password"]), (
            f"예상치 못한 alert 메시지: {msg}"
        )
    else:
        # 페이지 내 에러 메시지 확인 (동적 렌더링 대기)
        error_selectors = [
            ".error",
            ".alert",
            ".msg",
            "[class*='error']",
            "[class*='alert']",
            "[class*='msg']",
        ]
        error_found = False
        for selector in error_selectors:
            locator = page.locator(selector).first
            if locator.is_visible():
                error_found = True
                break

        # 에러 메시지가 없어도 페이지 이동이 없으면 유효성 검증 통과로 간주
        # (브라우저 native validation 등)
        if not error_found:
            # 아이디 필드가 여전히 visible이면 로그인이 차단된 것
            expect(page.locator("#userId")).to_be_visible()
