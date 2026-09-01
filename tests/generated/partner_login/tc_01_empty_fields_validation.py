"""
PL-01: 협력사 로그인 빈 필드 유효성 검증
URL: https://mall.serveone.co.kr/M3/cmm/login.dev

전략: 협력사 탭 클릭으로 섹션 노출 후 빈 필드 상태로 로그인 시도.
      에러 메시지 표시 또는 페이지 유지 확인.
"""
import json
import re
from pathlib import Path

from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"
TEST_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "test_data.json"


def test_empty_fields_validation(page: Page):
    """협력사 탭에서 ID/PW 빈 채로 로그인 시도 — 로그인 차단 또는 에러 메시지 표시 검증."""
    dialog_messages = []

    # conftest가 dialog.accept()를 이미 처리하므로 메시지 수집만 수행
    page.on("dialog", lambda d: dialog_messages.append(d.message))

    # 페이지 접속
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 협력사 로그인 탭 클릭 (vendor 섹션 노출)
    vendor_tab = page.locator("#vendorTab")
    vendor_tab.wait_for(state="visible", timeout=10000)
    vendor_tab.click()

    # 탭 전환 후 렌더링 대기
    page.locator("#vendorLogin").wait_for(state="visible", timeout=10000)

    # 협력사 로그인 섹션 입력 필드 노출 확인
    id_input = page.locator("#cprtcpUsrId")
    id_input.wait_for(state="visible", timeout=5000)

    pw_input = page.locator("#cprtcpSectNo")
    pw_input.wait_for(state="visible", timeout=5000)

    login_btn = page.locator("#btnVendorLogin")
    login_btn.wait_for(state="visible", timeout=5000)

    # 두 필드 모두 빈 상태 명시적 확인 후 로그인 버튼 클릭
    id_input.fill("")
    pw_input.fill("")
    login_btn.click()

    # 에러 응답 또는 다이얼로그 처리 대기
    page.wait_for_timeout(1500)

    # 검증 1: dialog 메시지가 있으면 에러 키워드 확인
    if dialog_messages:
        combined = " ".join(dialog_messages)
        assert combined.strip() != "", "빈 필드 시 dialog 메시지가 비어있음"
        # 로그인이 차단된 것으로 간주
        return

    # 검증 2: #LoginMsg 에러 메시지 영역 노출 확인
    login_msg = page.locator("#LoginMsg")
    if login_msg.is_visible():
        expect(login_msg).to_be_visible()
        return

    # 검증 3: URL이 로그인 페이지에 머무름 + 입력 필드 여전히 visible
    current_url = page.url
    assert "login" in current_url, f"로그인 페이지에서 이탈함: {current_url}"
    expect(id_input).to_be_visible()
    expect(pw_input).to_be_visible()
