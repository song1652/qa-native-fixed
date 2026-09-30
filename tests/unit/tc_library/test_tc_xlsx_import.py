from __future__ import annotations

from _tc_template import analyze_workbook
from _tc_xlsx_import import import_workbook, split_note


def _import(template_xlsx):
    profiles = analyze_workbook(template_xlsx)
    return import_workbook(template_xlsx, profiles, ["혜택", "홈"], {"혜택": "BEN", "홈": "HOME"})


def test_blank_hierarchy_cells_inherit_from_row_above(template_xlsx):
    cases = {c["case_id"]: c for c in _import(template_xlsx)}

    assert cases["BEN_0001"]["path"] == ["혜택 탭", "", ""]
    assert cases["BEN_0003"]["path"] == ["혜택 탭", "상단 배너", ""]
    # D16:D17 병합 + 17행 기능 칸 비어 있음 → 위 행의 소분류·기능을 이어받는다
    assert cases["BEN_0005"]["path"] == ["혜택 탭", "신규회원 한정 혜택", "돈불리기"]
    assert cases["BEN_0005"]["feature"] == "진입 불가"
    assert cases["HOME_0001"]["path"] == ["걷고 받기 탭", "", ""]


def test_cells_are_parsed_into_model_fields(template_xlsx):
    cases = {c["case_id"]: c for c in _import(template_xlsx)}
    first, banner, entry = cases["BEN_0001"], cases["BEN_0002"], cases["BEN_0004"]

    assert first["steps"] == ["앱 실행", "혜택 탭 선택"]
    assert first["priority"] == "P0" and first["status"] == "approved"
    assert banner["bullets"] == [{"text": "수동, 자동 스크롤", "verified": True}]
    assert entry["precondition"] == "- D+0 가입일자"
    assert entry["note"] == "돈불리기 정책 변경"
    assert entry["source_refs"] == ["xlsx:야핏무브_Full.xlsx#혜택!R16"]


def test_platform_results_merge_and_blank_stays_not_run(template_xlsx):
    cases = {c["case_id"]: c for c in _import(template_xlsx)}

    assert cases["BEN_0001"]["execution_result"] == ""        # 빈 칸 = 미실행
    assert cases["BEN_0002"]["execution_result"] == "pass"
    assert cases["BEN_0003"]["execution_result"] == "fail"    # Fail + Pass → fail
    assert cases["BEN_0005"]["execution_result"] == "na"


def test_split_note_reads_system_line_and_keeps_human_note():
    assert split_note("정책 변경\nid:BEN_0004 | src:conf:1@v2") == ("정책 변경", "BEN_0004", ["conf:1@v2"])
    assert split_note("id:BEN_0001") == ("", "BEN_0001", [])
    assert split_note("메모만 있음") == ("메모만 있음", None, [])
