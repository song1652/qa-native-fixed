"""
자동 생성된 Playwright 테스트 코드
URL: http://localhost:8877
케이스: registration_success_message (TSD_04)

TC: testcases/tc_studio_demo/tc_TSD_04_정상_회원_등록_완료_표시.md
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
EXPECTED_RESULT = f"등록 완료: {INPUT_NAME} ({INPUT_EMAIL})"


def test_registration_success_message(page: Page) -> None:
    """유효한 정보와 약관 동의로 등록하면 등록 완료 메시지가 표시된다."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Step 1~2. 이름·이메일 입력
    page.locator(NAME_INPUT).fill(INPUT_NAME)
    page.locator(EMAIL_INPUT).fill(INPUT_EMAIL)

    # Step 3. 약관 동의를 체크한다
    page.locator(TERMS_CHECKBOX).check()
    expect(page.locator(TERMS_CHECKBOX)).to_be_checked()

    # Step 4. 등록 버튼을 누른다
    page.locator(SUBMIT_BUTTON).click()

    # Expected: 등록 완료 메시지가 표시된다 ("등록 완료: 테스터 (qa@example.test)")
    expect(page.locator(RESULT_MESSAGE)).to_have_text(EXPECTED_RESULT)
    expect(page.locator(RESULT_MESSAGE)).to_be_visible()
    # 정상 등록이므로 오류 메시지는 표시되지 않는다
    expect(page.locator(ERROR_MESSAGE)).to_have_text("")
