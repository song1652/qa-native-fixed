from __future__ import annotations

import json

import pytest

import _paths
import _tc_library as lib
import _tc_md_export as md
import parse_cases
from _tc_template import analyze_workbook
from _tc_xlsx_import import import_workbook

SUITE = "야핏무브"


@pytest.fixture
def project(library_dir, template_xlsx, tmp_path, monkeypatch):
    root = tmp_path / "project"
    (root / "testcases").mkdir(parents=True)
    (root / "config").mkdir()
    (root / "config" / "pages.json").write_text(json.dumps(
        {"_comment": "x", "yafit_benefit": "https://m.yafit.example/benefit"}), encoding="utf-8")
    for name, value in {"PROJECT_ROOT": root, "TESTCASES_DIR": root / "testcases", "PAGES_JSON": root / "config" / "pages.json",
                        "IMPORT_DIR": root / "import", "IMPORT_SESSIONS_DIR": root / "state" / "import_sessions",
                        "IMPORT_SNAPSHOTS_DIR": root / "state" / "import_snapshots"}.items():
        monkeypatch.setattr(_paths, name, value)
    profiles = analyze_workbook(template_xlsx)
    lib.save_template(SUITE, template_xlsx, profiles)
    lib.import_cases(SUITE, ["혜택", "홈"], import_workbook(template_xlsx, profiles, ["혜택", "홈"], {"혜택": "BEN", "홈": "HOME"}), "t")
    # 우선순위를 보완하고 BEN_0004는 추정 문구가 있게 만든다
    for case_id in ("BEN_0001", "BEN_0002", "BEN_0003", "BEN_0004"):
        case = lib.get_case(SUITE, case_id)
        lib.patch_case(SUITE, case_id, case["rev"], {"priority": case["priority"] or "P1"}, "t")
    case = lib.get_case(SUITE, "BEN_0004")
    lib.patch_case(SUITE, "BEN_0004", case["rev"], {"bullets": [{"text": "추정 문구", "verified": False}]}, "t")
    return root


def test_group_mapping_is_validated(project):
    with pytest.raises(lib.LibraryError) as exc:
        md.save_group(SUITE, ["혜택", "혜택 탭"], "no_such_group", "YFB")
    assert exc.value.code == "GROUP_NOT_IN_PAGES"
    with pytest.raises(lib.LibraryError) as exc:
        md.save_group(SUITE, ["혜택", "혜택 탭"], "yafit_benefit", "yfb")
    assert exc.value.code == "INVALID_MD_CODE"
    with pytest.raises(lib.LibraryError):
        md.save_group(SUITE, ["혜택"], "yafit_benefit", "YFB")


def test_eligibility_funnel_and_reasons(project):
    before = md.eligibility(SUITE)
    assert [f["count"] for f in before["funnel"]] == [6, 6, 5, 0]
    assert {e["case_id"]: e["reason"] for e in before["excluded"]}["BEN_0004"] == '추정 문구 "추정 문구"'
    md.save_group(SUITE, ["혜택", "혜택 탭"], "yafit_benefit", "YFB")
    after = md.eligibility(SUITE)
    assert after["funnel"][-1]["count"] == 4
    assert {tuple(b["path"]): b["group"] for b in after["branches"]} == {
        ("혜택", "혜택 탭"): "yafit_benefit", ("혜택", "혜택 탭", "상단 배너"): "yafit_benefit",
        ("혜택", "혜택 탭", "신규회원 한정 혜택"): "yafit_benefit", ("홈", "걷고 받기 탭"): ""}


def test_preview_commit_parses_and_ids_are_stable(project):
    md.save_group(SUITE, ["혜택", "혜택 탭"], "yafit_benefit", "YFB")
    run = md.preview(SUITE)
    assert run["summary"]["added"] == 4 and [r["tc_id"] for r in run["rows"]] == ["YFB_01", "YFB_02", "YFB_03", "YFB_04"]
    result = md.commit(SUITE, run["run_id"], [])
    assert result["created"] == 4

    cases = parse_cases.load_cases(project / "testcases" / "yafit_benefit")
    assert [c["id"] for c in cases] == ["YFB_01", "YFB_02", "YFB_03", "YFB_04"]
    first = cases[0]
    assert (first["priority"], first["source_ref"], first["data_key"]) == ("very_high", "tc-library:야핏무브/BEN_0001", None)
    assert first["steps"] == ["1. 앱 실행", "2. 혜택 탭 선택"] and first["title"] == "혜택 탭 버튼"

    again = md.preview(SUITE)
    assert again["summary"]["same"] == 4 and md.load_config(SUITE)["ids"]["BEN_0002"] == "YFB_02"


