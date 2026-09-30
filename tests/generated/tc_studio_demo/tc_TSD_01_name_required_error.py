"""
자동 생성된 Playwright 테스트 코드
URL: http://localhost:8877
케이스: name_required_error (TSD_01)

TC: testcases/tc_studio_demo/tc_TSD_01_이름_미입력_오류_표시.md
Claude Code가 plan 기반으로 완성한 파일.
수동 편집 가능.
"""
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8877"

NAME_INPUT = '[name="name"]'
SUBMIT_BUTTON = 'button[type="submit"]'
ERROR_MESSAGE = "#error"
RESULT_MESSAGE = "#result"

EXPECTED_ERROR = "이름을 입력하세요."


def test_name_required_error(page: Page) -> None:
    """이름을 비운 채 등록하면 이름 입력을 요구하는 오류 메시지가 표시된다."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Step 1. 이름을 비워 둔다 (사전 조건: 새 페이지이므로 빈 값인지 단정)
    expect(page.locator(NAME_INPUT)).to_have_value("")

    # Step 2. 등록 버튼을 누른다
    page.locator(SUBMIT_BUTTON).click()

    # Expected: 이름 입력을 요구하는 오류 메시지가 표시된다 ("이름을 입력하세요.")
    expect(page.locator(ERROR_MESSAGE)).to_have_text(EXPECTED_ERROR)
    expect(page.locator(ERROR_MESSAGE)).to_be_visible()
    # 오류 상황이므로 완료 메시지는 표시되지 않는다
    expect(page.locator(RESULT_MESSAGE)).to_have_text("")
