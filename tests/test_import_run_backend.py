from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

import openpyxl
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import _import_commit as backend


MAPPINGS = {
    "tc_id": "A열", "title": "B열", "steps": "C열", "expected": "D열",
    "group": "E열", "priority": "F열", "tags": "G열",
}


def make_book(path: Path, sheets: dict[str, list[list[object]]]) -> None:
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, rows in sheets.items():
        ws = wb.create_sheet(name)
        for row in rows:
            ws.append(row)
    wb.save(path)


@pytest.fixture
def roots(tmp_path):
    project = tmp_path / "project"
    result = {
        "project": project,
        "imports": project / "import",
        "testcases": project / "testcases",
        "runs": project / "state" / "import_sessions",
        "snapshots": project / "state" / "import_snapshots",
    }
    for path in result.values():
        path.mkdir(parents=True, exist_ok=True)
    return result


def preview(roots, sources):
    return backend.create_preview(
        {"sources": sources}, roots["imports"], roots["testcases"], roots["runs"]
    )


def test_multi_file_sheet_preview_has_one_run_and_provenance(roots):
    make_book(roots["imports"] / "a.xlsx", {
        "one": [["보고서 제목"], ["TC ID", "Title", "Steps", "Expected", "Group"],
                ["A_01", "첫째", "1. 실행", "성공", "login"],
                ["bad id!", "형식 오류", "실행", "실패", "login"]],
        "two": [["TC ID", "Title", "Steps", "Expected", "Group"],
                ["A_02", "둘째", "실행", "성공", "login"]],
    })
    make_book(roots["imports"] / "b.xlsx", {
        "main": [["TC ID", "Title", "Steps", "Expected", "Group"],
                 ["B_01", "셋째", "실행", "성공", "checkout"]],
    })
    run = preview(roots, [
        {"file_id": "a.xlsx", "sheet_name": "one", "mappings": MAPPINGS},
        {"file_id": "a.xlsx", "sheet_name": "two", "mappings": MAPPINGS},
        {"file_id": "b.xlsx", "sheet_name": "main", "mappings": MAPPINGS},
    ])

    assert run["run_id"].startswith("run_")
    assert len(run["sources"]) == 3
    assert len(run["rows"]) == 4
    assert run["summary"] == {"added": 3, "updated": 0, "conflict": 0, "error": 1, "same": 0}
    assert run["rows"][0]["_source_file"] == "a.xlsx"
    assert run["rows"][0]["_source_sheet"] == "one"
    assert run["rows"][0]["_row"] == 3
    assert run["rows"][1]["reason"] == "tc_id 형식 오류"
    assert (roots["runs"] / f"{run['run_id']}.json").exists()


def test_duplicate_id_in_selected_sources_is_conflict(roots):
    make_book(roots["imports"] / "a.xlsx", {
        "one": [["TC ID", "Title", "Steps", "Expected", "Group"], ["D_01", "one", "s", "e", "g"]],
        "two": [["TC ID", "Title", "Steps", "Expected", "Group"], ["D_01", "two", "s", "e", "g"]],
    })
    run = preview(roots, [
        {"file_id": "a.xlsx", "sheet_name": sheet, "mappings": MAPPINGS}
        for sheet in ("one", "two")
    ])
    assert run["summary"]["conflict"] == 2
    assert all(row["status"] == "conflict" for row in run["rows"])


def test_commit_and_rollback_restore_modified_renamed_and_new_files(roots):
    old = roots["testcases"] / "login" / "tc_A_01_old.md"
    old.parent.mkdir(parents=True)
    old_content = "---\nid: A_01\n---\n# Old\n\n## Steps\nold\n\n## Expected\nold\n"
    old.write_text(old_content, encoding="utf-8")
    before = backend._tree_hash(roots["testcases"])
    make_book(roots["imports"] / "a.xlsx", {
        "main": [["TC ID", "Title", "Steps", "Expected", "Group"],
                 ["A_01", "Renamed title", "new", "new", "login"],
                 ["A_02", "Brand new", "new", "new", "login"]]
    })
    run = preview(roots, [{"file_id": "a.xlsx", "sheet_name": "main", "mappings": MAPPINGS}])
    result = backend.commit_run(run["run_id"], roots["imports"], roots["testcases"], roots["runs"],
                                roots["snapshots"], roots["project"])
    assert result["committed"] == 2
    assert not old.exists()
    assert len(list(roots["testcases"].rglob("tc_*.md"))) == 2
    manifest = json.loads((roots["snapshots"] / result["snapshot_id"] / "manifest.json").read_text())
    assert manifest["status"] == "committed"
    assert len(manifest["entries"]) == 3

    rolled = backend.rollback_run(run["run_id"], roots["runs"], roots["snapshots"], roots["project"])
    assert rolled == {"run_id": run["run_id"], "status": "rolled_back",
                      "restored": 1, "deleted": 2, "verified": True}
    assert old.read_text(encoding="utf-8") == old_content
    assert backend._tree_hash(roots["testcases"]) == before


