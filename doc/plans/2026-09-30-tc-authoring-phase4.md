# TC Authoring Studio Phase 4 Implementation Plan — md 내보내기 (파이프라인 연결)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 라이브러리에서 웹으로 자동화할 수 있는 승인 케이스를 파이프라인용 `testcases/{group}/tc_*.md`로 내보내고, 미리보기·충돌 처리·반영·롤백을 스튜디오 안에서 끝낸다.

**Architecture:** 파일 쓰기·스냅샷·롤백은 Import Studio(`_import_commit`)를 그대로 쓴다. `create_preview`에서 행 분류 부분을 떼어 `create_preview_from_rows`를 만들고, 커밋의 원본 엑셀 해시 검사는 엑셀 출처에만 적용한다. `_tc_md_export`는 대상 판정 퍼널, 가지 → pages.json 그룹 매핑, case_id → tc_id 고정 배정, 드리프트(사람이 파일을 직접 고친 경우) 감지를 맡는다. 그 전에 파이프라인 쪽 계약 세 가지(PRD O1·O3·O7)를 정리한다.

**Tech Stack:** Python 3.14, 기존 Import Studio 커밋 엔진, 바닐라 JS, pytest + Playwright

**Spec:** [PRD](../TC_AUTHORING_PRD.md) F7, O1·O3·O7 · [명세](../TC_AUTHORING_ELEMENT_SPEC.md) 5.2장 · [목업](../../design-previews/tc-authoring-studio.html) 797~845행(md 카드) · [로드맵](../TC_AUTHORING_ROADMAP.md) · 선행: [Phase 1 계획](2026-09-29-tc-authoring-phase1.md) (Phase 2·3과는 독립이지만, 이 계획의 diff는 Phase 3까지 적용한 상태 기준이다)

> **검증 상태 (2026-09-30):** Phase 3까지 적용한 저장소 사본에 이 계획을 적용해 새 테스트 14개(단위·API 12 + E2E 2)를 포함한 `tests/unit/tc_library` 113개와 전체 789개가 통과했고, 전체를 3번 연속 돌려도 모두 통과했다. 기존 Import Studio·대시보드 테스트 186개는 `_import_commit.py` 수정 후에도 그대로 통과했다.

## Global Constraints

- 파일 쓰기·스냅샷·롤백은 `_import_commit.commit_run`·`rollback_run`만 쓴다. `testcases/`에 직접 쓰지 않는다.
- md 우선순위: P0 → `very_high`, P1 → `high`, P2 → `medium`, P3 → `low` (PRD O7). 파이프라인이 모르는 값은 여전히 `medium`.
- md 대상: `auto = "Y-web"` · `status = "approved"` · 검증 오류 없음 · 모든 화면 문구가 `verified` · 가지가 pages.json 그룹에 매핑됨 (PRD F7.1).
- `data_key`는 항상 `null`로 쓴다 (모바일 수동 TC에서 온 케이스). 계약은 `"{프로덕트}.{데이터셋}"` (PRD O1, 이 계획의 M1).
- frontmatter 추가 키는 한 줄 flat만: `source_ref: "tc-library:{suite}/{case_id}"`. 값에 `---`를 넣지 않는다 (parse_cases가 frontmatter를 끊는다).
- tc_id는 `{접두어}_{NN}`, 한번 배정하면 바뀌지 않는다. 파일 이름은 Import Studio `_target_for` 규칙(`tc_{tc_id}_{제목 slug}.md`)을 따른다.
- 커밋 메시지 끝: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

## Phase 4 결정

| # | 결정 | 이유 |
|---|---|---|
| V1 | `data_key` 계약 = `"{프로덕트}.{데이터셋}"` → `test_data[프로덕트][데이터셋]`. 점이 없으면 그룹 폴더명을 프로덕트로 본다 | 실제 데이터 구조(`test_data/serveone.json` → `{"login": …}`)와 생성 코드(`test_data["serveone"]["login"]`)에 맞춘다. 지금 TC는 모두 `null`이라 깨지는 것이 없다 |
| V2 | 충돌마다 "건너뛰기"를 고른 것만 `exclude` 결정으로 보내고, 정책은 `overwrite` | Import Studio 결정은 `exclude`만 받으므로, 나머지를 덮어쓰기로 처리하면 행별 선택이 된다 |
| V3 | 드리프트 = 마지막 내보내기 때 기록한 파일 해시와 지금 해시가 다름 → 미리보기에서 `FILE_DRIFT` 충돌로 올린다 | 라이브러리가 원본이지만, 사람이 고친 내용을 말없이 덮어쓰지 않는다 (PRD F7.5) |
| V4 | 롤백하면 "마지막 내보내기" 기록도 커밋 직전 상태로 되돌린다 | 롤백 뒤 드리프트 판정이 맞아야 한다 |
| V5 | 태그는 `_tc_review.classify`(positive·negative·validation) + 화면 문구가 있으면 `content` | 템플릿의 표준 태그만 쓴다 (비표준 `general`을 쓰지 않는다) |

---

## File Structure

| 파일 | 책임 | 작업 |
|---|---|---|
| `scripts/_import_commit.py` (수정) | 행 분류 공용화(`_preview_row`·`_save_run`), `create_preview_from_rows`, 엑셀 외 출처 해시 검사 제외, `very_high`, `source_ref` 줄 | M1 |
| `scripts/parse_cases.py` (수정) | `source_ref` 보존, `split_data_key`, `validate_data_keys` 방향 수정 | M1 |
| `scripts/coverage_matrix.py`, `scripts/sync_test_data.py`, `templates/tc-template.md` (수정) | `very_high` 집계 / `data_key` 계약 / 템플릿 문구 | M1 |
| `scripts/_tc_md_export.py` | 퍼널·그룹 매핑·tc_id 배정·드리프트·미리보기·커밋·롤백 | M2 |
| `agents/dashboard/routes_tc_md.py` (+ `routes_tc_library.py`, `serve.py`, 테스트 지원 수정) | md 내보내기 API | M3 |
| `agents/dashboard/static/js/tc-studio/{api,export}.js` (수정) | md 카드 | W12 |
| `doc/TEST_CASE_GUIDE.md` 외 | 문서 | W13 |

---

## Task M1: 파이프라인 계약 정리 + Import Studio 확장 (O1·O3·O7)

**Files:**
- Modify: `scripts/_import_commit.py`, `scripts/parse_cases.py`, `scripts/coverage_matrix.py`, `scripts/sync_test_data.py`, `templates/tc-template.md` (아래 diff)
- Test: `tests/unit/tc_library/test_pipeline_compat.py`

**Interfaces:**
- Produces:
  - `_import_commit.PRIORITIES = ("very_high", "high", "medium", "low")`, `_render(row)`가 `row["source_ref"]`를 한 줄로 쓴다
  - `_import_commit.create_preview_from_rows(rows, source, testcases_dir, runs_dir, *, conflict_policy=None) -> run` — `rows`: `{tc_id, title, precondition, steps(문자열), expected(문자열), priority, tags, group, source_ref?, _source_sheet, _row}`, `source`: `{"kind": "tc_library", "suite"}`
  - `commit_run`은 `source.get("kind", "excel") != "excel"`인 출처의 파일 해시를 검사하지 않는다 (트리 해시 검사는 그대로)
  - `parse_cases.split_data_key(data_key, group) -> (product, dataset)`, 파싱 결과에 `source_ref`
  - `sync_test_data.sync(testcases_dir, *, dry_run=False) -> 추가한 개수` (`main()`은 이것을 부른다)

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/unit/tc_library/test_pipeline_compat.py`

```python
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
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_pipeline_compat.py -q`
Expected: FAIL — `very_high`가 `medium`으로 바뀜, `split_data_key` 없음, 템플릿 문구 없음

- [ ] **Step 3: Import Studio 커밋 엔진** — 행 분류를 함수로 떼는 리팩터링이 들어 있다. 동작은 바꾸지 않는다 (오류 문구도 그대로)

```diff
--- a/scripts/_import_commit.py
+++ b/scripts/_import_commit.py
@@ -25,6 +25,8 @@
 
 
 STATUSES = ("added", "updated", "conflict", "error", "same")
+# md frontmatter priority 허용 값 (very_high는 TC 스튜디오 P0, PRD O7)
+PRIORITIES = ("very_high", "high", "medium", "low")
 
 
 class ImportRunError(RuntimeError):
@@ -142,35 +144,45 @@
                 tc_id = str(row.get("tc_id") or "").strip()
                 current_group = existing.get(tc_id, {}).get("group")
                 row["group"] = current_group or str(source["sheet_name"])
