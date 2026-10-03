"""Recovery notices use the real dashboard server and browser interactions."""
from pathlib import Path
import sys

import pytest
from playwright.sync_api import sync_playwright, expect

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts'))
from tests.unit.import_studio.import_studio_test_support import dashboard_server

NOTICE = {
    'id': 'run:failed-1:failed', 'run_id': 'failed-1', 'groups': ['회원등록'],
    'category': 'assertion', 'title': '검증 결과 불일치',
    'message': '실제 결과와 테스트의 기대값을 비교하세요.',
    'action_label': '실행 기록 확인', 'href': '/?view=history',
    'severity': 'error', 'created_at': '2026-10-03T01:00:00Z',
}


def test_notice_acknowledgment_persists_only_in_the_same_browser(tmp_path):
    with dashboard_server(tmp_path / 'project') as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        context = browser.new_context()
        context.route('**/api/recovery-notices', lambda route: route.fulfill(json={'ok': True, 'notices': [NOTICE]}))
        page = context.new_page()
        page.goto(base)
        expect(page.locator('#recovery-notices')).to_be_visible()
        page.locator('#recovery-notices summary').click()
        expect(page.locator('.recovery-notice')).to_contain_text('회원등록')
        page.get_by_role('button', name='확인했어요').click()
        expect(page.locator('#recovery-notices')).to_be_hidden()
        page.reload()
        page.wait_for_function('!_recoveryNotices.busy && _recoveryNotices.items.length === 1')
        expect(page.locator('#recovery-notices')).to_be_hidden()
        other = browser.new_context()
        other.route('**/api/recovery-notices', lambda route: route.fulfill(json={'ok': True, 'notices': [NOTICE]}))
        other_page = other.new_page()
        other_page.goto(base)
        expect(other_page.locator('#recovery-notices')).to_be_visible()
        browser.close()


def test_transient_notice_reads_retry_without_replaying_actions(tmp_path):
    with dashboard_server(tmp_path / 'project') as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        reads = []
        def respond(route):
            reads.append(route.request.method)
            if len(reads) < 3:
                route.fulfill(status=503, json={'ok': False})
            else:
                route.fulfill(json={'ok': True, 'notices': [NOTICE]})
        page.route('**/api/recovery-notices', respond)
        page.goto(base)
        expect(page.locator('#recovery-notices')).to_be_visible()
        assert reads == ['GET', 'GET', 'GET']
        error = page.evaluate("async () => {try {await safeNoticeGet('/api/run_script', {method:'POST'});} catch(e) {return e.message;}}")
        assert '허용되지 않은' in error
        assert reads == ['GET', 'GET', 'GET']
        browser.close()


def test_connection_failure_keeps_notices_and_recovers(tmp_path):
    with dashboard_server(tmp_path / 'project') as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        payload = {'status': 200, 'json': {'ok': True, 'notices': [NOTICE]}}
        page.route('**/api/recovery-notices', lambda route: route.fulfill(**payload))
        page.goto(base)
        expect(page.locator('#recovery-notices')).to_be_visible()
        payload.update(status=403, json={'ok': False})
        page.evaluate('recoveryNoticesRefresh()')
        expect(page.locator('#recovery-connection-warning')).to_be_visible()
        page.locator('#recovery-notices summary').click()
        expect(page.locator('.recovery-notice')).to_contain_text(NOTICE['title'])
        payload.update(status=200, json={'ok': True, 'notices': [NOTICE]})
        page.evaluate('recoveryNoticesRefresh()')
        expect(page.locator('#recovery-connection-warning')).to_be_hidden()
        expect(page.locator('#recovery-announcement')).to_contain_text('복구')
        browser.close()


