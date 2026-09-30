"""통합 가져오기 기능을 사용자가 클릭하는 흐름으로 확인한다."""
from pathlib import Path
import json
import urllib.request

import openpyxl
from playwright.sync_api import expect

from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json


def workbook(path: Path, sheet='회원등록', title='이름 오류 표시'):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(['ID', '제목', '절차', '기대 결과', '태그', 'AUTO'])
    ws.append(['REG_01', title, '1. 등록 버튼을 누른다.', '이름 입력 안내가 표시된다.', 'validation,smoke', 'Y(web)'])
    wb.save(path)
    wb.close()
    return path


def test_mapping_profile_management_is_available_in_tc_import(page, tmp_path):
    with dashboard_server(tmp_path / 'project') as base:
        page.goto(base + '/tc-studio')
        page.locator('[data-id="btn-import-xlsx"]').click()
        page.locator('#import-mapping-mode').select_option('custom')
        expect(page.locator('[data-id="import-profile-save"]')).to_be_visible()
        expect(page.locator('[data-id="import-history-open"]')).to_be_visible()
        page.locator('[data-map="source_tc_id"]').fill('A')
        page.locator('[data-map="feature"]').fill('B')
        page.locator('[data-map="steps"]').fill('C')
        page.locator('[data-map="expected"]').fill('D')
        page.locator('[data-map="tags"]').fill('E')
        page.locator('#import-profile-name').fill('회원등록 양식')
        page.locator('[data-id="import-profile-save"]').click()
        expect(page.locator('#import-mapping-profile option')).to_contain_text(['직접 입력', '회원등록 양식'])
        page.reload()
        page.locator('[data-id="btn-import-xlsx"]').click()
        page.locator('#import-mapping-mode').select_option('custom')
        page.locator('#import-mapping-profile').select_option(label='회원등록 양식')
        expect(page.locator('[data-map="source_tc_id"]')).to_have_value('A')
        page.locator('#import-profile-name').fill('회원등록 수정')
        page.locator('[data-id="import-profile-update"]').click()
        expect(page.locator('#import-mapping-profile option')).to_contain_text(['직접 입력', '회원등록 수정'])
        page.locator('[data-id="import-profile-delete"]').click()
        expect(page.locator('#import-mapping-profile option')).to_have_count(1)


def test_import_preview_commit_history_and_rollback(page, tmp_path):
    with dashboard_server(tmp_path / 'project') as base:
        page.goto(base + '/tc-studio')
        page.locator('[data-id="btn-import-xlsx"]').click()
        page.locator('#import-mapping-mode').select_option('custom')
        for key, col in {'source_tc_id':'A','feature':'B','steps':'C','expected':'D','tags':'E'}.items():
            page.locator(f'[data-map="{key}"]').fill(col)
        page.locator('#import-file').set_input_files(str(workbook(tmp_path/'practice.xlsx')))
        page.locator('#import-suite').fill('통합확인')
        page.locator('[data-id="import-plan"]').click()
        expect(page.locator('[data-id="import-plan-rows"]')).to_contain_text('이름 오류 표시')
        page.locator('#import-confirm').click()
        expect(page.locator('#suite-select')).to_have_value('통합확인')
        expect(page.locator('#grid-body tr[data-case]')).to_have_count(1)
        page.locator('#grid-body tr[data-case]').first.click()
        expect(page.locator('[data-id="detail-source-tc-id"]')).to_have_value('REG_01')
        expect(page.locator('[data-id="detail-source-tc-id"]')).to_have_attribute('readonly', '')
        expect(page.locator('[data-id="detail-tags"]')).to_have_value('validation, smoke')
        page.locator('[data-id="btn-import-xlsx"]').click()
        page.locator('[data-id="import-history-open"]').click()
        expect(page.locator('[data-id="import-history-list"]')).to_contain_text('통합확인')
        page.locator('[data-id="import-history-list"] [data-action="view"]').first.click()
        expect(page.locator('[data-id="import-history-detail"]')).to_contain_text('이름 오류 표시')
        page.locator('[data-id="import-history-detail"] [data-action="rollback"]').click()
        expect(page.locator('[data-id="import-history-detail"]')).to_contain_text('rolled_back')
        page.reload()
        expect(page.locator('#grid-body tr[data-case]')).to_have_count(0)