-            result = {**row, **classify_row(row, existing)}
-            result["_source_file_id"] = source["file_id"]
-            tc_id = str(row.get("tc_id", "")).strip()
-            if tc_id and tc_id in seen:
-                result.update(status="conflict", reason="선택한 Excel 범위 안에서 tc_id 중복",
-                              reason_code="DUPLICATE_SOURCE_TC_ID")
-                first = seen[tc_id]
-                first.update(status="conflict", reason="선택한 Excel 범위 안에서 tc_id 중복",
-                             reason_code="DUPLICATE_SOURCE_TC_ID",
-                             excluded=body.get("conflict_policy") == "exclude",
-                             decision="exclude" if body.get("conflict_policy") == "exclude" else "pending")
-            elif tc_id:
-                seen[tc_id] = result
-            current = existing.get(tc_id)
-            result["before"] = ({
-                field: current.get(field)
-                for field in ("title", "precondition", "steps", "expected", "priority", "tags", "group", "hash")
-            } | {"file_name": current["path"].name} if current else None)
-            result["after"] = {field: result.get(field) for field in
-                               ("tc_id", "title", "precondition", "steps", "expected", "priority", "tags", "group")}
-            if result.get("status") == "conflict":
-                excluded = body.get("conflict_policy") == "exclude"
-                result["excluded"] = excluded
-                result["decision"] = "exclude" if excluded else "pending"
-            else:
-                result["excluded"] = result.get("status") not in {"added", "updated"}
-                result["decision"] = "automatic"
-            rows.append(result)
+            rows.append(_preview_row(row, existing, seen, body.get("conflict_policy"),
+                                     source_id=source["file_id"]))
+    return _save_run(rows, source_records, testcases_dir, runs_dir)
+
+
+def _preview_row(row: dict, existing: dict, seen: dict, conflict_policy: str | None, *,
+                 source_id: str) -> dict:
+    """행 1개를 분류하고 before/after·결정 기본값을 붙인다 (Excel·TC 스튜디오 공용)."""
+    result = {**row, **classify_row(row, existing)}
+    result["_source_file_id"] = source_id
+    tc_id = str(row.get("tc_id", "")).strip()
+    if tc_id and tc_id in seen:
+        result.update(status="conflict", reason="선택한 Excel 범위 안에서 tc_id 중복",
+                      reason_code="DUPLICATE_SOURCE_TC_ID")
+        first = seen[tc_id]
+        first.update(status="conflict", reason="선택한 Excel 범위 안에서 tc_id 중복",
+                     reason_code="DUPLICATE_SOURCE_TC_ID",
+                     excluded=conflict_policy == "exclude",
+                     decision="exclude" if conflict_policy == "exclude" else "pending")
+    elif tc_id:
+        seen[tc_id] = result
+    current = existing.get(tc_id)
+    result["before"] = ({
+        field: current.get(field)
+        for field in ("title", "precondition", "steps", "expected", "priority", "tags", "group", "hash")
+    } | {"file_name": current["path"].name} if current else None)
+    result["after"] = {field: result.get(field) for field in
+                       ("tc_id", "title", "precondition", "steps", "expected", "priority", "tags", "group")}
+    if result.get("status") == "conflict":
+        excluded = conflict_policy == "exclude"
+        result["excluded"] = excluded
+        result["decision"] = "exclude" if excluded else "pending"
+    else:
+        result["excluded"] = result.get("status") not in {"added", "updated"}
+        result["decision"] = "automatic"
+    return result
 
