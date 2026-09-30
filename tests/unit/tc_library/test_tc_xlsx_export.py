from __future__ import annotations

from datetime import date

import openpyxl

from _tc_model import new_case
from _tc_template import analyze_workbook
from _tc_xlsx_export import export_workbook
from _tc_xlsx_import import import_workbook


def _load(template_xlsx):
    profiles = analyze_workbook(template_xlsx)
    cases = import_workbook(template_xlsx, profiles, ["혜택", "홈"], {"혜택": "BEN", "홈": "HOME"})
    by_sheet: dict[str, list[dict]] = {}
    for case in cases:
        by_sheet.setdefault(case["sheet"], []).append(case)
    return profiles, by_sheet


def test_export_rewrites_rows_formulas_merges_and_dropdowns(template_xlsx, tmp_path):
    profiles, by_sheet = _load(template_xlsx)
    by_sheet["혜택"][4]["priority"] = "P3"
    out = tmp_path / "out.xlsx"
    export_workbook(template_xlsx, profiles, by_sheet, out, history_note="8.6.0 반영",
                    today=date(2026, 9, 30))

    wb = openpyxl.load_workbook(out)
    ws = wb["혜택"]
    assert ws["A17"].value == '=IF(H17<>"",ROW(B17)-12, "")'
    assert ws["J4"].value == "=COUNTIF($K$13:$K$17,I4)"               # #REF! 복구
    assert ws["J9"].value == "=IF($L3=0,0,COUNTA($A$13:$A$17))"       # 고정 범위 → 실제 범위
    assert {str(r) for r in ws.merged_cells.ranges} == {"B13:B17", "C14:C15", "C16:C17", "D16:D17", "E16:E17"}
    dvs = {dv.formula1: str(dv.sqref) for dv in ws.data_validations.dataValidation}
    assert dvs['"P0,P1,P2,P3"'] == "I13:I17"
    assert dvs['"Pass,Fail,NT,NA"'] == "K13:L17"
    assert ws["I17"].value == "P3"
    assert ws["K15"].value == ws["L15"].value == "Fail"
    assert ws["H17"].font.b is True                                  # 13행 스타일 복사
    assert ws["M16"].value == "돈불리기 정책 변경\nid:BEN_0004"
    assert [c.value for c in wb["History"][4]][1:3] == ["26.09.30", "8.6.0 반영"]
