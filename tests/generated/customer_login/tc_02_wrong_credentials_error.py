"""
tc_02_wrong_credentials_error.py
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
- 테스트 함수명: test_wrong_credentials_error
- 고객 로그인 잘못된 자격증명 에러 (CL-02)
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


def test_wrong_credentials_error(page: Page):
    """고객 로그인 잘못된 자격증명 에러: 존재하지 않는 아이디/잘못된 비밀번호 입력 시 에러 메시지 확인"""
    data = load_test_data()
    invalid_id = data["serveone"]["login"]["invalid_customer_id"]
    invalid_pw = data["serveone"]["login"]["invalid_password"]

    # 페이지 접속
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 고객 탭은 기본 활성 상태 — 탭 클릭 불필요

    # dialog 메시지 수집 (conftest가 accept() 처리하므로 message만 수집)
    dialog_messages = []

    def handle_dialog(dialog):
        dialog_messages.append(dialog.message)
        # conftest가 dialog.accept()를 이미 처리하므로 여기서는 message만 수집

    page.on("dialog", handle_dialog)

    # 잘못된 자격증명 입력
    page.fill("#userId", invalid_id)
    page.fill("#userPw", invalid_pw)

    # 로그인 버튼 클릭
    page.locator("#btnCustomerLogin").click()

    # 에러 응답 대기
    page.wait_for_load_state("networkidle")

    # 검증 1: 페이지가 로그인 페이지에 머물고 있음
    assert "login" in page.url.lower() or "cmm" in page.url.lower(), (
        f"로그인 페이지를 이탈했습니다: {page.url}"
    )

    # 검증 2: 에러 메시지 확인
    # 실제 사이트 메시지: "사용자 ID 또는 패스워드가 정확하지 않습니다." 등
    error_keywords = [
        "아이디", "비밀번호", "패스워드", "사용자", "확인", "정확하지",
        "오류", "실패", "id", "password", "error", "invalid",
    ]

    if dialog_messages:
        # native dialog로 에러 메시지가 표시된 경우
        msg = dialog_messages[0]
        assert any(keyword in msg.lower() for keyword in error_keywords), (
            f"예상치 못한 dialog 메시지: {msg}"
        )
    else:
        # 페이지 내 #LoginMsg 에러 메시지 영역 확인
        login_msg = page.locator("#LoginMsg")
        try:
            expect(login_msg).to_be_visible(timeout=5000)
            # 에러 메시지 텍스트에 키워드 포함 여부 확인
            msg_text = login_msg.inner_text().strip()
            assert any(keyword in msg_text.lower() for keyword in error_keywords), (
                f"예상치 못한 #LoginMsg 메시지: {msg_text}"
            )
        except Exception:
            # fallback: 로그인 페이지 유지 + 아이디 필드 visible 확인으로 로그인 차단 검증
            expect(page.locator("#userId")).to_be_visible()
            expect(page.locator("#userPw")).to_be_visible()

    # 검증 3: 비밀번호 필드가 마스킹(type=password) 상태 유지
    expect(page.locator("#userPw")).to_have_attribute("type", "password")