+
+def _save_run(rows: list[dict], source_records: list[dict], testcases_dir: Path, runs_dir: Path) -> dict:
     summary = {status: sum(row.get("status") == status for row in rows) for status in STATUSES}
     run_id = f"run_{datetime.now().strftime('%Y%m%dT%H%M%S')}_{uuid.uuid4().hex[:8]}"
     run = {
@@ -187,6 +199,20 @@
     return run
 
 
+def create_preview_from_rows(rows: list[dict], source: dict, testcases_dir: Path, runs_dir: Path,
+                             *, conflict_policy: str | None = None) -> dict:
+    """Excel 없이 이미 만든 행으로 미리보기 run을 만든다 (TC 스튜디오 md 내보내기, Phase 4).
+
+    rows: {tc_id, title, precondition, steps, expected, priority, tags, group, source_ref?}
+    source: {"kind": "tc_library", "suite": …} — commit_run은 kind가 excel이 아닌 출처의 파일 해시를 검사하지 않는다.
+    """
+    existing = load_existing_testcases(testcases_dir)
+    seen: dict[str, dict] = {}
+    preview = [_preview_row(dict(row), existing, seen, conflict_policy, source_id=str(source.get("suite", "")))
+               for row in rows]
+    return _save_run(preview, [source], testcases_dir, runs_dir)
+
+
 def load_run(runs_dir: Path, run_id: str) -> dict:
     if not re.fullmatch(r"run_[A-Za-z0-9_-]+|sess_[A-Za-z0-9_-]+", run_id):
         raise ImportRunError("invalid run_id", "INVALID_RUN_ID")
@@ -205,13 +231,17 @@
         raise ImportRunError("tags는 문자열 배열이어야 합니다", "INVALID_TAGS")
     tags_text = json.dumps([str(tag) for tag in tags], ensure_ascii=False)
     priority = str(row.get("priority") or "medium").lower()
-    if priority not in {"high", "medium", "low"}:
+    if priority not in PRIORITIES:
         priority = "medium"
     precondition = str(row.get("precondition") or "").strip()
+    # 한 줄짜리 flat 키만 쓴다 (parse_cases의 frontmatter 파서가 줄 단위라서). "---"가 들어가면 안 된다.
+    source_ref = str(row.get("source_ref") or "").replace("---", "").strip()
+    source_line = f"source_ref: {json.dumps(source_ref, ensure_ascii=False)}\n" if source_ref else ""
     precondition_section = f"## 사전 조건\n{precondition}\n\n" if precondition else ""
     return (
         f"---\nid: {json.dumps(str(row['tc_id']), ensure_ascii=False)}\ndata_key: null\n"
-        f"priority: {json.dumps(priority)}\ntags: {tags_text}\ntype: structured\n---\n"
+        f"priority: {json.dumps(priority)}\ntags: {tags_text}\ntype: structured\n"
+        f"{source_line}---\n"
         f"# {row['title']}\n\n{precondition_section}"
         f"## Steps\n{row['steps']}\n\n"
         f"## Expected\n{row['expected']}\n"
@@ -537,6 +567,8 @@
         run["request_fingerprint"] = request_fingerprint
         _atomic_json(runs_dir / f"{run_id}.json", run)
         for source in run.get("sources", []):
+            if source.get("kind", "excel") != "excel":   # TC 스튜디오 출처는 Excel 파일이 없다
+                continue
             path = _resolve_file(import_dir, source["file_id"])
             if file_sha256(path) != source["file_sha256"]:
                 raise ImportRunError(f"Preview 이후 원본 Excel 변경: {path.name}", "SOURCE_CHANGED")
```

- [ ] **Step 4: 파서·커버리지·동기화·템플릿**

```diff
--- a/scripts/parse_cases.py
+++ b/scripts/parse_cases.py
@@ -110,6 +110,8 @@
             case["data_key"] = meta.get("data_key")
             case["priority"] = meta.get("priority")
             case["tags"] = meta.get("tags", [])
+            # TC 스튜디오 출처 (한 줄 flat 키, PRD O3). 없으면 None
+            case["source_ref"] = meta.get("source_ref")
 
         cases.append(case)
 
@@ -150,6 +152,16 @@
     return normalized
 
 
+def split_data_key(data_key: str, group: str) -> tuple[str, str]:
+    """data_key → (프로덕트, 데이터셋). test_data[프로덕트][데이터셋]으로 읽는다 (PRD O1).
+
+    "serveone.login" → ("serveone", "login")   ← 권장 형식
+    "valid_user"     → (group, "valid_user")    ← 점이 없는 옛 형식: 그룹 폴더명을 프로덕트로 본다
+    """
+    product, dot, dataset = str(data_key).partition(".")
+    return (product, dataset) if dot else (group, product)
+
+
 def validate_data_keys(cases: list, group: str, test_data_path: str | Path = None) -> list:
     """
     케이스들의 data_key가 test_data/에 존재하는지 검증.
@@ -170,18 +182,17 @@
             return []
         with open(test_data_path, encoding="utf-8") as f:
             all_data = json.load(f)
-        group_data = all_data.get(group, {})
     else:
         from _paths import load_test_data
         all_data = load_test_data()
-        group_data = all_data.get(group, {})
 
     missing = []
     for case in cases:
         dk = case.get("data_key")
         if dk is None:
             continue
-        if dk not in group_data:
+        product, dataset = split_data_key(dk, group)
+        if not isinstance(all_data.get(product), dict) or dataset not in all_data[product]:
             missing.append(dk)
 
     if missing:
```

```diff
--- a/scripts/coverage_matrix.py
+++ b/scripts/coverage_matrix.py
@@ -42,7 +42,7 @@
 
             covered_groups.add(group)
             tags_count: dict[str, int] = {}
-            priority_count: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
+            priority_count: dict[str, int] = {"very_high": 0, "high": 0, "medium": 0, "low": 0}
 
             for c in cases:
                 for tag in c.get("tags", []):
```

```diff
--- a/scripts/sync_test_data.py
+++ b/scripts/sync_test_data.py
@@ -16,20 +16,21 @@
 _SCRIPTS_DIR = str(Path(__file__).parent)
 if _SCRIPTS_DIR not in sys.path:
     sys.path.insert(0, _SCRIPTS_DIR)
-from parse_cases import load_cases
+from parse_cases import load_cases, split_data_key
 from _paths import TEST_DATA_DIR, load_test_data
 
 
 def main():
-    dry_run = "--dry-run" in sys.argv
-
     project_root = Path(__file__).resolve().parent.parent
-    testcases_dir = project_root / "testcases"
-
     if not TEST_DATA_DIR.exists():
         print(f"[오류] test_data/ 폴더가 없습니다: {TEST_DATA_DIR}")
         sys.exit(1)
+    sync(project_root / "testcases", dry_run="--dry-run" in sys.argv)
 
+
+def sync(testcases_dir: Path, *, dry_run: bool = False) -> int:
+    """케이스의 data_key가 가리키는 test_data/{프로덕트}.json[데이터셋]이 없으면 빈 칸을 만든다. 추가한 개수를 돌려준다."""
+
     # 현재 전체 test_data 로드 (product → data_key dict)
     test_data = load_test_data()
 
@@ -46,55 +47,36 @@
             dk = case.get("data_key")
             if dk is None:
                 continue
+            # test_data[프로덕트][데이터셋] (parse_cases.split_data_key, PRD O1)
+            product, dataset = split_data_key(dk, group)
+            product_file = TEST_DATA_DIR / f"{product}.json"
+            product_example = TEST_DATA_DIR / f"{product}.example.json"
+            product_data = test_data.get(product, {})
+            if dataset in product_data:
+                continue
+            product_data[dataset] = {}
+            added_count += 1
+            print(f"  [추가] test_data/{product}.json → [{dataset}]  (케이스 그룹: {group})")
+            if not dry_run:
+                current = (json.loads(product_file.read_text(encoding="utf-8")) if product_file.exists()
+                           else {"_comment": f"{product} 테스트 데이터. 이 파일은 gitignored입니다."})
+                current[dataset] = {}
+                product_file.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
+                if not product_example.exists():
+                    example = {"_comment": f"{product} 테스트 데이터 템플릿. cp {product}.example.json {product}.json 후 값 입력.",
+                               dataset: {}}
+                    product_example.write_text(json.dumps(example, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
+            test_data[product] = product_data
 
-            # dk에 해당하는 product 파일이 없으면 생성
-            product_file = TEST_DATA_DIR / f"{dk}.json"
-            product_example = TEST_DATA_DIR / f"{dk}.example.json"
-
-            # 현재 product 데이터 로드
-            product_data = test_data.get(dk, {})
-
-            # group 키가 없으면 추가
-            if group not in product_data:
-                product_data[group] = {"username": "", "password": ""}
-                added_count += 1
-                print(f"  [추가] test_data/{dk}.json → [{group}]")
-
-                if not dry_run:
-                    # 실제 파일에 저장
-                    if product_file.exists():
-                        with open(product_file, encoding="utf-8") as f:
-                            current = json.load(f)
-                    else:
-                        current = {
-                            "_comment": f"{dk} 테스트 데이터. 이 파일은 gitignored입니다."
-                        }
-                    current[group] = product_data[group]
-                    with open(product_file, "w", encoding="utf-8") as f:
-                        json.dump(current, f, ensure_ascii=False, indent=2)
-                        f.write("\n")
-
-                    # example 파일도 없으면 같이 생성
-                    if not product_example.exists():
-                        example = {
-                            "_comment": f"{dk} 테스트 데이터 템플릿. cp {dk}.example.json {dk}.json 후 값 입력."
-                        }
-                        example[group] = {"username": "", "password": ""}
-                        with open(product_example, "w", encoding="utf-8") as f:
-                            json.dump(example, f, ensure_ascii=False, indent=2)
-                            f.write("\n")
-
-                # 캐시 갱신
-                test_data[dk] = product_data
-
     if added_count == 0:
         print("[동기화] 누락된 data_key 없음. test_data/ 폴더가 최신입니다.")
-        return
+        return 0
 
     if dry_run:
         print(f"\n[dry-run] {added_count}개 키 추가 예정 (실제 저장하지 않음)")
     else:
         print(f"\n[완료] {added_count}개 키 추가됨 → {TEST_DATA_DIR}")
+    return added_count
 
 
 if __name__ == "__main__":
```

```diff
--- a/templates/tc-template.md
+++ b/templates/tc-template.md
@@ -1,7 +1,7 @@
 ---
 id: "{그룹코드}_{번호}"
-data_key: {test_data.json 키} | null
-priority: high | medium | low
+data_key: {프로덕트}.{데이터셋} | null
+priority: very_high | high | medium | low
 tags: [{유형}, {분류}]
 type: structured | natural
 ---
@@ -11,8 +11,8 @@
 0. {테스트 시작 전 시스템 상태}
 
 ## Steps
-1. {필드명} 필드에 test_data[{data_key}].{속성} 입력
-2. {필드명} 필드에 test_data[{data_key}].{속성} 입력
+1. {필드명} 필드에 test_data[{프로덕트}][{데이터셋}].{속성} 입력
+2. {필드명} 필드에 test_data[{프로덕트}][{데이터셋}].{속성} 입력
 3. {버튼명} 버튼 클릭
 
 ## Expected
@@ -25,10 +25,10 @@
 - id: "{그룹코드}_{번호}" 형식으로 따옴표 포함 작성 (예: "CL_01", "PL_02") — 따옴표 없으면 파서가 정상 매핑 못할 수 있음
 - 1파일 = 1케이스
 - frontmatter 필수: id, data_key, priority, tags, type
-- data_key: test_data.json의 키와 1:1 매핑 (입력값 불필요 시 null)
-- Steps의 입력값은 test_data[data_key] 참조 (하드코딩 금지)
+- data_key: "{프로덕트}.{데이터셋}" 형식. test_data/{프로덕트}.json 안의 {데이터셋} 키를 가리킴 (예: serveone.login). 점이 없으면 그룹 폴더명을 프로덕트로 봄. 입력값 불필요 시 null
+- Steps의 입력값은 test_data[프로덕트][데이터셋] 참조 (하드코딩 금지)
 - Steps: 번호(1. 2. 3.) 형식 권장; 번호 없는 평문 줄도 파서 지원
 - UI 텍스트는 영어 원문 그대로 (번역 금지)
 - 유형 태그: positive, negative, smoke, auth, validation, security, edge_case, session, navigation, content
-- 우선순위: high(핵심기능) medium(보조기능) low(엣지케이스)
+- 우선순위: very_high(차단급 핵심 흐름) high(핵심기능) medium(보조기능) low(엣지케이스)
 -->
```

- [ ] **Step 5: 통과 확인 + Import Studio 회귀 (가장 중요)**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_pipeline_compat.py -q`
Expected: `6 passed`

Run: `.venv/bin/python -m pytest tests/unit/import_studio tests/unit/dashboard tests/unit/core -q`
Expected: 모두 통과 (Import Studio 동작이 그대로여야 한다)

- [ ] **Step 6: 기존 파이프라인 한 번 돌려 보기** — `.venv/bin/python scripts/coverage_matrix.py` 가 오류 없이 `state/coverage.json`을 쓰는지, `.venv/bin/python scripts/sync_test_data.py --dry-run`이 "누락된 data_key 없음"을 출력하는지 확인한다 (지금 TC는 모두 `data_key: null`).

- [ ] **Step 7: 커밋**

```bash
git add scripts/_import_commit.py scripts/parse_cases.py scripts/coverage_matrix.py scripts/sync_test_data.py templates/tc-template.md tests/unit/tc_library/test_pipeline_compat.py
git commit -m "feat(tc-studio): M1 very_high·source_ref·data_key 계약 정리와 행 기반 Import 미리보기"
```

---

## Task M2: md 내보내기 모듈

**Files:**
- Create: `scripts/_tc_md_export.py`
- Test: `tests/unit/tc_library/test_tc_md_export.py`

**Interfaces:**
- Consumes: M1 `create_preview_from_rows commit_run rollback_run load_run _target_for _atomic_json`, `load_existing_testcases`, Phase 1 저장소, Phase 2 `_tc_review.classify`
- Produces:
  - 저장 `state/tc_library/{suite}/md_export.json` = `{groups[{path, group, code}], ids{case_id: tc_id}, exported{tc_id: sha256}, before_commit{run_id: exported}}`
  - `PRIORITY_MAP`, `load_config(suite)`, `save_group(suite, path, group, code)` (오류: `INVALID_MD_GROUP` `GROUP_NOT_IN_PAGES` `INVALID_MD_CODE`), `group_for(case, groups)`(가장 긴 접두 일치)
  - `eligibility(suite) -> {funnel[5], branches[{path, group, code, count}], groups, pages, excluded[{case_id, feature, reason}], drifted[{tc_id, file}]}`
  - `build_rows(suite)`, `preview(suite) -> run`(`tc_library_suite` 표시, 드리프트는 `FILE_DRIFT` 충돌), `commit(suite, run_id, skip_tc_ids)`, `rollback(suite, run_id)`, `drifted_files(suite)`

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/unit/tc_library/test_tc_md_export.py`

```python
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
    # BEN_0001·0002·0003을 웹 자동화 대상으로, BEN_0004는 추정 문구가 있게 만든다
    for case_id in ("BEN_0001", "BEN_0002", "BEN_0003", "BEN_0004"):
        case = lib.get_case(SUITE, case_id)
        lib.patch_case(SUITE, case_id, case["rev"], {"auto": "Y-web", "priority": case["priority"] or "P1"}, "t")
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
    assert [f["count"] for f in before["funnel"]] == [6, 4, 4, 3, 0]
    assert {e["case_id"]: e["reason"] for e in before["excluded"]}["BEN_0004"] == '추정 문구 "추정 문구"'
    md.save_group(SUITE, ["혜택", "혜택 탭"], "yafit_benefit", "YFB")
    after = md.eligibility(SUITE)
    assert after["funnel"][-1]["count"] == 3
    assert {tuple(b["path"]): b["group"] for b in after["branches"]} == {
        ("혜택", "혜택 탭"): "yafit_benefit", ("혜택", "혜택 탭", "상단 배너"): "yafit_benefit"}


def test_preview_commit_parses_and_ids_are_stable(project):
    md.save_group(SUITE, ["혜택", "혜택 탭"], "yafit_benefit", "YFB")
    run = md.preview(SUITE)
    assert run["summary"]["added"] == 3 and [r["tc_id"] for r in run["rows"]] == ["YFB_01", "YFB_02", "YFB_03"]
    result = md.commit(SUITE, run["run_id"], [])
    assert result["created"] == 3

    cases = parse_cases.load_cases(project / "testcases" / "yafit_benefit")
    assert [c["id"] for c in cases] == ["YFB_01", "YFB_02", "YFB_03"]
    first = cases[0]
    assert (first["priority"], first["source_ref"], first["data_key"]) == ("very_high", "tc-library:야핏무브/BEN_0001", None)
    assert first["steps"] == ["1. 앱 실행", "2. 혜택 탭 선택"] and first["title"] == "혜택 탭 버튼"

    again = md.preview(SUITE)
    assert again["summary"]["same"] == 3 and md.load_config(SUITE)["ids"]["BEN_0002"] == "YFB_02"


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
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_md_export.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named '_tc_md_export'`

- [ ] **Step 3: 구현** — `scripts/_tc_md_export.py`

```python
"""TC 라이브러리 → 파이프라인용 testcases/{group}/tc_*.md (PRD F7, 로드맵 M4~M6).

미리보기·커밋·롤백은 Import Studio(_import_commit)를 그대로 쓴다. 이 모듈은 다음만 한다:
- 대상 판정 퍼널: 전체 → AUTO=Y-web → 승인 → 추정 문구·검증 오류 없음 → 그룹 매핑됨
- 라이브러리 가지(시트 › 대분류 › 중분류 › 소분류) → pages.json 그룹 + tc_id 접두어 매핑 (가장 긴 접두 일치)
- case_id → md tc_id 고정 배정 (다시 내보내도 같은 파일을 갱신)
- 드리프트: 마지막으로 내보낸 뒤 testcases/ 파일을 사람이 직접 고쳤으면 충돌(FILE_DRIFT)로 올린다

state/tc_library/{suite}/md_export.json
  {"groups": [{"path": [시트, 대, 중, 소], "group": "yafit_invite", "code": "YFI"}],
   "ids": {case_id: tc_id}, "exported": {tc_id: 파일 sha256}}
"""
from __future__ import annotations

import hashlib
import json
import re

import _paths
from _import_commit import _atomic_json, _target_for, commit_run, create_preview_from_rows, load_run, rollback_run
from _import_validator import load_existing_testcases
from _state import read_state, update_state
from _tc_library import LibraryError, load_cases, suite_dir, with_issues
from _tc_model import format_steps, join_expected
from _tc_review import classify

PRIORITY_MAP = {"P0": "very_high", "P1": "high", "P2": "medium", "P3": "low"}
_GROUP = re.compile(r"[A-Za-z0-9_-]+")
_CODE = re.compile(r"[A-Z][A-Z0-9]{1,7}")


def _config_path(suite: str):
    return suite_dir(suite) / "md_export.json"


def load_config(suite: str) -> dict:
    cfg = read_state(_config_path(suite))
    return {"groups": cfg.get("groups", []), "ids": cfg.get("ids", {}), "exported": cfg.get("exported", {})}


def _pages() -> dict:
    try:
        data = json.loads(_paths.PAGES_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {k: v for k, v in data.items() if not k.startswith("_")}


def save_group(suite: str, path: list[str], group: str, code: str) -> dict:
    """가지 → 그룹 매핑 추가·교체. 그룹은 pages.json에 있어야 한다 (URL이 없으면 파이프라인이 못 돈다)."""
    path = [p for p in path if p]
    if len(path) < 2:
        raise LibraryError("시트와 대분류까지 고르세요", "INVALID_MD_GROUP")
    if not _GROUP.fullmatch(group or "") or group not in _pages():
        raise LibraryError(f"config/pages.json에 없는 그룹입니다: {group}. 페이지 URL 관리에서 먼저 추가하세요",
                           "GROUP_NOT_IN_PAGES")
    if not _CODE.fullmatch(code or ""):
        raise LibraryError("tc_id 접두어는 영문 대문자로 시작하는 2~8자입니다", "INVALID_MD_CODE")

    def mutate(cfg: dict) -> dict:
        groups = [g for g in cfg.get("groups", []) if g["path"] != path]
        if any(g["code"] == code and g["group"] != group for g in groups):
            raise LibraryError(f"접두어 {code}는 다른 그룹이 쓰고 있습니다", "INVALID_MD_CODE")
        return {**cfg, "groups": groups + [{"path": path, "group": group, "code": code}]}

    update_state(_config_path(suite), mutate)
    return load_config(suite)


def _keys(case: dict) -> list[str]:
    return [case["sheet"], *[p for p in case["path"] if p]]


def group_for(case: dict, groups: list[dict]) -> dict | None:
    keys = _keys(case)
    hits = [g for g in groups if keys[: len(g["path"])] == g["path"]]
    return max(hits, key=lambda g: len(g["path"])) if hits else None


def eligibility(suite: str) -> dict:
    """퍼널·가지별 매핑 상태·제외 이유·드리프트 파일 (원격 호출 없음)."""
    cfg = load_config(suite)
    cases = [with_issues(c) for c in load_cases(suite)]
    web = [c for c in cases if c["auto"] == "Y-web"]
    approved = [c for c in web if c["status"] == "approved"]
    clean = [c for c in approved if not c["has_error"] and all(b["verified"] for b in c["bullets"])]
    mapped = [c for c in clean if group_for(c, cfg["groups"])]
    excluded = []
    for c in web:
        if c["status"] != "approved":
            excluded.append({"case_id": c["case_id"], "feature": c["feature"], "reason": "미승인"})
        elif c["has_error"]:
            excluded.append({"case_id": c["case_id"], "feature": c["feature"], "reason": "검증 오류"})
        elif not all(b["verified"] for b in c["bullets"]):
            est = next(b["text"] for b in c["bullets"] if not b["verified"])
            excluded.append({"case_id": c["case_id"], "feature": c["feature"], "reason": f'추정 문구 "{est}"'})
        elif not group_for(c, cfg["groups"]):
            excluded.append({"case_id": c["case_id"], "feature": c["feature"], "reason": "그룹 매핑 없음"})
    branches: dict[tuple, dict] = {}
    for c in clean:
        key = tuple(_keys(c)[:3])
        g = group_for(c, cfg["groups"])
        item = branches.setdefault(key, {"path": list(key), "group": g["group"] if g else "",
                                         "code": g["code"] if g else "", "count": 0})
        item["count"] += 1
    return {
        "funnel": [{"label": "라이브러리 전체", "count": len(cases)}, {"label": "AUTO = Y-web", "count": len(web)},
                   {"label": "승인됨", "count": len(approved)}, {"label": "추정 문구·검증 오류 없음", "count": len(clean)},
                   {"label": "pages.json 그룹 매핑됨", "count": len(mapped)}],
        "branches": sorted(branches.values(), key=lambda b: b["path"]),
        "groups": cfg["groups"], "pages": sorted(_pages()), "excluded": excluded,
        "drifted": drifted_files(suite),
    }


def _file_sha(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def drifted_files(suite: str) -> list[dict]:
    cfg = load_config(suite)
    existing = load_existing_testcases(_paths.TESTCASES_DIR)
    out = []
    for tc_id, sha in cfg["exported"].items():
        entry = existing.get(tc_id)
        if entry and _file_sha(entry["path"]) != sha:
            out.append({"tc_id": tc_id, "file": f"{entry['group']}/{entry['path'].name}"})
    return out


def _allocate_ids(suite: str, cases: list[dict], groups: list[dict]) -> dict[str, str]:
    """case_id → tc_id ("{code}_{NN}"). 한번 배정한 번호는 유지하고, 새 번호는 기존 파일과도 겹치지 않게 한다."""
    existing = set(load_existing_testcases(_paths.TESTCASES_DIR))

    def mutate(cfg: dict) -> dict:
        ids = dict(cfg.get("ids", {}))
        used = set(ids.values()) | existing
        for case in cases:
            if case["case_id"] in ids:
                continue
            code = group_for(case, groups)["code"]
            n = 1 + max([int(m.group(1)) for i in used if (m := re.fullmatch(rf"{code}_(\d+)", i))] + [0])
            ids[case["case_id"]] = f"{code}_{n:02d}"
            used.add(ids[case["case_id"]])
        return {**cfg, "ids": ids}

    return update_state(_config_path(suite), mutate)["ids"]


def build_rows(suite: str) -> list[dict]:
    """대상 케이스 → Import Studio 행 (파일 쓰기 전)."""
    cfg = load_config(suite)
    cases = [c for c in (with_issues(c) for c in load_cases(suite))
             if c["auto"] == "Y-web" and c["status"] == "approved" and not c["has_error"]
             and all(b["verified"] for b in c["bullets"]) and group_for(c, cfg["groups"])]
    ids = _allocate_ids(suite, cases, cfg["groups"])
    rows = []
    for n, case in enumerate(cases, 1):
        tags = [{"positive": "positive", "negative": "negative", "validation": "validation"}[classify(case)]]
        if case["bullets"]:
            tags.append("content")
        rows.append({
            "tc_id": ids[case["case_id"]], "title": case["feature"], "precondition": case["precondition"],
            "steps": format_steps(case["steps"]), "expected": join_expected(case["expected"], case["bullets"]),
            "priority": PRIORITY_MAP.get(case["priority"], "medium"), "tags": tags,
            "group": group_for(case, cfg["groups"])["group"], "source_ref": f"tc-library:{suite}/{case['case_id']}",
            "case_id": case["case_id"], "_source_sheet": "tc_library", "_row": n,
        })
    return rows


def preview(suite: str) -> dict:
    rows = build_rows(suite)
    if not rows:
        raise LibraryError("내보낼 케이스가 없습니다. 대상 조건을 확인하세요", "NOTHING_TO_EXPORT")
    run = create_preview_from_rows(rows, {"kind": "tc_library", "suite": suite},
                                   _paths.TESTCASES_DIR, _paths.IMPORT_SESSIONS_DIR)
    drift = {d["tc_id"] for d in drifted_files(suite)}
    for row in run["rows"]:
        if row["tc_id"] in drift and row.get("status") in ("updated", "same"):
            row.update(status="conflict", reason="마지막 내보내기 이후 파일을 직접 고쳤습니다",
                       reason_code="FILE_DRIFT", excluded=False, decision="pending")
    run["summary"] = {s: sum(r.get("status") == s for r in run["rows"]) for s in run["summary"]}
    run["tc_library_suite"] = suite
    _atomic_json(_paths.IMPORT_SESSIONS_DIR / f"{run['run_id']}.json", run)
    return run


def commit(suite: str, run_id: str, skip_tc_ids: list[str]) -> dict:
    """충돌 중 skip_tc_ids는 건너뛰고 나머지 충돌은 라이브러리 값으로 덮어쓴다."""
    run = load_run(_paths.IMPORT_SESSIONS_DIR, run_id)
    if run.get("tc_library_suite") != suite:
        raise LibraryError("이 스위트의 md 미리보기가 아닙니다", "INVALID_RUN")
    conflicts = {r["tc_id"]: r for r in run["rows"] if r.get("status") == "conflict"}
    decisions = [{"action": "exclude", "file_id": suite, "sheet_name": "tc_library",
                  "source_row": conflicts[t]["_row"], "tc_id": t} for t in skip_tc_ids if t in conflicts]
    before = load_config(suite)["exported"]
    result = commit_run(run_id, _paths.IMPORT_DIR, _paths.TESTCASES_DIR, _paths.IMPORT_SESSIONS_DIR,
                        _paths.IMPORT_SNAPSHOTS_DIR, _paths.PROJECT_ROOT, "", decisions, policy="overwrite")
    written = [r for r in load_run(_paths.IMPORT_SESSIONS_DIR, run_id)["rows"] if not r.get("excluded")
               and (r.get("status") in ("added", "updated") or r.get("decision") == "overwrite")]

    def mutate(cfg: dict) -> dict:
        exported = dict(cfg.get("exported", {}))
        for row in written:
            target = _target_for(row, _paths.TESTCASES_DIR)
            if target.exists():
                exported[row["tc_id"]] = _file_sha(target)
        # 롤백하면 이 커밋 전의 "마지막 내보내기" 상태로 되돌린다
        return {**cfg, "exported": exported, "before_commit": {**cfg.get("before_commit", {}), run_id: before}}

    update_state(_config_path(suite), mutate)
    return result


def rollback(suite: str, run_id: str) -> dict:
    run = load_run(_paths.IMPORT_SESSIONS_DIR, run_id)
    if run.get("tc_library_suite") != suite:
        raise LibraryError("이 스위트의 md 미리보기가 아닙니다", "INVALID_RUN")
    result = rollback_run(run_id, _paths.IMPORT_SESSIONS_DIR, _paths.IMPORT_SNAPSHOTS_DIR,
                          _paths.PROJECT_ROOT, _paths.TESTCASES_DIR)

    def mutate(cfg: dict) -> dict:
        saved = dict(cfg.get("before_commit", {}))
        exported = saved.pop(run_id, cfg.get("exported", {}))
        return {**cfg, "exported": exported, "before_commit": saved}

    update_state(_config_path(suite), mutate)
    return result
```

- [ ] **Step 4: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_md_export.py -q`
Expected: `5 passed`

- [ ] **Step 5: 커밋**

```bash
git add scripts/_tc_md_export.py tests/unit/tc_library/test_tc_md_export.py
git commit -m "feat(tc-studio): M2 md 내보내기 (퍼널·그룹 매핑·tc_id 고정·드리프트)"
```

---

## Task M3: md 내보내기 API

**Files:**
- Create: `agents/dashboard/routes_tc_md.py`
- Modify: `agents/dashboard/routes_tc_library.py` (아래 diff), `agents/dashboard/serve.py`, `tests/unit/import_studio/import_studio_test_support.py`
- Test: `tests/unit/tc_library/test_tc_md_api.py`

**Interfaces:**

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/tc-library/{suite}/export/md/eligibility` | 퍼널·가지 매핑·제외·드리프트 |
| PUT | `/api/tc-library/{suite}/md-groups` | `{path, group, code}` |
| POST | `/api/tc-library/{suite}/export/md` | 미리보기 → `{run_id, summary, rows[{tc_id, case_id, status, reason, reason_code, file, excluded, before, after}]}` |
| POST | `/api/tc-library/{suite}/md-exports/{run_id}/commit` | `{skip: [tc_id]}` → Import Studio 커밋 결과 |
| POST | `/api/tc-library/{suite}/md-exports/{run_id}/rollback` | 롤백 |

`ImportRunError`는 409 `{code}`로 바뀐다 (예: 롤백한 run을 다시 커밋 → 409 `INVALID_RUN_STATE`).

- [ ] **Step 1: 테스트 격리 경로** — `import_studio_test_support.py`의 `configure_isolated_project` 딕셔너리에 (Phase 1에서 넣은 `TC_LIBRARY_DIR` 줄 아래):

```python
        "PAGES_JSON": project_root / "config" / "pages.json",
```

- [ ] **Step 2: 실패하는 테스트 작성** — `tests/unit/tc_library/test_tc_md_api.py`

```python
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

import pytest

from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json
from tests.unit.tc_library.tc_fixtures import build_template_workbook
from tests.unit.tc_library.test_tc_library_api import _post_bytes

S = quote("야핏무브")


@pytest.fixture
def api(tmp_path: Path):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    (project / "config").mkdir()
    (project / "config" / "pages.json").write_text(json.dumps({"yafit_benefit": "https://m.yafit.example/b"}), encoding="utf-8")
    with dashboard_server(project) as base_url:          # PAGES_JSON도 project/config/pages.json으로 격리된다
        _, preview = _post_bytes(base_url, "/api/tc-library/import/preview?filename=a.xlsx",
                                 build_template_workbook(tmp_path / "src.xlsx").read_bytes())
        request_json(base_url, "POST", "/api/tc-library/import", {
            "preview_id": preview["preview_id"], "suite": "야핏무브", "sheets": ["혜택"], "prefixes": {"혜택": "BEN"}})
        for case_id in ("BEN_0001", "BEN_0002"):
            request_json(base_url, "PATCH", f"/api/tc-library/{S}/cases/{case_id}", {"rev": 1, "auto": "Y-web", "priority": "P0"})
        yield base_url, project


def test_md_export_flow(api):
    base_url, project = api
    body = request_json(base_url, "GET", f"/api/tc-library/{S}/export/md/eligibility")[1]
    assert [f["count"] for f in body["funnel"]] == [5, 2, 2, 2, 0] and body["pages"] == ["yafit_benefit"]
    status, body = request_json(base_url, "PUT", f"/api/tc-library/{S}/md-groups",
                                {"path": ["혜택", "혜택 탭"], "group": "yafit_benefit", "code": "YFB"})
    assert status == 200 and body["groups"][0]["code"] == "YFB"

    status, run = request_json(base_url, "POST", f"/api/tc-library/{S}/export/md")
    assert status == 200 and run["summary"]["added"] == 2
    assert run["rows"][0]["file"].startswith("yafit_benefit/tc_YFB_01_")
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/md-exports/{run['run_id']}/commit", {"skip": []})
    assert (status, body["created"]) == (200, 2)
    assert len(list((project / "testcases" / "yafit_benefit").glob("tc_YFB_*.md"))) == 2
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/md-exports/{run['run_id']}/rollback")
    assert status == 200 and not list((project / "testcases" / "yafit_benefit").glob("tc_YFB_*.md"))
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/md-exports/{run['run_id']}/commit", {"skip": []})
    assert (status, body["code"]) == (409, "INVALID_RUN_STATE")
    assert request_json(base_url, "PUT", f"/api/tc-library/{S}/md-groups",
                        {"path": ["혜택", "혜택 탭"], "group": "nope", "code": "YFB"})[1]["code"] == "GROUP_NOT_IN_PAGES"
```

- [ ] **Step 3: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_md_api.py -q`
Expected: FAIL — `/export/md/eligibility`가 404

- [ ] **Step 4: 라우트 Mixin** — `agents/dashboard/routes_tc_md.py`

```python
"""routes_tc_md.py — TC 스튜디오 md 내보내기 API (PRD F7, 로드맵 M6).

미리보기·커밋·롤백 본체는 Import Studio(_import_commit)다. ImportRunError는 409 JSON으로 바꾼다.
"""
from __future__ import annotations

import re

from dash_http import _read_body

_SUITE = r"(?P<suite>[^/]+)"
_RUN = r"(?P<run_id>run_[A-Za-z0-9_-]+)"

MD_ROUTES: list[tuple[str, re.Pattern, str]] = [
    (m, re.compile(p + r"\Z"), h) for m, p, h in [
        ("GET", rf"/api/tc-library/{_SUITE}/export/md/eligibility", "_tcm_eligibility"),
        ("PUT", rf"/api/tc-library/{_SUITE}/md-groups", "_tcm_save_group"),
        ("POST", rf"/api/tc-library/{_SUITE}/export/md", "_tcm_preview"),
        ("POST", rf"/api/tc-library/{_SUITE}/md-exports/{_RUN}/commit", "_tcm_commit"),
        ("POST", rf"/api/tc-library/{_SUITE}/md-exports/{_RUN}/rollback", "_tcm_rollback"),
    ]
]


def _translate(fn):
    """ImportRunError → LibraryError(409) (디스패처가 JSON으로 바꾼다)."""
    from _import_commit import ImportRunError
    from _tc_library import LibraryError
    try:
        return fn()
    except ImportRunError as exc:
        raise LibraryError(str(exc), exc.code, 409) from exc


def _row_view(row: dict) -> dict:
    import _paths
    from _import_commit import _target_for
    target = _target_for(row, _paths.TESTCASES_DIR)
    return {"tc_id": row["tc_id"], "case_id": row.get("case_id", ""), "status": row.get("status"),
            "reason": row.get("reason", ""), "reason_code": row.get("reason_code", ""),
            "file": f"{target.parent.name}/{target.name}", "excluded": row.get("excluded", False),
            "before": row.get("before"), "after": row.get("after")}


class TcMdRoutesMixin:
    def _tcm_eligibility(self, suite: str):
        from _tc_md_export import eligibility
        self._tcl_json({"ok": True, **eligibility(suite)})

    def _tcm_save_group(self, suite: str):
        from _tc_md_export import save_group
        body = _read_body(self)
        cfg = save_group(suite, list(body.get("path") or []), str(body.get("group", "")), str(body.get("code", "")))
        self._tcl_json({"ok": True, "groups": cfg["groups"]})

    def _tcm_preview(self, suite: str):
        from _tc_md_export import preview
        run = _translate(lambda: preview(suite))
        self._tcl_json({"ok": True, "run_id": run["run_id"], "summary": run["summary"],
                        "rows": [_row_view(r) for r in run["rows"]]})

    def _tcm_commit(self, suite: str, run_id: str):
        from _tc_md_export import commit
        skip = [str(t) for t in _read_body(self).get("skip", [])]
        self._tcl_json({"ok": True, **_translate(lambda: commit(suite, run_id, skip))})

    def _tcm_rollback(self, suite: str, run_id: str):
        from _tc_md_export import rollback
        self._tcl_json({"ok": True, **_translate(lambda: rollback(suite, run_id))})
```

- [ ] **Step 5: 라우트 표 결합**

```diff
--- a/agents/dashboard/routes_tc_library.py
+++ b/agents/dashboard/routes_tc_library.py
@@ -47,8 +47,9 @@
 # 생성·검토 라우트(Phase 2)가 앞에 와야 `/api/tc-library/{suite}` 패턴에 먼저 잡히지 않는다
 from routes_tc_authoring import AUTHORING_ROUTES  # noqa: E402
 from routes_tc_connectors import CONNECTOR_ROUTES  # noqa: E402  (Phase 3)
+from routes_tc_md import MD_ROUTES  # noqa: E402  (Phase 4)
 
-ROUTES[:0] = CONNECTOR_ROUTES + AUTHORING_ROUTES
+ROUTES[:0] = MD_ROUTES + CONNECTOR_ROUTES + AUTHORING_ROUTES
 
 
 class TcLibraryRoutesMixin:
```

- [ ] **Step 6: serve.py** — `from routes_tc_connectors import …` 줄 아래에 `from routes_tc_md import TcMdRoutesMixin                          # TC 스튜디오 md 내보내기`, 클래스 상속의 `TcConnectorRoutesMixin,` 아래에 `TcMdRoutesMixin,`

- [ ] **Step 7: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library -q -k "not e2e"`
Expected: 모두 통과

- [ ] **Step 8: 커밋**

```bash
git add agents/dashboard/routes_tc_md.py agents/dashboard/routes_tc_library.py agents/dashboard/serve.py tests/unit/import_studio/import_studio_test_support.py tests/unit/tc_library/test_tc_md_api.py
git commit -m "feat(tc-studio): M3 md 내보내기 API"
```

---

## Task W12: 내보내기 화면 md 카드

**Files:**
- Modify: `agents/dashboard/static/js/tc-studio/api.js`, `export.js` (아래 diff)
- Test: `tests/unit/tc_library/test_tc_md_e2e.py`

**Interfaces:**
- `data-id` (명세 5.2장): `md-card` `md-eligibility` `md-group-map` `md-map-group` `md-map-code` `md-map-fix` `md-drift-warning` `md-excluded-list` `md-preview` `md-preview-panel` `md-conflict-decision` `md-commit` `md-rollback`

목업과 다른 점: 매핑 추가는 페이지 관리 화면으로 보내지 않고 카드 안에서 pages.json 그룹을 고르고 접두어를 적는다(그룹 자체를 새로 만드는 것은 기존 "페이지 URL 관리" 화면). 미리보기 표는 전체 행을 보여 주고, 충돌 행만 "선택 필요"다.

- [ ] **Step 1: 실패하는 E2E 테스트 작성** — `tests/unit/tc_library/test_tc_md_e2e.py`

```python
"""TC 스튜디오 md 내보내기 화면 (Phase 4 W12)."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import Page, expect

from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json
from tests.unit.tc_library.test_tc_studio_e2e import _seed

S = quote("야핏무브")


@pytest.fixture
def studio(tmp_path: Path, page: Page):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    (project / "config").mkdir()
    (project / "config" / "pages.json").write_text(json.dumps({"yafit_benefit": "https://m.yafit.example/b"}), encoding="utf-8")
    with dashboard_server(project) as base_url:
        _seed(base_url, tmp_path)
        for case_id in ("BEN_0001", "BEN_0002"):
            request_json(base_url, "PATCH", f"/api/tc-library/{S}/cases/{case_id}", {"rev": 1, "auto": "Y-web", "priority": "P0"})
        page.goto(base_url + "/tc-studio")
        page.locator('[data-id="nav-tab-export"]').click()
        yield base_url, page, project


# ── W12: md 카드 ────────────────────────────────────────────────
def test_map_preview_commit_and_rollback(studio):
    _, page, project = studio
    expect(page.locator('[data-id="md-eligibility"] .v').last).to_have_text("0")
    page.locator('[data-id="md-map-code"]').first.fill("YFB")
    page.locator('[data-id="md-map-fix"]').first.click()
    expect(page.locator('[data-id="md-eligibility"] .v').last).to_have_text("2")
    page.locator('[data-id="md-preview"]').click()
    expect(page.locator('[data-id="md-preview-panel"] tbody tr')).to_have_count(2)
    page.locator('[data-id="md-commit"]').click()
    expect(page.locator("#md-result-text")).to_have_text("반영 완료 · 신규 2 · 갱신 0")
    assert len(list((project / "testcases" / "yafit_benefit").glob("tc_YFB_*.md"))) == 2
    page.locator('[data-id="md-rollback"]').click()
    expect(page.locator('[data-id="md-preview-panel"]')).to_be_hidden()
    assert not list((project / "testcases" / "yafit_benefit").glob("tc_YFB_*.md"))


def test_drifted_file_needs_a_decision(studio):
    base_url, page, project = studio
    request_json(base_url, "PUT", f"/api/tc-library/{S}/md-groups", {"path": ["혜택", "혜택 탭"], "group": "yafit_benefit", "code": "YFB"})
    run = request_json(base_url, "POST", f"/api/tc-library/{S}/export/md")[1]
    request_json(base_url, "POST", f"/api/tc-library/{S}/md-exports/{run['run_id']}/commit", {"skip": []})
    target = next((project / "testcases" / "yafit_benefit").glob("tc_YFB_01_*.md"))
    target.write_text(target.read_text(encoding="utf-8") + "\n사람이 고친 줄\n", encoding="utf-8")

    page.reload()
    page.locator('[data-id="nav-tab-export"]').click()
    expect(page.locator('[data-id="md-drift-warning"]')).to_contain_text("직접 바뀐 파일 1개")
    page.locator('[data-id="md-preview"]').click()
    expect(page.locator('[data-id="md-commit"]')).to_be_disabled()
    page.locator('[data-id="md-conflict-decision"]').select_option("skip")
    page.locator('[data-id="md-commit"]').click()
    expect(page.locator("#md-result-text")).to_contain_text("건너뜀 1")
    assert "사람이 고친 줄" in target.read_text(encoding="utf-8")
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_md_e2e.py -q`
Expected: FAIL — `md-eligibility`를 찾지 못함

- [ ] **Step 3: 구현**

```diff
--- a/agents/dashboard/static/js/tc-studio/api.js
+++ b/agents/dashboard/static/js/tc-studio/api.js
@@ -78,5 +78,11 @@
     scanSources: (suite) => request('POST', `${S(suite)}/source-changes/scan`),
     sourceDiff: (ref) => request('GET', `/api/tc-library/source-diff?ref=${enc(ref)}`),
     ackSource: (suite, id) => request('POST', `${C(suite, id)}/ack-source`),
+    // ── Phase 4: md 내보내기 ──
+    mdEligibility: (suite) => request('GET', `${S(suite)}/export/md/eligibility`),
+    saveMdGroup: (suite, path, group, code) => request('PUT', `${S(suite)}/md-groups`, { path, group, code }),
+    mdPreview: (suite) => request('POST', `${S(suite)}/export/md`),
+    mdCommit: (suite, runId, skip) => request('POST', `${S(suite)}/md-exports/${enc(runId)}/commit`, { skip }),
+    mdRollback: (suite, runId) => request('POST', `${S(suite)}/md-exports/${enc(runId)}/rollback`),
   };
 })(window.TCS_NS = window.TCS_NS || {});
