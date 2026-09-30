"""TC 스튜디오 생성·검토 화면 실제 브라우저 검증 (Phase 2 W5·W6). 가짜 claude CLI를 쓴다."""
from __future__ import annotations

from pathlib import Path

import openpyxl
import pytest
from playwright.sync_api import Page, expect

from tests.unit.import_studio.import_studio_test_support import dashboard_server
from tests.unit.tc_library.source_fixtures import PRD_MD
from tests.unit.tc_library.test_tc_studio_e2e import _seed


@pytest.fixture
def studio(tmp_path: Path, page: Page, fake_claude):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    with dashboard_server(project) as base_url:
        _seed(base_url, tmp_path)
        page.goto(base_url + "/tc-studio")
        expect(page.locator("#grid-body tr[data-case]")).to_have_count(6)
        yield base_url, page, tmp_path


def _generate(page: Page, tmp_path: Path) -> None:
    prd = tmp_path / "prd.md"
    prd.write_text(PRD_MD, encoding="utf-8")
    page.locator('[data-id="nav-tab-generate"]').click()
    page.locator('[data-id="src-file-input"]').set_input_files(str(prd))
    expect(page.locator('[data-id="src-chip"]')).to_have_count(1)
    page.locator('[data-id="gen-target-sheet"]').select_option("혜택")
    page.locator('[data-id="gen-path-l2"]').select_option("상단 배너")
    page.locator('[data-id="gen-submit"]').click()


# ── W5: 새로 생성 ─────────────────────────────────────────────
def test_generate_job_runs_to_done(studio):
    _, page, tmp_path = studio
    _generate(page, tmp_path)
    expect(page.locator("#job-done")).to_be_visible(timeout=15000)
    expect(page.locator("#job-done-tag")).to_have_text("초안 2건 · 형식 오류 0건")


def test_failed_job_shows_log_and_retry(studio, monkeypatch):
    _, page, tmp_path = studio
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "error")
    _generate(page, tmp_path)
    expect(page.locator("#job-fail")).to_be_visible(timeout=15000)
    expect(page.locator('[data-id="job-log-tail"]')).to_contain_text("CLAUDE_ERROR")
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "ok")
    page.locator('[data-id="job-retry"]').click()
    expect(page.locator("#job-done")).to_be_visible(timeout=15000)


def test_profile_edit_and_save(studio):
    _, page, _ = studio
    page.locator('[data-id="nav-tab-generate"]').click()
    page.locator('[data-id="gen-profile-edit"]').click()
    page.locator('[data-id="gen-rules-input"]').fill("경계값을 모두 쓴다\n금액은 원 단위")
    page.locator('[data-id="gen-profile-name"]').fill("결제 엄격")
    page.locator('[data-id="gen-profile-save"]').click()
    expect(page.locator('[data-id="gen-profile"]')).to_have_value("결제 엄격")
    expect(page.locator("#gen-rules li").first).to_have_text("경계값을 모두 쓴다")


# ── W6: 초안 검토 (계획의 빈 테스트 블록 보완) ──────────────────
def _open_review(page, tmp_path):
    _generate(page, tmp_path)
    expect(page.locator("#job-done")).to_be_visible(timeout=15000)
    expect(page.locator("#cnt-review")).to_have_text("2")
    page.locator('[data-id="job-open-review"]').click()
    expect(page.locator('[data-id="draft-card"]')).to_have_count(2)
    return page.locator('[data-id="draft-card"]')


def test_review_quote_approve_reject_and_undo(studio):
    _, page, tmp_path = studio
    cards = _open_review(page, tmp_path)
    expect(page.locator('[data-id="source-excerpt"] mark')).to_have_count(1)
    expect(cards.first).to_contain_text("추정")
    cards.first.locator('[data-id="draft-approve"]').click()
    expect(cards.first).to_contain_text("승인")
    expect(page.locator("#rv-ok")).to_have_text("1")
    expect(page.locator("#cnt-review")).to_have_text("1")
    page.locator('[data-id="draft-undo"]').click()
    expect(page.locator("#rv-ok")).to_have_text("0")
    expect(page.locator("#rv-left")).to_have_text("2")
    cards.nth(1).locator('[data-id="draft-reject"]').click()
    expect(page.locator("#rv-rej")).to_have_text("1")
    expect(page.locator("#cnt-review")).to_have_text("1")


def test_review_regeneration_preserves_case_and_bulk_skips_estimates(studio):
    _, page, tmp_path = studio
    cards = _open_review(page, tmp_path)
    case_id = cards.first.get_attribute("data-case")
    page.locator('[data-id="review-approve-clean"]').click()
    expect(page.locator("#rv-left")).to_have_text("2")
    cards.first.locator('[data-id="draft-regen"]').click()
    cards.first.locator('[data-id="draft-regen-note"]').fill("배너 경계 조건을 다시 확인하세요")
    cards.first.locator('[data-id="draft-regen-submit"]').click()
    expect(page.locator("#tcs-toasts")).to_contain_text("다시 만들었습니다", timeout=15000)
    expect(cards.first).to_have_attribute("data-case", case_id)
    expect(cards).to_have_count(2)
    expect(cards.first.locator('[data-id="draft-approve"]')).to_be_enabled()

