"""실행 결과 목록의 TC 상세 펼침이 새 실행 결과를 따르는지 실제 대시보드 JS로 확인한다."""
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts'))
from tests.unit.import_studio.import_studio_test_support import dashboard_server

NODEID = 'tests/generated/customer_login/tc_CL_02_x.py::test_x[chromium]'


def test_stale_failure_detail_is_dropped_when_result_changes(tmp_path):
    with dashboard_server(tmp_path / 'project') as base, sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.goto(base)
        page.wait_for_function("typeof buildTestListHtml === 'function'")
        result = page.evaluate("""(nodeid) => {
            const key = 'quick|' + nodeid;
            const failed = [{nodeid, name: 'test_x', outcome: 'failed', error: 'E   FileNotFoundError'}];
            const render = (tests, run) => buildTestListHtml(tests, 'quick', 'customer_login', run)
                .includes('id="stale"');
            const cache = () => { _testDetailOpen[key] = true; _testDetailContent[key] = '<div id="stale">실패 원인</div>'; };
            render(failed, 'run1');
            cache();
            const sameRun = render(failed, 'run1');
            const otherList = buildTestListHtml(failed, 'parallel', 'customer_login', 'run1').includes('id="stale"');
            const passed = render([{nodeid, name: 'test_x', outcome: 'passed'}], 'run2');
            const reopened = !!_testDetailOpen[key];
            render(failed, 'run3');
            cache();
            const sameErrorNewRun = render(failed, 'run4');
            return {sameRun, otherList, passed, reopened, sameErrorNewRun};
        }""", NODEID)
        browser.close()
    assert result == {'sameRun': True, 'otherList': False, 'passed': False, 'reopened': False, 'sameErrorNewRun': False}