```

```diff
--- a/agents/dashboard/static/js/tc-studio/export.js
+++ b/agents/dashboard/static/js/tc-studio/export.js
@@ -34,12 +34,104 @@
           <div class="field"><span class="label">파일 이름</span><div class="fname" id="xlsx-filename" data-id="xlsx-filename">—</div></div>
           <button class="btn btn-primary" data-id="xlsx-download" id="xlsx-download" disabled style="justify-self:start">검사 후 내려받기</button>
         </div>
+        ${mdCardHtml()}
       </div>
     </div>
   </section>`;
   }
 
+  // ── md 카드 (Phase 4, 목업 797~845행) ──────────────────────
+  let mdRun = null;
+
+  function mdCardHtml() {
+    return `<div class="panel exp-card" style="padding:16px" data-id="md-card">
+      <div class="head"><div class="fmt md">.md</div><div><b style="font-size:14px">파이프라인용 md로 내보내기</b>
+        <div class="help">AUTO=Y-web · 승인 · 추정 문구 없음 · 그룹 매핑된 케이스만 testcases/에 씁니다. 반영과 롤백은 Import Studio와 같은 방식입니다.</div></div></div>
+      <div class="field"><span class="label">대상 조건</span><div class="funnel" data-id="md-eligibility" id="md-funnel"></div></div>
+      <div class="field"><span class="label">그룹 매핑 (config/pages.json)</span><div data-id="md-group-map" id="md-groups"></div></div>
+      <div class="warnbox" data-id="md-drift-warning" id="md-drift" hidden></div>
+      <details data-id="md-excluded-list" id="md-excluded"></details>
+      <div class="row"><button class="btn btn-primary" data-id="md-preview" id="md-preview">md 미리보기</button><span class="help" id="md-preview-hint"></span></div>
+      <div class="md-preview" id="md-preview-panel" data-id="md-preview-panel" hidden></div>
+    </div>`;
+  }
+
+  async function loadMd() {
+    if (!state.suite) return;
+    const el = await api.mdEligibility(state.suite);
+    const max = Math.max(el.funnel[0].count, 1);
+    $('#md-funnel', root).innerHTML = el.funnel.map((f) => `<div class="f"><span>${esc(f.label)}</span><span class="track"><i style="width:${(f.count / max) * 100}%"></i></span><span class="v">${f.count}</span></div>`).join('');
+    const pageOpts = el.pages.map((p) => `<option>${esc(p)}</option>`).join('');
+    $('#md-groups', root).innerHTML = el.branches.map((b, i) => `<div class="maprow"><span>${esc(b.path.join(' › '))} <span class="faint">→ ${b.group ? `${esc(b.group)} (${esc(b.code)})` : '(없음)'}</span></span>
+      ${b.group ? `<span class="tag ok">매핑됨 · ${b.count}건</span>` : `<span class="row"><span class="tag err">그룹 없음 · ${b.count}건 제외</span>
+        <select class="fselect" data-id="md-map-group" data-i="${i}">${pageOpts || '<option value="">pages.json이 비어 있음</option>'}</select>
+        <input class="input mono" data-id="md-map-code" data-i="${i}" placeholder="접두어" maxlength="8" style="width:80px">
+        <button class="btn-sm" data-id="md-map-fix" data-i="${i}">매핑 추가</button></span>`}</div>`).join('')
+      || '<span class="help">AUTO=Y-web이고 승인된 케이스가 없습니다</span>';
+    $$('[data-id="md-map-fix"]', root).forEach((b) => b.addEventListener('click', async () => {
+      const i = b.dataset.i;
+      try {
+        await api.saveMdGroup(state.suite, el.branches[i].path, $(`[data-id="md-map-group"][data-i="${i}"]`, root).value,
+          $(`[data-id="md-map-code"][data-i="${i}"]`, root).value.trim().toUpperCase());
+        toast('그룹 매핑을 저장했습니다.', 'ok');
+        await loadMd();
+      } catch (err) { toast(`매핑하지 못했습니다: ${esc(err.message)}`, 'err'); }
+    }));
+    const drift = $('#md-drift', root);
+    drift.hidden = !el.drifted.length;
+    drift.innerHTML = el.drifted.length ? `<b>testcases/에서 직접 바뀐 파일 ${el.drifted.length}개</b>
+      <span class="mono" style="font-size:11px">${el.drifted.map((d) => esc(d.file)).join(' · ')}</span>
+      <span>라이브러리가 원본입니다. 미리보기에서 파일마다 건너뛰기 또는 덮어쓰기를 고릅니다.</span>` : '';
+    $('#md-excluded', root).innerHTML = `<summary class="muted" style="cursor:pointer;font-size:12px">제외된 ${el.excluded.length}건 보기</summary>
+      <ul class="checks" style="margin-top:8px">${el.excluded.map((x) => `<li><span class="wr">!</span>${esc(x.case_id)} ${esc(x.feature)} · ${esc(x.reason)}</li>`).join('')}</ul>`;
+    $('#md-preview', root).disabled = !el.funnel[4].count;
+    $('#md-preview', root).textContent = `md 미리보기 (${el.funnel[4].count}건)`;
+  }
+
+  const STATUS_TAG = { added: ['ok', '신규'], updated: ['info', '갱신'], conflict: ['warn', '충돌'], same: ['', '동일'], error: ['err', '오류'] };
+
+  function renderMdPreview() {
+    const s = mdRun.summary;
+    const conflicts = mdRun.rows.filter((r) => r.status === 'conflict');
+    $('#md-preview-panel', root).hidden = false;
+    $('#md-preview-panel', root).innerHTML = `<div class="row"><b>md 변경 미리보기</b><span class="tag info mono">${esc(mdRun.run_id)}</span></div>
+      <div class="row">${Object.entries(STATUS_TAG).map(([k, [cls, l]]) => `<span class="tag ${cls}">${l} ${s[k] || 0}</span>`).join('')}</div>
+      <div style="overflow-x:auto"><table aria-label="md 내보내기 미리보기"><thead><tr><th>상태</th><th>케이스 / 대상 파일</th><th>이유</th><th>처리</th></tr></thead><tbody>
+      ${mdRun.rows.map((r) => `<tr><td><span class="tag ${STATUS_TAG[r.status][0]}">${STATUS_TAG[r.status][1]}</span></td><td class="mono">${esc(r.case_id)} · ${esc(r.file)}</td><td>${esc(r.reason)}</td>
+        <td>${r.status === 'conflict' ? `<select class="select md-conflict-decision" data-id="md-conflict-decision" data-tc="${esc(r.tc_id)}" aria-label="${esc(r.tc_id)} 충돌 처리"><option value="">선택 필요</option><option value="skip">건너뛰기</option><option value="overwrite">라이브러리 값으로 덮어쓰기</option></select>` : r.excluded ? '반영 안 함' : '자동'}</td></tr>`).join('')}
+      </tbody></table></div>
+      <div class="row"><button class="btn btn-success" id="md-commit" data-id="md-commit">md 반영</button><span class="help" id="md-commit-hint"></span></div>
+      <div id="md-result" hidden class="row"><span class="tag ok" id="md-result-text"></span><button class="btn btn-ghost" id="md-rollback" data-id="md-rollback">이 작업 롤백</button></div>`;
+    const update = () => {
+      const pending = $$('.md-conflict-decision', root).filter((x) => !x.value).length;
+      $('#md-commit', root).disabled = pending > 0;
+      $('#md-commit-hint', root).textContent = pending ? `미결정 충돌 ${pending}건` : (conflicts.length ? '선택 완료' : '');
+    };
+    $$('.md-conflict-decision', root).forEach((x) => x.addEventListener('change', update));
+    update();
+    $('#md-commit', root).addEventListener('click', async () => {
+      const skip = $$('.md-conflict-decision', root).filter((x) => x.value === 'skip').map((x) => x.dataset.tc);
+      try {
+        const res = await api.mdCommit(state.suite, mdRun.run_id, skip);
+        $('#md-commit', root).disabled = true;
+        $('#md-result', root).hidden = false;
+        $('#md-result-text', root).textContent = `반영 완료 · 신규 ${res.created} · 갱신 ${res.updated}${skip.length ? ` · 건너뜀 ${skip.length}` : ''}`;
+        toast('md 파일을 반영했습니다. 필요하면 이 작업을 롤백할 수 있습니다.', 'ok');
+        await loadMd();
+      } catch (err) { toast(`반영하지 못했습니다: ${esc(err.message)}`, 'err'); }
+    });
+    $('#md-rollback', root).addEventListener('click', async () => {
+      try {
+        await api.mdRollback(state.suite, mdRun.run_id);
+        $('#md-preview-panel', root).hidden = true;
+        toast('이 작업의 md 변경을 되돌렸습니다.', 'ok');
+        await loadMd();
+      } catch (err) { toast(`롤백하지 못했습니다: ${esc(err.message)}`, 'err'); }
+    });
+  }
+
   function onShow() {
+    loadMd();
     lastExport = null;
     const suite = state.suites.find((s) => s.suite === state.suite);
     $('#x-all-n', root).textContent = suite ? suite.count : 0;
@@ -93,6 +185,14 @@
     $$('input[name="xscope"]', root).forEach((i) => i.addEventListener('change', () => resetCheck('범위가 바뀌었습니다. 검사를 다시 실행하세요')));
     $('#xlsx-sheets', root).addEventListener('change', () => resetCheck('범위가 바뀌었습니다. 검사를 다시 실행하세요'));
     $('#xlsx-run-check', root).addEventListener('click', runCheck);
+    $('#md-preview', root).addEventListener('click', async () => {
+      try {
+        mdRun = await api.mdPreview(state.suite);
+        renderMdPreview();
+        const conflicts = mdRun.rows.filter((r) => r.status === 'conflict').length;
+        toast(conflicts ? `md 미리보기를 만들었습니다. 충돌 ${conflicts}건의 처리 방법을 고르세요.` : 'md 미리보기를 만들었습니다.', '');
+      } catch (err) { toast(`미리보기를 만들지 못했습니다: ${esc(err.message)}`, 'err'); }
+    });
     $('#xlsx-download', root).addEventListener('click', () => {
       if (!lastExport) return;
       const a = document.createElement('a');
```