def test_notice_refresh_preserves_keyboard_focus_and_rejects_external_links(tmp_path):
    with dashboard_server(tmp_path / 'project') as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        notices = [dict(NOTICE, href='//external.example/')]
        page.route('**/api/recovery-notices', lambda route: route.fulfill(json={'ok': True, 'notices': notices}))
        page.goto(base)
        expect(page.locator('#recovery-notices')).to_be_visible()
        page.locator('#recovery-notices summary').click()
        assert page.locator('.recovery-notice a').count() == 0
        acknowledge = page.get_by_role('button', name='확인했어요')
        acknowledge.focus()
        notices[0]['message'] = '수정된 안내'
        page.evaluate('recoveryNoticesRefresh()')
        expect(acknowledge).to_be_focused()
        page.keyboard.press('Enter')
        expect(page.locator('.header-title')).to_be_focused()
        page.locator('#tab-pages').click()
        expect(page.locator('#pg-url')).to_be_visible()
        browser.close()


def test_failed_history_without_a_report_does_not_appear_as_passed(tmp_path):
    with dashboard_server(tmp_path / 'project') as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.route('**/api/run_history', lambda route: route.fulfill(json=[{
            'run_id': 'failed-1', 'timestamp': '2026-10-03 10:00:00', 'pipeline': 'single',
            'status': 'failed', 'failed': 0, 'passed': 0, 'total': 0, 'report_path': None,
            'recovery': {key: NOTICE[key] for key in ('title', 'message', 'category')},
        }]))
        page.goto(base + '/?view=history')
        row = page.locator('.hist-card')
        expect(row).to_contain_text('실패')
        expect(row).to_contain_text('리포트 없음')
        expect(row).to_contain_text(NOTICE['message'])
        expect(row).not_to_contain_text('첫 실행 통과')
        browser.close()


def test_restarted_browser_tracks_owned_execution_and_cancels_once(tmp_path):
    with dashboard_server(tmp_path / 'project') as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        execution = {'run_id': 'workflow-1', 'tag': 'run_quick', 'status': 'running', 'pid': 42}
        cancellations = []
        page.route('**/api/execution_status', lambda route: route.fulfill(json={'ok': True, 'execution': execution}))
        def cancel(route):
            cancellations.append(route.request.post_data_json)
            execution['status'] = 'cancelled'
            route.fulfill(json={'ok': True, 'run_id': 'workflow-1', 'status': 'cancelled'})
        page.route('**/api/cancel', cancel)
        page.goto(base)
        expect(page.locator('#execution-status')).to_contain_text('빠른 실행')
        page.get_by_role('button', name='실행 중단', exact=True).click()
        assert cancellations == [{'run_id': 'workflow-1'}]
        expect(page.locator('#execution-status')).to_contain_text('중단')
        expect(page.locator('#execution-cancel')).to_be_hidden()
        page.reload()
        expect(page.locator('#execution-status')).to_contain_text('중단')
        assert cancellations == [{'run_id': 'workflow-1'}]
        browser.close()


@pytest.mark.parametrize('view', ['quick_run', 'parallel_pipeline', 'single_pipeline'])
def test_reportless_workflow_failure_shows_guidance_in_execution_screen(tmp_path, view):
    with dashboard_server(tmp_path / 'project') as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        state = {'step': 'init', 'status': 'testing', 'workflow_status': 'failed', 'url': 'https://example.org',
                 'execution_result': {'status': 'failed', 'total': 0, 'passed': 0, 'failed': 0,
                                      'report_path': None, 'recovery': {'title': '실행 설정 확인', 'message': '실행할 테스트 파일을 확인하세요.'}}}
        page.route('**/api/quick_state*', lambda route: route.fulfill(json=state))
        page.route('**/api/pipeline_state*', lambda route: route.fulfill(json=state))
        page.route('**/api/batch_state*', lambda route: route.fulfill(json={'parallel_state': state}))
        page.goto(base + '/?view=' + view)
        expect(page.locator('#main')).to_contain_text('실행할 테스트 파일을 확인하세요.')
        expect(page.locator('#main')).not_to_contain_text('모두 통과')
        expect(page.locator('#main')).not_to_contain_text('undefined')
        browser.close()