def test_import_bookmark_moves_to_tc_studio_without_old_menu(page, tmp_path):
    with dashboard_server(tmp_path / 'project') as base:
        page.goto(base + '/import-studio')
        expect(page).to_have_url(base + '/tc-studio')
        expect(page.locator('#tab-import_studio')).to_have_count(0)
        expect(page.locator('#tc-studio-root')).to_be_visible()


def test_initial_loading_preserves_user_selected_screen(page, tmp_path):
    from tests.unit.tc_library.test_tc_studio_e2e import _seed
    with dashboard_server(tmp_path / 'project') as base:
        _seed(base, tmp_path, suite='초기화확인')
        page.goto(base + '/tc-studio')
        page.evaluate("""async () => {
            while (!window.TCS_NS?.api) await new Promise(r => setTimeout(r, 10));
            const ns = window.TCS_NS;
            while (!ns.state.suites) await new Promise(r => setTimeout(r, 10));
        }""")
        expect(page.locator('#grid-body tr[data-case]')).to_have_count(6)
        # 새로고침 초기화를 결정적으로 재현한다. 응답은 실제 API 결과를 사용한다.
        page.evaluate("""async () => {
            const ns = window.TCS_NS;
            const original = ns.api.authoringContext;
            ns.state.suite = '__initializing__';
            ns.api.authoringContext = async (...args) => {
                const result = await original(...args);
                await new Promise(resolve => { window.finishAuthoringContext = resolve; });
                return result;
            };
            window.suiteLoading = ns.reloadSuites();
        }""")
        page.wait_for_function('typeof window.finishAuthoringContext === "function"')
        page.locator('[data-id="nav-tab-export"]').click()
        page.evaluate('async () => { window.finishAuthoringContext(); await window.suiteLoading; }')
        expect(page.locator('[data-id="nav-tab-export"]')).to_have_attribute('aria-selected', 'true')


def test_imported_tags_edit_save_and_reload(page, tmp_path):
    with dashboard_server(tmp_path / 'project') as base:
        page.goto(base + '/tc-studio')
        page.locator('[data-id="btn-import-xlsx"]').click()
        page.locator('#import-mapping-mode').select_option('custom')
        for key, col in {'source_tc_id':'A','feature':'B','steps':'C','expected':'D','tags':'E'}.items():
            page.locator(f'[data-map="{key}"]').fill(col)
        page.locator('#import-file').set_input_files(str(workbook(tmp_path/'tags.xlsx')))
        page.locator('#import-suite').fill('태그확인')
        page.locator('[data-id="import-plan"]').click()
        expect(page.locator('[data-id="import-plan-rows"]')).to_contain_text('이름 오류 표시')
        page.locator('#import-confirm').click()
        expect(page.locator('#grid-body tr[data-case]')).to_have_count(1)
        page.locator('#grid-body tr[data-case]').first.click()
        expect(page.locator('[data-id="detail-tags"]')).to_have_value('validation, smoke')
        page.locator('[data-id="detail-tags"]').fill('validation, regression, regression')
        page.locator('[data-id="detail-save"]').click()
        expect(page.locator('[data-id="detail-save"]')).to_be_disabled()
        expect(page.locator('[data-id="detail-tags"]')).to_have_value('validation, regression')
        page.reload()
        page.locator('#grid-body tr[data-case]').first.click()
        expect(page.locator('[data-id="detail-tags"]')).to_have_value('validation, regression')
        expect(page.locator('[data-id="detail-source-tc-id"]')).to_have_value('REG_01')


def test_editing_import_target_discards_pending_preview(page, tmp_path):
    with dashboard_server(tmp_path / 'project') as base:
        page.goto(base + '/tc-studio')
        page.locator('[data-id="btn-import-xlsx"]').click()
        page.locator('#import-mapping-mode').select_option('custom')
        page.locator('#import-file').set_input_files(str(workbook(tmp_path/'pending.xlsx')))
        page.locator('#import-suite').fill('변경전')
        page.evaluate("""() => {
            const ns = window.TCS_NS;
            const original = ns.api.importPlan;
            ns.api.importPlan = async (...args) => {
                const result = await original(...args);
                await new Promise(resolve => { window.releaseImportPreview = resolve; });
                return result;
            };
        }""")
        page.locator('[data-id="import-plan"]').click()
        page.wait_for_function('typeof window.releaseImportPreview === "function"')
        page.locator('#import-suite').fill('변경후')
        page.evaluate('window.releaseImportPreview()')
        expect(page.locator('#import-plan')).to_be_enabled()
        expect(page.locator('#import-confirm')).to_be_disabled()
        expect(page.locator('#import-plan-panel')).to_be_hidden()


