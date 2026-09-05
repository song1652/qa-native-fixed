"""
tc_PL_02_partner_login_wrong_credentials_error.py
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
- 테스트 함수명: test_partner_login_wrong_credentials_error
"""
import json
from pathlib import Path
from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"
TEST_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "test_data.json"


def test_partner_login_wrong_credentials_error(page: Page) -> None:
    """TC PL-02: 협력사 로그인 잘못된 자격증명 에러"""
    # Arrange: 테스트 데이터 로드
    with open(TEST_DATA_PATH) as f:
        test_data = json.load(f)
    partner_id = test_data["serveone"]["login"]["invalid_partner_id"]
    invalid_pw = test_data["serveone"]["login"]["invalid_password"]

    # Arrange: dialog 핸들러를 버튼 클릭 전에 등록 (race condition 방지)
    dialog_message = []
    page.on("dialog", lambda d: (dialog_message.append(d.message), d.accept()))

    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Act: 협력사 탭 클릭 — 초기 hidden이므로 탭 전환 필수
    page.locator("#vendorTab").click()
    page.wait_for_selector("#vendorLogin", state="visible", timeout=5000)

    # 필드가 visible한지 확인 후 자격증명 입력
    id_input = page.locator("#cprtcpUsrId")
    pw_input = page.locator("#cprtcpSectNo")
    expect(id_input).to_be_visible()
    expect(pw_input).to_be_visible()

    id_input.fill(partner_id)
    pw_input.fill(invalid_pw)

    # 협력사 로그인 버튼 클릭
    page.locator("#btnVendorLogin").click()

    # SPA 렌더링 대기 (dialog가 발생할 시간)
    page.wait_for_timeout(2000)

    # Assert: 잘못된 자격증명 에러 다이얼로그 검증
    assert len(dialog_message) > 0, "잘못된 자격증명 로그인 시 다이얼로그가 표시되어야 합니다"
    error_keywords = ["아이디", "패스워드", "확인"]
    assert any(keyword in dialog_message[0] for keyword in error_keywords), (
        f"예상 키워드가 포함되지 않음: '{dialog_message[0]}'"
    )

    # 페이지 이동 없이 로그인 페이지 유지 검증
    assert "/cmm/login" in page.url, (
        f"잘못된 자격증명 로그인 후 로그인 페이지를 벗어남: {page.url}"
    )