def test_cancelled_history_is_not_shown_as_a_successful_test(tmp_path):
    with dashboard_server(tmp_path / 'project') as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.route('**/api/run_history', lambda route: route.fulfill(json=[{
            'timestamp': '2026-10-03 11:00:00', 'pipeline': 'quick', 'status': 'cancelled',
            'passed': 0, 'failed': 0, 'total': 0, 'report_path': None,
        }]))
        page.goto(base + '/?view=history')
        expect(page.locator('.hist-card')).to_contain_text('중단')
        expect(page.locator('.hist-card')).not_to_contain_text('통과')
        browser.close()


def test_overview_preserves_failed_cancelled_and_unmeasured_run_status(tmp_path):
    history = [
        {'timestamp': '2026-10-03T10:57:00', 'pipeline': 'quick', 'groups': [name],
         'status': status, 'passed': 0, 'failed': 0, 'total': 0, 'pass_rate': 0}
        for name, status in [('empty', 'failed'), ('wait', 'cancelled'), ('unknown', '')]]
    with dashboard_server(tmp_path / 'project') as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.route('**/api/run_history', lambda route: route.fulfill(json=history))
        page.goto(base)
        for name, label in [('empty', '실패'), ('wait', '중단'), ('unknown', '미실행')]:
            row = page.locator('.ov-table tbody tr').filter(has_text=name)
            expect(row.locator('.ov-result')).to_have_text(label)
            expect(row.locator('.ov-time')).to_have_text('10-03 10:57')
        expect(page.locator('.oax-trend-empty')).to_have_text('측정된 테스트 결과 없음')
        expect(page.locator('.ov-summary-item').filter(has_text='마지막 실행').locator('.ov-result')).to_have_text('미실행')
        browser.close()


def test_overview_trend_percentage_labels_do_not_overlap_time_labels(tmp_path):
    history = [
        {'timestamp': '2026-10-03 10:5'+str(i)+':00', 'pipeline': 'quick',
         'groups': [str(i)], 'total': 1, 'passed': 0, 'failed': 1, 'pass_rate': 0}
        for i in range(8)]
    with dashboard_server(tmp_path / 'project') as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        page.route('**/api/run_history', lambda route: route.fulfill(json=history))
        page.goto(base)
        expect(page.locator('.oax-trend-svg circle')).to_have_count(8)
        for width in [1440, 390]:
            page.set_viewport_size({'width': width, 'height': 1000})
            collisions = page.locator('.oax-trend-svg text').evaluate_all('''els => {
                const rects = els.map(e => e.getBoundingClientRect());
                return rects.flatMap((a,i)=>rects.slice(i+1).filter(b=>
                    a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top));
            }''')
            assert not collisions, f'Chart labels overlap at {width}px'
        browser.close()


def test_overview_explains_failure_and_successful_recovery(tmp_path):
    history = [
        {'timestamp': '2026-10-03 11:00:00', 'pipeline': 'quick', 'groups': ['empty'],
         'status': 'failed', 'total': 0, 'failed': 0, 'error': '<실행 파일 없음>'},
        {'timestamp': '2026-10-03 11:01:00', 'pipeline': 'quick', 'groups': ['healed'],
         'status': 'passed', 'total': 1, 'passed': 1, 'heal_count': 1},
    ]
    with dashboard_server(tmp_path / 'project') as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.route('**/api/run_history', lambda route: route.fulfill(json=history))
        page.goto(base)
        row = page.locator('.ov-table tbody tr').filter(has_text='empty')
        expect(row.locator('.ov-result-detail')).to_contain_text('<실행 파일 없음>')
        expect(row.locator('.ov-result-detail')).to_contain_text('실행된 테스트 없음 · 통과율 집계 제외')
        expect(page.locator('.ov-table tbody tr').filter(has_text='healed').locator('.ov-result-detail')).to_have_text('자동 복구 후 통과')
        browser.close()