# ── W7: 가져오기 직접 매핑 ─────────────────────────────────────
def test_import_with_custom_mapping(studio):
    _, page, tmp_path = studio
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "로그인"
    ws.append(["ID", "제목", "절차", "기대 결과"])
    ws.append(["L-1", "로그인 성공", "1. 아이디 입력\n2. 로그인 선택", "홈으로 이동한다."])
    path = tmp_path / "other.xlsx"
    wb.save(path)
    page.locator('[data-id="btn-import-xlsx"]').click()
    page.locator('[data-id="import-mapping-mode"]').select_option("custom")
    page.locator('[data-id="import-file-input"]').set_input_files(str(path))
    expect(page.locator('[data-id="import-sheets"] .radio')).to_have_count(1)
    page.locator('[data-id="import-suite"]').fill("웹")
    page.locator('[data-prefix="로그인"]').fill("LOG")
    page.locator('[data-id="import-plan"]').click()
    page.locator('[data-id="import-confirm"]').click()
    expect(page.locator('[data-id="suite-select"]')).to_have_value("웹")
    expect(page.locator("#grid-body tr[data-case]")).to_have_count(1)


def test_reload_restores_saved_sources_target_and_review_job(studio):
    _, page, tmp_path = studio
    _generate(page, tmp_path)
    expect(page.locator('#job-done')).to_be_visible(timeout=15000)
    page.reload()
    page.locator('[data-id="nav-tab-generate"]').click()
    expect(page.locator('[data-id="src-chip"]')).to_have_count(1)
    expect(page.locator('[data-id="gen-target-sheet"]')).to_have_value('혜택')
    expect(page.locator('[data-id="gen-path-l2"]')).to_have_value('상단 배너')
    expect(page.locator('[data-id="job-open-review"]')).to_be_visible()
    page.locator('[data-id="job-open-review"]').click()
    expect(page.locator('[data-id="draft-card"]')).to_have_count(2)
    expect(page.locator('[data-id="draft-regen"]').first).to_be_enabled()
    # 새 브라우저에서도 세션 저장소 없이 서버에 남은 소스를 읽는다.
    other = page.context.browser.new_context()
    try:
        fresh = other.new_page()
        fresh.goto(page.url)
        fresh.locator('[data-id="nav-tab-generate"]').click()
        expect(fresh.locator('[data-id="src-chip"]')).to_have_count(1)
        expect(fresh.locator('[data-id="gen-target-sheet"]')).to_have_value('혜택')
    finally:
        other.close()


def test_profile_style_imported_from_excel_and_saved(studio):
    _, page, tmp_path = studio
    page.locator('[data-id="nav-tab-generate"]').click()
    page.locator('[data-id="gen-profile-edit"]').click()
    page.locator('[data-id="gen-style-file"]').set_input_files(str(tmp_path / "seed.xlsx"))
    expect(page.locator("#tcs-toasts")).to_contain_text("문체를 읽었습니다")
    expect(page.locator('[data-id="gen-endings-input"]')).not_to_have_value("")
    expect(page.locator('[data-id="gen-profile-examples"]')).to_contain_text("기준 예시")
    expect(page.locator('[data-id="gen-profile-name"]')).to_have_value("seed")
    page.locator('[data-id="gen-profile-save"]').click()
    expect(page.locator('[data-id="gen-profile"]')).to_have_value("seed")
    expect(page.locator("#gen-rules")).to_contain_text("Expected 끝맺음")
    expect(page.locator("#gen-rules")).to_contain_text("기준 예시")


def test_review_marks_drafts_that_break_profile_style_and_bulk_skips_them(studio):
    base_url, page, tmp_path = studio
    from tests.unit.import_studio.import_studio_test_support import request_json
    status, _ = request_json(base_url, "PUT", "/api/tc-library/profiles/%EB%AC%B8%EC%B2%B4",
                             {"rules": ["규칙"], "expected_endings": ["없는끝."]})
    assert status == 200
    page.reload()
    expect(page.locator("#grid-body tr[data-case]")).to_have_count(6)       # 첫 로딩이 끝난 뒤 조작 (선택이 덮이지 않게)
    page.locator('[data-id="nav-tab-generate"]').click()
    page.locator('[data-id="gen-profile"]').select_option("문체")
    expect(page.locator("#gen-rules")).to_contain_text("없는끝.")            # 이 프로필로 생성된다
    cards = _open_review(page, tmp_path)
    expect(cards.first.locator('[data-id="draft-style"]')).to_have_attribute("title", "Expected 끝맺음이 작성 규칙과 다릅니다 (없는끝.)")
    page.locator('[data-id="review-approve-clean"]').click()
    expect(page.locator("#rv-left")).to_have_text("2")
