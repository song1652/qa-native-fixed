"""Large-screen readability and responsive chart/report interactions."""
import json
import sys
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts'))

from tests.unit.import_studio.import_studio_test_support import dashboard_server
from tests.unit.tc_library.test_tc_studio_e2e import _seed


@pytest.fixture
def page():
    # A function-scoped context allows the adjacent tests to own Sync Playwright.
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        yield page
        browser.close()
        assert not errors, errors


@pytest.mark.parametrize("width", [1920, 2560, 3840])
def test_standard_views_share_title_and_body_edges(tmp_path, page, width):
    project = tmp_path / 'project'
    (project / 'state').mkdir(parents=True)
    (project / 'state' / 'run_history.json').write_text(json.dumps([
        {'timestamp': '2026-10-11 12:00:00', 'pipeline': 'quick',
         'total': 1, 'passed': 1, 'pass_rate': 100, 'status': 'done'}
    ]))
    page.set_viewport_size({'width': width, 'height': 1080})
    with dashboard_server(project) as base:
        page.goto(base + '/?view=quick_run')
        expect(page.locator('.quick-run-grid')).to_be_visible()
        reference = page.locator('.quick-run-grid').bounding_box()
        native_left = 232 + 32 + max(0, (width - 232 - 64 - 2000) / 2)
        assert abs(reference['x'] - native_left) < 1
        for view, body, title in [('', '.ov-summary-row', '.ov-heading'),
                                  ('reports', '.report-workspace', '.pipeline-title'),
                                  ('history', '.hist-stat-row', '.hist-heading')]:
            page.evaluate('(view) => selectView(view)', view)
            expect(page.locator(body)).to_be_visible()
            bounds = page.locator(body).bounding_box()
            assert abs(bounds['x'] - reference['x']) < 1
            assert abs(bounds['width'] - reference['width']) < 1
            assert abs(page.locator(title).bounding_box()['x'] - reference['x']) < 1
        for view in ['single_pipeline', 'parallel_pipeline', 'pages', 'team_new', 'tc_studio']:
            page.evaluate('(view) => selectView(view)', view)
            heading = page.locator('#main .pipeline-title, #main .page-title')
            expect(heading).to_be_visible()
            assert abs(heading.bounding_box()['x'] - native_left) < 1
        for screen, body in [('generate', '.gen'), ('review', '.review'),
                             ('export', '.exp'), ('library', '#lib')]:
            page.locator(f'[data-id="nav-tab-{screen}"]').click()
            expect(page.locator(body)).to_be_visible()
            assert abs(page.locator(body).bounding_box()['x'] - native_left) < 1
            bounds = page.locator(body).bounding_box()
            right = bounds['x'] + bounds['width']
            for selector in ['#btn-import-xlsx', '.tc-studio .wizard']:
                control = page.locator(selector).bounding_box()
                assert abs(control['x'] + control['width'] - right) < 1, (screen, selector)


@pytest.mark.parametrize("width", [1920, 2560, 3840])
def test_large_screens_bound_content_without_hiding_studio_controls(tmp_path, page, width):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    page.set_viewport_size({"width": width, "height": 1080})
    with dashboard_server(project) as base:
        _seed(base, tmp_path)
        page.goto(base + "/tc-studio")
        expect(page.locator('#grid-body tr[data-case]')).to_have_count(6)
        assert page.locator('#tc-studio-root').bounding_box()['width'] <= 2000
        expect(page.locator('label[for="suite-select"]')).to_have_text('스위트')
        expect(page.locator('.tree-tools > b')).to_have_text('계층 트리')
        expect(page.locator('#grid th .xl').first).to_be_hidden()
        library = page.locator('#lib').bounding_box()
        main = page.locator('#main').bounding_box()
        assert abs(library['y'] + library['height'] - (main['y'] + main['height'] - 28)) < 2
        assert page.locator('.tree-pane').bounding_box()['width'] == 240
        assert page.locator('#grid-wrap').bounding_box()['height'] > 650
        assert page.locator('#lib-filter-platform').count() == 0
        page.locator('[data-id="nav-tab-generate"]').click()
        assert page.locator('.gen').bounding_box()['width'] <= 1440
        page.locator('[data-id="nav-tab-library"]').click()
        page.locator('#grid-body tr[data-case]').first.locator('td.no').click()
        expect(page.locator('.detail')).to_be_visible()
        box = page.locator('.detail').bounding_box()
        assert box['x'] + box['width'] <= width
        page.locator('#btn-import-xlsx').click()
        expect(page.locator('#import-modal')).to_be_visible()
        modal = page.locator('#import-modal .modal').bounding_box()
        assert modal['x'] >= 0 and modal['x'] + modal['width'] <= width
        assert modal['y'] >= 0 and modal['y'] + modal['height'] <= 1080