def test_overview_trend_matches_app_layout_and_keeps_each_execution(tmp_path):
    history = [
        {'timestamp': '2026-10-03 11:0'+str(i)+':00', 'pipeline': 'quick',
         'groups': ['same-group'], 'total': 1, 'passed': 1, 'failed': 0,
         'status': 'passed', 'pass_rate': 100, 'duration_sec': 2}
        for i in range(8)]
    with dashboard_server(tmp_path / 'project') as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.route('**/api/run_history', lambda route: route.fulfill(json=history))
        page.goto(base)
        expect(page.locator('.oax-trend-svg circle')).to_have_count(8)
        expect(page.locator('.oax-trend-svg')).to_have_attribute('viewBox', '0 0 480 190')
        expect(page.locator('.oax-trend-footer')).to_contain_text('2초 · 통과')
        assert page.locator('.oax-trend-svg polyline').evaluate('(e)=>getComputedStyle(e).stroke') == page.evaluate('''() => {const e=document.createElement('span');e.style.color='var(--accent)';document.body.append(e);const c=getComputedStyle(e).color;e.remove();return c;}''')
        browser.close()


def test_overview_trend_zero_and_full_pass_align_with_grid_lines(tmp_path):
    history = [
        {'timestamp': '2026-10-03 11:00:00', 'pipeline': 'quick', 'groups': ['fail'], 'total': 1, 'passed': 0, 'failed': 1},
        {'timestamp': '2026-10-03 11:01:00', 'pipeline': 'quick', 'groups': ['pass'], 'total': 1, 'passed': 1, 'failed': 0},
    ]
    with dashboard_server(tmp_path / 'project') as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.route('**/api/run_history', lambda route: route.fulfill(json=history))
        page.goto(base)
        expect(page.locator('.oax-trend-svg circle')).to_have_count(2)
        grid_y = page.locator('.oax-trend-svg line').evaluate_all('(els)=>els.map(e=>Number(e.getAttribute("y1")))')
        point_y = page.locator('.oax-trend-svg circle').evaluate_all('(els)=>els.map(e=>Number(e.getAttribute("cy")))')
        assert point_y == [max(grid_y), min(grid_y)]
        assert len(grid_y) == 6
        browser.close()


def test_overview_table_matches_app_fonts_and_keeps_execution_type_on_one_line(tmp_path):
    history = [{'timestamp': '2026-10-03 11:00:00', 'pipeline': 'quick',
                'groups': ['audit_ios_final_20261002'], 'total': 0, 'status': 'failed',
                'error': '실행 환경을 확인하고 다시 실행해 주세요. ' * 8}]
    with dashboard_server(tmp_path / 'project') as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1000})
        page.route('**/api/run_history', lambda route: route.fulfill(json=history))
        page.goto(base)
        row = page.locator('.ov-table tbody tr')
        expect(row).to_have_count(1)
        style = row.locator('td').nth(1).evaluate('''e => {
            const s=getComputedStyle(e),r=document.createRange();r.selectNodeContents(e);
            return {size:s.fontSize,font:s.fontFamily,nowrap:s.whiteSpace,height:r.getBoundingClientRect().height,line:parseFloat(s.lineHeight)};
        }''')
        assert style['size'] == '13px'
        assert style['font'].startswith('"IBM Plex Sans KR"')
        assert style['nowrap'] == 'nowrap'
        assert style['height'] <= style['line']
        assert row.locator('td').nth(4).evaluate('(e)=>getComputedStyle(e).fontFamily').startswith('"IBM Plex Sans KR"')
        assert float(row.locator('.ov-result-detail').evaluate('(e)=>parseFloat(getComputedStyle(e).fontSize)')) == pytest.approx(13 * 5 / 6, abs=0.05)
        browser.close()