- [ ] **Step 4: 통과 확인 + 전체 회귀 3회**

Run: `.venv/bin/python -m pytest tests/unit/tc_library -q`
Expected: `113 passed`

Run: `for i in 1 2 3; do .venv/bin/python -m pytest -q | tail -1; done`
Expected: 3번 모두 `790 passed, 1 skipped` (기존 677 + TC 스튜디오 113)

- [ ] **Step 5: 커밋**

```bash
git add agents/dashboard/static/js/tc-studio/api.js agents/dashboard/static/js/tc-studio/export.js tests/unit/tc_library/test_tc_md_e2e.py
git commit -m "feat(tc-studio): W12 내보내기 화면 md 카드"
```

---

## Task W13: 문서 갱신 + 실제 파이프라인 연결 확인 + Phase 4 완료

**Files:**
- Modify: `doc/TEST_CASE_GUIDE.md`, `doc/API_REFERENCE.md`, `doc/SCRIPTS_GUIDE.md`, `scripts/update_directory.py`, `doc/TC_AUTHORING_PRD.md`, `doc/TC_AUTHORING_ROADMAP.md`

- [ ] **Step 1: TC 작성 가이드** — `doc/TEST_CASE_GUIDE.md`
  - 75행 표: `` `high` \| `medium` \| `low` `` → `` `very_high` \| `high` \| `medium` \| `low` ``, 설명 끝에 "(very_high = 차단급 핵심 흐름, TC 스튜디오 P0)"
  - 74행 표: data_key 값 설명을 `` `{프로덕트}.{데이터셋}` \| `null` `` 로, 설명을 "test_data/{프로덕트}.json 안의 {데이터셋} 키. 점이 없으면 그룹 폴더명을 프로덕트로 본다"로
  - 94~96행 "data_key 규칙"과 170행·259행의 `test_data[{data_key}].{속성}` → `test_data[{프로덕트}][{데이터셋}].{속성}`
  - 257행 체크리스트: `high` / `medium` / `low` → `very_high` / `high` / `medium` / `low`
  - 258행 체크리스트: "`config/test_data.json` 키와 일치" → "`test_data/{프로덕트}.json`에 {데이터셋} 키가 있음"
  - 예시(43·207·229행)의 `data_key: valid_user`처럼 점이 없는 값은 그대로 둔다 (그룹=프로덕트인 옛 형식으로 계속 동작)
  - 표 아래에 한 줄: "추가 frontmatter 키 `source_ref`는 TC 스튜디오가 쓰는 출처다 (`tc-library:{스위트}/{case_id}`). 파서는 보존만 하고 파이프라인은 쓰지 않는다."

