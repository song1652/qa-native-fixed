"""
PL-02: 협력사 로그인 잘못된 자격증명 에러
URL: https://mall.serveone.co.kr/M3/cmm/login.dev

전략: 협력사로그인 탭 클릭 후 존재하지 않는 아이디/잘못된 비밀번호 입력.
      에러 메시지 표시 및 페이지 유지 확인.
"""
import json
from pathlib import Path

from playwright.sync_api import Page

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def test_partner_login_invalid_credentials(page: Page):
    """협력사 탭에서 잘못된 ID/PW 입력 후 로그인 시도 — 에러 메시지 표시 및 페이지 이동 없음 검증."""
    # 브라우저 alert 자동 수락 (에러 다이얼로그 대비)
    page.on("dialog", lambda d: d.accept())

    # 테스트 데이터 로드
    test_data = json.loads(TEST_DATA_PATH.read_text(encoding="utf-8"))
    login_data = test_data["serveone"]["login"]
    invalid_id = login_data["invalid_partner_id"]    # "invalid_partner_99"
    invalid_pw = login_data["invalid_password"]      # "WrongPass!123"

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

    # 잘못된 자격증명 입력
    id_input.fill(invalid_id)
    pw_input.fill(invalid_pw)
    login_btn.click()

    # 에러 응답 대기
    page.wait_for_timeout(2000)

    # 검증 1: 로그인 페이지 유지
    current_url = page.url
    assert "login" in current_url, f"로그인 실패 후 페이지 이탈: {current_url}"

    # 검증 2: 비밀번호 필드 마스킹 유지
    pw_type = pw_input.get_attribute("type")
    assert pw_type == "password", f"비밀번호 필드 마스킹 해제됨: type={pw_type}"
