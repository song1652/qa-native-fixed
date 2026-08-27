"""
PL-01: 협력사 로그인 빈 필드 유효성 검증
URL: https://mall.serveone.co.kr/M3/cmm/login.dev

전략: 협력사로그인 탭 클릭으로 섹션 노출 후 빈 필드 상태로 로그인 시도.
      에러 메시지 표시 또는 페이지 유지 확인.
"""
from pathlib import Path

from playwright.sync_api import Page

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def test_partner_login_empty_field_validation(page: Page):
    """협력사 탭에서 ID/PW 빈 채로 로그인 시도 — 로그인 차단 또는 에러 메시지 표시 검증."""
    # 브라우저 alert 자동 수락 (빈 필드 경고 alert 대비)
    page.on("dialog", lambda d: d.accept())

    # 페이지 접속
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 협력사로그인 탭 클릭 (vendor 섹션 노출)
    vendor_tab = page.locator("#vendorTab")
    vendor_tab.wait_for(state="visible", timeout=10000)
    vendor_tab.click()
    # SPA 탭 전환 후 렌더링 대기 (networkidle 미발생)
    page.wait_for_timeout(800)

    # 협력사 로그인 섹션 노출 확인
    id_input = page.locator("#cprtcpUsrId")
    id_input.wait_for(state="visible", timeout=5000)

    pw_input = page.locator("#cprtcpSectNo")
    pw_input.wait_for(state="visible", timeout=5000)

    login_btn = page.locator("#btnVendorLogin")
    login_btn.wait_for(state="visible", timeout=5000)

    # 두 필드 모두 비운 상태로 로그인 버튼 클릭
    id_input.fill("")
    pw_input.fill("")
    login_btn.click()

    # 에러 응답 또는 다이얼로그 처리 대기
    page.wait_for_timeout(1500)

    # 검증: 로그인 페이지 유지 (URL에 login 포함)
    current_url = page.url
    assert "login" in current_url, f"로그인 페이지에서 이탈함: {current_url}"