- [ ] **Step 2: API·스크립트 문서** — `doc/API_REFERENCE.md`에 M3 표를 "TC 스튜디오" 절 끝에 추가. `doc/SCRIPTS_GUIDE.md`의 `_tc_source_watch.py` 행 아래:

```markdown
| `scripts/_tc_md_export.py` | TC 라이브러리 → testcases/{group}/tc_*.md (퍼널·그룹 매핑·tc_id 고정·드리프트, 커밋·롤백은 Import Studio) | ❌ (대시보드가 import) |
```

`scripts/update_directory.py`의 `"_tc_source_watch.py"` 줄 아래: `"_tc_md_export.py":         "TC 라이브러리 → 파이프라인 md 내보내기",`. 같은 파일의 `parse_cases.py`·`sync_test_data.py` 설명에 data_key 계약(`{프로덕트}.{데이터셋}`)이 틀리게 적혀 있으면 함께 고친다.

- [ ] **Step 3: PRD 미결 사항 닫기** — `doc/TC_AUTHORING_PRD.md` 9장 O1·O3·O7 행 끝에 "→ 해결: Phase 4 M1 (결정 V1)"을 붙인다.

- [ ] **Step 4: 실제 파이프라인으로 확인**
  1. `config/pages.json`에 웹으로 열리는 그룹 하나를 추가한다 (예: 야핏무브 친구 초대 웹 랜딩 URL)
  2. 라이브러리에서 그 화면 케이스 1~2건을 AUTO=Y-web · 승인으로 만들고, 화면 문구가 모두 "확인"인지 본다
  3. 내보내기 → md 카드 → 매핑 추가 → 미리보기 → 반영
  4. 대시보드 "빠른 실행"이나 `python run_qa.py --url <URL> --cases testcases/<그룹>/`으로 파이프라인을 돌려 생성·실행까지 되는지 본다 (첫 실행 통과율이 PRD §11의 지표다)
  5. 생성된 md를 직접 한 줄 고친 뒤 다시 미리보기 → 드리프트 충돌이 뜨는지 확인한다