def test_commit_rejects_changed_excel_and_changed_target(roots):
    book = roots["imports"] / "a.xlsx"
    make_book(book, {"main": [["TC ID", "Title", "Steps", "Expected", "Group"], ["A_01", "one", "s", "e", "g"]]})
    run = preview(roots, [{"file_id": "a.xlsx", "sheet_name": "main", "mappings": MAPPINGS}])
    book.write_bytes(book.read_bytes() + b"changed")
    with pytest.raises(backend.ImportRunError, match="원본 Excel") as error:
        backend.commit_run(run["run_id"], roots["imports"], roots["testcases"], roots["runs"],
                           roots["snapshots"], roots["project"])
    assert error.value.code == "SOURCE_CHANGED"

    make_book(book, {"main": [["TC ID", "Title", "Steps", "Expected", "Group"], ["A_01", "one", "s", "e", "g"]]})
    run = preview(roots, [{"file_id": "a.xlsx", "sheet_name": "main", "mappings": MAPPINGS}])
    external = roots["testcases"] / "g" / "tc_X_01_external.md"
    external.parent.mkdir(parents=True)
    external.write_text("external", encoding="utf-8")
    with pytest.raises(backend.ImportRunError, match="테스트케이스가 변경") as error:
        backend.commit_run(run["run_id"], roots["imports"], roots["testcases"], roots["runs"],
                           roots["snapshots"], roots["project"])
    assert error.value.code == "TARGET_CHANGED"


def test_mid_commit_failure_automatically_restores_every_path(roots, monkeypatch):
    old = roots["testcases"] / "g" / "tc_A_01_old.md"
    old.parent.mkdir(parents=True)
    old.write_text("---\nid: A_01\n---\n# Old\n\n## Steps\ns\n\n## Expected\ne\n", encoding="utf-8")
    before = backend._tree_hash(roots["testcases"])
    make_book(roots["imports"] / "a.xlsx", {
        "main": [["TC ID", "Title", "Steps", "Expected", "Group"],
                 ["A_01", "Changed", "s2", "e2", "g"], ["A_02", "New", "s", "e", "g"]]
    })
    run = preview(roots, [{"file_id": "a.xlsx", "sheet_name": "main", "mappings": MAPPINGS}])
    real_replace = backend._replace_file
    calls = 0
    def fail_second(temp, target):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected write failure")
        real_replace(temp, target)
    monkeypatch.setattr(backend, "_replace_file", fail_second)

    with pytest.raises(backend.ImportRunError) as error:
        backend.commit_run(run["run_id"], roots["imports"], roots["testcases"], roots["runs"],
                           roots["snapshots"], roots["project"])
    assert error.value.code == "COMMIT_RECOVERED"
    assert backend._tree_hash(roots["testcases"]) == before
    assert backend.load_run(roots["runs"], run["run_id"])["status"] == "preview_ready"


def test_skipped_csv_contains_provenance(roots):
    make_book(roots["imports"] / "a.xlsx", {
        "main": [["TC ID", "Title", "Steps", "Expected", "Group"], ["bad id", "Bad", "s", "e", "g"]]
    })
    run = preview(roots, [{"file_id": "a.xlsx", "sheet_name": "main", "mappings": MAPPINGS}])
    csv_text = backend.rows_csv(run, skipped_only=True).decode("utf-8-sig")
    assert "source_file_id,file,sheet,row,tc_id" in csv_text
    assert ",a.xlsx,main,2,bad id" in csv_text


