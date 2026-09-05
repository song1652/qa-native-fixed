import json
from pathlib import Path
from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"
TEST_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "test_data.json"


def test_customer_login_wrong_credentials_error(page: Page) -> None:
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # test_data.json에서 잘못된 자격증명 읽기
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        test_data = json.load(f)

    invalid_customer_id = test_data["serveone"]["login"]["invalid_customer_id"]
    invalid_password = test_data["serveone"]["login"]["invalid_password"]

    # 아이디/비밀번호 입력
    page.fill("#userId", invalid_customer_id)
    page.fill("#userPw", invalid_password)

    # 고객 로그인 버튼 클릭
    page.click("#btnCustomerLogin")

    # #LoginMsg 요소가 visible 상태가 될 때까지 대기
    page.wait_for_selector("#LoginMsg", state="visible", timeout=20000)

    # 에러 메시지 텍스트 추출
    msg_text = page.inner_text("#LoginMsg")

    # 에러 메시지 검증 (키워드 포함 여부 확인)
    error_keywords = ["사용자 id", "패스워드", "정확하지 않습니다"]
    assert any(keyword in msg_text.lower() for keyword in error_keywords), (
        f"예상 에러 메시지 키워드가 포함되지 않았습니다. 실제 메시지: {msg_text}"
    )

    # 페이지 이동 없이 로그인 페이지 유지 확인
    assert "/cmm/login" in page.url, (
        f"페이지가 로그인 페이지를 벗어났습니다. 현재 URL: {page.url}"
    )
