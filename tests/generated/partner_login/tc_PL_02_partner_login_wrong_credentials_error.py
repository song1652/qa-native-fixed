"""
tc_PL_02_partner_login_wrong_credentials_error.py
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
- 테스트: 협력사 로그인 잘못된 자격증명 에러
- 기대: "아이디 또는 패스워드를 확인하시기 바랍니다." 다이얼로그 팝업 표시
"""
import json
import re
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"
TEST_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "test_data.json"


def test_partner_login_wrong_credentials_error(page: Page):
    """협력사 로그인 — 잘못된 자격증명 제출 시 에러 다이얼로그 팝업 검증"""
    # 테스트 데이터 로드
    with open(TEST_DATA_PATH, encoding="utf-8") as f:
        test_data = json.load(f)

    invalid_partner_id = test_data["serveone"]["login"]["invalid_partner_id"]
    invalid_password = test_data["serveone"]["login"]["invalid_password"]

    # 페이지 이동
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Dialog 핸들러 등록 (click 전 필수, goto 직후 등록)
    dialog_messages: list[str] = []

    def _handle_dialog(dialog):
        dialog_messages.append(dialog.message)
        dialog.accept()

    page.on("dialog", _handle_dialog)

    # 협력사 로그인 탭 클릭
    page.locator("#vendorTab").click()

    # 탭 전환 후 협력사 폼 활성화 대기 (초기 visible:false → 전환 후 visible)
    page.locator("#cprtcpUsrId").wait_for(state="visible", timeout=5000)

    # 잘못된 자격증명 입력
    page.locator("#cprtcpUsrId").fill(invalid_partner_id)
    page.locator("#cprtcpSectNo").fill(invalid_password)

    # 협력사 로그인 버튼 클릭
    page.locator("#btnVendorLogin").click()

    # Dialog 발생 대기 (서버 응답 + SPA 비동기 처리 고려)
    page.wait_for_timeout(3000)

    # Assertions
    assert len(dialog_messages) > 0, "다이얼로그가 표시되지 않았습니다"

    error_keywords = ["아이디", "패스워드", "비밀번호", "확인"]
    assert any(
        keyword in dialog_messages[0] for keyword in error_keywords
    ), f"예상 키워드가 다이얼로그 메시지에 없습니다. 실제 메시지: {dialog_messages[0]}"

    # 페이지 잔류 확인 (로그인 페이지에서 이동 없음)
    assert "/cmm/login" in page.url, f"로그인 페이지에 잔류해야 합니다. 현재 URL: {page.url}"

    # 증거 스크린샷
    page.screenshot(path="tests/screenshots/tc_PL_02_partner_login_wrong_credentials_error.png")
