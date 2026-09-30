"""
자동 생성된 Playwright 테스트 코드
URL: http://localhost:8877
케이스: invalid_email_format_error (TSD_02)

TC: testcases/tc_studio_demo/tc_TSD_02_잘못된_이메일_형식_오류_표시.md
Claude Code가 plan 기반으로 완성한 파일.
수동 편집 가능.
"""
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8877"

NAME_INPUT = '[name="name"]'
EMAIL_INPUT = '[name="email"]'
SUBMIT_BUTTON = 'button[type="submit"]'
ERROR_MESSAGE = "#error"
RESULT_MESSAGE = "#result"

INPUT_NAME = "테스터"
INVALID_EMAIL = "invalid"
EXPECTED_ERROR = "이메일 형식을 확인하세요."


def test_invalid_email_format_error(page: Page) -> None:
    """잘못된 이메일 형식으로 등록하면 이메일 형식 오류 메시지가 표시된다."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Step 1~2. 이름 "테스터", 이메일 "invalid" 입력
    page.locator(NAME_INPUT).fill(INPUT_NAME)
    page.locator(EMAIL_INPUT).fill(INVALID_EMAIL)

    # Step 3. 등록 버튼을 누른다
    page.locator(SUBMIT_BUTTON).click()

    # Expected: 이메일 형식 오류 메시지가 표시된다 ("이메일 형식을 확인하세요.")
    expect(page.locator(ERROR_MESSAGE)).to_have_text(EXPECTED_ERROR)
    expect(page.locator(ERROR_MESSAGE)).to_be_visible()
    # 이름은 채웠으므로 이름 오류가 아닌 이메일 오류여야 한다
    expect(page.locator(RESULT_MESSAGE)).to_have_text("")
