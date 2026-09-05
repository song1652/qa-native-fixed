"""
tc_PL_01_partner_login_empty_fields_validation.py
- BASE_URL, import, 상수를 이 파일에 직접 포함 (공유 헬퍼 금지)
- 테스트 함수명: test_partner_login_empty_fields_validation
"""
from playwright.sync_api import Page, expect

BASE_URL = "https://mall.serveone.co.kr/M3/cmm/login.dev"


def test_partner_login_empty_fields_validation(page: Page) -> None:
    """TC PL-01: 협력사 로그인 빈 필드 유효성 검증"""
    # Arrange: dialog 핸들러를 버튼 클릭 전에 등록 (race condition 방지)
    dialog_message = []
    page.on("dialog", lambda d: (dialog_message.append(d.message), d.accept()))

    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle")

    # Act: 협력사 탭 클릭 — 초기 hidden이므로 탭 전환 필수
    page.locator("#vendorTab").click()
    page.wait_for_selector("#vendorLogin", state="visible", timeout=5000)

    # 필드가 visible한지 확인 후 진행
    id_input = page.locator("#cprtcpUsrId")
    pw_input = page.locator("#cprtcpSectNo")
    expect(id_input).to_be_visible()
    expect(pw_input).to_be_visible()

    # 빈 상태로 로그인 버튼 클릭
    id_input.fill("")
    pw_input.fill("")
    page.locator("#btnVendorLogin").click()

    # SPA 렌더링 대기 (dialog가 발생할 시간)
    page.wait_for_timeout(1500)

    # Assert: "사용자 아이디는 필수입력 입니다." 다이얼로그 팝업 검증
    assert len(dialog_message) > 0, "빈 필드 로그인 시 다이얼로그가 표시되어야 합니다"
    assert "사용자 아이디는 필수입력 입니다." in dialog_message[0], (
        f"예상 메시지가 포함되지 않음: '{dialog_message[0]}'"
    )

    # 페이지 이동 없이 로그인 페이지 유지 검증
    assert "/cmm/login" in page.url, (
        f"빈 필드 로그인 후 로그인 페이지를 벗어남: {page.url}"
    )