def test_multiple_files_use_individual_sheet_mapping(page, tmp_path):
    with dashboard_server(tmp_path / 'project') as base:
        first = workbook(tmp_path/'first.xlsx', sheet='가입')
        second = workbook(tmp_path/'second.xlsx', sheet='설정')
        wb = openpyxl.load_workbook(second)
        wb.active['A2'] = 'SET_01'
        wb.active['B2'] = '1. 설정을 누른다.'
        wb.active['C2'] = '설정 페이지 표시'
        wb.save(second)
        wb.close()
        page.goto(base + '/tc-studio')
        page.locator('[data-id="btn-import-xlsx"]').click()
        page.locator('#import-mapping-mode').select_option('custom')
        for key, col in {'source_tc_id':'A','feature':'C','steps':'B','expected':'D','tags':'E'}.items():
            page.locator(f'[data-map="{key}"]').fill(col)
        page.locator('#import-profile-name').fill('설정 양식')
        page.locator('[data-id="import-profile-save"]').click()
        expect(page.locator('#import-mapping-profile')).not_to_have_value('')
        page.locator('[data-map="feature"]').fill('B')
        page.locator('[data-map="steps"]').fill('C')
        page.locator('#import-file').set_input_files([str(first), str(second)])
        page.locator('#import-suite').fill('다중파일확인')
        page.locator('[data-sheet-profile="설정"]').select_option(label='설정 양식')
        page.locator('[data-id="import-plan"]').click()
        expect(page.locator('[data-id="import-plan-rows"]')).to_contain_text('이름 오류 표시')
        expect(page.locator('[data-id="import-plan-rows"]')).to_contain_text('설정 페이지 표시')
        page.locator('#import-confirm').click()
        expect(page.locator('#grid-body tr[data-case]')).to_have_count(2)
        page.reload()
        expect(page.locator('#grid-body')).to_contain_text('설정 페이지 표시')
        expect(page.locator('#grid-body')).to_contain_text('이름 오류 표시')


def test_mapping_change_during_upload_discards_stale_analysis(page, tmp_path):
    with dashboard_server(tmp_path / 'project') as base:
        page.goto(base + '/tc-studio')
        page.locator('[data-id="btn-import-xlsx"]').click()
        page.locator('#import-mapping-mode').select_option('custom')
        page.evaluate("""() => {
            const original = window.TCS_NS.api.importPreview;
            window.TCS_NS.api.importPreview = async (...args) => {
                const result = await original(...args);
                await new Promise(resolve => { window.releaseAnalysis = resolve; });
                return result;
            };
        }""")
        page.locator('#import-file').set_input_files(str(workbook(tmp_path/'race.xlsx')))
        page.wait_for_function('typeof window.releaseAnalysis === "function"')
        page.locator('[data-map="feature"]').fill('D')
        page.evaluate('window.releaseAnalysis()')
        # The continuation has finished by the following browser task.
        page.evaluate('() => new Promise(resolve => setTimeout(resolve, 0))')
        page.locator('#import-suite').evaluate("element => { element.value='경쟁확인'; element.dispatchEvent(new Event('input', {bubbles:true})); }")
        expect(page.locator('#import-plan')).to_be_disabled()
        expect(page.locator('#import-confirm')).to_be_disabled()
        expect(page.locator('#import-preview')).to_be_hidden()
        page.evaluate('delete window.releaseAnalysis')
        page.locator('#import-mapping-apply').click()
        page.wait_for_function('typeof window.releaseAnalysis === "function"')
        page.evaluate('window.releaseAnalysis()')
        expect(page.locator('#import-plan')).to_be_enabled()
        expect(page.locator('#import-preview')).to_be_visible()