def test_next_commit_recovers_interrupted_write_ahead_journal(roots):
    target = roots["testcases"] / "g" / "tc_A_01_case.md"
    target.parent.mkdir(parents=True)
    target.write_text("mutated", encoding="utf-8")
    snapshot = roots["snapshots"] / "snap_interrupted"
    backup = snapshot / "backup" / "testcases" / "g" / target.name
    backup.parent.mkdir(parents=True)
    backup.write_text("original", encoding="utf-8")
    before_sha = hashlib.sha256(b"original").hexdigest()
    after_sha = hashlib.sha256(b"mutated").hexdigest()
    (snapshot / "manifest.json").write_text(json.dumps({
        "snapshot_id": "snap_interrupted", "run_id": "run_old", "status": "applying",
        "entries": [{"target": f"testcases/g/{target.name}", "before_exists": True,
                     "backup": f"backup/testcases/g/{target.name}", "before_sha256": before_sha,
                     "after_exists": True, "after_sha256": after_sha}],
    }), encoding="utf-8")
    make_book(roots["imports"] / "a.xlsx", {
        "main": [["TC ID", "Title", "Steps", "Expected", "Group"], ["B_01", "New", "s", "e", "g"]]
    })
    run = preview(roots, [{"file_id": "a.xlsx", "sheet_name": "main", "mappings": MAPPINGS}])
    # Preview was taken while the interrupted mutation existed; after recovery
    # the stale-target guard aborts this commit, but recovery must still finish.
    with pytest.raises(backend.ImportRunError) as error:
        backend.commit_run(run["run_id"], roots["imports"], roots["testcases"], roots["runs"],
                           roots["snapshots"], roots["project"])
    assert error.value.code == "TARGET_CHANGED"
    assert target.read_text(encoding="utf-8") == "original"
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "recovered"