def test_trend_uses_available_width_and_resizes_without_scaling_text(tmp_path, page):
    project = tmp_path / "project"
    (project / "state").mkdir(parents=True)
    (project / "state" / "run_history.json").write_text(json.dumps([
        {"timestamp": f"2026-10-10T12:0{i}:00", "total": 4, "passed": i,
         "failed": 4-i, "status": "done"} for i in range(1, 5)
    ]))
    page.set_viewport_size({"width": 2560, "height": 1440})
    with dashboard_server(project) as base:
        page.goto(base + "/")
        expect(page.locator('.oax-trend-svg')).to_be_visible()
        for width in [2560, 1280, 1920]:
            page.set_viewport_size({"width": width, "height": 1080})
            page.wait_for_function("""() => {
                const svg = document.querySelector('.oax-trend-svg');
                return Math.abs(svg.viewBox.baseVal.width - svg.clientWidth) < 2;
            }""")
            svg = page.locator('.oax-trend-svg')
            bounds = svg.bounding_box()
            last = svg.locator('circle').last.bounding_box()
            assert last['x'] > bounds['x'] + bounds['width'] * .8
            assert svg.locator('text').first.bounding_box()['height'] >= 12


def test_history_formats_iso_and_space_timestamps_consistently(tmp_path, page):
    project = tmp_path / 'project'
    (project / 'state').mkdir(parents=True)
    (project / 'state' / 'run_history.json').write_text(json.dumps([
        {'timestamp': timestamp, 'pipeline': 'quick', 'total': 1, 'passed': 1,
         'pass_rate': 100, 'status': 'done'} for timestamp in
        ['2026-10-10T01:09:55.190147', '2026-10-10 01:09:55']
    ]))
    with dashboard_server(project) as base:
        page.goto(base + '/?view=history')
        expect(page.locator('.hist-time')).to_have_count(2)
        for cell in page.locator('.hist-time').all():
            expect(cell).to_have_text('2026-10-1001:09:55')
            expect(cell.locator('.muted')).to_have_text('01:09:55')


def test_long_discussion_titles_keep_review_actions_visible(tmp_path, page):
    with dashboard_server(tmp_path / 'project') as base:
        page.goto(base + '/')
        page.evaluate('''() => {
            currentView = 'team_0';
            lastData = {team_sessions: [{stage: 'team_discussion', stage_label: '검토',
                status: 'discussed', messages: [], conclusion_items: [{id: 1,
                status: 'pending', title: 'long'.repeat(200), text: 'https://example.com/' + 'long'.repeat(200)}]}]};
            renderTeamView(document.getElementById('main'));
        }''')
        for width in [1280, 1920, 2560, 3840]:
            page.set_viewport_size({'width': width, 'height': 1080})
            for selector in ['.vote-item-title', '.vote-item-body', '.vote-btn-n', '.vote-btn-y']:
                bounds = page.locator(selector).bounding_box()
                assert bounds['x'] >= 0 and bounds['x'] + bounds['width'] <= width
            assert page.locator('.vote-item').evaluate('(e) => e.scrollWidth <= e.clientWidth + 1')


def test_discussion_draft_survives_refresh_and_navigation(tmp_path, page):
    with dashboard_server(tmp_path / 'project') as base:
        page.goto(base + '/?view=team_new')
        topic = page.locator('#new-topic-input')
        topic.fill('작성 중인 토론 주제')
        page.evaluate('renderCurrentView()')
        expect(topic).to_have_value('작성 중인 토론 주제')
        expect(topic).to_be_focused()
        page.evaluate("selectView('pages')")
        page.evaluate("selectView('team_new')")
        expect(topic).to_have_value('작성 중인 토론 주제')
        page.evaluate('''() => {
            const originalFetch = window.fetch;
            window.fetch = (url, options) => url === '/api/discuss/start'
                ? new Promise(resolve => { window.resolveDiscussion = resolve; })
                : originalFetch(url, options);
        }''')
        page.locator('#new-topic-btn').click()
        page.evaluate("selectView('pages')")
        page.evaluate("selectView('team_new')")
        expect(page.locator('#new-topic-btn')).to_be_disabled()
        expect(page.locator('#topic-status')).to_have_text('전송 중…')
        page.evaluate("resolveDiscussion({json: async () => ({ok: false, error: '검토 오류'})})")
        expect(page.locator('#new-topic-btn')).to_be_enabled()
        expect(page.locator('#topic-status')).to_have_text('검토 오류')
        expect(topic).to_have_value('작성 중인 토론 주제')