def test_drift_conflict_skip_overwrite_and_rollback(project):
    md.save_group(SUITE, ["혜택", "혜택 탭"], "yafit_benefit", "YFB")
    md.commit(SUITE, md.preview(SUITE)["run_id"], [])
    target = next((project / "testcases" / "yafit_benefit").glob("tc_YFB_02_*.md"))
    target.write_text(target.read_text(encoding="utf-8").replace("가로 스크롤", "세로 스크롤"), encoding="utf-8")
    assert md.drifted_files(SUITE) == [{"tc_id": "YFB_02", "file": f"yafit_benefit/{target.name}"}]

    run = md.preview(SUITE)
    drift = next(r for r in run["rows"] if r["tc_id"] == "YFB_02")
    assert (drift["status"], drift["reason_code"]) == ("conflict", "FILE_DRIFT")
    md.commit(SUITE, run["run_id"], ["YFB_02"])                     # 건너뛰기 → 사람이 고친 내용 유지
    assert "세로 스크롤" in target.read_text(encoding="utf-8")

    run = md.preview(SUITE)
    md.commit(SUITE, run["run_id"], [])                              # 덮어쓰기 → 라이브러리 값
    assert "가로 스크롤" in target.read_text(encoding="utf-8") and md.drifted_files(SUITE) == []

    md.rollback(SUITE, run["run_id"])                                # 롤백 → 다시 사람이 고친 내용
    assert "세로 스크롤" in target.read_text(encoding="utf-8")
    assert md.drifted_files(SUITE)[0]["tc_id"] == "YFB_02"


def test_nothing_to_export(project):
    with pytest.raises(lib.LibraryError) as exc:
        md.preview(SUITE)
    assert exc.value.code == "NOTHING_TO_EXPORT"


def test_source_id_tags_and_existing_assignment(project):
    md.save_group(SUITE, ['혜택', '혜택 탭'], 'yafit_benefit', 'YFB')
    case = lib.get_case(SUITE, 'BEN_0001')
    lib.patch_case(SUITE, case['case_id'], case['rev'], {'source_tc_id': 'LEGACY_1', 'tags': ['smoke']}, 't')
    rows = md.build_rows(SUITE)
    assert rows[0]['tc_id'] == 'LEGACY_1' and 'smoke' in rows[0]['tags']
    case = lib.get_case(SUITE, 'BEN_0001')
    lib.patch_case(SUITE, case['case_id'], case['rev'], {'source_tc_id': 'CHANGED'}, 't')
    assert md.build_rows(SUITE)[0]['tc_id'] == 'LEGACY_1'


def test_duplicate_source_ids_do_not_allocate_same_md_id(project):
    md.save_group(SUITE, ['혜택', '혜택 탭'], 'yafit_benefit', 'YFB')
    for cid in ('BEN_0001', 'BEN_0002'):
        case = lib.get_case(SUITE, cid)
        lib.patch_case(SUITE, cid, case['rev'], {'source_tc_id': 'DUP'}, 't')
    with pytest.raises(lib.LibraryError) as exc:
        md.preview(SUITE)
    assert exc.value.code == 'DUPLICATE_SOURCE_ID'


def test_original_id_link_requires_conflict_choice_for_existing_md(project):
    from _import_commit import _render
    folder = project / 'testcases' / 'yafit_benefit'
    folder.mkdir()
    (folder / 'tc_LEGACY_1_old.md').write_text(_render({
        'tc_id': 'LEGACY_1', 'title': 'Old title', 'precondition': 'Logged out',
        'steps': 'Click', 'expected': 'Shown', 'priority': 'high', 'tags': ['smoke'],
        'group': 'yafit_benefit'}), encoding='utf-8')
    md.save_group(SUITE, ['혜택', '혜택 탭'], 'yafit_benefit', 'YFB')
    case = lib.get_case(SUITE, 'BEN_0001')
    lib.patch_case(SUITE, case['case_id'], case['rev'], {'source_tc_id': 'LEGACY_1'}, 't')
    run = md.preview(SUITE)
    row = next(r for r in run['rows'] if r['tc_id'] == 'LEGACY_1')
    assert row['status'] == 'conflict' and row['reason_code'] == 'EXISTING_MD_LINK'


def test_md_export_accepts_approved_cases_with_legacy_auto_values(project):
    from _state import update_state
    md.save_group(SUITE, ['혜택', '혜택 탭'], 'yafit_benefit', 'YFB')
    def legacy(data):
        for case, value in zip(data['cases'], ('N', '', 'Y-app')):
            case['auto'] = value
        return data
    update_state(lib._cases_path(SUITE), legacy)
    assert md.eligibility(SUITE)['funnel'][-1]['count'] == 4
    assert len(md.build_rows(SUITE)) == 4
    assert all('AUTO' not in f['label'] for f in md.eligibility(SUITE)['funnel'])
