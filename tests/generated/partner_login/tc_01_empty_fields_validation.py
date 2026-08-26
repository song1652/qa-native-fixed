"""협력사 로그인 빈 필드 유효성 검증."""
import json
import re
from pathlib import Path

from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"

TEST_DATA_PATH = Path(__file__).parent.parent.parent.parent / "config" / "test_data.json"
with open(TEST_DATA_PATH, encoding="utf-8") as f:
    test_data = json.load(f)


def test_partner_login_empty_fields_validation(page: Page):
    # 빈 필드 제출 시 뜨는 alert 처리
    page.on("dialog", lambda d: d.dismiss())

    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 협력사 탭 클릭 → 협력사 폼 노출
    page.locator("#vendorTab").click()
    page.locator("#cprtcpUsrId").wait_for(state="visible")

    # 아이디/비밀번호 모두 비운 상태 보장
    page.locator("#cprtcpUsrId").fill("")
    page.locator("#cprtcpSectNo").fill("")

    login_button = (
        page.locator("#frmVendorLogin").get_by_role("button", name="로그인").first
    )
    login_button.click()
    page.wait_for_load_state("networkidle")

    # 로그인 페이지에 머물러야 함 (유효성 검증 실패로 진행 차단)
    expect(page).to_have_url(re.compile(r"login"))
    expect(page.locator("#cprtcpUsrId")).to_have_value("")
