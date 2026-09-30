"""
자동 생성된 Playwright 테스트 코드
URL: http://localhost:8877
케이스: terms_not_agreed_error (TSD_03)

TC: testcases/tc_studio_demo/tc_TSD_03_약관_미동의_오류_표시.md
Claude Code가 plan 기반으로 완성한 파일.
수동 편집 가능.
"""
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8877"

NAME_INPUT = '[name="name"]'
EMAIL_INPUT = '[name="email"]'
TERMS_CHECKBOX = '[name="terms"]'
SUBMIT_BUTTON = 'button[type="submit"]'
ERROR_MESSAGE = "#error"
RESULT_MESSAGE = "#result"

INPUT_NAME = "테스터"
INPUT_EMAIL = "qa@example.test"
EXPECTED_ERROR = "약관에 동의하세요."


def test_terms_not_agreed_error(page: Page) -> None:
    """약관 동의 없이 등록하면 약관 동의를 요구하는 오류 메시지가 표시된다."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Step 1~2. 유효한 이름·이메일 입력
    page.locator(NAME_INPUT).fill(INPUT_NAME)
    page.locator(EMAIL_INPUT).fill(INPUT_EMAIL)

    # Step 3. 약관 동의를 체크하지 않은 상태로 둔다
    expect(page.locator(TERMS_CHECKBOX)).not_to_be_checked()

    # Step 4. 등록 버튼을 누른다
    page.locator(SUBMIT_BUTTON).click()

    # Expected: 약관 동의를 요구하는 오류 메시지가 표시된다 ("약관에 동의하세요.")
    expect(page.locator(ERROR_MESSAGE)).to_have_text(EXPECTED_ERROR)
    expect(page.locator(ERROR_MESSAGE)).to_be_visible()
    # 이름·이메일은 유효하므로 등록 완료 메시지는 표시되지 않는다
    expect(page.locator(RESULT_MESSAGE)).to_have_text("")
