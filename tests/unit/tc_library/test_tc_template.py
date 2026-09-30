from __future__ import annotations

from _tc_template import TemplateProfile, analyze_workbook


def test_header_row_skips_summary_block_and_finds_sub_header(template_xlsx):
    profiles = analyze_workbook(template_xlsx)

    assert list(profiles) == ["혜택", "홈"]          # History는 TC 시트가 아니다
    benefit = profiles["혜택"]
    assert benefit.header_row == 11
    assert benefit.data_start_row == 13
    assert benefit.result_columns == {"And": 11, "iOS": 12}
    assert benefit.columns["l1"] == 2 and benefit.columns["note"] == 13


def test_dropdowns_and_no_formula_are_captured(template_xlsx):
    benefit = analyze_workbook(template_xlsx)["혜택"]

    assert benefit.validations == {
        "priority": ["P0", "P1", "P2"],
        "auto": ["AUTO"],
        "execution_result": ["Pass", "Fail", "NT", "NA"],
    }
    assert benefit.no_formula == '=IF(H{r}<>"",ROW(B{r})-12, "")'
    assert "우선순위 드롭다운을 내보낼 때 P0~P3으로 넓힙니다" in benefit.warnings


def test_profile_round_trips_through_dict(template_xlsx):
    benefit = analyze_workbook(template_xlsx)["혜택"]
    assert TemplateProfile.from_dict(benefit.to_dict()) == benefit
