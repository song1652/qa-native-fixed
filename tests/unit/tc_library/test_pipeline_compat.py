"""Phase 4 선행 과제: very_high(O7) · source_ref 보존(O3) · data_key 계약(O1)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import _paths
import coverage_matrix
import parse_cases
import sync_test_data
from _import_commit import _render


def _row(**kw):
    base = {"tc_id": "YFI_01", "title": "초대 링크 복사", "precondition": "", "steps": "1. 링크 복사 선택",
            "expected": "토스트가 노출된다.\n- 링크가 복사되었어요", "priority": "very_high", "tags": ["content"]}
    base.update(kw)
    return base


def test_render_keeps_very_high_and_source_ref_and_parser_reads_them():
    text = _render(_row(source_ref="tc-library:야핏무브/BEN_0172"))
    assert 'priority: "very_high"' in text and 'source_ref: "tc-library:야핏무브/BEN_0172"' in text
    (case,) = parse_cases.parse_md(text)
    assert (case["priority"], case["source_ref"], case["id"]) == ("very_high", "tc-library:야핏무브/BEN_0172", "YFI_01")
    assert 'priority: "medium"' in _render(_row(priority="urgent"))          # 모르는 값은 여전히 medium
    assert "source_ref" not in _render(_row())                                # 없으면 줄도 없다
    assert 'source_ref: "ab"' in _render(_row(source_ref="a---b"))          # "---"는 frontmatter를 끊으므로 뺀다


def test_coverage_counts_very_high(tmp_path, monkeypatch):
    group = tmp_path / "testcases" / "invite"
    group.mkdir(parents=True)
    (group / "tc_YFI_01_a.md").write_text(_render(_row()), encoding="utf-8")
    (group / "tc_YFI_02_b.md").write_text(_render(_row(tc_id="YFI_02", priority="low")), encoding="utf-8")
    monkeypatch.setattr(coverage_matrix, "TESTCASES_DIR", tmp_path / "testcases")
    monkeypatch.setattr(coverage_matrix, "PAGES_JSON", tmp_path / "pages.json")
    assert coverage_matrix.build_coverage()["invite"]["priority"] == {"very_high": 1, "high": 0, "medium": 0, "low": 1}


def test_data_key_contract(tmp_path, monkeypatch):
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    (data_dir / "serveone.json").write_text(json.dumps({"login": {"id": "x"}}), encoding="utf-8")
    (data_dir / "saucedemo.json").write_text(json.dumps({"valid_user": "standard_user"}), encoding="utf-8")
    monkeypatch.setattr(_paths, "TEST_DATA_DIR", data_dir)

    assert parse_cases.split_data_key("serveone.login", "customer_login") == ("serveone", "login")
    assert parse_cases.split_data_key("valid_user", "saucedemo") == ("saucedemo", "valid_user")
    cases = [{"data_key": "serveone.login"}, {"data_key": "valid_user"}, {"data_key": "serveone.logout"}, {"data_key": None}]
    assert parse_cases.validate_data_keys(cases[:1] + cases[2:], "customer_login") == ["serveone.logout"]
    assert parse_cases.validate_data_keys(cases[1:2], "saucedemo") == []


def test_sync_adds_missing_dataset(tmp_path, monkeypatch):
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    (data_dir / "serveone.json").write_text(json.dumps({"login": {}}), encoding="utf-8")
    monkeypatch.setattr(_paths, "TEST_DATA_DIR", data_dir)
    monkeypatch.setattr(sync_test_data, "TEST_DATA_DIR", data_dir)
    group = tmp_path / "testcases" / "customer_login"
    group.mkdir(parents=True)
    (group / "tc_CL_09_a.md").write_text(_render(_row(tc_id="CL_09")).replace("data_key: null", "data_key: serveone.signup"),
                                         encoding="utf-8")

    assert sync_test_data.sync(tmp_path / "testcases") == 1
    assert json.loads((data_dir / "serveone.json").read_text())["signup"] == {}
    assert json.loads((data_dir / "serveone.example.json").read_text())["signup"] == {}
    assert sync_test_data.sync(tmp_path / "testcases") == 0


@pytest.mark.parametrize("line", ["priority: very_high | high | medium | low", "data_key: {프로덕트}.{데이터셋} | null"])
def test_template_documents_contract(line):
    template = Path(__file__).resolve().parents[3] / "templates" / "tc-template.md"
    assert line in template.read_text(encoding="utf-8")