def test_deleting_sheet_profile_falls_back_and_invalidates_plan(page, tmp_path):
    with dashboard_server(tmp_path / 'project') as base:
        page.goto(base + '/tc-studio')
        page.locator('[data-id="btn-import-xlsx"]').click()
        page.locator('#import-mapping-mode').select_option('custom')
        page.locator('#import-profile-name').fill('시트양식')
        page.locator('[data-id="import-profile-save"]').click()
        expect(page.locator('#import-mapping-profile')).not_to_have_value('')
        page.locator('#import-file').set_input_files(str(workbook(tmp_path/'profile.xlsx')))
        page.locator('#import-suite').fill('삭제확인')
        page.locator('[data-sheet-profile]').select_option(label='시트양식')
        page.locator('#import-plan').click()
        expect(page.locator('#import-plan-panel')).to_be_visible()
        page.locator('[data-id="import-profile-delete"]').click()
        expect(page.locator('[data-sheet-profile] option')).to_have_count(1)
        expect(page.locator('#import-plan-panel')).to_be_hidden()
        page.locator('#import-plan').click()
        expect(page.locator('#import-plan-panel')).to_be_visible()


def test_import_diff_displays_changed_metadata(page, tmp_path):
    with dashboard_server(tmp_path / 'project') as base:
        page.goto(base + '/tc-studio')
        page.locator('[data-id="btn-import-xlsx"]').click()
        page.locator('#import-mapping-mode').select_option('custom')
        page.locator('#import-file').set_input_files(str(workbook(tmp_path/'diff.xlsx')))
        page.locator('#import-suite').fill('비교확인')
        page.evaluate("""() => {
            const original = window.TCS_NS.api.importPlan;
            window.TCS_NS.api.importPlan = async (...args) => {
                const result = await original(...args);
                result.rows[0].before = {feature:'Same',steps:['Click'],expected:'Shown',tags:['old-tag'],priority:'P3',precondition:'Before',path:['Old group'],source_tc_id:'OLD'};
                result.rows[0].after = {...result.rows[0].before,tags:['new-tag'],priority:'P0',precondition:'After',path:['New group'],source_tc_id:'NEW'};
                return result;
            };
        }""")
        page.locator('#import-plan').click()
        page.locator('#import-plan-rows details summary').first.click()
        comparison = page.locator('#import-plan-rows details').first
        for value in ('old-tag', 'new-tag', 'P3', 'P0', 'Before', 'After', 'Old group', 'New group', 'OLD', 'NEW'):
            expect(comparison).to_contain_text(value)


def test_auto_controls_are_removed_from_studio(page, tmp_path):
    from tests.unit.tc_library.test_tc_studio_e2e import _seed
    with dashboard_server(tmp_path / 'project') as base:
        _seed(base, tmp_path, suite='자동분류제거')
        page.goto(base + '/tc-studio')
        expect(page.locator('#grid-body tr[data-case]')).to_have_count(6)
        expect(page.locator('[data-id="lib-filter-auto"]')).to_have_count(0)
        expect(page.locator('[data-id="bulk-auto"]')).to_have_count(0)
        page.locator('#grid-body tr[data-case]').first.click()
        expect(page.locator('[data-id="detail-auto"]')).to_have_count(0)
        page.locator('[data-id="btn-import-xlsx"]').click()
        page.locator('#import-mapping-mode').select_option('custom')
        expect(page.locator('[data-map="auto"]')).to_have_count(0)
        expect(page.locator('#import-default-auto')).to_have_count(0)
        page.locator('#import-close').click()
        page.locator('[data-id="nav-tab-export"]').click()
        expect(page.locator('[data-id="md-card"]')).not_to_contain_text('AUTO')


def test_drop_zone_shows_analyzing_state_until_preview_returns(page, tmp_path):
    """분석이 늦어도 파일을 올린 자리에서 진행 중임이 보이고, 끝나면 원래 안내로 돌아간다."""
    with dashboard_server(tmp_path / 'project') as base:
        page.goto(base + '/tc-studio')
        page.locator('[data-id="btn-import-xlsx"]').click()
        held = []
        page.route('**/api/tc-library/import/preview**', lambda route: held.append(route))
        page.locator('#import-file').set_input_files(str(workbook(tmp_path / 'slow.xlsx')))
        analyzing = page.locator('[data-id="import-analyzing"]')
        expect(analyzing).to_be_visible()
        expect(page.locator('#import-drop')).to_contain_text('slow.xlsx')
        expect(page.locator('#import-drop')).to_have_attribute('aria-busy', 'true')
        page.wait_for_function('() => true')
        while not held:
            page.wait_for_timeout(50)
        held[0].continue_()
        expect(analyzing).to_have_count(0)
        expect(page.locator('#import-drop')).to_contain_text('엑셀 파일을 끌어다 놓거나 눌러서 선택')
