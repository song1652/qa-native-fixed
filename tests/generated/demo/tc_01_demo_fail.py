"""Demo: trace 기능 검증용 실패 TC"""
from playwright.sync_api import expect


def test_demo_fail(page):
    page.goto("https://example.com")
    page.wait_for_load_state("networkidle")

    # 의도적 실패: example.com에 없는 버튼 클릭 시도
    expect(page.locator("#non-existent-login-button")).to_be_visible(timeout=3000)
