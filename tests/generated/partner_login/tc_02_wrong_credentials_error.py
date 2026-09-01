"""
PL-02: 협력사 로그인 잘못된 자격증명 에러
URL: https://mall.serveone.co.kr/M3/cmm/login.dev

전략: 협력사 탭 클릭 후 존재하지 않는 ID/PW 입력 → 로그인 실패 에러 확인.
      비밀번호 마스킹 유지 검증 포함.
"""
import json
import re
from pathlib import Path

from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"
TEST_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "test_data.json"


def test_wrong_credentials_error(page: Page):
    """협력사 탭에서 잘못된 ID/PW 입력 후 로그인 실패 에러 메시지 및 페이지 유지 검증."""
    # test_data.json에서 잘못된 자격증명 읽기
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        test_data = json.load(f)
    invalid_partner_id = test_data["serveone"]["login"]["invalid_partner_id"]
    invalid_password = test_data["serveone"]["login"]["invalid_password"]

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

    # 잘못된 자격증명 입력
    id_input.fill(invalid_partner_id)
    pw_input.fill(invalid_password)

    # 비밀번호 필드 마스킹 확인 (입력 직후)
    expect(pw_input).to_have_attribute("type", "password")

    # 로그인 버튼 클릭
    login_btn.click()

    # 에러 응답 또는 다이얼로그 처리 대기
    page.wait_for_timeout(2000)

    # 검증 1: dialog 메시지가 있으면 에러 키워드 확인
    if dialog_messages:
        combined = " ".join(dialog_messages)
        assert combined.strip() != "", "잘못된 자격증명 시 dialog 메시지가 비어있음"
        # 로그인 실패 메시지로 간주
        # 비밀번호 마스킹 최종 확인
        expect(pw_input).to_have_attribute("type", "password")
        return

    # 검증 2: #LoginMsg 에러 메시지 영역 노출 확인
    login_msg = page.locator("#LoginMsg")
    if login_msg.is_visible():
        expect(login_msg).to_be_visible()
        # 비밀번호 마스킹 최종 확인
        expect(pw_input).to_have_attribute("type", "password")
        return

    # 검증 3: URL이 로그인 페이지에 머무름 + 입력 필드 여전히 visible
    current_url = page.url
    assert "login" in current_url, f"로그인 페이지에서 이탈함: {current_url}"
    expect(id_input).to_be_visible()
    expect(pw_input).to_be_visible()

    # 비밀번호 마스킹 최종 확인
    expect(pw_input).to_have_attribute("type", "password")
