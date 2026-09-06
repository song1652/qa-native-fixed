"""
tc_02_customer_login_wrong_credentials_error.py
- TC CL-02: 고객 로그인 잘못된 자격증명 에러
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
- 테스트 함수명: test_customer_login_wrong_credentials_error
"""
from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"
INVALID_USER_ID = "invalid_test_user_99"
INVALID_PASSWORD = "WrongPass!123"
EXPECTED_ERROR_KEYWORDS = ["사용자 id 또는 패스워드가 정확하지 않습니다", "사용자 아이디 또는 패스워드"]


def test_customer_login_wrong_credentials_error(page: Page) -> None:
    """TC CL-02: 잘못된 자격증명으로 로그인 시 #LoginMsg 인라인 에러 확인"""
    # ── Arrange ──────────────────────────────────────────────────
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 고객 로그인 폼 요소 확인
    id_input = page.locator("#userId")
    pw_input = page.locator("#userPw")
    login_btn = page.locator("#btnCustomerLogin")

    expect(id_input).to_be_visible()
    expect(pw_input).to_be_visible()
    expect(login_btn).to_be_visible()

    # ── Act ───────────────────────────────────────────────────────
    id_input.fill(INVALID_USER_ID)
    pw_input.fill(INVALID_PASSWORD)
    login_btn.click()

    # #LoginMsg 영역이 visible해질 때까지 대기
    error_loc = page.locator("#LoginMsg")
    error_loc.wait_for(state="visible", timeout=8000)

    # ── Assert ────────────────────────────────────────────────────
    expect(error_loc).to_be_visible()

    msg_text = (error_loc.inner_text() or "").strip()
    assert msg_text, "#LoginMsg에 에러 메시지가 표시되어야 합니다."

    assert any(kw in msg_text.lower() for kw in EXPECTED_ERROR_KEYWORDS), (
        f"에러 메시지에 예상 키워드가 없습니다.\n"
        f"  기대 키워드: {EXPECTED_ERROR_KEYWORDS}\n"
        f"  실제 메시지: {msg_text!r}"
    )

    # 페이지 이동 없이 로그인 페이지에 머뭄
    assert "/cmm/login" in page.url, f"로그인 페이지를 벗어남: {page.url}"