def test_interrupted_recovery_preserves_divergent_post_crash_edit(roots):
    target = roots["testcases"] / "g" / "tc_A_01_case.md"
    target.parent.mkdir(parents=True)
    target.write_text("external edit", encoding="utf-8")
    snapshot = roots["snapshots"] / "snap_interrupted"
    backup = snapshot / "backup" / "testcases" / "g" / target.name
    backup.parent.mkdir(parents=True)
    backup.write_text("original", encoding="utf-8")
    (snapshot / "manifest.json").write_text(json.dumps({
        "snapshot_id": "snap_interrupted", "run_id": "run_old", "status": "applying",
        "entries": [{
            "target": f"testcases/g/{target.name}", "before_exists": True,
            "backup": f"backup/testcases/g/{target.name}",
            "before_sha256": hashlib.sha256(b"original").hexdigest(),
            "after_exists": True,
            "after_sha256": hashlib.sha256(b"transaction write").hexdigest(),
        }],
    }), encoding="utf-8")
    make_book(roots["imports"] / "a.xlsx", {
        "main": [["TC ID", "Title", "Steps", "Expected", "Group"],
                 ["B_01", "New", "s", "e", "g"]]
    })
    run = preview(roots, [{"file_id": "a.xlsx", "sheet_name": "main", "mappings": MAPPINGS}])

    with pytest.raises(backend.ImportRunError) as error:
        backend.commit_run(run["run_id"], roots["imports"], roots["testcases"], roots["runs"],
                           roots["snapshots"], roots["project"])

    assert error.value.code == "RECOVERY_CONFLICT"
    assert target.read_text(encoding="utf-8") == "external edit"
    manifest = json.loads((snapshot / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "recovery_conflict"
    with pytest.raises(backend.ImportRunError) as repeated:
        backend.commit_run(run["run_id"], roots["imports"], roots["testcases"], roots["runs"],
                           roots["snapshots"], roots["project"])
    assert repeated.value.code == "RECOVERY_CONFLICT"
    assert target.read_text(encoding="utf-8") == "external edit"


def test_partial_mapped_row_is_reported_not_dropped(roots):
    make_book(roots["imports"] / "a.xlsx", {
        "main": [["TC ID", "Title", "Steps", "Expected", "Group"], ["", "partial", "", "", "g"]]
    })
    run = preview(roots, [{"file_id": "a.xlsx", "sheet_name": "main", "mappings": MAPPINGS}])
    assert len(run["rows"]) == 1
    assert run["rows"][0]["reason_code"] == "MISSING_TC_ID"


def test_conflicts_require_exact_explicit_exclude_decisions(roots):
    existing = roots["testcases"] / "old" / "tc_A_01_old.md"
    existing.parent.mkdir(parents=True)
    existing.write_text("---\nid: A_01\n---\n# Old\n\n## Steps\ns\n\n## Expected\ne\n", encoding="utf-8")
    make_book(roots["imports"] / "a.xlsx", {
        "main": [["TC ID", "Title", "Steps", "Expected", "Group"], ["A_01", "Move", "s", "e", "new"]]
    })
    run = preview(roots, [{"file_id": "a.xlsx", "sheet_name": "main", "mappings": MAPPINGS}])
    args = (run["run_id"], roots["imports"], roots["testcases"], roots["runs"],
            roots["snapshots"], roots["project"])
    with pytest.raises(backend.ImportRunError) as error:
        backend.commit_run(*args)
    assert error.value.code == "UNRESOLVED_CONFLICT"
    decision = [{"file_name": "a.xlsx", "sheet_name": "main", "source_row": 2,
                 "tc_id": "A_01", "action": "exclude"}]
    result = backend.commit_run(*args, decisions=decision)
    assert result["committed"] == 0
    assert backend.load_run(roots["runs"], run["run_id"])["decisions"] == decision


def test_idempotency_replay_requires_same_canonical_decisions(roots):
    for tc_id in ("A_01", "A_02"):
        existing = roots["testcases"] / "old" / f"tc_{tc_id}_old.md"
        existing.parent.mkdir(parents=True, exist_ok=True)
        existing.write_text(
            f"---\nid: {tc_id}\n---\n# Old\n\n## Steps\ns\n\n## Expected\ne\n",
            encoding="utf-8",
        )
    make_book(roots["imports"] / "a.xlsx", {
        "main": [["TC ID", "Title", "Steps", "Expected", "Group"],
                 ["A_01", "Move one", "s", "e", "new"],
                 ["A_02", "Move two", "s", "e", "new"]]
    })
    run = preview(roots, [{"file_id": "a.xlsx", "sheet_name": "main", "mappings": MAPPINGS}])
    decisions = [
        {"file_name": "a.xlsx", "sheet_name": "main", "source_row": row,
         "tc_id": tc_id, "action": "exclude"}
        for row, tc_id in ((2, "A_01"), (3, "A_02"))
    ]
    args = (run["run_id"], roots["imports"], roots["testcases"], roots["runs"],
            roots["snapshots"], roots["project"])

    committed = backend.commit_run(*args, idempotency_key="stable-key", decisions=decisions)
    tree_after_commit = backend._tree_hash(roots["testcases"])
    replayed = backend.commit_run(
        *args, idempotency_key="stable-key",
        decisions=[{**decision, "source_row": str(decision["source_row"]), "ignored": True}
                   for decision in reversed(decisions)],
    )

    assert replayed["replayed"] is True
    persisted = backend.load_run(roots["runs"], run["run_id"])
    manifest = json.loads(
        (roots["snapshots"] / committed["snapshot_id"] / "manifest.json").read_text(encoding="utf-8")
    )
    assert persisted["request_fingerprint"] == manifest["request_fingerprint"]
    assert len(persisted["request_fingerprint"]) == 64

    changed = [{**decision} for decision in decisions]
    changed[0]["action"] = "include"
    with pytest.raises(backend.ImportRunError) as conflict:
        backend.commit_run(*args, idempotency_key="stable-key", decisions=changed)
    assert conflict.value.code == "IDEMPOTENCY_CONFLICT"
    assert backend._tree_hash(roots["testcases"]) == tree_after_commit


def test_rollback_rejects_external_post_commit_change(roots):
    make_book(roots["imports"] / "a.xlsx", {
        "main": [["TC ID", "Title", "Steps", "Expected", "Group"], ["A_01", "New", "s", "e", "g"]]
    })
    run = preview(roots, [{"file_id": "a.xlsx", "sheet_name": "main", "mappings": MAPPINGS}])
    backend.commit_run(run["run_id"], roots["imports"], roots["testcases"], roots["runs"],
                       roots["snapshots"], roots["project"])
    target = next(roots["testcases"].rglob("tc_*.md"))
    target.write_text(target.read_text(encoding="utf-8") + "external", encoding="utf-8")
    with pytest.raises(backend.ImportRunError) as error:
        backend.rollback_run(run["run_id"], roots["runs"], roots["snapshots"], roots["project"],
                             roots["testcases"])
    assert error.value.code == "ROLLBACK_CONFLICT"


def test_rollback_reports_final_digest_verification_failure(roots, monkeypatch):
    make_book(roots["imports"] / "a.xlsx", {
        "main": [["TC ID", "Title", "Steps", "Expected", "Group"], ["A_01", "New", "s", "e", "g"]]
    })
    run = preview(roots, [{"file_id": "a.xlsx", "sheet_name": "main", "mappings": MAPPINGS}])
    backend.commit_run(run["run_id"], roots["imports"], roots["testcases"], roots["runs"],
                       roots["snapshots"], roots["project"])
    real_hash = backend._tree_hash
    calls = 0
    def mismatch_after_restore(path):
        nonlocal calls
        calls += 1
        return real_hash(path) if calls == 1 else "mismatch"
    monkeypatch.setattr(backend, "_tree_hash", mismatch_after_restore)
    with pytest.raises(backend.ImportRunError) as error:
        backend.rollback_run(run["run_id"], roots["runs"], roots["snapshots"], roots["project"],
                             roots["testcases"])
    assert error.value.code == "ROLLBACK_VERIFICATION_FAILED"
    assert backend.load_run(roots["runs"], run["run_id"])["status"] == "rollback_verification_failed"


def test_rollback_preflights_all_backups_before_mutating_any_target(roots):
    for tc_id in ("A_01", "A_02"):
        path = roots["testcases"] / "g" / f"tc_{tc_id}_old.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"---\nid: {tc_id}\n---\n# Old {tc_id}\n\n## Steps\nold\n\n## Expected\nold\n",
            encoding="utf-8",
        )
    make_book(roots["imports"] / "a.xlsx", {
        "main": [["TC ID", "Title", "Steps", "Expected", "Group"],
                 ["A_01", "New One", "new", "new", "g"],
                 ["A_02", "New Two", "new", "new", "g"]]
    })
    run = preview(roots, [{"file_id": "a.xlsx", "sheet_name": "main", "mappings": MAPPINGS}])
    committed = backend.commit_run(run["run_id"], roots["imports"], roots["testcases"], roots["runs"],
                                   roots["snapshots"], roots["project"])
    manifest_path = roots["snapshots"] / committed["snapshot_id"] / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    backup_entry = next(entry for entry in manifest["entries"] if entry.get("backup"))
    backup = roots["snapshots"] / committed["snapshot_id"] / backup_entry["backup"]
    backup.write_text("corrupt", encoding="utf-8")
    committed_contents = {
        path: path.read_bytes() for path in roots["testcases"].rglob("tc_*.md")
    }

    with pytest.raises(backend.ImportRunError) as error:
        backend.rollback_run(run["run_id"], roots["runs"], roots["snapshots"], roots["project"],
                             roots["testcases"])

    assert error.value.code == "SNAPSHOT_CORRUPT"
    assert {path: path.read_bytes() for path in roots["testcases"].rglob("tc_*.md")} == committed_contents


def test_interrupted_rollback_recovery_preserves_divergent_external_edit(roots):
    original = roots["testcases"] / "g" / "tc_A_01_old.md"
    original.parent.mkdir(parents=True)
    original.write_text(
        "---\nid: A_01\n---\n# Old\n\n## Steps\nold\n\n## Expected\nold\n",
        encoding="utf-8",
    )
    make_book(roots["imports"] / "a.xlsx", {
        "main": [["TC ID", "Title", "Steps", "Expected", "Group"],
                 ["A_01", "New", "new", "new", "g"]]
    })
    run = preview(roots, [{"file_id": "a.xlsx", "sheet_name": "main", "mappings": MAPPINGS}])
    committed = backend.commit_run(
        run["run_id"], roots["imports"], roots["testcases"], roots["runs"],
        roots["snapshots"], roots["project"],
    )
    manifest_path = roots["snapshots"] / committed["snapshot_id"] / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "rolling_back"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    committed_target = next(roots["testcases"].rglob("tc_*.md"))
    committed_target.write_text("external post-crash edit", encoding="utf-8")

    with pytest.raises(backend.ImportRunError) as error:
        backend.rollback_run(run["run_id"], roots["runs"], roots["snapshots"], roots["project"],
                             roots["testcases"])

    assert error.value.code == "RECOVERY_CONFLICT"
    assert committed_target.read_text(encoding="utf-8") == "external post-crash edit"
    persisted_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    persisted_run = backend.load_run(roots["runs"], run["run_id"])
    assert persisted_manifest["status"] == "recovery_conflict"
    assert persisted_manifest["recovery_operation"] == "rollback"
    assert persisted_run["status"] == "recovery_conflict"
    with pytest.raises(backend.ImportRunError) as repeated:
        backend.rollback_run(run["run_id"], roots["runs"], roots["snapshots"], roots["project"],
                             roots["testcases"])
    assert repeated.value.code == "RECOVERY_CONFLICT"
    assert committed_target.read_text(encoding="utf-8") == "external post-crash edit"


@pytest.mark.parametrize("prefix", ["", " ", "\t", "\n", "\x01", "\x7f", "\ufeff"])
@pytest.mark.parametrize("operator", ["=", "+", "-", "@"])
def test_csv_export_sanitizes_formula_cells_after_whitespace_or_control(prefix, operator):
    dangerous = f"{prefix}{operator}SUM(1,1)"
    row = {
        key: dangerous for key in (
            "_source_file_id", "_source_file", "_source_sheet", "_row", "tc_id",
            "title", "group", "status", "reason_code", "reason",
        )
    }

    parsed = list(csv.reader(io.StringIO(backend.rows_csv({"rows": [row]}).decode("utf-8-sig"))))

    assert parsed[1] == ["'" + dangerous] * 10


def test_rendered_frontmatter_safely_round_trips_adversarial_tags(roots):
    tags = ["normal", "]\n---\nid: EVIL", 'quote" and comma, value', "@formula"]
    row = {
        "tc_id": "SAFE_01", "title": "Safe", "steps": "one", "expected": "done",
        "priority": "HIGH", "tags": tags, "group": "safe",
    }
    target = roots["testcases"] / "safe" / "tc_SAFE_01_safe.md"
    target.parent.mkdir(parents=True)
    rendered = backend._render(row)
    target.write_text(rendered, encoding="utf-8")

    assert rendered.splitlines().count("---") == 2
    assert 'id: "SAFE_01"' in rendered
    assert "\\n---\\nid: EVIL" in rendered
    parsed = backend.load_existing_testcases(roots["testcases"])["SAFE_01"]
    assert parsed["tags"] == tags
    assert parsed["priority"] == "high"
    assert parsed["title"] == "Safe"
    assert parsed["steps"] == "one"
    assert parsed["expected"] == "done"


def test_preview_before_contains_existing_comparison_fields(roots):
    existing = roots["testcases"] / "g" / "tc_A_01_old.md"
    existing.parent.mkdir(parents=True)
    existing.write_text(
        '---\nid: "A_01"\npriority: "low"\ntags: ["old", "stable"]\n---\n'
        "# Old title\n\n## Steps\nold steps\n\n## Expected\nold expected\n",
        encoding="utf-8",
    )
    make_book(roots["imports"] / "a.xlsx", {
        "main": [["TC ID", "Title", "Steps", "Expected", "Group"],
                 ["A_01", "New title", "new steps", "new expected", "g"]]
    })

    run = preview(roots, [{"file_id": "a.xlsx", "sheet_name": "main", "mappings": MAPPINGS}])

    assert run["rows"][0]["before"] == {
        "title": "Old title", "steps": "old steps", "expected": "old expected",
        "priority": "low", "tags": ["old", "stable"], "group": "g",
        "hash": backend.load_existing_testcases(roots["testcases"])["A_01"]["hash"],
        "file_name": "tc_A_01_old.md",
    }