def test_long_report_names_expand_for_mouse_and_keyboard(tmp_path, page):
    project = tmp_path / "project"
    reports = project / "tests" / "reports"
    reports.mkdir(parents=True)
    name = 'parallel_index_20261010_013452_d2a02d3f.html'
    (reports / name).write_text('<html><body>Report</body></html>')
    with dashboard_server(project) as base:
        page.goto(base + '/?view=reports')
        expect(page.locator('.report-item')).to_have_count(1)
        summary = page.locator('.report-filename summary')
        expect(summary).to_be_visible()
        expect(page.locator('.report-full-name')).to_be_hidden()
        summary.focus()
        page.keyboard.press('Enter')
        expect(page.locator('.report-full-name')).to_have_text(name)
        expect(page.locator('.report-full-name')).to_be_visible()
        page.evaluate('_renderReportsOnly()')
        expect(page.locator('.report-full-name')).to_be_visible()
        expect(summary).to_be_focused()
        summary.click()
        expect(page.locator('.report-full-name')).to_be_hidden()
        page.locator('[data-action="open"]').click()
        expect(page.locator('#report-iframe')).to_be_visible()


def test_import_modal_keeps_keyboard_focus_and_escape_returns_to_opener(tmp_path, page):
    project = tmp_path / 'project'
    (project / 'testcases').mkdir(parents=True)
    with dashboard_server(project) as base:
        _seed(base, tmp_path)
        page.goto(base + '/tc-studio')
        expect(page.locator('#grid-body tr[data-case]')).to_have_count(6)
        opener = page.locator('#btn-import-xlsx')
        opener.click()
        page.keyboard.press('Escape')
        expect(page.locator('#import-modal')).to_be_hidden()
        expect(opener).to_be_focused()
        opener.click()
        expect(page.locator('#import-close')).to_be_focused()
        page.keyboard.press('Shift+Tab')
        expect(page.locator('#import-cancel')).to_be_focused()
        page.keyboard.press('Tab')
        expect(page.locator('#import-close')).to_be_focused()
        page.locator('#import-drop').focus()
        with page.expect_file_chooser():
            page.keyboard.press('Enter')


def test_review_list_selects_one_draft_and_keyboard_skips_filtered_cases(tmp_path, page):
    project = tmp_path / 'project'
    (project / 'testcases').mkdir(parents=True)
    page.set_viewport_size({'width': 1920, 'height': 1080})
    with dashboard_server(project) as base:
        _seed(base, tmp_path)
        page.goto(base + '/tc-studio')
        expect(page.locator('#grid-body tr[data-case]')).to_have_count(6)
        page.evaluate('''async () => {
            const ns = window.TCS_NS;
            for (let i = 0; i < 2; i++)
                await ns.api.createCase(ns.state.suite, {sheet: '웹', path: ['로그인', '', ''],
                    feature: '로그인 확인 ' + i, steps: ['웹 페이지 열기'], expected: '로그인 화면 표시'});
        }''')
        page.locator('[data-id="nav-tab-review"]').click()
        buttons = page.locator('[data-review-index]')
        expect(buttons).to_have_count(2)
        expect(page.locator('.dcard:visible')).to_have_count(1)
        buttons.last.click()
        expect(buttons.last).to_have_attribute('aria-pressed', 'true')
        expect(page.locator('.dcard.focus')).to_have_attribute('data-i', '1')
        page.keyboard.press('k')
        expect(page.locator('.dcard.focus')).to_have_attribute('data-i', '0')
        for width in [1920, 1280, 390]:
            page.set_viewport_size({'width': width, 'height': 1080})
            panels = [page.locator(selector).bounding_box() for selector in
                      ['.rv-list-pane', '#drafts', '.rv-right']]
            for i, a in enumerate(panels):
                for b in panels[i + 1:]:
                    assert (a['x'] + a['width'] <= b['x'] + 1 or
                            b['x'] + b['width'] <= a['x'] + 1 or
                            a['y'] + a['height'] <= b['y'] + 1 or
                            b['y'] + b['height'] <= a['y'] + 1)
        page.locator('[data-f="invalid"]').click()
        expect(buttons).to_have_count(0)
        page.keyboard.press('a')
        expect(page.locator('#rv-left')).to_have_text('2')
