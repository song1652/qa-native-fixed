"""Trace Viewer Locator 확인용 — 링크 클릭으로 5단계 페이지 이동"""
from playwright.sync_api import expect


def test_five_steps(page):
    # Step 1: 홈 접속 → "Docs" 링크 클릭으로 이동
    page.goto("https://playwright.dev")
    page.wait_for_load_state("networkidle")
    page.get_by_role("link", name="Docs").click()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_role("heading", name="Installation")).to_be_visible()

    # Step 2: Intro 페이지 → 사이드바 "Release notes" 클릭으로 이동
    page.get_by_role("link", name="Release notes").click()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_role("heading", level=1).first).to_be_visible()

    # Step 3: Release Notes → 상단 네비 "API" 클릭으로 이동 (네비 영역으로 스코프 한정)
    page.get_by_role("navigation", name="Main").get_by_role("link", name="API").click()
    page.wait_for_load_state("networkidle")
    expect(page.get_by_role("heading", level=1).first).to_be_visible()

    # Step 4: API 페이지 → Trace Viewer 문서로 직접 이동 후 검색 버튼 클릭
    page.goto("https://playwright.dev/docs/trace-viewer")
    page.wait_for_load_state("networkidle")
    expect(page.get_by_role("heading", name="Trace viewer").first).to_be_visible()
    page.get_by_role("button", name="Search").click()
    page.keyboard.press("Escape")

    # Step 5: 없는 버튼 클릭 시도 → 의도적 실패 (Locator 확인)
    page.get_by_role("button", name="존재하지않는버튼").click(timeout=3000)
