"""
tc_CL_02_customer_login_wrong_credentials_error.py
- 고객 로그인 잘못된 자격증명 에러 검증
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
- 테스트 함수명: test_customer_login_wrong_credentials_error
"""
import json
import re
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"
TEST_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "test_data.json"


def _load_test_data() -> dict:
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def test_customer_login_wrong_credentials_error(page: Page):
    """
    CL_02: 존재하지 않는 아이디와 잘못된 비밀번호로 고객 로그인 시도 시
    #LoginMsg DOM 에러 메시지 영역에 오류 텍스트가 표시되고 페이지 이동이 없는지 확인.
    """
    # 테스트 데이터 로드 — 하드코딩 금지
    test_data = _load_test_data()
    login_data = test_data["serveone"]["login"]
    invalid_customer_id = login_data["invalid_customer_id"]
    invalid_password = login_data["invalid_password"]

    # 페이지 이동 및 초기 로드 대기
    page.goto(BASE_URL)
    # SPA 페이지이므로 networkidle 대신 특정 요소 visible 대기
    page.locator("#userId").wait_for(state="visible", timeout=15000)

    # 고객 로그인 탭이 기본 active이므로 #userId / #userPw 바로 사용 가능
    page.locator("#userId").fill(invalid_customer_id)
    page.locator("#userPw").fill(invalid_password)

    # 로그인 버튼 클릭
    page.locator("#btnCustomerLogin").click()

    # #LoginMsg 에러 메시지 영역 가시성 대기 (parallel_plan: wait_for visible timeout=8000)
    error_loc = page.locator("#LoginMsg")
    error_loc.wait_for(state="visible", timeout=8000)

    msg_text = error_loc.inner_text().strip()

    # assertion 무결성: 단순 assert msg_text 금지, 키워드 조건 검사 필수
    # lessons_learned 2026-09-01: assert msg_text → assert any(keyword in ...) 복원
    error_keywords = ["아이디", "패스워드", "정확하지 않습니다", "id", "password"]
    assert any(keyword in msg_text.lower() for keyword in [k.lower() for k in error_keywords]), (
        f"예상 에러 메시지 없음. 실제: {msg_text!r}"
    )

    # 페이지 잔류 확인 — 로그인 페이지에 머무는지 검증
    assert "/cmm/login" in page.url, (
        f"로그인 페이지에 머물러야 하나 URL 변경됨: {page.url!r}"
    )

    # 증거 스크린샷
    page.screenshot(path="tests/screenshots/tc_CL_02_customer_login_wrong_credentials_error.png")
