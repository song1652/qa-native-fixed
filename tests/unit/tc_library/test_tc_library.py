from __future__ import annotations

import pytest

import _tc_library as lib
from _tc_template import analyze_workbook
from _tc_xlsx_import import import_workbook

SUITE = "야핏무브"


@pytest.fixture
def seeded(library_dir, template_xlsx):
    profiles = analyze_workbook(template_xlsx)
    cases = import_workbook(template_xlsx, profiles, ["혜택", "홈"], {"혜택": "BEN", "홈": "HOME"})
    lib.save_template(SUITE, template_xlsx, profiles)
    lib.import_cases(SUITE, ["혜택", "홈"], cases, "tester")
    return cases


def test_import_is_idempotent_and_updates_by_case_id(seeded):
    assert lib.import_cases(SUITE, ["혜택", "홈"], seeded, "tester") == \
        {"created": 0, "updated": 0, "unchanged": 6}
    changed = [dict(c) for c in seeded]
    changed[0]["priority"] = "P1"
    assert lib.import_cases(SUITE, ["혜택", "홈"], changed, "tester")["updated"] == 1
    assert lib.get_case(SUITE, "BEN_0001")["rev"] == 2
    assert lib.list_suites() == [{"suite": SUITE, "sheets": ["혜택", "홈"], "count": 6}]


def test_patch_bumps_rev_and_rejects_stale_rev(seeded):
    case = lib.patch_case(SUITE, "BEN_0002", 1, {"priority": "P1"}, "tester")
    assert (case["rev"], case["priority"]) == (2, "P1")

    with pytest.raises(lib.RevConflict) as exc:
        lib.patch_case(SUITE, "BEN_0002", 1, {"priority": "P2"}, "tester")
    assert exc.value.server_case["rev"] == 2 and exc.value.status == 409

    with pytest.raises(lib.LibraryError) as exc:
        lib.patch_case(SUITE, "BEN_0002", 2, {"rev": 99}, "tester")
    assert exc.value.code == "FIELD_NOT_EDITABLE"


def test_bulk_patch_applies_matching_revs_and_reports_conflicts(seeded):
    result = lib.bulk_patch(SUITE, [{"case_id": "BEN_0001", "rev": 1},
                                    {"case_id": "BEN_0002", "rev": 7}], {"auto": "Y-app"}, "t")
    assert result["updated"] == ["BEN_0001"]
    assert [c["case_id"] for c in result["conflicts"]] == ["BEN_0002"]


def test_history_and_revert(seeded):
    lib.patch_case(SUITE, "BEN_0002", 1, {"priority": "P1"}, "tester")
    entry = next(e for e in lib.history(SUITE, "BEN_0002") if e["field"] == "priority")
    assert (entry["before"], entry["after"], entry["actor"]) == ("", "P1", "tester")

    reverted = lib.revert(SUITE, "BEN_0002", entry["history_id"], 2, "tester")
    assert (reverted["priority"], reverted["rev"]) == ("", 3)


def test_create_duplicate_delete_restore(seeded):
    created = lib.create_case(SUITE, {"sheet": "혜택", "feature": "새 기능",
                                      "path": ["혜택 탭", "상단 배너", ""]}, "t", after="BEN_0003")
    assert (created["case_id"], created["status"]) == ("BEN_0006", "draft")
    order = [c["case_id"] for c in lib.load_cases(SUITE)]
    assert order.index("BEN_0006") == order.index("BEN_0003") + 1

    dup = lib.duplicate_case(SUITE, "BEN_0001", "t")
    assert (dup["case_id"], dup["feature"], dup["status"]) == ("BEN_0007", "혜택 탭 버튼", "draft")
    assert dup["source_refs"] == lib.get_case(SUITE, "BEN_0001")["source_refs"]

    assert lib.delete_cases(SUITE, [{"case_id": "BEN_0001", "rev": 1}], "t")["deleted"] == ["BEN_0001"]
    assert "BEN_0001" not in [c["case_id"] for c in lib.load_cases(SUITE)]
    assert lib.restore_case(SUITE, "BEN_0001", "t")["rev"] == 3


def test_tree_counts_and_filters(seeded):
    lib.create_case(SUITE, {"sheet": "혜택", "feature": "새 기능",
                            "path": ["혜택 탭", "상단 배너", ""]}, "t")
    tree = lib.build_tree(lib.load_cases(SUITE))
    benefit = tree[0]
    assert (benefit["name"], benefit["level"], benefit["count"], benefit["draft"]) == ("혜택", "sheet", 6, 1)
    banner = benefit["children"][0]["children"][1]
    assert (banner["name"], banner["level"], banner["count"], banner["invalid"]) == ("상단 배너", "l2", 3, 1)

    cases = lib.load_cases(SUITE)
    ids = lambda q: [c["case_id"] for c in lib.filter_cases(cases, q)]
    assert ids({"path": "혜택/혜택 탭/상단 배너"}) == ["BEN_0002", "BEN_0003", "BEN_0006"]
    assert ids({"q": "돈불리기"}) == ["BEN_0004", "BEN_0005"]
    assert ids({"invalid": "1"}) == ["BEN_0006"]
    assert ids({"execution_result": "fail"}) == ["BEN_0003"]
    assert ids({"priority": "-", "sheet": "홈"}) == []


def test_suite_name_cannot_escape_library_dir(library_dir):
    for bad in ("../etc", "_uploads", ""):
        with pytest.raises(lib.LibraryError):
            lib.suite_dir(bad)
