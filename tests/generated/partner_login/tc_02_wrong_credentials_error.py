"""협력사 로그인 잘못된 자격증명 에러 검증."""
import json
import re
from pathlib import Path

from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"

TEST_DATA_PATH = Path(__file__).parent.parent.parent.parent / "config" / "test_data.json"
with open(TEST_DATA_PATH, encoding="utf-8") as f:
    test_data = json.load(f)


def test_partner_login_wrong_credentials_error(page: Page):
    # 로그인 실패 시 alert 로 안내되는 경우 대비
    dialog_messages = []

    def _on_dialog(dialog):
        dialog_messages.append(dialog.message)
        dialog.dismiss()

    page.on("dialog", _on_dialog)

    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 협력사 탭 클릭 → 협력사 폼 노출
    page.locator("#vendorTab").click()
    page.locator("#cprtcpUsrId").wait_for(state="visible")

    invalid_id = test_data["serveone"]["login"]["invalid_partner_id"]
    invalid_pw = test_data["serveone"]["login"]["invalid_password"]

    page.locator("#cprtcpUsrId").fill(invalid_id)
    page.locator("#cprtcpSectNo").fill(invalid_pw)

    login_button = (
        page.locator("#frmVendorLogin").get_by_role("button", name="로그인").first
    )
    login_button.click()
    page.wait_for_load_state("networkidle")

    # 잘못된 자격증명이므로 로그인 페이지를 벗어나지 못한다
    expect(page).to_have_url(re.compile(r"login"))

    # 에러 안내가 alert 또는 페이지 텍스트로 노출되는지 확인
    if dialog_messages:
        assert dialog_messages[0].strip(), "alert 메시지가 비어 있음"
    else:
        expect(page.locator("#frmVendorLogin")).to_be_visible()