- [ ] **Step 5: 완료 표시 + 커밋** — 로드맵 상단 "상세 계획" 표의 Phase 4 행에 `✅ 완료 (YYYY-MM-DD)`

```bash
git add doc/TEST_CASE_GUIDE.md doc/API_REFERENCE.md doc/SCRIPTS_GUIDE.md scripts/update_directory.py doc/TC_AUTHORING_PRD.md doc/TC_AUTHORING_ROADMAP.md
git commit -m "docs(tc-studio): W13 Phase 4 md 내보내기·data_key 계약 문서 갱신"
```

---

## Self-Review 결과

- **PRD 대응:** F7.1(M2 퍼널·W12) · F7.2(M1 `create_preview_from_rows`, M2) · F7.3(M2 우선순위·source_ref·파일명) · F7.4(M1 `_render`, M2 테스트의 `parse_cases` 왕복) · F7.5(M2 드리프트, 결정 V3) · F7.6(M3·W12 반영·롤백) · O1(M1 `split_data_key`) · O3(M1 `source_ref`) · O7(M1 `very_high`)
- **남은 위험:** 모바일 앱 TC 중 실제로 웹에서 돌 수 있는 케이스는 적다(웹뷰·랜딩 정도). md 내보내기는 그런 케이스에만 쓰인다. 파일명 slug는 Import Studio 규칙대로 한글 제목이 들어간다(생성되는 `.py`는 파이프라인이 영문 snake_case로 따로 짓는다).
- **이름 일관성:** `create_preview_from_rows`, `_preview_row`, `_save_run`, `PRIORITIES`, `split_data_key`, `md_export.json`, `FILE_DRIFT`, `TcMdRoutesMixin`·`_tcm_*`
