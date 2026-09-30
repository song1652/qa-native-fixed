"""탐색 테스트에서 찾은 TC 스튜디오 문제 회귀 검증 (doc: TC_Studio_문제점_정리 #1~#12).
실행: .venv/bin/python -m pytest tests/unit/tc_library/test_tc_studio_fixes_e2e.py"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json
from tests.unit.tc_library.source_fixtures import PRD_MD
from tests.unit.tc_library.test_tc_studio_e2e import S, _seed


@pytest.fixture
def studio(tmp_path: Path, page: Page, fake_claude):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    with dashboard_server(project) as base_url:
        _seed(base_url, tmp_path)
        page.goto(base_url + "/tc-studio")
        expect(rows(page)).to_have_count(6)
        yield base_url, page, tmp_path


def rows(page: Page):
    return page.locator("#grid-body tr[data-case]")


def case(base: str, case_id: str) -> dict:
    status, body = request_json(base, "GET", f"/api/tc-library/{S}/cases/{case_id}")
    assert status == 200, body
    return body["case"]


def total(base: str) -> int:
    return request_json(base, "GET", f"/api/tc-library/{S}?limit=1")[1]["total"]


def add_case(base: str, **fields) -> dict:
    body = {"sheet": "혜택", "path": ["혜택 탭", "상단 배너", ""], "feature": "추가 케이스",
            "steps": ["앱 실행"], "expected": "결과", "priority": "P2", **fields}
    status, res = request_json(base, "POST", f"/api/tc-library/{S}/cases", body)
    assert status in (200, 201), res
    return res["case"]


def open_row(page: Page, n: int) -> str:
    row = rows(page).nth(n)
    row.locator("td.no").click()
    case_id = row.get_attribute("data-case")
    expect(page.locator("#d-id")).to_have_text(case_id)
    return case_id


def generate(page: Page, tmp_path: Path) -> None:
    prd = tmp_path / "prd.md"
    prd.write_text(PRD_MD, encoding="utf-8")
    page.locator('[data-id="nav-tab-generate"]').click()
    page.locator('[data-id="src-file-input"]').set_input_files(str(prd))
    expect(page.locator('[data-id="src-chip"]')).to_have_count(1)
    page.locator('[data-id="gen-target-sheet"]').select_option("혜택")
    page.locator('[data-id="gen-path-l2"]').select_option("상단 배너")
    page.locator('[data-id="gen-submit"]').click()
    expect(page.locator("#job-done")).to_be_visible(timeout=15000)


# ── #1 저장하지 않은 변경 ──────────────────────────────────────
def test_unsaved_detail_edit_asks_before_switching_case(studio):
    base, page, _ = studio
    first = open_row(page, 0)
    original = case(base, first)["expected"]
    page.locator('[data-id="detail-expected"]').fill("저장하지 않은 수정")

    rows(page).nth(1).locator("td.no").click()
    expect(page.locator('[data-id="dirty-modal"]')).to_be_visible()
    page.locator('[data-id="dirty-cancel"]').click()
    expect(page.locator("#d-id")).to_have_text(first)
    expect(page.locator('[data-id="detail-expected"]')).to_have_value("저장하지 않은 수정")

    rows(page).nth(1).locator("td.no").click()
    page.locator('[data-id="dirty-discard"]').click()
    expect(page.locator("#d-id")).to_have_text(rows(page).nth(1).get_attribute("data-case"))
    assert case(base, first)["expected"] == original

    second = page.locator("#d-id").inner_text()
    page.locator('[data-id="detail-expected"]').fill("저장하고 이동")
    rows(page).nth(2).locator("td.no").click()
    page.locator('[data-id="dirty-save"]').click()
    expect(page.locator("#d-id")).to_have_text(rows(page).nth(2).get_attribute("data-case"))
    assert case(base, second)["expected"] == "저장하고 이동"


def test_unsaved_detail_edit_blocks_suite_switch_until_confirmed(studio):
    base, page, tmp_path = studio
    _seed(base, tmp_path, suite="다른스위트", sheets=["홈"])
    page.reload()
    open_row(page, 0)
    page.locator('[data-id="detail-expected"]').fill("저장하지 않은 수정")
    page.locator('[data-id="suite-select"]').select_option("다른스위트")
    expect(page.locator('[data-id="dirty-modal"]')).to_be_visible()
    page.keyboard.press("Escape")
    expect(page.locator('[data-id="dirty-modal"]')).to_be_hidden()
    expect(page.locator('[data-id="suite-select"]')).to_have_value("야핏무브")
    expect(page.locator('[data-id="detail-expected"]')).to_have_value("저장하지 않은 수정")


# ── #6·#7 저장 실패 롤백 · 연타 ────────────────────────────────
def test_failed_grid_save_restores_server_value(studio):
    base, page, _ = studio
    row = rows(page).first
    case_id = row.get_attribute("data-case")
    before = case(base, case_id)["priority"]
    new = "P3" if before != "P3" else "P0"
    page.route(re.compile(r".*/api/tc-library/.*/cases/.*"),
               lambda r: r.abort() if r.request.method == "PATCH" else r.continue_())
    row.locator('[data-id="grid-cell-priority"]').select_option(new)
    expect(page.locator(".toast.err")).to_contain_text(f"{case_id} 저장 실패")
    expect(rows(page).first.locator('[data-id="grid-cell-priority"]')).to_have_value(before)
    page.unroute(re.compile(r".*/api/tc-library/.*/cases/.*"))
    page.locator('[data-id="toast-save-retry"]').click()
    expect(page.locator(".toast.ok").last).to_contain_text(f"{case_id} 저장됨")
    assert case(base, case_id)["priority"] == new


def test_add_case_button_creates_one_case_per_press_burst(studio):
    base, page, _ = studio
    before = total(base)
    button = page.locator('[data-id="btn-add-case"]')
    for _ in range(3):
        button.click(force=True, no_wait_after=True)
    expect(page.locator("#d-id")).not_to_have_text("")
    expect(button).to_be_enabled()
    assert total(base) == before + 1
    expect(page.locator('[data-id="suite-select"] option')).to_have_text([f"야핏무브 ({before + 1})"])   # #10


# ── #3·#4·#5 레이아웃 · 대량 · 긴 셀 ───────────────────────────
def test_grid_stays_usable_on_laptop_width(studio):
    _, page, _ = studio
    page.set_viewport_size({"width": 1280, "height": 800})
    open_row(page, 0)
    width = lambda: page.locator("#grid-wrap").bounding_box()["width"]   # noqa: E731
    assert width() > 600, width()           # 상세 패널이 그리드 위에 겹쳐 뜬다 (이전 280px)
    page.locator('[data-id="tree-toggle"]').click()
    expect(page.locator(".tree-pane")).to_be_hidden()
    assert width() > 850
    page.reload()
    expect(page.locator(".tree-pane")).to_be_hidden()      # 트리 숨김은 기억한다
    page.set_viewport_size({"width": 390, "height": 800})
    assert page.evaluate("document.scrollingElement.scrollWidth - window.innerWidth") <= 0


def test_long_cell_is_clamped_and_large_lists_render_in_chunks(studio):
    base, page, _ = studio
    add_case(base, feature="긴 텍스트 " + "가" * 200, expected="아주 긴 기대 결과 문장입니다. " * 300)
    for n in range(160):
        add_case(base, feature=f"대량 케이스 {n}")
    page.reload()
    expect(rows(page)).to_have_count(150)
    expect(page.locator('[data-id="grid-more"]')).to_contain_text("150 / 167건")
    page.locator('[data-id="grid-more"]').scroll_into_view_if_needed()
    expect(rows(page)).to_have_count(167)
    expect(page.locator('[data-id="grid-more"]')).to_have_count(0)
    long_row = page.locator("#grid-body tr[data-case]", has_text="긴 텍스트")
    assert long_row.bounding_box()["height"] < 150


# ── #2·#8·#9·#10 생성 · 검토 ───────────────────────────────────
def test_generate_button_waits_for_target(studio):
    _, page, tmp_path = studio
    prd = tmp_path / "prd.md"
    prd.write_text(PRD_MD, encoding="utf-8")
    page.locator('[data-id="nav-tab-generate"]').click()
    page.locator('[data-id="src-file-input"]').set_input_files(str(prd))
    expect(page.locator('[data-id="gen-submit"]')).to_be_disabled()
    expect(page.locator("#gen-hint")).to_have_text("넣을 시트와 대분류를 고르세요")
    page.locator('[data-id="gen-target-sheet"]').select_option("혜택")
    expect(page.locator('[data-id="gen-submit"]')).to_be_enabled()


def test_restored_job_is_marked_past_and_can_be_dismissed(studio):
    _, page, tmp_path = studio
    generate(page, tmp_path)
    expect(page.locator('[data-id="job-when"]')).to_have_text("")
    page.reload()
    page.locator('[data-id="nav-tab-generate"]').click()
    expect(page.locator('[data-id="job-when"]')).to_have_text(re.compile(r"^지난 작업 · \d\d-\d\d \d\d:\d\d$"))
    page.locator('[data-id="job-dismiss"]').click()
    expect(page.locator("#job")).to_be_hidden()
    page.reload()
    page.locator('[data-id="nav-tab-generate"]').click()
    expect(page.locator("#job")).to_be_hidden()


def test_reviewed_job_resets_generate_form_to_blank(studio):
    base, page, tmp_path = studio
    generate(page, tmp_path)
    page.locator('[data-id="job-open-review"]').click()
    expect(page.locator('[data-id="draft-card"]')).to_have_count(2)
    for _ in range(2):                      # 추정 문구가 있어 일괄 승인 대상이 아니므로 하나씩 승인한다
        page.locator('article.dcard.draft [data-id="draft-approve"]').first.click()
        page.wait_for_timeout(300)
    expect(page.locator("#rv-left")).to_have_text("0")
    expect(page.locator(".toast.ok").last).to_contain_text("새 양식으로 비웠습니다")
    page.locator('[data-id="nav-tab-generate"]').click()          # 검토를 마치면 바로 처음 양식
    expect(page.locator("#job")).to_be_hidden()
    expect(page.locator('[data-id="src-chip"]')).to_have_count(0)
    expect(page.locator('[data-id="gen-target-sheet"]')).to_have_value("")
    expect(page.locator('[data-id="gen-submit"]')).to_be_disabled()
    page.reload()                                                  # 다시 열어도 처음 양식
    page.locator('[data-id="nav-tab-generate"]').click()
    expect(page.locator('[data-id="gen-submit"]')).to_be_visible()
    expect(page.locator("#job")).to_be_hidden()
    expect(page.locator('[data-id="src-chip"]')).to_have_count(0)
    expect(page.locator('[data-id="gen-target-sheet"]')).to_have_value("")


def test_removing_source_after_generation_keeps_review_excerpt(studio):
    base, page, tmp_path = studio
    add_case(base, feature="사람이 추가한 초안")        # 작업 밖의 초안 (배지와 검토 화면 기준이 다른 경우)
    generate(page, tmp_path)
    page.locator('[data-id="src-chip-remove"]').click()
    expect(page.locator('[data-id="src-chip"]')).to_have_count(0)
    page.locator('[data-id="job-open-review"]').click()
    expect(page.locator('[data-id="draft-card"]')).to_have_count(2)
    expect(page.locator('[data-id="source-excerpt"]')).not_to_contain_text("불러오지 못했습니다")
    expect(page.locator('[data-id="source-excerpt"] h5')).to_be_visible()
    page.locator('[data-id="review-show-all"]').click()
    expect(page.locator('[data-id="draft-card"]')).to_have_count(3)


# ── #12 공통 폴링 ──────────────────────────────────────────────
def test_studio_does_not_poll_dashboard_apis_every_five_seconds(studio):
    _, page, _ = studio
    calls = []
    page.on("request", lambda r: calls.append(r.url) if "/api/dialogs" in r.url else None)
    page.wait_for_timeout(12000)          # time.sleep은 sync API의 이벤트 전달을 막는다
    assert len(calls) <= 1, calls


# ── 스위트 목록: 디자인 목록을 항상 아래로 연다 ────────────────
def test_suite_list_opens_below_with_studio_style(studio):
    base, page, tmp_path = studio
    _seed(base, tmp_path, suite="다른스위트", sheets=["홈"])
    page.reload()
    select = page.locator('[data-id="suite-select"]')
    assert select.evaluate("e => getComputedStyle(e).appearance") == "base-select"
    select.click()
    first = page.locator('[data-id="suite-select"] option').first
    expect(first).to_be_visible()
    box = select.bounding_box()
    assert first.bounding_box()["y"] >= box["y"] + box["height"]
    page.locator('[data-id="suite-select"] option', has_text="다른스위트").click()
    expect(rows(page)).to_have_count(1)


# ── 스위트 삭제·휴지통 ─────────────────────────────────────────
def open_suite_delete(page: Page):
    page.locator('[data-id="suite-menu-btn"]').click()
    page.locator('[data-id="suite-menu-delete"]').click()
    expect(page.locator('[data-id="suite-delete-modal"]')).to_be_visible()


def test_delete_suite_switches_to_next_and_undo_restores(studio):
    base, page, tmp_path = studio
    _seed(base, tmp_path, suite="다른스위트", sheets=["홈"])
    page.reload()
    page.locator('[data-id="suite-select"]').select_option("야핏무브")
    expect(rows(page)).to_have_count(6)
    open_suite_delete(page)
    expect(page.locator("#sd-title")).to_have_text("'야핏무브' 스위트를 삭제할까요?")
    expect(page.locator('[data-id="suite-delete-summary"]')).to_have_text(re.compile(r"TC\s*6\s*건\s*시트\s*2\s*개"))
    page.locator('[data-id="suite-delete-confirm"]').click()
    expect(page.locator('[data-id="suite-delete-modal"]')).to_be_hidden()
    expect(page.locator('[data-id="suite-select"] option')).to_have_text(["다른스위트 (1)"])
    expect(page.locator(".toast.ok").last).to_contain_text("'다른스위트' 스위트로 전환했습니다")
    status, body = request_json(base, "POST", f"/api/tc-library/{S}/cases", {"sheet": "혜택", "path": ["혜택 탭"], "feature": "늦은 요청"})
    assert status == 404 and body["code"] == "SUITE_NOT_FOUND"          # 지운 스위트를 되살리지 않는다
    page.locator('[data-id="suite-delete-undo"]').click()
    expect(page.locator('[data-id="suite-select"]')).to_have_value("야핏무브")
    expect(rows(page)).to_have_count(6)


def test_deleted_suite_can_be_restored_from_trash_list(studio):
    base, page, _ = studio
    open_suite_delete(page)
    page.locator('[data-id="suite-delete-confirm"]').click()
    expect(page.locator('[data-id="suite-select"] option')).to_have_text(["스위트 없음"])
    page.locator('[data-id="suite-menu-btn"]').click()
    expect(page.locator("#trash-n")).to_have_text("1")
    page.locator('[data-id="suite-menu-trash"]').click()
    item = page.locator('[data-id="trash-list"] li')
    expect(item).to_contain_text("야핏무브")
    expect(item).to_contain_text("TC 6건 · 시트 2개")
    expect(item).to_contain_text("30일 남음")
    item.locator('[data-id="trash-restore"]').click()
    expect(page.locator('[data-id="trash-modal"]')).to_be_hidden()
    expect(page.locator('[data-id="suite-select"]')).to_have_value("야핏무브")
    expect(rows(page)).to_have_count(6)


def test_suite_delete_is_blocked_while_generation_runs(studio, monkeypatch):
    base, page, tmp_path = studio
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "slow")
    prd = tmp_path / "prd.md"
    prd.write_text(PRD_MD, encoding="utf-8")
    page.locator('[data-id="nav-tab-generate"]').click()
    page.locator('[data-id="src-file-input"]').set_input_files(str(prd))
    page.locator('[data-id="gen-target-sheet"]').select_option("혜택")
    page.locator('[data-id="gen-submit"]').click()
    expect(page.locator('[data-id="job-cancel"]')).to_be_visible()
    open_suite_delete(page)
    expect(page.locator('[data-id="suite-delete-block"]')).to_contain_text("초안 생성이 진행 중입니다")
    expect(page.locator('[data-id="suite-delete-confirm"]')).to_be_disabled()
    status, body = request_json(base, "DELETE", f"/api/tc-library/{S}?confirm={S}")
    assert status == 409 and body["code"] == "JOB_RUNNING"
    page.locator('[data-id="suite-delete-cancel"]').click()
    page.locator('[data-id="job-cancel"]').click()
    expect(page.locator("#job-fail")).to_be_visible(timeout=15000)
