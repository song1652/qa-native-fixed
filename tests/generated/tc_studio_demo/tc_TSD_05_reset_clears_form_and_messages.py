"""
자동 생성된 Playwright 테스트 코드
URL: http://localhost:8877
케이스: reset_clears_form_and_messages (TSD_05)

TC: testcases/tc_studio_demo/tc_TSD_05_초기화_후_입력과_메시지_제거.md
Claude Code가 plan 기반으로 완성한 파일.
수동 편집 가능.
"""
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8877"

NAME_INPUT = '[name="name"]'
EMAIL_INPUT = '[name="email"]'
TERMS_CHECKBOX = '[name="terms"]'
SUBMIT_BUTTON = 'button[type="submit"]'
RESET_BUTTON = 'button[type="reset"]'
ERROR_MESSAGE = "#error"
RESULT_MESSAGE = "#result"

INPUT_NAME = "테스터"
INPUT_EMAIL = "qa@example.test"
EXPECTED_RESULT = f"등록 완료: {INPUT_NAME} ({INPUT_EMAIL})"


def test_reset_clears_form_and_messages(page: Page) -> None:
    """초기화 버튼은 입력값·약관 체크와 오류·완료 메시지를 모두 제거한다."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # 사전 조건: 이름·이메일·약관 동의를 입력해 등록을 완료한 상태
    page.locator(NAME_INPUT).fill(INPUT_NAME)
    page.locator(EMAIL_INPUT).fill(INPUT_EMAIL)
    page.locator(TERMS_CHECKBOX).check()
    page.locator(SUBMIT_BUTTON).click()
    expect(page.locator(RESULT_MESSAGE)).to_have_text(EXPECTED_RESULT)

    # Step 1. 초기화 버튼을 누른다
    page.locator(RESET_BUTTON).click()

    # Expected: 입력값이 빈 값으로 바뀌고 약관 체크가 해제된다
    expect(page.locator(NAME_INPUT)).to_have_value("")
    expect(page.locator(EMAIL_INPUT)).to_have_value("")
    expect(page.locator(TERMS_CHECKBOX)).not_to_be_checked()

    # Expected: 오류 메시지와 완료 메시지가 표시되지 않는 상태가 된다
    expect(page.locator(ERROR_MESSAGE)).to_have_text("")
    expect(page.locator(RESULT_MESSAGE)).to_have_text("")
    expect(page.locator(RESULT_MESSAGE)).to_be_hidden()
