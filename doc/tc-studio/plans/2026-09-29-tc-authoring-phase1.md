# TC Authoring Studio Phase 1 Implementation Plan — 라이브러리 + 엑셀 왕복

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 엑셀 Full TC(야핏무브 양식)를 웹 TC 라이브러리로 가져와 보고·고치고, 같은 양식의 새 엑셀로 다시 내보낸다.

**Architecture:** 형식 중립 케이스 모델(`_tc_model`)을 중심으로, 템플릿 분석(`_tc_template`) → 엑셀 가져오기(`_tc_xlsx_import`) → 저장소(`_tc_library`, `state/tc_library/{suite}/`) → 엑셀 내보내기(`_tc_xlsx_export`)를 `scripts/`에 둔다. 대시보드는 정규식 라우트 Mixin(`routes_tc_library.py`)으로 API를 열고, 화면은 Import Studio처럼 `static/js/tc-studio/` 네임스페이스 모듈 + 스코프 CSS로 붙인다.

**Tech Stack:** Python 3.14, openpyxl 3.1.5, 표준 `http.server` 기반 대시보드, 바닐라 JS, pytest + Playwright(E2E)

**Spec:** [PRD](../TC_AUTHORING_PRD.md) · [요소별 동작 명세](../TC_AUTHORING_ELEMENT_SPEC.md) · [목업](../../../design-previews/tc-authoring-studio.html) · [로드맵](../TC_AUTHORING_ROADMAP.md)

> **검증 상태 (2026-09-29):** 이 계획의 백엔드 코드(B1~B10)와 테스트는 저장소 밖 임시 폴더에서 실제로 실행해 **32개 테스트 통과**를 확인했다. 실제 `야핏무브_Full.xlsx`(6시트 926건)도 가져오기 → 내보내기 → 다시 가져오기 후 내용이 전부 일치했고 요약 수식 `#REF!`는 0개였다. 화면(W1~W8) 코드는 검증 전이며 E2E 테스트가 합격 기준이다.

## Global Constraints

- 외부 LLM SDK·API 키 금지 (CLAUDE.md 절대 규칙). Phase 1에는 생성 기능이 없다.
- 상태 파일 쓰기는 `_state.update_state(path, mutator)` 원자 패턴만 쓴다 (CLAUDE.md P43). `read → 수정 → write` 금지.
- 원본 xlsx는 절대 수정하지 않는다. 내보내기는 항상 `state/tc_library/{suite}/template.xlsx`의 **사본**에 쓴다 (PRD D5).
- 우선순위 허용 값은 `P0` `P1` `P2` `P3`. 템플릿 드롭다운 `"P0,P1,P2"`는 내보낼 때 `"P0,P1,P2,P3"`으로 넓힌다 (PRD F6.2).
- 실행 결과 값은 `""`(미실행) `pass` `fail` `not_test` `na`. 엑셀 값은 `Pass` `Fail` `NT` `NA` ↔ 위 값, 빈 칸 ↔ `""` (로드맵 Z1).
- 상태를 바꾸는 요청(POST·PATCH·PUT·DELETE)은 모두 `_check_csrf_origin`을 통과해야 한다.
- 요청 바디 상한: JSON 2MB, xlsx 업로드 25MB. 초과 시 413 `PAYLOAD_TOO_LARGE`.
- 케이스 API 경로는 `/api/tc-library/{suite}/cases/{case_id}` (로드맵 Z2). 명세서 8장은 W8에서 이 경로로 고친다.
- 화면 요소의 `data-id`는 목업·명세서와 같은 값을 쓴다. UI 문구는 한국어.
- 테스트 실행: `.venv/bin/python -m pytest …` (저장소 루트에서). 단위 테스트 위치: `tests/unit/tc_library/`.
- 코드 패치 중 반복 실수를 찾으면 `agents/lessons_learned.md`에 기록한다 (CLAUDE.md).
- 커밋 메시지 끝에 다음 줄을 붙인다: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

---

## File Structure

| 파일 | 책임 | 작업 |
|---|---|---|
| `scripts/_tc_model.py` | 케이스 dict 기본값, 허용 값, Step·Expected 파싱/포맷, 결과 병합, id 발급, 검증(F5.8) | B1 |
| `scripts/_tc_template.py` | 헤더·하위 헤더·컬럼·드롭다운·No. 수식 탐지 → `TemplateProfile` | B2 |
| `scripts/_tc_xlsx_import.py` | 시트 행 → 케이스 (병합·빈 칸 이어받기, 기타 칸 id·src 분리) | B3 |
| `scripts/_tc_library.py` | 스위트 저장소: 가져오기 upsert, rev 수정, 일괄, 생성·복제·삭제·복원, 이력·되돌리기, 트리·필터 | B4, B5 |
| `scripts/_tc_xlsx_export.py` | 템플릿 사본에 행·스타일·병합·드롭다운·요약 수식·History 쓰기 + 무결성 검사 | B6, B7 |
| `scripts/_paths.py` | `TC_LIBRARY_DIR` 상수 추가 | B4 |
| `agents/dashboard/dash_http.py` | 바디 상한(`BodyTooLarge`, `_read_raw_body`) | B8 |
| `agents/dashboard/routes_tc_library.py` | 정규식 라우트 표 + 핸들러 | B8~B10 |
| `agents/dashboard/serve.py` | Mixin 연결, `/tc-studio` 경로, PATCH 처리, 413 처리 | B8 |
| `tests/unit/import_studio/import_studio_test_support.py` | 격리 프로젝트에 `TC_LIBRARY_DIR` 추가 | B8 |
| `tests/unit/tc_library/` | 단위·API·E2E 테스트, 테스트용 워크북 생성기 | 전 작업 |
| `agents/dashboard/static/js/tc-studio/{api,state,library,detail,import,export,main}.js` | 화면 모듈 (`window.TCS_NS` 네임스페이스, 공개 API `window.TCS.init`) | W1~W7 |
| `agents/dashboard/static/css/tc-studio.css` | `.tc-studio` 스코프 스타일 (목업 CSS 이식) | W1 |
| `agents/dashboard/index.html`, `static/js/router.js` | 사이드바 메뉴·스크립트 로드·라우팅 | W1 |
| `doc/API_REFERENCE.md`, `doc/SCRIPTS_GUIDE.md`, `doc/tc-studio/TC_AUTHORING_ELEMENT_SPEC.md`, `scripts/update_directory.py` | 문서 갱신 | W8 |

---

## Task B1: 케이스 모델과 검증 규칙

**Files:**
- Create: `scripts/_tc_model.py`
- Create: `tests/unit/tc_library/__init__.py` (빈 파일)
- Create: `tests/unit/tc_library/conftest.py`
- Test: `tests/unit/tc_library/test_tc_model.py`

**Interfaces:**
- Produces:
  - 상수 `PRIORITIES`, `AUTO_VALUES`, `EXECUTION_RESULTS`, `STATUSES`, `EXCEL_TO_RESULT`(소문자 엑셀 값→모델), `RESULT_TO_EXCEL`, `EDITABLE_FIELDS`
  - `new_case(**fields) -> dict` — 키: `case_id sheet path[3] feature precondition steps[] expected bullets[{text,verified}] priority auto execution_result status note source_refs[] rev deleted updated_at`
  - `parse_steps(text) -> list[str]`, `format_steps(steps) -> str`
  - `split_expected(text) -> (str, list[dict])`, `join_expected(expected, bullets) -> str`
  - `merge_results(values) -> str`, `next_case_id(prefix, existing: set[str]) -> str`, `now_iso() -> str`
  - `validate_case(case) -> list[{"level": "error"|"warning", "code", "message"}]`

- [ ] **Step 1: 테스트 공용 설정 작성**

`tests/unit/tc_library/__init__.py`는 빈 파일로 만든다. `conftest.py`:

```python
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
for _p in (REPO_ROOT / "agents" / "dashboard", REPO_ROOT / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))



@pytest.fixture
def template_xlsx(tmp_path: Path) -> Path:
    from tests.unit.tc_library.tc_fixtures import build_template_workbook

    return build_template_workbook(tmp_path / "야핏무브_Full.xlsx")


@pytest.fixture
def library_dir(tmp_path: Path, monkeypatch) -> Path:
    import _paths

    target = tmp_path / "state" / "tc_library"
    monkeypatch.setattr(_paths, "TC_LIBRARY_DIR", target)
    return target


@pytest.fixture(scope="module")
def browser():
    """E2E용 Chromium (모듈마다 1개). HEADED=1이면 창을 띄운다."""
    import os

    from playwright.sync_api import expect, sync_playwright

    # 대시보드 전체 테스트와 함께 돌면 느려질 수 있어 기본 5초 대신 10초까지 기다린다
    expect.set_options(timeout=10_000)
    with sync_playwright() as playwright:
        b = playwright.chromium.launch(headless=os.environ.get("HEADED") != "1")
        yield b
        b.close()


@pytest.fixture
def page(browser):
    """새 브라우저 컨텍스트의 페이지. 테스트가 끝날 때 처리되지 않은 JS 오류가 있으면 실패시킨다."""
    context = browser.new_context(viewport={"width": 1440, "height": 900}, accept_downloads=True)
    p = context.new_page()
    errors: list[str] = []
    p.on("pageerror", lambda exc: errors.append(str(exc)))
    yield p
    context.close()
    assert not errors, errors
```

- [ ] **Step 2: 실패하는 테스트 작성** — `tests/unit/tc_library/test_tc_model.py`

```python
from __future__ import annotations

from _tc_model import (
    format_steps, join_expected, merge_results, new_case, next_case_id, parse_steps,
    split_expected, validate_case,
)


def _codes(case: dict) -> list[str]:
    return [issue["code"] for issue in validate_case(case)]


def _valid(**overrides) -> dict:
    fields = dict(case_id="BEN_0001", sheet="혜택", path=["혜택 탭", "", ""],
                  feature="혜택 탭 버튼", steps=["앱 실행"], expected="혜택 탭 화면으로 진입된다.",
                  priority="P0")
    fields.update(overrides)
    return new_case(**fields)


def test_parse_steps_strips_numbers_and_joins_continuation_lines():
    assert parse_steps("1. 앱 실행\n2) 혜택 탭 선택\n   (하단 탭)\n") == ["앱 실행", "혜택 탭 선택\n(하단 탭)"]
    assert format_steps(["앱 실행", "혜택 탭 선택"]) == "1. 앱 실행\n2. 혜택 탭 선택"


def test_split_expected_separates_ui_text_bullets():
    expected, bullets = split_expected("팝업이 노출된다.\n- 내일부터 참여할 수 있어요\n- 확인")
    assert expected == "팝업이 노출된다."
    assert bullets == [{"text": "내일부터 참여할 수 있어요", "verified": True},
                       {"text": "확인", "verified": True}]
    assert join_expected(expected, bullets) == "팝업이 노출된다.\n- 내일부터 참여할 수 있어요\n- 확인"


def test_merge_results_prefers_fail_then_na_and_keeps_blank_as_not_run():
    assert merge_results(["fail", "pass"]) == "fail"
    assert merge_results(["pass", "na"]) == "na"
    assert merge_results(["", ""]) == ""


def test_next_case_id_continues_after_highest_number():
    assert next_case_id("BEN", {"BEN_0002", "BEN_0010", "HOME_0099"}) == "BEN_0011"
    assert next_case_id("BEN", set()) == "BEN_0001"


def test_valid_case_has_no_issues():
    assert validate_case(_valid()) == []


def test_empty_priority_is_only_a_warning():
    issues = validate_case(_valid(priority=""))
    assert [(i["level"], i["code"]) for i in issues] == [("warning", "PRIORITY_EMPTY")]


def test_invalid_values_are_errors():
    assert "PRIORITY_INVALID" in _codes(_valid(priority="상"))
    assert "AUTO_INVALID" in _codes(_valid(auto="AUTO"))
    assert "RESULT_INVALID" in _codes(_valid(execution_result="done"))
    assert "STEP_EMPTY" in _codes(_valid(steps=["앱 실행", " "]))
    assert "PATH_EMPTY" in _codes(_valid(path=["", "", ""]))
    assert "MISSING_FIELD" in _codes(_valid(expected=""))


def test_vague_expected_is_rejected_even_inside_bullets():
    assert "VAGUE_EXPECTED" in _codes(_valid(expected="팝업이 정상적으로 노출된다."))
    assert "VAGUE_EXPECTED" in _codes(_valid(bullets=[{"text": "정상 동작", "verified": False}]))
```

- [ ] **Step 3: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_model.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named '_tc_model'`

- [ ] **Step 4: 구현** — `scripts/_tc_model.py`

```python
"""TC 라이브러리 케이스 모델 — 엑셀·md 어느 쪽에도 묶이지 않는 형식 (PRD §5)."""
from __future__ import annotations

import re
from datetime import datetime

PRIORITIES = ("P0", "P1", "P2", "P3")
AUTO_VALUES = ("Y-web", "Y-app", "N")
# "" = 미실행. 엑셀의 빈 결과 칸과 1:1로 대응해야 왕복 시 NT로 바뀌지 않는다 (로드맵 Z1).
EXECUTION_RESULTS = ("", "pass", "fail", "not_test", "na")
STATUSES = ("draft", "approved", "rejected", "needs_review")
EXCEL_TO_RESULT = {"pass": "pass", "fail": "fail", "nt": "not_test", "na": "na"}
RESULT_TO_EXCEL = {"pass": "Pass", "fail": "Fail", "not_test": "NT", "na": "NA"}
# 여러 플랫폼 결과를 하나로 합칠 때 앞쪽이 이긴다.
RESULT_PRECEDENCE = ("fail", "na", "pass", "not_test")
EDITABLE_FIELDS = (
    "sheet", "path", "feature", "precondition", "steps", "expected", "bullets",
    "priority", "auto", "execution_result", "status", "note",
)
_VAGUE = (re.compile(r"정상\s*동작"), re.compile(r"정상적으로\s*노출"))
_STEP_NO = re.compile(r"^\s*\d+\s*[.)]\s*")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def new_case(**fields) -> dict:
    case = {
        "case_id": "", "sheet": "", "path": ["", "", ""], "feature": "",
        "precondition": "", "steps": [], "expected": "", "bullets": [],
        "priority": "", "auto": "", "execution_result": "", "status": "draft",
        "note": "", "source_refs": [], "rev": 1, "deleted": False,
        "updated_at": now_iso(),
    }
    case.update(fields)
    case["path"] = (list(case["path"]) + ["", "", ""])[:3]
    return case


def parse_steps(text: str) -> list[str]:
    """'1. a\\n2. b' → ['a', 'b']. 번호 없는 줄은 앞 Step에 이어 붙인다."""
    steps: list[str] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if _STEP_NO.match(line) or not steps:
            steps.append(_STEP_NO.sub("", line))
        else:
            steps[-1] = f"{steps[-1]}\n{line}"
    return steps


def format_steps(steps: list[str]) -> str:
    return "\n".join(f"{i}. {s}" for i, s in enumerate(steps, 1))


def split_expected(text: str) -> tuple[str, list[dict]]:
    """Expected 셀 → (결과 문장, UI 문구 불릿). 엑셀에서 온 문구는 확인된 문구로 본다."""
    head: list[str] = []
    bullets: list[dict] = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("-"):
            bullets.append({"text": line[1:].strip(), "verified": True})
        elif bullets:
            bullets[-1]["text"] += f"\n{line}"
        else:
            head.append(line)
    return "\n".join(head), bullets


def join_expected(expected: str, bullets: list[dict]) -> str:
    lines = [expected] if expected else []
    lines += [f"- {b['text']}" for b in bullets]
    return "\n".join(lines)


def merge_results(values: list[str]) -> str:
    present = {v for v in values if v}
    for candidate in RESULT_PRECEDENCE:
        if candidate in present:
            return candidate
    return ""


def next_case_id(prefix: str, existing: set[str]) -> str:
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)$")
    top = max((int(m.group(1)) for i in existing if (m := pattern.match(i))), default=0)
    return f"{prefix}_{top + 1:04d}"


def validate_case(case: dict) -> list[dict]:
    """PRD F5.8 검증. level은 error(내보내기 차단) 또는 warning."""
    issues: list[dict] = []

    def add(level: str, code: str, message: str) -> None:
        issues.append({"level": level, "code": code, "message": message})

    for field, label in (("feature", "기능"), ("expected", "Expected")):
        if not str(case.get(field, "")).strip():
            add("error", "MISSING_FIELD", f"{label}이(가) 비어 있습니다")
    steps = case.get("steps") or []
    if not steps:
        add("error", "MISSING_FIELD", "Test Step이 비어 있습니다")
    elif any(not str(s).strip() for s in steps):
        add("error", "STEP_EMPTY", "빈 Step이 있습니다")
    if not case.get("path", [""])[0]:
        add("error", "PATH_EMPTY", "대분류가 비어 있습니다")
    priority = case.get("priority", "")
    if not priority:
        add("warning", "PRIORITY_EMPTY", "우선순위가 지정되지 않았습니다")
    elif priority not in PRIORITIES:
        add("error", "PRIORITY_INVALID", f"우선순위 {priority!r}는 허용 값이 아닙니다 (P0~P3)")
    if case.get("auto", "") not in ("",) + AUTO_VALUES:
        add("error", "AUTO_INVALID", f"AUTO {case.get('auto')!r}는 허용 값이 아닙니다")
    if case.get("execution_result", "") not in EXECUTION_RESULTS:
        add("error", "RESULT_INVALID", "실행 결과 값이 올바르지 않습니다")
    text = join_expected(case.get("expected", ""), case.get("bullets", []))
    if any(p.search(text) for p in _VAGUE):
        add("error", "VAGUE_EXPECTED", "모호한 표현이 있습니다 (정상 동작 / 정상적으로 노출)")
    return issues
```

- [ ] **Step 5: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_model.py -q`
Expected: `8 passed`

- [ ] **Step 6: 커밋**

```bash
git add scripts/_tc_model.py tests/unit/tc_library/__init__.py tests/unit/tc_library/conftest.py tests/unit/tc_library/test_tc_model.py
git commit -m "feat(tc-studio): B1 케이스 모델과 검증 규칙"
```

---

## Task B2: 템플릿 분석 + 테스트용 워크북

**Files:**
- Create: `scripts/_tc_template.py`
- Create: `tests/unit/tc_library/tc_fixtures.py`
- Test: `tests/unit/tc_library/test_tc_template.py`

**Interfaces:**
- Consumes: 없음 (B1과 독립)
- Produces:
  - `TemplateProfile` dataclass: `sheet header_row data_start_row columns{field:col} result_columns{플랫폼:col} validations{field:[값]} no_formula("...{r}...") style_row warnings[]`, `to_dict()`, `from_dict()`
  - `HEADER_ALIASES`, `REQUIRED_COLUMNS`, `detect_header_row(ws) -> int|None`, `analyze_sheet(ws) -> TemplateProfile|None`, `analyze_workbook(path) -> dict[str, TemplateProfile]`
  - 테스트용 `build_template_workbook(path) -> Path` — 야핏무브 구조(요약 표 2~9행, 헤더 11행, 하위 헤더 12행, 데이터 13행~, `D16:D17` 병합, 드롭다운 3종, History 시트)를 흉내 낸 워크북

> 실제 `야핏무브_Full.xlsx`는 사내 데이터라 저장소에 넣지 않는다. 테스트는 항상 `build_template_workbook`으로 만든 파일을 쓴다.

- [ ] **Step 1: 테스트용 워크북 생성기 작성** — `tests/unit/tc_library/tc_fixtures.py`

```python
"""야핏무브 Full TC 구조를 흉내 낸 작은 워크북 (실제 파일은 저장소에 넣지 않는다)."""
from __future__ import annotations

from pathlib import Path

import openpyxl
from openpyxl.styles import Font
from openpyxl.worksheet.datavalidation import DataValidation

HEADERS = ["No.", "대분류", "중분류", "소분류", "기능", "사전 조건", "Test Step",
           "Expected Result", "우선순위", "AUTO", "환경", None, "기타"]
NO_FORMULA = '=IF(H{r}<>"",ROW(B{r})-12, "")'

BENEFIT_ROWS = [
    # B, C, D, E, F, G, H, I, J, K, L, M
    ("혜택 탭", None, None, "혜택 탭 버튼", None, "1. 앱 실행\n2. 혜택 탭 선택",
     "혜택 탭 화면으로 진입된다.", "P0", None, None, None, None),
    (None, "상단 배너", None, "배너 스크롤", None, "1. 혜택 탭 선택",
     "상단에 광고 배너가 가로 스크롤 동작되어 노출된다.\n- 수동, 자동 스크롤",
     None, None, "Pass", "Pass", None),
    (None, None, None, "광고 배너", None, "1. 혜택 탭 선택\n2. 광고 배너 선택",
     "해당 상세 페이지로 진입된다.", None, None, "Fail", "Pass", None),
    (None, "신규회원 한정 혜택", "돈불리기", "진입 불가", "- D+0 가입일자",
     "1. 혜택 탭 선택\n2. 돈불리기 선택",
     "진입 불가 안내 팝업이 노출된다.\n- 내일부터 참여할 수 있어요",
     None, None, None, None, "돈불리기 정책 변경"),
    (None, None, None, None, "- D+13 가입일자", "1. 혜택 탭 선택\n2. 돈불리기 선택",
     "진입 불가 안내 팝업이 노출된다.\n- 마지막 날이에요", "P2", None, "NA", None, None),
]
HOME_ROWS = [
    ("걷고 받기 탭", None, None, "코호트 별 홈 화면", "- 가입일(D day) ~ D+3", "1. 앱 실행",
     "가입일(D day) ~ D+3 상태 홈 화면이 노출된다.", "P1", None, None, None, None),
]


def _summary_block(ws) -> None:
    ws["I2"], ws["J2"] = "구분", "COUNT"
    ws["J3"], ws["K3"], ws["L3"], ws["M3"] = "And", "iOS", "And", "iOS"
    ws["I4"] = "Pass"
    ws["J4"], ws["K4"] = "=COUNTIF(#REF!,I4)", "=COUNTIF(#REF!,I4)"
    ws["I9"] = "Total Case"
    ws["J9"] = "=IF($L3=0,0,COUNTA($A$13:$A$390))"
    ws["K9"] = "=IF($L3=0,0,COUNTA($A$13:$A$390))"


def _tc_sheet(wb, title: str, rows: list[tuple]) -> None:
    ws = wb.create_sheet(title)
    _summary_block(ws)
    for col, header in enumerate(HEADERS, 1):
        ws.cell(11, col).value = header
    ws["K12"], ws["L12"] = "And", "iOS"
    for i, row in enumerate(rows):
        r = 13 + i
        ws.cell(r, 1).value = NO_FORMULA.format(r=r)
        for col, value in enumerate(row, 2):
            ws.cell(r, col).value = value
    ws["H13"].font = Font(bold=True)
    for formula, ref in (('"P0,P1,P2"', "I13:I40"), ('"AUTO"', "J13:J40"),
                         ('"Pass,Fail,NT,NA"', "K13:L40")):
        dv = DataValidation(type="list", formula1=formula)
        dv.add(ref)
        ws.add_data_validation(dv)


def build_template_workbook(path: Path) -> Path:
    wb = openpyxl.Workbook()
    history = wb.active
    history.title = "History"
    history["B1"] = "Full TC 관리"
    history["B2"], history["C2"] = "날짜", "반영 내용"
    history["B3"], history["C3"] = "25.09.11", "초기 작성"
    _tc_sheet(wb, "혜택", BENEFIT_ROWS)
    wb["혜택"].merge_cells("D16:D17")
    _tc_sheet(wb, "홈", HOME_ROWS)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    wb.close()
    return path
```

- [ ] **Step 2: 실패하는 테스트 작성** — `tests/unit/tc_library/test_tc_template.py`

```python
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
```

- [ ] **Step 3: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_template.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named '_tc_template'`

- [ ] **Step 4: 구현** — `scripts/_tc_template.py`

```python
"""엑셀 TC 템플릿 분석 — 헤더 위치·컬럼·드롭다운·No. 수식 (PRD F2.1~F2.3, F2.6)."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "no": ("no.", "no"),
    "l1": ("대분류",),
    "l2": ("중분류",),
    "l3": ("소분류",),
    "feature": ("기능",),
    "precondition": ("사전 조건", "사전조건"),
    "steps": ("test step", "test steps", "테스트 절차"),
    "expected": ("expected result", "기대결과", "기대 결과"),
    "priority": ("우선순위",),
    "auto": ("auto",),
    "env": ("환경",),
    "note": ("기타", "비고"),
}
REQUIRED_COLUMNS = ("l1", "feature", "steps", "expected")


def _norm(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


@dataclass
class TemplateProfile:
    sheet: str
    header_row: int
    data_start_row: int
    columns: dict[str, int]                 # field → 1-based column
    result_columns: dict[str, int] = field(default_factory=dict)   # 플랫폼 → column
    validations: dict[str, list[str]] = field(default_factory=dict)  # field → 목록 값
    no_formula: str | None = None            # "=IF(H{r}<>\"\",ROW(B{r})-12, \"\")"
    style_row: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TemplateProfile":
        return cls(**data)


def _match_field(value) -> str | None:
    text = _norm(value)
    for key, aliases in HEADER_ALIASES.items():
        if text in aliases:
            return key
    return None


def detect_header_row(ws, max_scan: int = 40) -> int | None:
    """필수 헤더 4개(대분류·기능·Test Step·Expected Result)가 모두 있는 첫 행.

    요약 표(구분/COUNT/Pass…)는 필수 헤더가 없어서 자연히 건너뛴다 (명세 피드백 #4).
    """
    for row in ws.iter_rows(min_row=1, max_row=max_scan):
        found = {_match_field(c.value) for c in row}
        if all(key in found for key in REQUIRED_COLUMNS):
            return row[0].row
    return None


def analyze_sheet(ws) -> TemplateProfile | None:
    header_row = detect_header_row(ws)
    if header_row is None:
        return None
    columns: dict[str, int] = {}
    for cell in ws[header_row]:
        key = _match_field(cell.value)
        if key and key not in columns:
            columns[key] = cell.column

    result_columns: dict[str, int] = {}
    sub_row = header_row + 1
    if "env" in columns:
        col = columns["env"]
        while col <= ws.max_column:
            label = ws.cell(sub_row, col).value
            header_here = ws.cell(header_row, col).value
            if not label or (col != columns["env"] and header_here):
                break
            result_columns[str(label).strip()] = col
            col += 1
    data_start = sub_row + 1 if result_columns else sub_row

    validations: dict[str, list[str]] = {}
    col_to_field = {c: f for f, c in columns.items()}
    for platform_col in result_columns.values():
        col_to_field[platform_col] = "execution_result"
    for dv in ws.data_validations.dataValidation:
        if dv.type != "list" or not dv.formula1:
            continue
        first = min(r.min_col for r in dv.sqref.ranges)
        key = col_to_field.get(first)
        if key:
            validations[key] = [v.strip() for v in dv.formula1.strip('"').split(",")]

    no_formula = None
    if "no" in columns:
        value = ws.cell(data_start, columns["no"]).value
        if isinstance(value, str) and value.startswith("="):
            no_formula = re.sub(rf"(?<=[A-Z]){data_start}(?!\d)", "{r}", value)

    warnings = []
    if getattr(ws, "_images", None):
        warnings.append(f"이미지 {len(ws._images)}개는 다시 저장하면 사라질 수 있습니다")
    if getattr(ws, "_charts", None):
        warnings.append(f"차트 {len(ws._charts)}개는 다시 저장하면 사라질 수 있습니다")
    if "priority" in validations and validations["priority"] != ["P0", "P1", "P2", "P3"]:
        warnings.append("우선순위 드롭다운을 내보낼 때 P0~P3으로 넓힙니다")

    return TemplateProfile(
        sheet=ws.title, header_row=header_row, data_start_row=data_start,
        columns=columns, result_columns=result_columns, validations=validations,
        no_formula=no_formula, style_row=data_start, warnings=warnings,
    )


def analyze_workbook(path: Path) -> dict[str, TemplateProfile]:
    import openpyxl

    wb = openpyxl.load_workbook(str(path))
    try:
        profiles = {}
        for ws in wb.worksheets:
            profile = analyze_sheet(ws)
            if profile:
                profiles[ws.title] = profile
        return profiles
    finally:
        wb.close()
```

핵심 규칙: 필수 헤더 4개(대분류·기능·Test Step·Expected Result)가 **정확히 일치하는** 첫 행을 헤더로 본다. 요약 표의 `구분`·`COUNT`·`AUTO`는 필수 헤더가 아니라서 걸리지 않는다 (명세 피드백 #4).

- [ ] **Step 5: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_template.py -q`
Expected: `3 passed`

- [ ] **Step 6: 커밋**

```bash
git add scripts/_tc_template.py tests/unit/tc_library/tc_fixtures.py tests/unit/tc_library/test_tc_template.py
git commit -m "feat(tc-studio): B2 엑셀 템플릿 분석"
```

---

## Task B3: 엑셀 → 케이스 가져오기

**Files:**
- Create: `scripts/_tc_xlsx_import.py`
- Test: `tests/unit/tc_library/test_tc_xlsx_import.py`

**Interfaces:**
- Consumes: B1 `new_case parse_steps split_expected merge_results next_case_id EXCEL_TO_RESULT`, B2 `TemplateProfile`
- Produces:
  - `split_note(text) -> (note, case_id|None, source_refs)` — 기타 칸 마지막 줄 `id:BEN_0001 | src:…`를 시스템 영역으로 분리
  - `read_sheet_cases(ws, profile, *, source_name, prefix, existing_ids) -> list[dict]`
  - `import_workbook(path, profiles, sheets, prefixes) -> list[dict]` — 시트 순서대로, 접두어 없으면 `S01`, `S02`…

가져오기 규칙 (야핏무브 관례):
- 대·중·소분류 칸이 비어 있으면 위 행 값을 이어받는다. 값이 **바뀌면** 그 아래 단계와 기능을 초기화한다.
- 병합 칸은 병합 범위의 왼쪽 위 값을 쓴다.
- 기능 칸이 비어 있으면 같은 가지 안에서 위 행 기능을 이어받는다.
- Step·Expected가 모두 비고 기타 칸에 시스템 id도 없는 행은 서식만 있는 빈 행으로 보고 건너뛴다.
- And·iOS 결과가 다르면 `fail > na > pass > not_test` 순으로 합친다. 둘 다 비면 `""`(미실행).
- 기타 칸에 `id:`가 있으면 그 id를 쓴다 → 내보낸 엑셀을 다시 가져오면 같은 케이스로 갱신된다 (F6.7).

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/unit/tc_library/test_tc_xlsx_import.py`

```python
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
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_xlsx_import.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named '_tc_xlsx_import'`

- [ ] **Step 3: 구현** — `scripts/_tc_xlsx_import.py`

```python
"""엑셀 시트 → 라이브러리 케이스 (PRD F2.2, F2.4, F6.7)."""
from __future__ import annotations

import re
from pathlib import Path

from _tc_model import (
    EXCEL_TO_RESULT, merge_results, new_case, next_case_id, parse_steps, split_expected,
)
from _tc_template import TemplateProfile

_SYSTEM_LINE = re.compile(r"^id:(?P<id>[\w-]+)(?P<rest>(\s*\|\s*src:\S+)*)\s*$")


def split_note(text: str) -> tuple[str, str | None, list[str]]:
    """기타 칸 → (사람 메모, case_id, source_refs). 시스템 줄은 마지막 줄 `id:… | src:…`."""
    lines = (text or "").splitlines()
    if lines and (m := _SYSTEM_LINE.match(lines[-1].strip())):
        refs = re.findall(r"src:(\S+)", m.group("rest") or "")
        return "\n".join(lines[:-1]).strip(), m.group("id"), refs
    return (text or "").strip(), None, []


def _merged_lookup(ws) -> dict[tuple[int, int], object]:
    """병합 범위의 모든 칸 → 왼쪽 위 칸 값."""
    lookup = {}
    for rng in ws.merged_cells.ranges:
        top_left = ws.cell(rng.min_row, rng.min_col).value
        for r in range(rng.min_row, rng.max_row + 1):
            for c in range(rng.min_col, rng.max_col + 1):
                lookup[(r, c)] = top_left
    return lookup


def read_sheet_cases(
    ws, profile: TemplateProfile, *, source_name: str, prefix: str,
    existing_ids: set[str],
) -> list[dict]:
    merged = _merged_lookup(ws)
    cols = profile.columns

    def value(row: int, key: str) -> str:
        col = cols.get(key)
        if col is None:
            return ""
        raw = merged.get((row, col), ws.cell(row, col).value)
        return "" if raw is None else str(raw).strip()

    used = set(existing_ids)
    cases: list[dict] = []
    path = ["", "", ""]
    feature = ""
    for r in range(profile.data_start_row, ws.max_row + 1):
        steps_text, expected_text = value(r, "steps"), value(r, "expected")
        raw_note = value(r, "note")
        if not (steps_text or expected_text or split_note(raw_note)[1]):
            continue  # 서식만 있는 빈 행. 라이브러리에서 온 행은 기타 칸의 id로 살린다
        for depth, key in enumerate(("l1", "l2", "l3")):
            cell = value(r, key)
            if cell and cell != path[depth]:
                path[depth] = cell
                for deeper in range(depth + 1, 3):
                    path[deeper] = ""
                feature = ""
        feature = value(r, "feature") or feature
        note, case_id, refs = split_note(raw_note)
        if not case_id or case_id in used:
            case_id = next_case_id(prefix, used)
        used.add(case_id)
        expected, bullets = split_expected(expected_text)
        results = [
            EXCEL_TO_RESULT.get(str(ws.cell(r, c).value or "").strip().lower(), "")
            for c in profile.result_columns.values()
        ]
        cases.append(new_case(
            case_id=case_id, sheet=profile.sheet, path=list(path), feature=feature,
            precondition=value(r, "precondition"), steps=parse_steps(steps_text),
            expected=expected, bullets=bullets, priority=value(r, "priority"),
            auto=value(r, "auto"), execution_result=merge_results(results),
            status="approved", note=note,
            source_refs=refs or [f"xlsx:{source_name}#{profile.sheet}!R{r}"],
        ))
    return cases


def import_workbook(
    path: Path, profiles: dict[str, TemplateProfile], sheets: list[str],
    prefixes: dict[str, str],
) -> list[dict]:
    import openpyxl

    wb = openpyxl.load_workbook(str(path), data_only=False)
    try:
        cases: list[dict] = []
        used: set[str] = set()
        for index, sheet in enumerate(sheets, 1):
            prefix = prefixes.get(sheet) or f"S{index:02d}"
            sheet_cases = read_sheet_cases(
                wb[sheet], profiles[sheet], source_name=path.name, prefix=prefix,
                existing_ids=used,
            )
            used.update(c["case_id"] for c in sheet_cases)
            cases.extend(sheet_cases)
        return cases
    finally:
        wb.close()
```

- [ ] **Step 4: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_xlsx_import.py -q`
Expected: `4 passed`

- [ ] **Step 5: 실제 파일로 수동 확인 (저장소에 넣지 않음)**

```bash
.venv/bin/python - <<'EOF'
import sys; sys.path.insert(0, "scripts")
from pathlib import Path
from _tc_template import analyze_workbook
from _tc_xlsx_import import import_workbook
src = Path.home() / "Downloads" / "야핏무브_Full.xlsx"
profiles = analyze_workbook(src)
cases = import_workbook(src, profiles, list(profiles), {})
counts = {}
for c in cases:
    counts[c["sheet"]] = counts.get(c["sheet"], 0) + 1
print(counts, len(cases))
EOF
```

Expected: `{'온보딩': 226, '홈': 454, '혜택': 186, '렛츠두두': 27, '주행': 13, '마일리지': 20} 926`

- [ ] **Step 6: 커밋**

```bash
git add scripts/_tc_xlsx_import.py tests/unit/tc_library/test_tc_xlsx_import.py
git commit -m "feat(tc-studio): B3 엑셀 시트를 라이브러리 케이스로 가져오기"
```

---

## Task B4: 라이브러리 저장소 (수정·일괄·생성·삭제·이력)

**Files:**
- Modify: `scripts/_paths.py` — `IMPORT_PROFILES_PATH` 줄(122행) 아래에 추가
- Create: `scripts/_tc_library.py` (이 작업에서는 `with_issues` 앞까지)
- Test: `tests/unit/tc_library/test_tc_library.py`

**Interfaces:**
- Consumes: B1 `EDITABLE_FIELDS next_case_id now_iso validate_case new_case`, B2 `TemplateProfile`, 기존 `_state.read_state/update_state`, `_validators.is_valid_group_name`, `_paths._file_lock`
- Produces:
  - `LibraryError(message, code, status=400)`, `RevConflict(server_case)` (status 409)
  - `suite_dir(suite) -> Path` — 빈 값·`_`로 시작·경로 문자 거부
  - `list_suites() -> [{"suite","sheets","count"}]`, `load_cases(suite, *, include_deleted=False)`, `load_profiles(suite) -> dict[str, TemplateProfile]`, `get_case(suite, case_id)`
  - `save_template(suite, xlsx_path, profiles)`, `import_cases(suite, sheets, incoming, actor) -> {"created","updated","unchanged"}`
  - `patch_case(suite, case_id, base_rev, changes, actor) -> case`, `bulk_patch(suite, items[{case_id,rev}], changes, actor) -> {"updated":[id], "conflicts":[case]}`
  - `create_case(suite, fields, actor, *, after=None)`, `duplicate_case(suite, case_id, actor)`
  - `delete_cases(suite, items, actor) -> {"deleted":[id], "conflicts":[case]}`, `restore_case(suite, case_id, actor)`
  - `history(suite, case_id) -> [entry]`(최신 먼저), `revert(suite, case_id, history_id, base_rev, actor)`
  - 이력 항목: `{"history_id","case_id","field","before","after","actor","kind":"edit|create|delete|restore","at"}`

저장소 파일 (`state/tc_library/{suite}/`): `cases.json`(update_state로만 씀), `history.jsonl`(append 전용, 락), `template.xlsx`, `template_profile.json`. `state/`는 이미 gitignore 대상이다.

- [ ] **Step 1: 경로 상수 추가** — `scripts/_paths.py`의 `IMPORT_PROFILES_PATH = STATE_DIR / "import_profiles.json"` 바로 아래:

```python
# TC 스튜디오 라이브러리 (doc/tc-studio/TC_AUTHORING_PRD.md §5). 스위트마다 하위 폴더,
# "_uploads"·"_exports"처럼 "_"로 시작하는 폴더는 스위트가 아니라 작업 공간이다.
TC_LIBRARY_DIR = STATE_DIR / "tc_library"
```

- [ ] **Step 2: 실패하는 테스트 작성** — `tests/unit/tc_library/test_tc_library.py` (트리·필터 테스트는 B5에서 추가)

```python
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


def test_suite_name_cannot_escape_library_dir(library_dir):
    for bad in ("../etc", "_uploads", ""):
        with pytest.raises(lib.LibraryError):
            lib.suite_dir(bad)
```

- [ ] **Step 3: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_library.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named '_tc_library'`

- [ ] **Step 4: 구현** — `scripts/_tc_library.py`

```python
"""TC 라이브러리 저장소 — state/tc_library/{suite}/ (PRD §5, F5.2~F5.4, F5.11, F6.7).

파일 구성:
  cases.json             {"suite", "sheets": [...], "cases": [...]}  ← update_state 원자 쓰기
  history.jsonl          변경 1건 = 1줄 (append 전용)
  template.xlsx          가져온 원본의 사본 (내보내기 템플릿)
  template_profile.json  시트별 TemplateProfile
"""
from __future__ import annotations

import json
import secrets
import shutil
from pathlib import Path

import _paths
from _state import read_state, update_state
from _tc_model import EDITABLE_FIELDS, next_case_id, now_iso, validate_case
from _tc_template import TemplateProfile
from _validators import is_valid_group_name


class LibraryError(Exception):
    def __init__(self, message: str, code: str, status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


class RevConflict(LibraryError):
    def __init__(self, server_case: dict):
        super().__init__("다른 곳에서 먼저 바뀌었습니다", "REV_CONFLICT", 409)
        self.server_case = server_case


def suite_dir(suite: str) -> Path:
    if not suite or suite.startswith("_") or not is_valid_group_name(suite):
        raise LibraryError(f"스위트 이름이 올바르지 않습니다: {suite!r}", "INVALID_SUITE")
    return _paths.TC_LIBRARY_DIR / suite


def _cases_path(suite: str) -> Path:
    return suite_dir(suite) / "cases.json"


def _history_path(suite: str) -> Path:
    return suite_dir(suite) / "history.jsonl"


def list_suites() -> list[dict]:
    root = _paths.TC_LIBRARY_DIR
    if not root.exists():
        return []
    suites = []
    for d in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")):
        data = read_state(d / "cases.json")
        live = [c for c in data.get("cases", []) if not c.get("deleted")]
        suites.append({"suite": d.name, "sheets": data.get("sheets", []), "count": len(live)})
    return suites


def load_cases(suite: str, *, include_deleted: bool = False) -> list[dict]:
    cases = read_state(_cases_path(suite)).get("cases", [])
    return cases if include_deleted else [c for c in cases if not c.get("deleted")]


def load_profiles(suite: str) -> dict[str, TemplateProfile]:
    path = suite_dir(suite) / "template_profile.json"
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {name: TemplateProfile.from_dict(p) for name, p in raw.items()}


def get_case(suite: str, case_id: str) -> dict:
    for case in load_cases(suite, include_deleted=True):
        if case["case_id"] == case_id:
            return case
    raise LibraryError(f"케이스가 없습니다: {case_id}", "CASE_NOT_FOUND", 404)


def _entry(case_id: str, field: str, before, after, actor: str, kind: str = "edit") -> dict:
    return {"history_id": "h_" + secrets.token_hex(6), "case_id": case_id, "field": field,
            "before": before, "after": after, "actor": actor, "kind": kind, "at": now_iso()}


def _append_history(suite: str, entries: list[dict]) -> None:
    if not entries:
        return
    path = _history_path(suite)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _paths._file_lock(path.with_suffix(".lock"), path):
        with path.open("a", encoding="utf-8") as fh:
            for entry in entries:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _apply(case: dict, changes: dict, actor: str) -> list[dict]:
    entries = []
    for field, value in changes.items():
        if field not in EDITABLE_FIELDS:
            raise LibraryError(f"수정할 수 없는 필드입니다: {field}", "FIELD_NOT_EDITABLE")
        if case.get(field) != value:
            entries.append(_entry(case["case_id"], field, case.get(field), value, actor))
            case[field] = value
    if entries:
        case["rev"] += 1
        case["updated_at"] = now_iso()
    return entries


def _find(data: dict, case_id: str, *, deleted: bool = False) -> dict:
    for case in data.get("cases", []):
        if case["case_id"] == case_id and bool(case.get("deleted")) == deleted:
            return case
    raise LibraryError(f"케이스가 없습니다: {case_id}", "CASE_NOT_FOUND", 404)


def save_template(suite: str, xlsx_path: Path, profiles: dict[str, TemplateProfile]) -> None:
    target = suite_dir(suite)
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(xlsx_path, target / "template.xlsx")
    (target / "template_profile.json").write_text(
        json.dumps({k: v.to_dict() for k, v in profiles.items()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def import_cases(suite: str, sheets: list[str], incoming: list[dict], actor: str) -> dict:
    """case_id가 같으면 갱신, 없으면 추가 (F6.7). 같은 내용이면 건드리지 않는다."""
    summary = {"created": 0, "updated": 0, "unchanged": 0}
    history: list[dict] = []

    def mutate(data: dict) -> dict:
        data.setdefault("suite", suite)
        data["sheets"] = list(dict.fromkeys(data.get("sheets", []) + sheets))
        cases = data.setdefault("cases", [])
        by_id = {c["case_id"]: c for c in cases}
        for new in incoming:
            old = by_id.get(new["case_id"])
            if old is None:
                cases.append(new)
                by_id[new["case_id"]] = new
                history.append(_entry(new["case_id"], "*", None, "import", actor, "create"))
                summary["created"] += 1
                continue
            changes = {f: new[f] for f in EDITABLE_FIELDS if f != "status" and old.get(f) != new[f]}
            if old.get("deleted"):
                old["deleted"] = False
                changes.setdefault("status", old["status"])
            if changes:
                history.extend(_apply(old, changes, actor))
                summary["updated"] += 1
            else:
                summary["unchanged"] += 1
        return data

    update_state(_cases_path(suite), mutate)
    _append_history(suite, history)
    return summary


def patch_case(suite: str, case_id: str, base_rev: int, changes: dict, actor: str) -> dict:
    out: dict = {}

    def mutate(data: dict) -> dict:
        case = _find(data, case_id)
        if case["rev"] != base_rev:
            raise RevConflict(dict(case))
        out["entries"] = _apply(case, changes, actor)
        out["case"] = dict(case)
        return data

    update_state(_cases_path(suite), mutate)
    _append_history(suite, out["entries"])
    return out["case"]


def bulk_patch(suite: str, items: list[dict], changes: dict, actor: str) -> dict:
    """rev가 맞는 케이스만 바꾸고 나머지는 conflicts로 돌려준다 (피드백 #15)."""
    result: dict = {"updated": [], "conflicts": []}
    history: list[dict] = []

    def mutate(data: dict) -> dict:
        for item in items:
            case = _find(data, item["case_id"])
            if case["rev"] != item["rev"]:
                result["conflicts"].append(dict(case))
                continue
            history.extend(_apply(case, changes, actor))
            result["updated"].append(case["case_id"])
        return data

    update_state(_cases_path(suite), mutate)
    _append_history(suite, history)
    return result


def _prefix_for(cases: list[dict], sheet: str) -> str:
    for case in cases:
        if case["sheet"] == sheet and "_" in case["case_id"]:
            return case["case_id"].rsplit("_", 1)[0]
    return "TC"


def create_case(suite: str, fields: dict, actor: str, *, after: str | None = None) -> dict:
    from _tc_model import new_case

    out: dict = {}

    def mutate(data: dict) -> dict:
        cases = data.setdefault("cases", [])
        sheet = fields.get("sheet") or (data.get("sheets") or [""])[0]
        case_id = next_case_id(_prefix_for(cases, sheet), {c["case_id"] for c in cases})
        base = {k: v for k, v in fields.items() if k in EDITABLE_FIELDS or k == "source_refs"}
        base.update(case_id=case_id, sheet=sheet, status="draft")
        case = new_case(**base)
        index = next((i + 1 for i, c in enumerate(cases) if c["case_id"] == after), len(cases))
        cases.insert(index, case)
        out["case"] = dict(case)
        return data

    update_state(_cases_path(suite), mutate)
    _append_history(suite, [_entry(out["case"]["case_id"], "*", None, "create", actor, "create")])
    return out["case"]


def duplicate_case(suite: str, case_id: str, actor: str) -> dict:
    source = get_case(suite, case_id)
    fields = {f: source[f] for f in EDITABLE_FIELDS}
    fields["source_refs"] = list(source.get("source_refs", []))
    created = create_case(suite, fields, actor, after=case_id)
    return created


def delete_cases(suite: str, items: list[dict], actor: str) -> dict:
    result: dict = {"deleted": [], "conflicts": []}
    history: list[dict] = []

    def mutate(data: dict) -> dict:
        for item in items:
            case = _find(data, item["case_id"])
            if case["rev"] != item["rev"]:
                result["conflicts"].append(dict(case))
                continue
            case["deleted"] = True
            case["rev"] += 1
            case["updated_at"] = now_iso()
            history.append(_entry(case["case_id"], "deleted", False, True, actor, "delete"))
            result["deleted"].append(case["case_id"])
        return data

    update_state(_cases_path(suite), mutate)
    _append_history(suite, history)
    return result


def restore_case(suite: str, case_id: str, actor: str) -> dict:
    out: dict = {}

    def mutate(data: dict) -> dict:
        case = _find(data, case_id, deleted=True)
        case["deleted"] = False
        case["rev"] += 1
        case["updated_at"] = now_iso()
        out["case"] = dict(case)
        return data

    update_state(_cases_path(suite), mutate)
    _append_history(suite, [_entry(case_id, "deleted", True, False, actor, "restore")])
    return out["case"]


def history(suite: str, case_id: str) -> list[dict]:
    path = _history_path(suite)
    if not path.exists():
        return []
    entries = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return [e for e in reversed(entries) if e["case_id"] == case_id]


def revert(suite: str, case_id: str, history_id: str, base_rev: int, actor: str) -> dict:
    entry = next((e for e in history(suite, case_id) if e["history_id"] == history_id), None)
    if entry is None or entry["kind"] != "edit":
        raise LibraryError("되돌릴 수 없는 이력입니다", "HISTORY_NOT_REVERTIBLE")
    return patch_case(suite, case_id, base_rev, {entry["field"]: entry["before"]}, actor)
```

주의: `update_state`의 mutator 안에서 예외(`RevConflict` 등)가 나면 파일을 쓰지 않는다. 그래서 rev 확인은 반드시 mutator 안에서 한다 (읽고 나서 확인하면 경쟁 조건이 생긴다).

- [ ] **Step 5: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_library.py -q`
Expected: `6 passed`

- [ ] **Step 6: 커밋**

```bash
git add scripts/_paths.py scripts/_tc_library.py tests/unit/tc_library/test_tc_library.py
git commit -m "feat(tc-studio): B4 라이브러리 저장소와 변경 이력"
```

---

## Task B5: 트리 집계와 목록 필터

**Files:**
- Modify: `scripts/_tc_library.py` (파일 끝에 추가)
- Modify: `tests/unit/tc_library/test_tc_library.py` (`test_suite_name_cannot_escape_library_dir` 앞에 추가)

**Interfaces:**
- Consumes: B4 저장소, B1 `validate_case`
- Produces:
  - `with_issues(case) -> case + {"issues": [...], "has_error": bool}`
  - `filter_cases(cases, query: dict[str,str]) -> list[case+issues]` — 키: `sheet path("시트/대/중/소/기능" 접두 일치) status execution_result(빈 값 = 미실행, "*" = 전체) priority("-" = 미지정) auto("-" = 미지정) source(접두어: xlsx·conf·figma·file) invalid("1") q(기능·사전 조건·Step·Expected·UI 문구 부분 일치)`
  - `build_tree(cases) -> [node]` — node: `{"name","level":"sheet|l1|l2|l3|feature","path":[…],"count","draft","needs_review","invalid","children":[…]}`

- [ ] **Step 1: 실패하는 테스트 추가** — `test_suite_name_cannot_escape_library_dir` 바로 앞에:

```python
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
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_library.py -q`
Expected: FAIL — `AttributeError: module '_tc_library' has no attribute 'build_tree'`

- [ ] **Step 3: 구현** — `scripts/_tc_library.py` 끝에 추가:

```python
def with_issues(case: dict) -> dict:
    issues = validate_case(case)
    return {**case, "issues": issues, "has_error": any(i["level"] == "error" for i in issues)}


def filter_cases(cases: list[dict], query: dict) -> list[dict]:
    """GET /api/tc-library/{suite} 필터 (F5.4). query 값은 문자열."""
    q = (query.get("q") or "").strip()
    path = [p for p in (query.get("path") or "").split("/") if p]
    out = []
    for case in map(with_issues, cases):
        if query.get("sheet") and case["sheet"] != query["sheet"]:
            continue
        keys = [case["sheet"], *[p for p in case["path"] if p], case["feature"]]
        if path and keys[: len(path)] != path:
            continue
        if query.get("status") and case["status"] != query["status"]:
            continue
        if "execution_result" in query and query["execution_result"] != "*" \
                and case["execution_result"] != query["execution_result"]:
            continue
        if query.get("priority") and (case["priority"] or "-") != query["priority"]:
            continue
        if query.get("auto") and (case["auto"] or "-") != query["auto"]:
            continue
        if query.get("source") and not any(r.startswith(query["source"] + ":")
                                           for r in case["source_refs"]):
            continue
        if query.get("invalid") == "1" and not case["has_error"]:
            continue
        if q:
            haystack = json.dumps([case["feature"], case["precondition"], case["steps"],
                                   case["expected"], case["bullets"]], ensure_ascii=False)
            if q not in haystack:
                continue
        out.append(case)
    return out


def build_tree(cases: list[dict]) -> list[dict]:
    """시트 › 대분류 › 중분류 › 소분류 › 기능 트리 + 가지별 집계 (F2.2, F5.1)."""
    roots: list[dict] = []
    index: dict[tuple, dict] = {}
    for case in map(with_issues, cases):
        keys = [case["sheet"], *[p for p in case["path"] if p], case["feature"]]
        children = roots
        for depth, name in enumerate(keys):
            key = tuple(keys[: depth + 1])
            node = index.get(key)
            if node is None:
                level = "sheet" if depth == 0 else "feature" if depth == len(keys) - 1 else f"l{depth}"
                node = {"name": name, "level": level, "path": list(key), "count": 0,
                        "draft": 0, "needs_review": 0, "invalid": 0, "children": []}
                index[key] = node
                children.append(node)
            node["count"] += 1
            node["draft"] += case["status"] == "draft"
            node["needs_review"] += case["status"] == "needs_review"
            node["invalid"] += case["has_error"]
            children = node["children"]
    return roots
```

- [ ] **Step 4: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_library.py -q`
Expected: `7 passed`

- [ ] **Step 5: 커밋**

```bash
git add scripts/_tc_library.py tests/unit/tc_library/test_tc_library.py
git commit -m "feat(tc-studio): B5 계층 트리 집계와 목록 필터"
```

---

## Task B6: 케이스 → 템플릿 사본 쓰기

**Files:**
- Create: `scripts/_tc_xlsx_export.py` (이 작업에서는 `verify_export` 앞까지)
- Test: `tests/unit/tc_library/test_tc_xlsx_export.py`

**Interfaces:**
- Consumes: B1 `PRIORITIES RESULT_TO_EXCEL format_steps join_expected`, B2 `TemplateProfile`
- Produces:
  - `note_cell(case) -> str` — `"{메모}\nid:{case_id} | src:{비 xlsx 출처}…"`
  - `write_sheet(ws, profile, cases) -> int` (마지막 데이터 행)
  - `append_history(wb, note, today)` — History 시트 B열 마지막 행 아래에 `YY.MM.DD`·반영 내용 (명세 피드백 #17)
  - `export_workbook(template_path, profiles, cases_by_sheet, out_path, *, history_note="", today=None, drop_sheets=())`

쓰기 순서 (시트마다):
1. 데이터 영역(`data_start_row` 이후)과 겹치는 병합을 모두 푼다.
2. 스타일 기준 행(`style_row`)의 칸 스타일을 복사해 둔 뒤 데이터 행을 모두 지운다.
3. 케이스를 순서대로 쓴다: 스타일 복사 → 값 → `No.` 수식 → 결과 칸(모든 플랫폼에 같은 값, 미실행은 빈 칸).
4. 대분류·중분류·소분류·기능이 연속으로 같으면 세로 병합한다.
5. 목록형 드롭다운 범위를 `data_start_row`~마지막 행으로 맞추고, 우선순위 목록은 `P0,P1,P2,P3`으로 바꾼다.
6. 요약 표 수식(헤더 위쪽)의 `$A$13:$A$390` 같은 고정 범위를 실제 범위로, `COUNTIF(#REF!,…)`를 해당 플랫폼 결과 열 범위로 다시 쓴다 (F6.3).

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/unit/tc_library/test_tc_xlsx_export.py` (왕복 테스트는 B7에서 추가)

```python
from __future__ import annotations

from datetime import date

import openpyxl

from _tc_model import new_case
from _tc_template import analyze_workbook
from _tc_xlsx_export import export_workbook, verify_export
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
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_xlsx_export.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named '_tc_xlsx_export'`

- [ ] **Step 3: 구현** — `scripts/_tc_xlsx_export.py`

```python
"""라이브러리 케이스 → 템플릿 사본 xlsx (PRD F6.2~F6.6)."""
from __future__ import annotations

import re
from copy import copy
from datetime import date
from pathlib import Path

from openpyxl.utils import get_column_letter
from openpyxl.worksheet.cell_range import MultiCellRange

from _tc_model import PRIORITIES, RESULT_TO_EXCEL, format_steps, join_expected
from _tc_template import TemplateProfile

_HIER = ("l1", "l2", "l3", "feature")


def note_cell(case: dict) -> str:
    system = " | ".join(
        [f"id:{case['case_id']}"]
        + [f"src:{r}" for r in case.get("source_refs", []) if not r.startswith("xlsx:")]
    )
    return f"{case['note']}\n{system}" if case.get("note") else system


def _hier_key(case: dict, depth: int) -> tuple:
    keys = list(case["path"]) + [case["feature"]]
    return tuple(keys[: depth + 1])


def write_sheet(ws, profile: TemplateProfile, cases: list[dict]) -> int:
    """데이터 영역을 cases로 다시 쓰고 마지막 데이터 행 번호를 돌려준다."""
    start, cols = profile.data_start_row, profile.columns
    max_col = ws.max_column
    styles = [copy(ws.cell(profile.style_row, c)._style) for c in range(1, max_col + 1)]
    for rng in list(ws.merged_cells.ranges):
        if rng.max_row >= start:
            ws.unmerge_cells(str(rng))
    if ws.max_row >= start:
        ws.delete_rows(start, ws.max_row - start + 1)

    for i, case in enumerate(cases):
        r = start + i
        for c in range(1, max_col + 1):
            ws.cell(r, c)._style = copy(styles[c - 1])
        values = {
            "l1": case["path"][0], "l2": case["path"][1], "l3": case["path"][2],
            "feature": case["feature"], "precondition": case["precondition"],
            "steps": format_steps(case["steps"]),
            "expected": join_expected(case["expected"], case["bullets"]),
            "priority": case["priority"], "auto": case["auto"], "note": note_cell(case),
        }
        for key, val in values.items():
            if key in cols:
                ws.cell(r, cols[key]).value = val or None
        if profile.no_formula and "no" in cols:
            ws.cell(r, cols["no"]).value = profile.no_formula.format(r=r)
        excel_result = RESULT_TO_EXCEL.get(case["execution_result"])
        for col in profile.result_columns.values():
            ws.cell(r, col).value = excel_result

    last = start + max(len(cases), 1) - 1
    _merge_hierarchy(ws, profile, cases)
    _extend_validations(ws, profile, last)
    _rewrite_summary(ws, profile, last)
    return last


def _merge_hierarchy(ws, profile: TemplateProfile, cases: list[dict]) -> None:
    start = profile.data_start_row
    for depth, key in enumerate(_HIER):
        col = profile.columns.get(key)
        if col is None:
            continue
        run_start = 0
        for i in range(1, len(cases) + 1):
            same = (
                i < len(cases)
                and _hier_key(cases[i], depth) == _hier_key(cases[run_start], depth)
            )
            if same:
                continue
            value = (list(cases[run_start]["path"]) + [cases[run_start]["feature"]])[depth]
            if i - run_start > 1 and value:
                ws.merge_cells(
                    start_row=start + run_start, start_column=col,
                    end_row=start + i - 1, end_column=col,
                )
            run_start = i


def _extend_validations(ws, profile: TemplateProfile, last: int) -> None:
    start = profile.data_start_row
    priority_col = profile.columns.get("priority")
    for dv in ws.data_validations.dataValidation:
        if dv.type != "list":
            continue
        lo = min(r.min_col for r in dv.sqref.ranges)
        hi = max(r.max_col for r in dv.sqref.ranges)
        dv.sqref = MultiCellRange(
            f"{get_column_letter(lo)}{start}:{get_column_letter(hi)}{last}"
        )
        if lo == priority_col:
            dv.formula1 = '"' + ",".join(PRIORITIES) + '"'


def _rewrite_summary(ws, profile: TemplateProfile, last: int) -> None:
    """요약 표 수식의 고정 범위·#REF!를 실제 데이터 범위로 다시 쓴다 (F6.3)."""
    start = profile.data_start_row
    platform_of_col: dict[int, str] = {}
    for row in ws.iter_rows(min_row=1, max_row=profile.header_row - 1):
        for cell in row:
            if isinstance(cell.value, str) and cell.value.strip() in profile.result_columns:
                platform_of_col.setdefault(cell.column, cell.value.strip())
    for row in ws.iter_rows(min_row=1, max_row=profile.header_row - 1):
        for cell in row:
            v = cell.value
            if not (isinstance(v, str) and v.startswith("=")):
                continue
            v = re.sub(r"\$A\$\d+:\$A\$\d+", f"$A${start}:$A${last}", v)
            if "#REF!" in v and cell.column in platform_of_col:
                col = get_column_letter(profile.result_columns[platform_of_col[cell.column]])
                v = v.replace("#REF!", f"${col}${start}:${col}${last}")
            cell.value = v


def append_history(wb, note: str, today: date) -> None:
    if "History" not in wb.sheetnames or not note.strip():
        return
    ws = wb["History"]
    last = max((c.row for c in ws["B"] if c.value not in (None, "")), default=2)
    for col in (2, 3):
        ws.cell(last + 1, col)._style = copy(ws.cell(last, col)._style)
    ws.cell(last + 1, 2).value = today.strftime("%y.%m.%d")
    ws.cell(last + 1, 3).value = note.strip()


def export_workbook(
    template_path: Path, profiles: dict[str, TemplateProfile],
    cases_by_sheet: dict[str, list[dict]], out_path: Path, *,
    history_note: str = "", today: date | None = None, drop_sheets: tuple[str, ...] = (),
) -> None:
    import openpyxl

    wb = openpyxl.load_workbook(str(template_path))
    try:
        for name in drop_sheets:
            if name in wb.sheetnames:
                del wb[name]
        for sheet, profile in profiles.items():
            if sheet in wb.sheetnames and sheet not in drop_sheets:
                write_sheet(wb[sheet], profile, cases_by_sheet.get(sheet, []))
        append_history(wb, history_note, today or date.today())
        out_path.parent.mkdir(parents=True, exist_ok=True)
        wb.save(str(out_path))
    finally:
        wb.close()
```

- [ ] **Step 4: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_xlsx_export.py -q`
Expected: `1 passed`

- [ ] **Step 5: 커밋**

```bash
git add scripts/_tc_xlsx_export.py tests/unit/tc_library/test_tc_xlsx_export.py
git commit -m "feat(tc-studio): B6 템플릿 사본에 케이스 쓰기"
```

---

## Task B7: 내보내기 무결성 검사 + 왕복 보장

**Files:**
- Modify: `scripts/_tc_xlsx_export.py` (파일 끝에 추가)
- Modify: `tests/unit/tc_library/test_tc_xlsx_export.py` (파일 끝에 추가)

**Interfaces:**
- Consumes: B6 `export_workbook`, B3 `read_sheet_cases`
- Produces: `verify_export(out_path, profiles, cases_by_sheet) -> [{"level":"ok"|"error","code":"ROUNDTRIP"|"SUMMARY_REF","message"}]`

- [ ] **Step 1: 실패하는 테스트 추가** — 파일 끝에:

```python
def test_export_then_reimport_is_lossless(template_xlsx, tmp_path):
    profiles, by_sheet = _load(template_xlsx)
    by_sheet["혜택"].append(new_case(case_id="BEN_0006", sheet="혜택",
                                     path=["혜택 탭", "상단 배너", ""], feature="새 기능"))
    out = tmp_path / "out.xlsx"
    export_workbook(template_xlsx, profiles, by_sheet, out)

    checks = verify_export(out, profiles, by_sheet)
    assert {c["level"] for c in checks} == {"ok"}, checks
    again = import_workbook(out, analyze_workbook(out), ["혜택", "홈"], {"혜택": "ZZZ", "홈": "ZZZ"})
    assert [c["case_id"] for c in again] == [c["case_id"] for s in by_sheet.values() for c in s]


def test_verify_export_reports_mismatch(template_xlsx, tmp_path):
    profiles, by_sheet = _load(template_xlsx)
    out = tmp_path / "out.xlsx"
    export_workbook(template_xlsx, profiles, by_sheet, out)
    by_sheet["홈"][0]["feature"] = "다른 이름"

    checks = verify_export(out, profiles, by_sheet)
    assert ("error", "ROUNDTRIP") in {(c["level"], c["code"]) for c in checks}
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_xlsx_export.py -q`
Expected: FAIL — `ImportError: cannot import name 'verify_export'`

- [ ] **Step 3: 구현** — 파일 끝에 추가:

```python
def verify_export(
    out_path: Path, profiles: dict[str, TemplateProfile],
    cases_by_sheet: dict[str, list[dict]],
) -> list[dict]:
    """저장한 파일을 다시 열어 라이브러리와 같은지 검사한다 (F6.6)."""
    import openpyxl
    from _tc_xlsx_import import read_sheet_cases

    checks: list[dict] = []
    wb = openpyxl.load_workbook(str(out_path))
    try:
        for sheet, expected in cases_by_sheet.items():
            if sheet not in wb.sheetnames:
                continue
            ws, profile = wb[sheet], profiles[sheet]
            got = read_sheet_cases(ws, profile, source_name=out_path.name, prefix="X",
                                   existing_ids=set())
            key = lambda c: (c["case_id"], tuple(c["path"]), c["feature"], tuple(c["steps"]),
                             c["expected"], c["priority"], c["execution_result"], c["note"])
            same = [key(c) for c in got] == [key(c) for c in expected]
            checks.append({
                "level": "ok" if same else "error", "code": "ROUNDTRIP",
                "message": f"{sheet}: {len(got)}건 {'라이브러리와 일치' if same else '라이브러리와 다름'}",
            })
            refs = [
                c.coordinate for row in ws.iter_rows(max_row=profile.header_row)
                for c in row if isinstance(c.value, str) and "#REF!" in c.value
            ]
            checks.append({
                "level": "error" if refs else "ok", "code": "SUMMARY_REF",
                "message": f"{sheet}: 요약 수식 #REF! {len(refs)}개",
            })
    finally:
        wb.close()
    return checks
```

- [ ] **Step 4: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_xlsx_export.py -q`
Expected: `3 passed`

- [ ] **Step 5: 실제 파일 왕복 수동 확인 (저장소에 넣지 않음)**

```bash
.venv/bin/python - <<'EOF'
import sys, tempfile; sys.path.insert(0, "scripts")
from pathlib import Path
from _tc_template import analyze_workbook
from _tc_xlsx_import import import_workbook
from _tc_xlsx_export import export_workbook, verify_export
src = Path.home() / "Downloads" / "야핏무브_Full.xlsx"
profiles = analyze_workbook(src)
by_sheet = {}
for c in import_workbook(src, profiles, list(profiles), {}):
    by_sheet.setdefault(c["sheet"], []).append(c)
out = Path(tempfile.mkdtemp()) / "roundtrip.xlsx"
export_workbook(src, profiles, by_sheet, out, history_note="왕복 확인")
for check in verify_export(out, profiles, by_sheet):
    print(check["level"], check["message"])
EOF
```

Expected: 12줄 모두 `ok` (시트 6개 × 왕복·`#REF!` 검사)

- [ ] **Step 6: 커밋**

```bash
git add scripts/_tc_xlsx_export.py tests/unit/tc_library/test_tc_xlsx_export.py
git commit -m "feat(tc-studio): B7 내보내기 무결성 검사와 왕복 보장"
```

---

## Task B8: API 골격 — 바디 상한, 라우트 Mixin, 조회·가져오기

**Files:**
- Modify: `agents/dashboard/dash_http.py` — `_read_body` 교체 (16~19행)
- Modify: `agents/dashboard/serve.py` — import, 클래스 상속, `do_GET` `do_POST` `do_DELETE`, `do_PATCH` 추가
- Modify: `tests/unit/import_studio/import_studio_test_support.py` — `configure_isolated_project`
- Create: `agents/dashboard/routes_tc_library.py`
- Test: `tests/unit/tc_library/test_tc_library_api.py`

**Interfaces:**
- Consumes: B2~B5
- Produces:
  - `dash_http.BodyTooLarge`, `dash_http._read_raw_body(handler, limit) -> bytes`, `dash_http._read_body(handler, limit=MAX_JSON_BODY_BYTES) -> dict`
  - `TcLibraryRoutesMixin._tcl_dispatch(method) -> bool` (True면 처리 완료)
  - API: `GET /api/tc-library` → `{ok, suites}` · `GET /api/tc-library/{suite}/tree` → `{ok, tree}` · `GET /api/tc-library/{suite}?…` → `{ok, total, items}` (items는 `issues`·`has_error` 포함, `offset`·`limit` 최대 1000) · `GET /api/tc-library/{suite}/cases/{id}` → `{ok, case}` · `POST /api/tc-library/import/preview?filename=` (본문 = xlsx 바이트) → `{ok, preview_id, filename, sheets:[{name, header_row, data_start_row, cases, result_columns, warnings}]}` · `POST /api/tc-library/import` `{preview_id, suite, sheets, prefixes}` → `{ok, suite, created, updated, unchanged}`
  - 오류 응답: `{ok:false, error, code}` (+ 409는 `server_case`)

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/unit/tc_library/test_tc_library_api.py` (쓰기·내보내기 테스트는 B9·B10에서 추가)

```python
from __future__ import annotations

import http.client
import json
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote, urlparse

import pytest

from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json
from tests.unit.tc_library.tc_fixtures import build_template_workbook

S = quote("야핏무브")


def _post_bytes(base_url: str, path: str, data: bytes) -> tuple[int, dict]:
    req = urllib.request.Request(base_url + path, data=data, method="POST",
                                 headers={"Content-Type": "application/octet-stream"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as err:
        return err.code, json.loads(err.read())


@pytest.fixture
def api(tmp_path: Path):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    with dashboard_server(project) as base_url:
        xlsx = build_template_workbook(tmp_path / "src.xlsx").read_bytes()
        status, preview = _post_bytes(
            base_url, "/api/tc-library/import/preview?filename=" + quote("야핏무브_Full.xlsx"), xlsx)
        assert status == 200, preview
        status, body = request_json(base_url, "POST", "/api/tc-library/import", {
            "preview_id": preview["preview_id"], "suite": "야핏무브",
            "sheets": ["혜택", "홈"], "prefixes": {"혜택": "BEN", "홈": "HOME"}})
        assert (status, body["created"]) == (200, 6), body
        yield base_url, preview


def test_import_preview_describes_sheets(api):
    _, preview = api
    assert [(s["name"], s["header_row"], s["cases"]) for s in preview["sheets"]] == \
        [("혜택", 11, 5), ("홈", 11, 1)]


def test_import_preview_rejects_non_xlsx_and_oversized_body(api):
    base_url, _ = api
    assert _post_bytes(base_url, "/api/tc-library/import/preview?filename=a.xlsx", b"hello")[0] == 400
    parsed = urlparse(base_url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=10)
    conn.putrequest("POST", "/api/tc-library/import/preview?filename=a.xlsx")
    conn.putheader("Content-Length", str(30 * 1024 * 1024))
    conn.endheaders()
    response = conn.getresponse()
    assert (response.status, json.loads(response.read())["code"]) == (413, "PAYLOAD_TOO_LARGE")
    conn.close()


def test_read_endpoints(api):
    base_url, _ = api
    assert request_json(base_url, "GET", "/api/tc-library")[1]["suites"] == \
        [{"suite": "야핏무브", "sheets": ["혜택", "홈"], "count": 6}]
    tree = request_json(base_url, "GET", f"/api/tc-library/{S}/tree")[1]["tree"]
    assert [(n["name"], n["count"]) for n in tree] == [("혜택", 5), ("홈", 1)]
    listing = request_json(base_url, "GET",
                           f"/api/tc-library/{S}?path=" + quote("혜택/혜택 탭/상단 배너"))[1]
    assert (listing["total"], [c["case_id"] for c in listing["items"]]) == (2, ["BEN_0002", "BEN_0003"])
    not_run = request_json(base_url, "GET", f"/api/tc-library/{S}?execution_result=")[1]
    assert [c["case_id"] for c in not_run["items"]] == ["BEN_0001", "BEN_0004", "HOME_0001"]
    case = request_json(base_url, "GET", f"/api/tc-library/{S}/cases/BEN_0002")[1]["case"]
    assert [i["code"] for i in case["issues"]] == ["PRIORITY_EMPTY"]


def test_rejects_bad_suite_and_cross_origin_writes(api):
    base_url, _ = api
    status, body = request_json(base_url, "GET", "/api/tc-library/..%2Fetc/tree")
    assert (status, body["code"]) == (400, "INVALID_SUITE")
    req = urllib.request.Request(f"{base_url}/api/tc-library/{S}/cases/BEN_0001", method="PATCH",
                                 data=b'{"rev": 1}', headers={"Origin": "http://evil.example",
                                                              "Content-Type": "application/json"})
    with pytest.raises(urllib.error.HTTPError) as err:
        urllib.request.urlopen(req, timeout=10)
    assert err.value.code == 403
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_library_api.py -q`
Expected: FAIL — 가져오기 미리보기 요청이 404 (`assert status == 200`)

- [ ] **Step 3: 바디 상한** — `agents/dashboard/dash_http.py`의 기존 `_read_body`(16~19행)를 아래로 바꾼다. 호출부 20곳은 시그니처가 같아서 그대로 둔다.

```python
MAX_JSON_BODY_BYTES = 2 * 1024 * 1024


class BodyTooLarge(Exception):
    pass


def _content_length(handler) -> int:
    try:
        return max(int(handler.headers.get("Content-Length", 0)), 0)
    except ValueError:
        return 0


def _read_raw_body(handler, limit: int) -> bytes:
    length = _content_length(handler)
    if length > limit:
        raise BodyTooLarge(length)
    return handler.rfile.read(length) if length else b""


def _read_body(handler, limit: int = MAX_JSON_BODY_BYTES) -> dict:
    """요청 바디를 JSON으로 파싱해 반환. 바디 없으면 빈 dict. 상한 초과는 BodyTooLarge."""
    raw = _read_raw_body(handler, limit)
    return json.loads(raw.decode("utf-8")) if raw else {}
```

- [ ] **Step 4: 라우트 Mixin 작성** — `agents/dashboard/routes_tc_library.py`

```python
"""routes_tc_library.py — TC 스튜디오 라이브러리 API (PRD F2·F5·F6, 로드맵 B8~B10).

serve.py의 do_GET/do_POST/do_PATCH/do_DELETE가 맨 앞에서 `_tcl_dispatch`를 호출한다.
경로에 변수가 있어 GET_ROUTES/POST_ROUTES 딕셔너리 대신 정규식 표를 쓴다.
설계 원칙은 routes_import.py와 같다 (serve를 import하지 않음, 경로는 _paths.X).
"""
from __future__ import annotations

import json
import re
import secrets
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote

import _paths
from dash_http import BodyTooLarge, _read_body, _read_raw_body

_SUITE = r"(?P<suite>[^/]+)"
_CASE = r"(?P<case_id>[\w-]+)"
_ID = r"(?P<item_id>[\w-]+)"
MAX_XLSX_BYTES = 25 * 1024 * 1024

ROUTES: list[tuple[str, re.Pattern, str]] = [
    (m, re.compile(p + r"\Z"), h) for m, p, h in [
        ("GET", r"/api/tc-library", "_tcl_suites"),
        ("POST", r"/api/tc-library/import/preview", "_tcl_import_preview"),
        ("POST", r"/api/tc-library/import", "_tcl_import_commit"),
        ("GET", rf"/api/tc-library/{_SUITE}/tree", "_tcl_tree"),
        ("GET", rf"/api/tc-library/{_SUITE}", "_tcl_list"),
        ("GET", rf"/api/tc-library/{_SUITE}/cases/{_CASE}", "_tcl_get_case"),
        ("GET", rf"/api/tc-library/{_SUITE}/cases/{_CASE}/history", "_tcl_history"),
    ]
]


class TcLibraryRoutesMixin:
    """DashboardHandler(TcLibraryRoutesMixin, …, BaseHTTPRequestHandler) 형태로 쓴다."""

    # ── 공통 ──────────────────────────────────────────────────────
    def _tcl_dispatch(self, method: str) -> bool:
        path, _, query = self.path.partition("?")
        if not path.startswith("/api/tc-library"):
            return False
        for route_method, pattern, handler in ROUTES:
            match = pattern.match(path)
            if match and route_method == method:
                params = {k: unquote(v) for k, v in match.groupdict().items()}
                self._tcl_query = {k: v[-1] for k, v in parse_qs(query, keep_blank_values=True).items()}
                try:
                    getattr(self, handler)(**params)
                except BodyTooLarge:
                    self._tcl_json({"ok": False, "error": "요청이 너무 큽니다",
                                    "code": "PAYLOAD_TOO_LARGE"}, 413)
                except Exception as exc:  # LibraryError 계열은 상태 코드를 그대로
                    from _tc_library import LibraryError, RevConflict
                    if not isinstance(exc, LibraryError):
                        raise
                    body = {"ok": False, "error": str(exc), "code": exc.code}
                    if isinstance(exc, RevConflict):
                        body["server_case"] = exc.server_case
                    self._tcl_json(body, exc.status)
                return True
        self._tcl_json({"ok": False, "error": "not found", "code": "NOT_FOUND"}, 404)
        return True

    def _tcl_json(self, payload, status: int = 200) -> None:
        self._serve_bytes(json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                          "application/json; charset=utf-8", status=status)

    def _tcl_actor(self) -> str:
        return self.headers.get("X-TC-Actor", "web")[:40] or "web"

    # ── 조회 ──────────────────────────────────────────────────────
    def _tcl_suites(self):
        from _tc_library import list_suites
        self._tcl_json({"ok": True, "suites": list_suites()})

    def _tcl_tree(self, suite: str):
        from _tc_library import build_tree, load_cases
        self._tcl_json({"ok": True, "tree": build_tree(load_cases(suite))})

    def _tcl_list(self, suite: str):
        from _tc_library import filter_cases, load_cases
        items = filter_cases(load_cases(suite), self._tcl_query)
        offset = int(self._tcl_query.get("offset", 0))
        limit = min(int(self._tcl_query.get("limit", 200)), 1000)
        self._tcl_json({"ok": True, "total": len(items), "items": items[offset:offset + limit]})

    def _tcl_get_case(self, suite: str, case_id: str):
        from _tc_library import get_case, with_issues
        self._tcl_json({"ok": True, "case": with_issues(get_case(suite, case_id))})

    def _tcl_history(self, suite: str, case_id: str):
        from _tc_library import history
        self._tcl_json({"ok": True, "history": history(suite, case_id)})

    # ── 가져오기 ──────────────────────────────────────────────────
    def _tcl_import_preview(self):
        """본문 = xlsx 원본 바이트 (로드맵 Z3). ?filename= 필수."""
        from _tc_template import analyze_workbook
        from _tc_library import LibraryError
        filename = Path(self._tcl_query.get("filename", "")).name
        if not filename.lower().endswith(".xlsx"):
            raise LibraryError(".xlsx 파일만 가져올 수 있습니다", "UNSUPPORTED_FILE")
        data = _read_raw_body(self, MAX_XLSX_BYTES)
        if not data.startswith(b"PK"):
            raise LibraryError("xlsx 형식이 아닙니다", "UNSUPPORTED_FILE")
        preview_id = "imp_" + secrets.token_hex(6)
        upload_dir = _paths.TC_LIBRARY_DIR / "_uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        xlsx = upload_dir / f"{preview_id}.xlsx"
        xlsx.write_bytes(data)
        try:
            profiles = analyze_workbook(xlsx)
        except Exception as exc:
            xlsx.unlink(missing_ok=True)
            raise LibraryError(f"엑셀을 읽을 수 없습니다: {exc}", "UNREADABLE_XLSX") from exc
        (upload_dir / f"{preview_id}.json").write_text(
            json.dumps({"filename": filename}, ensure_ascii=False), encoding="utf-8")
        from _tc_xlsx_import import import_workbook
        sheets = []
        for name, profile in profiles.items():
            cases = import_workbook(xlsx, profiles, [name], {})
            sheets.append({"name": name, "header_row": profile.header_row,
                           "data_start_row": profile.data_start_row, "cases": len(cases),
                           "result_columns": list(profile.result_columns),
                           "warnings": profile.warnings})
        self._tcl_json({"ok": True, "preview_id": preview_id, "filename": filename,
                        "sheets": sheets})

    def _tcl_import_commit(self):
        from _tc_library import LibraryError, import_cases, save_template
        from _tc_template import analyze_workbook
        from _tc_xlsx_import import import_workbook
        body = _read_body(self)
        preview_id = str(body.get("preview_id", ""))
        if not re.fullmatch(r"imp_[0-9a-f]{12}", preview_id):
            raise LibraryError("미리보기 id가 올바르지 않습니다", "INVALID_PREVIEW")
        upload = _paths.TC_LIBRARY_DIR / "_uploads" / f"{preview_id}.xlsx"
        if not upload.exists():
            raise LibraryError("미리보기가 만료됐습니다. 파일을 다시 선택하세요", "PREVIEW_EXPIRED", 410)
        meta = json.loads(upload.with_suffix(".json").read_text(encoding="utf-8"))
        suite = str(body.get("suite", "")).strip()
        profiles = analyze_workbook(upload)
        sheets = [s for s in body.get("sheets", []) if s in profiles]
        if not sheets:
            raise LibraryError("가져올 시트를 하나 이상 고르세요", "NO_SHEETS")
        prefixes = {k: v for k, v in (body.get("prefixes") or {}).items()
                    if re.fullmatch(r"[A-Z][A-Z0-9]{0,7}", str(v))}
        renamed = upload.with_name(meta["filename"])
        cases = import_workbook(upload, profiles, sheets, prefixes)
        for case in cases:
            case["source_refs"] = [r.replace(upload.name, renamed.name) for r in case["source_refs"]]
        save_template(suite, upload, {s: profiles[s] for s in sheets})
        summary = import_cases(suite, sheets, cases, self._tcl_actor())
        upload.unlink(missing_ok=True)
        upload.with_suffix(".json").unlink(missing_ok=True)
        self._tcl_json({"ok": True, "suite": suite, **summary})
```

- [ ] **Step 5: serve.py 연결**

1. import 추가 (`from routes_ops import OpsRoutesMixin` 아래):

```python
from routes_tc_library import TcLibraryRoutesMixin                # TC 스튜디오
from dash_http import BodyTooLarge
```

2. 클래스 상속 맨 앞에 Mixin 추가:

```python
class DashboardHandler(                                            # Phase-4/5/6
    TcLibraryRoutesMixin,
    ImportRoutesMixin,
    GetRoutesMixin,
    OpsRoutesMixin,
    BaseHTTPRequestHandler,
):
```

3. `do_GET` 첫 줄 `path = self.path.split("?")[0]` 바로 아래에 추가하고, index 경로 목록에 `/tc-studio`를 넣는다:

```python
        if self._tcl_dispatch("GET"):
            return

        # index
        if path in ("/", "/index.html", "/import-studio", "/tc-studio"):
```

4. `do_POST`의 `try:` 바로 아래 첫 줄에 추가하고, `except Exception as e:` 앞에 413 처리를 넣는다:

```python
        try:
            if self._tcl_dispatch("POST"):
                return
            if path.startswith("/api/import/runs/") and path.endswith("/rollback"):
            …
        except BodyTooLarge:
            self._serve_bytes(b'{"ok":false,"error":"request too large","code":"PAYLOAD_TOO_LARGE"}',
                              "application/json; charset=utf-8", status=413)
        except Exception as e:
```

5. `do_DELETE`의 CSRF 검사 바로 아래에 추가:

```python
        if self._tcl_dispatch("DELETE"):
            return
```

6. `do_PUT` 아래에 `do_PATCH` 추가:

```python
    def do_PATCH(self):
        """TC 스튜디오 케이스 부분 수정 (rev 필수)."""
        if not self._check_csrf_origin():
            self.send_response(403)
            self.end_headers()
            return
        if not self._tcl_dispatch("PATCH"):
            self.send_response(404)
            self.end_headers()
```

- [ ] **Step 6: 테스트 격리 경로 추가** — `tests/unit/import_studio/import_studio_test_support.py`의 `configure_isolated_project` `paths` 딕셔너리 마지막 항목 아래:

```python
        "TC_LIBRARY_DIR": project_root / "state" / "tc_library",
```

- [ ] **Step 7: 통과 확인 + 기존 테스트 회귀 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_library_api.py -q`
Expected: `4 passed`

Run: `.venv/bin/python -m pytest -q`
Expected: 기존 677개 + 새 테스트 모두 통과, 1 skipped

- [ ] **Step 8: 커밋**

```bash
git add agents/dashboard/dash_http.py agents/dashboard/serve.py agents/dashboard/routes_tc_library.py tests/unit/import_studio/import_studio_test_support.py tests/unit/tc_library/test_tc_library_api.py
git commit -m "feat(tc-studio): B8 라이브러리 조회·가져오기 API와 요청 바디 상한"
```

---

## Task B9: 쓰기 API

**Files:**
- Modify: `agents/dashboard/routes_tc_library.py`
- Modify: `tests/unit/tc_library/test_tc_library_api.py` (`test_rejects_bad_suite_and_cross_origin_writes` 앞에 추가)

**Interfaces:**
- Consumes: B4 저장소 함수
- Produces:
  - `PATCH /api/tc-library/{suite}/cases/{id}` `{rev, …필드}` → `{ok, case}` / 409 `{code:"REV_CONFLICT", server_case}`
  - `POST /api/tc-library/{suite}/bulk` `{items:[{case_id,rev}], op:"set"|"delete", field, value}` → `{ok, updated|deleted, conflicts}`
  - `POST /api/tc-library/{suite}/move` `{items, sheet, path[3], feature?}` → `{ok, moved, conflicts}`
  - `POST /api/tc-library/{suite}/cases` `{…필드, after?}` → 201 `{ok, case}`
  - `POST …/cases/{id}/duplicate` → 201 · `DELETE …/cases/{id}?rev=` → 200 / 409 · `POST …/cases/{id}/restore` · `GET …/cases/{id}/history` → `{ok, history}` · `POST …/cases/{id}/revert` `{history_id, rev}`
  - 요청 헤더 `X-TC-Actor`(최대 40자)가 이력의 `actor`가 된다. 없으면 `web`.

- [ ] **Step 1: 실패하는 테스트 추가**

```python
def test_patch_conflict_and_revert(api):
    base_url, _ = api
    path = f"/api/tc-library/{S}/cases/BEN_0002"
    status, body = request_json(base_url, "PATCH", path, {"rev": 1, "priority": "P1"})
    assert (status, body["case"]["rev"]) == (200, 2)
    status, body = request_json(base_url, "PATCH", path, {"rev": 1, "priority": "P2"})
    assert (status, body["code"], body["server_case"]["priority"]) == (409, "REV_CONFLICT", "P1")

    history = request_json(base_url, "GET", path + "/history")[1]["history"]
    hid = next(e["history_id"] for e in history if e["field"] == "priority")
    status, body = request_json(base_url, "POST", path + "/revert", {"history_id": hid, "rev": 2})
    assert (status, body["case"]["priority"]) == (200, "")


def test_bulk_create_duplicate_move_delete_restore(api):
    base_url, _ = api
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/bulk", {
        "items": [{"case_id": "BEN_0001", "rev": 1}, {"case_id": "BEN_0002", "rev": 9}],
        "op": "set", "field": "auto", "value": "Y-app"})
    assert (body["updated"], [c["case_id"] for c in body["conflicts"]]) == (["BEN_0001"], ["BEN_0002"])

    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/cases", {
        "sheet": "혜택", "path": ["혜택 탭", "상단 배너", ""], "feature": "새 기능", "after": "BEN_0003"})
    assert (status, body["case"]["case_id"]) == (201, "BEN_0006")
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/cases/BEN_0001/duplicate")
    assert (status, body["case"]["case_id"]) == (201, "BEN_0007")
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/move", {
        "items": [{"case_id": "BEN_0006", "rev": 1}], "sheet": "혜택",
        "path": ["혜택 탭", "신규회원 한정 혜택", "돈불리기"]})
    assert body["moved"] == ["BEN_0006"]

    assert request_json(base_url, "DELETE", f"/api/tc-library/{S}/cases/BEN_0003?rev=9")[0] == 409
    assert request_json(base_url, "DELETE", f"/api/tc-library/{S}/cases/BEN_0003?rev=1")[0] == 200
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/cases/BEN_0003/restore")
    assert (status, body["case"]["rev"]) == (200, 3)
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_library_api.py -q`
Expected: FAIL — PATCH가 404

- [ ] **Step 3: 라우트 표에 추가** — `ROUTES`의 `_tcl_list` 줄 아래에:

```python
        ("POST", rf"/api/tc-library/{_SUITE}/cases", "_tcl_create"),
        ("POST", rf"/api/tc-library/{_SUITE}/bulk", "_tcl_bulk"),
        ("POST", rf"/api/tc-library/{_SUITE}/move", "_tcl_move"),
```

`_tcl_get_case` 줄 아래에:

```python
        ("PATCH", rf"/api/tc-library/{_SUITE}/cases/{_CASE}", "_tcl_patch_case"),
        ("DELETE", rf"/api/tc-library/{_SUITE}/cases/{_CASE}", "_tcl_delete_case"),
        ("POST", rf"/api/tc-library/{_SUITE}/cases/{_CASE}/duplicate", "_tcl_duplicate"),
        ("POST", rf"/api/tc-library/{_SUITE}/cases/{_CASE}/restore", "_tcl_restore"),
        ("POST", rf"/api/tc-library/{_SUITE}/cases/{_CASE}/revert", "_tcl_revert"),
```

- [ ] **Step 4: 핸들러 추가** — 클래스 끝에:

```python
    # ── 쓰기 ──────────────────────────────────────────────────────
    def _tcl_patch_case(self, suite: str, case_id: str):
        from _tc_library import patch_case, with_issues
        body = _read_body(self)
        rev = int(body.pop("rev"))
        case = patch_case(suite, case_id, rev, body, self._tcl_actor())
        self._tcl_json({"ok": True, "case": with_issues(case)})

    def _tcl_bulk(self, suite: str):
        from _tc_library import LibraryError, bulk_patch, delete_cases
        body = _read_body(self)
        items = [{"case_id": str(i["case_id"]), "rev": int(i["rev"])} for i in body.get("items", [])]
        op = body.get("op", "set")
        if op == "delete":
            result = delete_cases(suite, items, self._tcl_actor())
        elif op == "set":
            result = bulk_patch(suite, items, {body["field"]: body["value"]}, self._tcl_actor())
        else:
            raise LibraryError(f"지원하지 않는 작업입니다: {op}", "INVALID_OP")
        self._tcl_json({"ok": True, **result})

    def _tcl_move(self, suite: str):
        from _tc_library import bulk_patch
        body = _read_body(self)
        items = [{"case_id": str(i["case_id"]), "rev": int(i["rev"])} for i in body.get("items", [])]
        changes = {"sheet": body["sheet"], "path": (list(body["path"]) + ["", "", ""])[:3]}
        if body.get("feature"):
            changes["feature"] = body["feature"]
        result = bulk_patch(suite, items, changes, self._tcl_actor())
        self._tcl_json({"ok": True, "moved": result["updated"], "conflicts": result["conflicts"]})

    def _tcl_create(self, suite: str):
        from _tc_library import create_case, with_issues
        body = _read_body(self)
        after = body.pop("after", None)
        case = create_case(suite, body, self._tcl_actor(), after=after)
        self._tcl_json({"ok": True, "case": with_issues(case)}, 201)

    def _tcl_duplicate(self, suite: str, case_id: str):
        from _tc_library import duplicate_case, with_issues
        self._tcl_json({"ok": True, "case": with_issues(
            duplicate_case(suite, case_id, self._tcl_actor()))}, 201)

    def _tcl_delete_case(self, suite: str, case_id: str):
        from _tc_library import delete_cases
        rev = int(self._tcl_query.get("rev", -1))
        result = delete_cases(suite, [{"case_id": case_id, "rev": rev}], self._tcl_actor())
        if result["conflicts"]:
            self._tcl_json({"ok": False, "code": "REV_CONFLICT",
                            "server_case": result["conflicts"][0]}, 409)
            return
        self._tcl_json({"ok": True, "deleted": result["deleted"]})

    def _tcl_restore(self, suite: str, case_id: str):
        from _tc_library import restore_case
        self._tcl_json({"ok": True, "case": restore_case(suite, case_id, self._tcl_actor())})

    def _tcl_revert(self, suite: str, case_id: str):
        from _tc_library import revert, with_issues
        body = _read_body(self)
        case = revert(suite, case_id, str(body["history_id"]), int(body["rev"]), self._tcl_actor())
        self._tcl_json({"ok": True, "case": with_issues(case)})
```

- [ ] **Step 5: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_library_api.py -q`
Expected: `6 passed`

- [ ] **Step 6: 커밋**

```bash
git add agents/dashboard/routes_tc_library.py tests/unit/tc_library/test_tc_library_api.py
git commit -m "feat(tc-studio): B9 케이스 수정·일괄·생성·삭제·이력 API"
```

---

## Task B10: 엑셀 내보내기 API + 다운로드

**Files:**
- Modify: `agents/dashboard/routes_tc_library.py`
- Modify: `tests/unit/tc_library/test_tc_library_api.py`

**Interfaces:**
- Consumes: B6·B7 `export_workbook verify_export`, B4 `load_profiles load_cases suite_dir`
- Produces:
  - `POST /api/tc-library/{suite}/export/xlsx` `{scope:"all"|"approved"|"sheets"|"case_ids", sheets?, case_ids?, history_note}` → `{ok, export_id, filename, checks, count}` / 409 `NO_TEMPLATE`
  - `GET /api/tc-library/exports/{export_id}/download` → xlsx (`Content-Disposition`에 RFC 5987 `filename*`)
  - 산출물: `state/tc_library/_exports/{export_id}.xlsx` + `.json`(스위트·파일명)
  - scope `sheets`: 고르지 않은 TC 시트는 사본에서 **삭제**한다. 나머지 scope는 모든 TC 시트를 다시 쓴다.

- [ ] **Step 1: 실패하는 테스트 추가** — `test_rejects_bad_suite_and_cross_origin_writes` 앞에:

```python
def test_export_and_download(api):
    base_url, _ = api
    status, body = request_json(base_url, "POST", f"/api/tc-library/{S}/export/xlsx",
                                {"scope": "all", "history_note": "Phase 1"})
    assert status == 200 and body["count"] == 6
    assert {c["level"] for c in body["checks"]} == {"ok"}, body["checks"]
    with urllib.request.urlopen(
            f"{base_url}/api/tc-library/exports/{body['export_id']}/download", timeout=10) as resp:
        assert resp.read(2) == b"PK"
        assert "filename*=UTF-8''" in resp.headers["Content-Disposition"]
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_library_api.py::test_export_and_download -q`
Expected: FAIL — 404

- [ ] **Step 3: 라우트 표에 추가** — `import` 줄 아래에:

```python
        ("GET", rf"/api/tc-library/exports/{_ID}/download", "_tcl_export_download"),
```

`_tcl_move` 줄 아래에:

```python
        ("POST", rf"/api/tc-library/{_SUITE}/export/xlsx", "_tcl_export_xlsx"),
```

- [ ] **Step 4: 핸들러 추가** — 클래스 끝에:

```python
    # ── 내보내기 ──────────────────────────────────────────────────
    def _tcl_export_xlsx(self, suite: str):
        from _tc_library import LibraryError, load_cases, load_profiles, suite_dir
        from _tc_xlsx_export import export_workbook, verify_export
        body = _read_body(self)
        profiles = load_profiles(suite)
        if not profiles:
            raise LibraryError("템플릿이 없습니다. 먼저 엑셀을 가져오세요", "NO_TEMPLATE", 409)
        cases = load_cases(suite)
        scope = body.get("scope", "all")
        drop: tuple[str, ...] = ()
        if scope == "approved":
            cases = [c for c in cases if c["status"] == "approved"]
        elif scope == "sheets":
            keep = set(body.get("sheets", []))
            cases = [c for c in cases if c["sheet"] in keep]
            drop = tuple(s for s in profiles if s not in keep)
        elif scope == "case_ids":
            keep = set(body.get("case_ids", []))
            cases = [c for c in cases if c["case_id"] in keep]
        by_sheet: dict[str, list[dict]] = {s: [] for s in profiles if s not in drop}
        for case in cases:
            if case["sheet"] in by_sheet:
                by_sheet[case["sheet"]].append(case)
        export_id = "exp_" + secrets.token_hex(6)
        out_dir = _paths.TC_LIBRARY_DIR / "_exports"
        out = out_dir / f"{export_id}.xlsx"
        export_workbook(suite_dir(suite) / "template.xlsx", profiles, by_sheet, out,
                        history_note=str(body.get("history_note", "")), drop_sheets=drop)
        checks = verify_export(out, {s: profiles[s] for s in by_sheet}, by_sheet)
        filename = f"{suite}_Full_{date.today():%Y%m%d}.xlsx"
        (out_dir / f"{export_id}.json").write_text(
            json.dumps({"suite": suite, "filename": filename}, ensure_ascii=False), encoding="utf-8")
        self._tcl_json({"ok": True, "export_id": export_id, "filename": filename,
                        "checks": checks, "count": sum(map(len, by_sheet.values()))})

    def _tcl_export_download(self, item_id: str):
        out_dir = _paths.TC_LIBRARY_DIR / "_exports"
        path, meta = out_dir / f"{item_id}.xlsx", out_dir / f"{item_id}.json"
        if not (re.fullmatch(r"exp_[0-9a-f]{12}", item_id) and path.exists() and meta.exists()):
            self._tcl_json({"ok": False, "code": "NOT_FOUND"}, 404)
            return
        filename = json.loads(meta.read_text(encoding="utf-8"))["filename"]
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type",
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.send_header("Content-Disposition",
                         f"attachment; filename=\"export.xlsx\"; filename*=UTF-8''{quote(filename)}")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)
```

- [ ] **Step 5: 통과 확인 + 전체 회귀**

Run: `.venv/bin/python -m pytest tests/unit/tc_library -q`
Expected: `32 passed`

Run: `.venv/bin/python -m pytest -q`
Expected: 전체 통과, 1 skipped

- [ ] **Step 6: 커밋**

```bash
git add agents/dashboard/routes_tc_library.py tests/unit/tc_library/test_tc_library_api.py
git commit -m "feat(tc-studio): B10 엑셀 내보내기와 다운로드 API"
```

---

## 화면 작업 공통 사항

- 모듈은 Import Studio처럼 즉시 실행 함수 + 네임스페이스(`window.TCS_NS`)로 만든다. 공개 API는 `window.TCS.init(selector)` 하나다.
- 로드 순서: `api` → `state` → `detail` → `library` → `import`(W2) → `export`(W3) → `main`. `main.js`는 `NS.importModal`·`NS.exportView`가 없으면 해당 버튼·탭을 그리지 않는다. 그래서 W1만 끝난 상태에서도 화면이 동작한다.
- 스타일은 목업 `<style>`을 생성 스크립트로 `.tc-studio` 범위에 옮긴다. **생성된 CSS는 직접 고치지 않는다.** 목업을 고친 뒤 다시 생성하고, 대시보드에서만 필요한 보정은 생성 스크립트의 `EXTRA`에 넣는다.
- **목업 버그 주의:** 목업은 빈 우선순위 칩에 `empty` 클래스를 붙이는데, 빈 화면용 `.empty`(padding 60px, `display:grid`)와 이름이 겹쳐 행 높이가 155px로 커진다. 구현은 `is-unset` 클래스를 쓴다 (W1 코드에 반영됨).
- E2E 테스트는 `tests/unit/tc_library/test_tc_studio_e2e.py` 하나에 작업별 절로 쌓는다. 기존 `test_report_management_e2e.py`처럼 실제 Chromium을 띄운다.

> **검증 상태:** 아래 화면 코드는 저장소 사본에 이 계획대로 적용해 W1만 → W2까지 → W3까지 단계별로 E2E를 돌려 모두 통과했다 (6 → 7 → 8개). 셸이 대시보드 안에서 목업과 같은 모습으로 그려지는 것도 스크린샷으로 확인했다.

---

## Task W1: 화면 셸 + 라이브러리 + 상세 패널

PRD 범위: F5.1~F5.4, F5.8, F5.11 (트리·그리드·필터·검색·셀 편집·칩·rev 충돌·일괄 편집·추가·복제·삭제·되돌리기·이동·상세 편집·이력)

**Files:**
- Create: `agents/dashboard/tools/scope_tc_studio_css.py`
- Create (생성물): `agents/dashboard/static/css/tc-studio.css`
- Create: `agents/dashboard/static/js/tc-studio/api.js`, `state.js`, `detail.js`, `library.js`, `main.js`
- Modify: `agents/dashboard/index.html` (CSS 링크 21행 아래, 사이드바 "Import Studio" 항목 아래, `router.js` 스크립트 앞)
- Modify: `agents/dashboard/static/js/router.js`
- Test: `tests/unit/tc_library/test_tc_studio_e2e.py`

**Interfaces:**
- Consumes: B8~B10 API 전부
- Produces:
  - `window.TCS.init(selector) -> Promise` (router가 호출)
  - `TCS_NS.api.*` — `suites tree list getCase patchCase createCase duplicate deleteCase restore history revert bulk move importPreview importCommit exportXlsx downloadUrl`
  - `TCS_NS.state` — `suites suite tree items total filters selected activeId screen`
  - `TCS_NS.toast(msg, kind, actions[{id,label,fn}], ms)`, `TCS_NS.esc`, `TCS_NS.$`, `TCS_NS.$$`, `TCS_NS.queryFromFilters(filters)`
  - `TCS_NS.library.{html, mount, refresh, reloadList, save, askDelete, openMove}`, `TCS_NS.detail.{html, mount, open(caseId, tab), close, refreshIfOpen}`
  - `TCS_NS.reloadSuites(preferSuite)` (W2 가져오기가 호출)
  - 화면 요소 `data-id`: 명세서 2장과 같다. 실행 결과 칩은 `grid-result`, 우선순위 칩은 `grid-cell-priority`.

- [ ] **Step 1: 실패하는 E2E 테스트 작성** — `tests/unit/tc_library/test_tc_studio_e2e.py`

```python
"""TC 스튜디오 실제 브라우저 검증 (로드맵 W1~W7). 실행: .venv/bin/python -m pytest tests/unit/tc_library/test_tc_studio_e2e.py"""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import quote

import pytest
from playwright.sync_api import Page, expect

from tests.unit.import_studio.import_studio_test_support import dashboard_server, request_json
from tests.unit.tc_library.tc_fixtures import build_template_workbook

S = quote("야핏무브")


def _seed(base_url: str, tmp_path: Path) -> None:
    data = build_template_workbook(tmp_path / "seed.xlsx").read_bytes()
    req = urllib.request.Request(
        base_url + "/api/tc-library/import/preview?filename=" + quote("야핏무브_Full.xlsx"),
        data=data, method="POST", headers={"Content-Type": "application/octet-stream"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        preview = json.loads(resp.read())
    status, body = request_json(base_url, "POST", "/api/tc-library/import", {
        "preview_id": preview["preview_id"], "suite": "야핏무브", "sheets": ["혜택", "홈"],
        "prefixes": {"혜택": "BEN", "홈": "HOME"}})
    assert status == 200, body


@pytest.fixture
def studio(tmp_path: Path, page: Page):
    project = tmp_path / "project"
    (project / "testcases").mkdir(parents=True)
    with dashboard_server(project) as base_url:
        _seed(base_url, tmp_path)
        page.goto(base_url + "/tc-studio")
        expect(page.locator("#grid-body tr[data-case]")).to_have_count(6)
        yield base_url, page


def rows(page: Page):
    return page.locator("#grid-body tr[data-case]")


# ── W1: 셸·라이브러리·상세 ──────────────────────────────────────────────────────────
def test_route_sidebar_and_tabs(studio):
    _, page = studio
    expect(page.locator("#tab-tc_studio")).to_have_class(re.compile("active"))
    expect(page.locator('[data-id="suite-select"] option')).to_have_text(["야핏무브 (6)"])
    expect(page.locator('[data-id="nav-tab-library"]')).to_be_visible()
    expect(page.locator('[data-id="nav-tab-generate"]')).to_have_count(0)


def test_tree_filters_and_search(studio):
    _, page = studio
    page.locator('[data-id="tree-node"][data-name="상단 배너"]').click()
    expect(rows(page)).to_have_count(2)
    expect(page.locator("#grid-crumb")).to_have_text("혜택 › 혜택 탭 › 상단 배너")
    page.locator('[data-id="lib-filter-reset"]').click()
    page.locator('[data-id="lib-search"]').fill("돈불리기")
    expect(rows(page)).to_have_count(2)
    page.locator('[data-id="lib-filter-reset"]').click()
    page.locator('[data-id="lib-filter-result"]').select_option("fail")
    expect(rows(page)).to_have_count(1)
    page.locator('[data-id="lib-filter-result"]').select_option("none")
    expect(rows(page)).to_have_count(3)


def test_chip_and_cell_edits_persist(studio):
    _, page = studio
    row = page.locator('tr[data-case="BEN_0002"]')
    row.locator('[data-id="grid-cell-priority"]').select_option("P3")
    expect(page.locator(".toast.ok").first).to_contain_text("BEN_0002 저장됨")
    cell = row.locator('[data-id="grid-cell-feature"]')
    cell.dblclick()
    page.keyboard.press("ControlOrMeta+a")
    page.keyboard.type("배너 가로 스크롤")
    page.keyboard.press("ControlOrMeta+Enter")
    expect(page.locator(".toast.ok").last).to_contain_text("rev 3")
    page.reload()
    row = page.locator('tr[data-case="BEN_0002"]')
    expect(row.locator('[data-id="grid-cell-priority"]')).to_have_value("P3")
    expect(row.locator('[data-id="grid-cell-feature"]')).to_have_text("배너 가로 스크롤")


def test_stale_rev_shows_conflict_toast(studio):
    base_url, page = studio
    request_json(base_url, "PATCH", f"/api/tc-library/{S}/cases/BEN_0003", {"rev": 1, "priority": "P0"})
    page.locator('tr[data-case="BEN_0003"] [data-id="grid-cell-priority"]').select_option("P2")
    expect(page.locator('[data-id="toast-conflict-reload"]')).to_be_visible()
    page.locator('[data-id="toast-conflict-reload"]').click()
    expect(page.locator('tr[data-case="BEN_0003"] [data-id="grid-cell-priority"]')).to_have_value("P0")


def test_bulk_add_delete_and_undo(studio):
    _, page = studio
    rows(page).nth(0).locator('[data-id="grid-row-check"]').check()
    rows(page).nth(1).locator('[data-id="grid-row-check"]').check()
    expect(page.locator('[data-id="bulk-bar"]')).to_contain_text("2건 선택")
    page.locator('[data-id="bulk-priority"]').select_option("P2")
    expect(page.locator('tr[data-case="BEN_0002"] [data-id="grid-cell-priority"]')).to_have_value("P2")

    page.locator('[data-id="btn-add-case"]').click()
    expect(rows(page)).to_have_count(7)
    expect(page.locator('[data-id="detail-panel"] #d-id')).to_have_text("BEN_0006")

    page.locator('[data-id="detail-delete"]').click()
    page.locator('[data-id="confirm-ok"]').click()
    expect(rows(page)).to_have_count(6)
    page.locator('[data-id="delete-undo"]').click()
    expect(rows(page)).to_have_count(7)


def test_detail_save_history_and_revert(studio):
    _, page = studio
    page.locator('tr[data-case="HOME_0001"] td.no').click()
    expect(page.locator("#d-id")).to_have_text("HOME_0001")
    page.locator('[data-id="detail-expected"]').fill("홈 화면 상단에 D+3 전용 카드가 노출된다.")
    page.locator('[data-id="detail-step-add"]').click()
    page.locator('[data-id="detail-step-input"]').last.fill("홈 카드 선택")
    page.locator('[data-id="detail-save"]').click()
    expect(page.locator("#d-rev")).to_have_text("rev 2")
    page.locator('[data-id="detail-tab-history"]').click()
    history = page.locator('[data-id="detail-history"] li')
    expect(history.first).to_contain_text("expected")
    page.locator('[data-id="detail-history-revert"]').first.click()
    expect(page.locator("#d-rev")).to_have_text("rev 3")
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_studio_e2e.py -q`
Expected: FAIL — `#grid-body tr[data-case]` 개수가 0 (스튜디오 스크립트가 아직 없음)

- [ ] **Step 3: CSS 생성 스크립트 작성 후 실행** — `agents/dashboard/tools/scope_tc_studio_css.py`

```python
"""목업 <style>을 대시보드용 .tc-studio 스코프 CSS로 옮긴다 (계획 W1에서 한 번 실행 후 결과를 커밋).

사용: .venv/bin/python scope_css.py design-previews/tc-authoring-studio.html agents/dashboard/static/css/tc-studio.css
규칙:
- 다크 전용 대시보드이므로 라이트 테마 블록(@media prefers-color-scheme, [data-theme=...])은 버린다.
- `:root { … }` 토큰은 `.tc-studio { … }`로 옮긴다 (Import Studio의 .import-studio 방식과 같다).
- `body { … }` 규칙은 `.tc-studio { … }`로 바꾼다.
- 나머지 모든 선택자 앞에 `.tc-studio `를 붙인다. @media 안쪽도 같다. @keyframes는 그대로 둔다.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# 목업 CSS를 대시보드에 붙일 때 필요한 보정. 목업의 .chip-select.empty는 빈 화면용 .empty
# (padding 60px, display:grid)와 이름이 겹쳐 행 높이가 커지므로 클래스를 is-unset으로 바꿔 쓴다.
EXTRA = """
/* ── 대시보드 보정 (scope_css.py EXTRA) ── */
.tc-studio { padding:16px; }
.tc-studio .chip-select.is-unset { color:var(--text3); font-style:italic; }
.tc-studio .chip-select.result-none { color:var(--text3); }
"""
HEADER = "/* TC 스튜디오 — design-previews/tc-authoring-studio.html <style>에서 생성 (scope_css.py). 직접 고치지 말고 목업을 고친 뒤 다시 생성한다. */\n"


def _blocks(css: str):
    """최상위 블록을 (prelude, body) 로 나눈다. 중괄호 깊이만 센다."""
    i, n = 0, len(css)
    while i < n:
        start = css.find("{", i)
        if start == -1:
            return
        prelude = css[i:start].strip()
        depth, j = 1, start + 1
        while depth and j < n:
            depth += {"{": 1, "}": -1}.get(css[j], 0)
            j += 1
        yield prelude, css[start + 1:j - 1]
        i = j


def _scope_selectors(prelude: str) -> str:
    parts = []
    for sel in prelude.split(","):
        sel = sel.strip()
        if sel in ("body", ":root"):
            parts.append(".tc-studio")
        elif sel.startswith("*"):
            parts.append(f".tc-studio {sel}")
        else:
            parts.append(f".tc-studio {sel}")
    return ", ".join(dict.fromkeys(parts))


def scope(css: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    out = [HEADER]
    for prelude, body in _blocks(css):
        if prelude.startswith("@media") and "prefers-color-scheme" in prelude:
            continue
        if "data-theme" in prelude:
            continue
        if prelude.startswith("@keyframes"):
            out.append(f"{prelude} {{{body}}}\n")
        elif prelude.startswith("@media"):
            inner = "".join(f"  {_scope_selectors(p)} {{{b}}}\n" for p, b in _blocks(body))
            out.append(f"{prelude} {{\n{inner}}}\n")
        else:
            out.append(f"{_scope_selectors(prelude)} {{{body}}}\n")
    return "".join(out) + EXTRA


def main(src: str, dst: str) -> None:
    html = Path(src).read_text(encoding="utf-8")
    css = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
    Path(dst).write_text(scope(css), encoding="utf-8")


if __name__ == "__main__":
    main(*sys.argv[1:3])
```

Run: `.venv/bin/python agents/dashboard/tools/scope_tc_studio_css.py design-previews/tc-authoring-studio.html agents/dashboard/static/css/tc-studio.css`
Expected: `tc-studio.css` 약 340줄, 첫 줄이 생성 안내 주석, `prefers-color-scheme`·`data-theme`·`body`·`:root`가 한 번도 나오지 않음, 끝에 "대시보드 보정" 블록

- [ ] **Step 4: API 클라이언트** — `agents/dashboard/static/js/tc-studio/api.js`

```javascript
// TC 스튜디오 — API 클라이언트 (agents/dashboard/routes_tc_library.py와 1:1)
(function (NS) {
  'use strict';

  const enc = encodeURIComponent;

  async function request(method, path, body) {
    const init = { method, headers: {} };
    if (body instanceof Blob) {
      init.body = body;
      init.headers['Content-Type'] = 'application/octet-stream';
    } else if (body !== undefined) {
      init.body = JSON.stringify(body);
      init.headers['Content-Type'] = 'application/json';
    }
    const res = await fetch(path, init);
    const data = await res.json().catch(() => ({ ok: false, code: 'BAD_RESPONSE' }));
    if (!res.ok) {
      const err = new Error(data.error || res.statusText);
      err.status = res.status;
      err.code = data.code;
      err.data = data;
      throw err;
    }
    return data;
  }

  const S = (suite) => `/api/tc-library/${enc(suite)}`;
  const C = (suite, id) => `${S(suite)}/cases/${enc(id)}`;

  NS.api = {
    suites: () => request('GET', '/api/tc-library'),
    tree: (suite) => request('GET', `${S(suite)}/tree`),
    list: (suite, query) => request('GET', `${S(suite)}?${new URLSearchParams(query)}`),
    getCase: (suite, id) => request('GET', C(suite, id)),
    patchCase: (suite, id, rev, changes) => request('PATCH', C(suite, id), { rev, ...changes }),
    createCase: (suite, fields) => request('POST', `${S(suite)}/cases`, fields),
    duplicate: (suite, id) => request('POST', `${C(suite, id)}/duplicate`),
    deleteCase: (suite, id, rev) => request('DELETE', `${C(suite, id)}?rev=${rev}`),
    restore: (suite, id) => request('POST', `${C(suite, id)}/restore`),
    history: (suite, id) => request('GET', `${C(suite, id)}/history`),
    revert: (suite, id, historyId, rev) =>
      request('POST', `${C(suite, id)}/revert`, { history_id: historyId, rev }),
    bulk: (suite, items, op, field, value) =>
      request('POST', `${S(suite)}/bulk`, { items, op, field, value }),
    move: (suite, items, sheet, path, feature) =>
      request('POST', `${S(suite)}/move`, { items, sheet, path, feature }),
    importPreview: (file) =>
      request('POST', `/api/tc-library/import/preview?filename=${enc(file.name)}`, file),
    importCommit: (payload) => request('POST', '/api/tc-library/import', payload),
    exportXlsx: (suite, payload) => request('POST', `${S(suite)}/export/xlsx`, payload),
    downloadUrl: (exportId) => `/api/tc-library/exports/${enc(exportId)}/download`,
  };
})(window.TCS_NS = window.TCS_NS || {});
```

- [ ] **Step 5: 상태·도우미** — `agents/dashboard/static/js/tc-studio/state.js`

```javascript
// TC 스튜디오 — 화면 상태와 공용 도우미
(function (NS) {
  'use strict';

  NS.state = {
    suites: [],
    suite: '',
    tree: [],
    items: [],          // 현재 필터 결과 (서버 응답 그대로, issues 포함)
    total: 0,
    filters: { q: '', path: '', status: '', execution_result: '', priority: '', auto: '',
               source: '', invalid: false },
    selected: new Set(),
    activeId: '',
    screen: 'library',
    lastUndo: null,     // { label, run: async () => {} }
  };

  NS.STATUS_LABEL = { draft: '초안', approved: '승인', rejected: '반려', needs_review: '재검토 필요' };
  NS.RESULT_LABEL = { '': '미실행', pass: 'Pass', fail: 'Fail', not_test: 'Not Test', na: 'N/A' };
  NS.PRIORITIES = ['P0', 'P1', 'P2', 'P3'];
  NS.AUTO_VALUES = ['Y-web', 'Y-app', 'N'];

  // 필터 → GET /api/tc-library/{suite} 쿼리. 실행 결과 "none" = 미실행(빈 값).
  NS.queryFromFilters = function (f) {
    const q = {};
    Object.entries(f).forEach(([k, v]) => {
      if (k === 'invalid') { if (v) q.invalid = '1'; return; }
      if (k === 'execution_result') {
        if (v === 'none') q.execution_result = '';
        else if (v) q.execution_result = v;
        return;
      }
      if (v) q[k] = v;
    });
    return q;
  };

  NS.esc = function (s) {
    return String(s ?? '').replace(/[&<>"]/g, (c) => (
      { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  };

  NS.$ = (sel, root = document) => root.querySelector(sel);
  NS.$$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  // 목업 toast() 이식. actions: [{ id, label, fn }]
  NS.toast = function (msg, kind = '', actions = [], ms = 3800) {
    const box = NS.$('#tcs-toasts');
    if (!box) return null;
    const el = document.createElement('div');
    el.className = 'toast ' + kind;
    el.innerHTML = `<div>${msg}</div>` + (actions.length
      ? `<div class="row">${actions.map((a, i) =>
        `<button class="btn-sm" data-id="${a.id}" data-i="${i}">${NS.esc(a.label)}</button>`).join('')}</div>`
      : '');
    actions.forEach((a, i) => el.querySelector(`[data-i="${i}"]`).addEventListener('click', async () => {
      el.remove();
      if (a.fn) await a.fn();
    }));
    box.appendChild(el);
    if (ms) setTimeout(() => el.remove(), ms);
    return el;
  };
})(window.TCS_NS = window.TCS_NS || {});
```

- [ ] **Step 6: 상세 패널** — `agents/dashboard/static/js/tc-studio/detail.js`

마크업은 목업 500~567행(`<aside class="detail">`)을 옮긴 것이다. 달라진 점: 선택지를 상수에서 만들고, "미실행" 선택지와 "메모 (기타)" 입력을 추가했다(명세 피드백 #5). 원문 탭은 Phase 1에서는 출처 목록만 보여 준다.

```javascript
// TC 스튜디오 — 케이스 상세 패널: 편집·Step 순서·UI 문구·검증·이력·되돌리기 (PRD F5.2, F5.8, F5.11)
(function (NS) {
  'use strict';

  const { state, api, esc, $, $$, toast } = NS;
  let root = null;
  let current = null;   // 서버에서 받은 케이스 (rev 기준)
  let draft = null;     // 편집 중인 사본

  NS.detail = { html, mount, open, close, refreshIfOpen };

  const opt = (v, label) => `<option value="${esc(v)}">${esc(label)}</option>`;

  function html() {
    return `
      <aside class="detail" id="detail" data-id="detail-panel" aria-label="케이스 상세">
        <div class="detail-head">
          <div class="row">
            <span class="mono faint" id="d-id"></span><span id="d-status"></span>
            <span id="d-rev" class="mono faint" style="font-size:10.5px"></span><span class="spacer"></span>
            <span id="d-dirty" hidden title="저장하지 않은 변경"><i class="dirty-dot"></i></span>
            <button class="icon-btn" data-id="detail-close" id="detail-close" aria-label="패널 닫기">✕</button>
          </div>
          <input class="input" id="detail-feature" data-id="detail-feature" style="font-weight:600;font-size:14px" aria-label="기능">
          <div class="row" style="font-size:11.5px"><span class="faint">경로</span><span id="d-path" class="crumbpath"></span>
            <button class="btn-sm" data-id="detail-move" id="detail-move">이동…</button></div>
        </div>
        <div class="detail-tabs" role="tablist">
          <button class="dtab" role="tab" data-id="detail-tab-edit" data-pane="edit" aria-selected="true">편집</button>
          <button class="dtab" role="tab" data-id="detail-tab-source" data-pane="source" aria-selected="false">원문</button>
          <button class="dtab" role="tab" data-id="detail-tab-history" data-pane="history" aria-selected="false">이력</button>
        </div>
        <div class="detail-body">
          <div class="dpane active" data-pane="edit">
            <div class="two">
              <div class="field"><span class="label">우선순위</span><select class="select" id="detail-priority" data-id="detail-priority">${opt('', '미지정')}${NS.PRIORITIES.map((p) => opt(p, p)).join('')}</select></div>
              <div class="field"><span class="label">AUTO</span><select class="select" id="detail-auto" data-id="detail-auto">${opt('', '미지정')}${NS.AUTO_VALUES.map((a) => opt(a, a)).join('')}</select></div>
              <div class="field"><span class="label">실행 결과</span><select class="select" id="detail-result" data-id="detail-result">${Object.entries(NS.RESULT_LABEL).map(([k, l]) => opt(k, l)).join('')}</select></div>
              <div class="field"><span class="label">검토 상태</span><select class="select" id="detail-status" data-id="detail-status">${Object.entries(NS.STATUS_LABEL).map(([k, l]) => opt(k, l)).join('')}</select></div>
            </div>
            <div class="field"><label class="label" for="detail-precondition">사전 조건</label><textarea class="textarea" id="detail-precondition" data-id="detail-precondition" rows="2"></textarea></div>
            <div class="field">
              <div class="row"><span class="label">Test Step</span><span class="spacer"></span><span class="faint" style="font-size:10.5px">끌어서 순서 변경 · <span class="kbd">Alt</span><span class="kbd">↑↓</span></span></div>
              <ol class="steps" id="d-steps" data-id="detail-steps"></ol>
              <button class="btn-sm" data-id="detail-step-add" id="detail-step-add" style="justify-self:start">+ Step 추가</button>
            </div>
            <div class="field"><label class="label" for="detail-expected">Expected Result</label>
              <textarea class="textarea" id="detail-expected" data-id="detail-expected" rows="2"></textarea><span class="help" id="d-exp-help"></span></div>
            <div class="field">
              <div class="row"><span class="label">UI 문구</span><span class="spacer"></span><span class="faint" style="font-size:10.5px">배지를 눌러 확인/추정 전환</span></div>
              <div class="bullets" id="d-bullets" data-id="detail-bullets"></div>
              <button class="btn-sm" data-id="detail-bullet-add" id="detail-bullet-add" style="justify-self:start">+ 문구 추가</button>
            </div>
            <div class="field"><label class="label" for="detail-note">메모 (기타)</label><textarea class="textarea" id="detail-note" data-id="detail-note" rows="2"></textarea></div>
            <div class="field"><span class="label">출처 (source_refs)</span><div class="row" id="d-refs"></div></div>
            <div class="field"><span class="label">검증</span><ul class="checks" id="d-checks" data-id="detail-validation"></ul></div>
          </div>
          <div class="dpane" data-pane="source" id="d-source"></div>
          <div class="dpane" data-pane="history"><ul class="hist" id="d-hist" data-id="detail-history"></ul></div>
        </div>
        <div class="detail-foot">
          <button class="btn btn-primary" data-id="detail-save" id="detail-save" disabled>저장</button>
          <button class="btn btn-ghost" data-id="detail-revert-edits" id="detail-revert-edits" disabled>변경 취소</button>
          <span class="spacer"></span>
          <button class="btn-sm" data-id="detail-duplicate" id="detail-duplicate">복제</button>
          <button class="btn btn-danger" data-id="detail-delete" id="detail-delete" style="padding:4px 10px;font-size:11px">삭제</button>
        </div>
      </aside>`;
  }

  async function open(caseId, tab = 'edit') {
    state.activeId = caseId;
    const { case: c } = await api.getCase(state.suite, caseId);
    current = c;
    draft = JSON.parse(JSON.stringify(c));
    $('#lib', root).classList.remove('no-detail');
    $$('#grid-body tr', root).forEach((tr) => tr.classList.toggle('active', tr.dataset.case === caseId));
    fill();
    selectTab(tab);
  }

  function close() {
    state.activeId = '';
    current = draft = null;
    $('#lib', root).classList.add('no-detail');
    $$('#grid-body tr.active', root).forEach((tr) => tr.classList.remove('active'));
  }

  async function refreshIfOpen() {
    if (!state.activeId || isDirty()) return;
    const still = state.items.some((c) => c.case_id === state.activeId);
    if (still) await open(state.activeId, currentTab());
  }

  const isDirty = () => current && draft && JSON.stringify(pick(current)) !== JSON.stringify(pick(draft));
  const pick = (c) => ({ feature: c.feature, precondition: c.precondition, steps: c.steps, expected: c.expected,
    bullets: c.bullets, priority: c.priority, auto: c.auto, execution_result: c.execution_result,
    status: c.status, note: c.note });
  const currentTab = () => ($('.dtab[aria-selected="true"]', root) || {}).dataset?.pane || 'edit';

  function markDirty() {
    const dirty = isDirty();
    $('#d-dirty', root).hidden = !dirty;
    $('#detail-save', root).disabled = !dirty;
    $('#detail-revert-edits', root).disabled = !dirty;
  }

  function fill() {
    const c = draft;
    $('#d-id', root).textContent = c.case_id;
    $('#d-status', root).innerHTML = `<span class="pill st-${current.status}">${NS.STATUS_LABEL[current.status]}</span>`;
    $('#d-rev', root).textContent = `rev ${current.rev}`;
    $('#detail-feature', root).value = c.feature;
    $('#d-path', root).textContent = [c.sheet, ...c.path.filter(Boolean)].join(' › ');
    $('#detail-priority', root).value = c.priority;
    $('#detail-auto', root).value = c.auto;
    $('#detail-result', root).value = c.execution_result;
    $('#detail-status', root).value = c.status;
    $('#detail-precondition', root).value = c.precondition;
    $('#detail-expected', root).value = c.expected;
    $('#detail-note', root).value = c.note;
    const vague = /정상\s*동작|정상적으로\s*노출/.test(c.expected);
    $('#d-exp-help', root).textContent = vague ? '모호한 표현이 있습니다. 화면에 보이는 결과를 구체적으로 적어 주세요.' : '';
    $('#d-exp-help', root).className = 'help' + (vague ? ' err' : '');
    renderSteps();
    renderBullets();
    $('#d-refs', root).innerHTML = c.source_refs.map((r) => `<span class="src-ref">${esc(r)}</span>`).join('');
    $('#d-checks', root).innerHTML = (current.issues.length ? current.issues : [{ level: 'ok', message: '문제 없음' }])
      .map((i) => `<li><span class="${i.level === 'error' ? 'bad' : i.level === 'warning' ? 'wr' : 'ok'}">${i.level === 'error' ? '✕' : i.level === 'warning' ? '!' : '✓'}</span>${esc(i.message)}</li>`).join('');
    $('#d-source', root).innerHTML = `<div class="excerpt"><h5>출처</h5>${c.source_refs.map((r) => `<div class="mono" style="font-size:11px">${esc(r)}</div>`).join('')}
      <p class="faint" style="margin:8px 0 0">문서 원문 하이라이트는 문서 기반 생성(Phase 2)부터 표시됩니다. 엑셀에서 온 케이스는 가져온 파일·시트·행을 보여줍니다.</p></div>`;
    loadHistory();
    markDirty();
  }

  function renderSteps() {
    $('#d-steps', root).innerHTML = draft.steps.map((t, i) => `<li class="step" draggable="true" data-i="${i}">
      <span class="drag" data-id="detail-step-drag" aria-hidden="true">⋮⋮</span><span class="idx">${i + 1}.</span>
      <input value="${esc(t)}" data-id="detail-step-input" aria-label="Step ${i + 1}">
      <button class="icon-btn" data-id="detail-step-remove" aria-label="Step ${i + 1} 삭제">✕</button></li>`).join('');
    let from = null;
    $$('#d-steps .step', root).forEach((li) => {
      const i = +li.dataset.i;
      const input = $('input', li);
      input.addEventListener('input', () => { draft.steps[i] = input.value; markDirty(); });
      input.addEventListener('keydown', (e) => {
        if (e.altKey && (e.key === 'ArrowUp' || e.key === 'ArrowDown')) {
          e.preventDefault();
          const j = i + (e.key === 'ArrowUp' ? -1 : 1);
          if (j < 0 || j >= draft.steps.length) return;
          [draft.steps[i], draft.steps[j]] = [draft.steps[j], draft.steps[i]];
          renderSteps(); markDirty();
          $$('#d-steps input', root)[j].focus();
        }
        if (e.key === 'Enter') {
          e.preventDefault();
          draft.steps.splice(i + 1, 0, '');
          renderSteps(); markDirty();
          $$('#d-steps input', root)[i + 1].focus();
        }
      });
      $('[data-id="detail-step-remove"]', li).addEventListener('click', () => { draft.steps.splice(i, 1); renderSteps(); markDirty(); });
      li.addEventListener('dragstart', () => { from = i; li.classList.add('dragging'); });
      li.addEventListener('dragend', () => li.classList.remove('dragging'));
      li.addEventListener('dragover', (e) => { e.preventDefault(); li.classList.add('over'); });
      li.addEventListener('dragleave', () => li.classList.remove('over'));
      li.addEventListener('drop', (e) => {
        e.preventDefault();
        const [moved] = draft.steps.splice(from, 1);
        draft.steps.splice(i, 0, moved);
        renderSteps(); markDirty();
      });
    });
  }

  function renderBullets() {
    $('#d-bullets', root).innerHTML = draft.bullets.map((b, i) => `<div class="bullet" data-i="${i}">
      <button class="vtoggle tag ${b.verified ? 'ok' : 'warn'}" data-id="detail-bullet-verify" title="${b.verified ? 'Figma·실서비스에서 확인한 문구' : 'PRD에만 있는 문구. md 내보내기에서 제외됩니다'}">${b.verified ? '확인' : '추정'}</button>
      <input value="${esc(b.text)}" data-id="detail-bullet-input" aria-label="UI 문구 ${i + 1}">
      <button class="icon-btn" data-id="detail-bullet-remove" aria-label="문구 삭제">✕</button></div>`).join('')
      || '<span class="help">UI 문구가 없습니다</span>';
    $$('#d-bullets .bullet', root).forEach((el) => {
      const i = +el.dataset.i;
      $('[data-id="detail-bullet-verify"]', el).addEventListener('click', () => { draft.bullets[i].verified = !draft.bullets[i].verified; renderBullets(); markDirty(); });
      $('input', el).addEventListener('input', (e) => { draft.bullets[i].text = e.target.value; markDirty(); });
      $('[data-id="detail-bullet-remove"]', el).addEventListener('click', () => { draft.bullets.splice(i, 1); renderBullets(); markDirty(); });
    });
  }

  async function loadHistory() {
    const caseId = draft.case_id;
    const { history } = await api.history(state.suite, caseId);
    if (!draft || draft.case_id !== caseId) return;
    const fmt = (v) => esc(typeof v === 'string' ? v : JSON.stringify(v));
    $('#d-hist', root).innerHTML = history.map((e) => `<li><span class="when">${esc(e.at.replace('T', ' ').slice(5, 16))}</span>
      <div><b>${esc(e.kind === 'edit' ? e.field : e.kind)}</b> · <span class="faint">${esc(e.actor)}</span>
        ${e.kind === 'edit' ? `<div class="diff"><del>${fmt(e.before) || '—'}</del> <ins>${fmt(e.after) || '—'}</ins></div>` : ''}</div>
      ${e.kind === 'edit' ? `<button class="btn-sm" data-id="detail-history-revert" data-h="${e.history_id}">되돌리기</button>` : '<span></span>'}</li>`).join('')
      || '<li class="faint">이력이 없습니다</li>';
    $$('[data-id="detail-history-revert"]', root).forEach((b) => b.addEventListener('click', async () => {
      try {
        await api.revert(state.suite, caseId, b.dataset.h, current.rev);
        toast('이전 값으로 되돌렸습니다. 되돌린 것도 이력에 남습니다.', 'ok');
        await NS.library.reloadList();
        await open(caseId, 'history');
      } catch (err) {
        toast(err.status === 409 ? '다른 곳에서 먼저 바뀌었습니다. 최신 값을 불러온 뒤 다시 시도하세요.' : esc(err.message), 'err');
      }
    }));
  }

  function selectTab(p) {
    $$('.dtab', root).forEach((t) => t.setAttribute('aria-selected', t.dataset.pane === p));
    $$('.dpane', root).forEach((d) => d.classList.toggle('active', d.dataset.pane === p));
  }

  async function saveDetail() {
    if (draft.steps.some((s) => !s.trim())) { toast('빈 Step이 있습니다. 내용을 쓰거나 지우고 저장하세요.', 'err'); return; }
    const changes = {};
    Object.entries(pick(draft)).forEach(([k, v]) => {
      if (JSON.stringify(v) !== JSON.stringify(current[k])) changes[k] = v;
    });
    const btn = $('#detail-save', root);
    btn.classList.add('loading');
    btn.disabled = true;
    try {
      const { case: saved } = await api.patchCase(state.suite, current.case_id, current.rev, changes);
      toast(`${saved.case_id} 저장됨 · rev ${saved.rev}`, 'ok', [], 1800);
      current = null;
      await NS.library.refresh();
      await open(saved.case_id);
    } catch (err) {
      btn.disabled = false;
      if (err.status === 409) {
        toast(`<b>${current.case_id}</b>를 저장하지 못했습니다. 다른 곳에서 먼저 바뀌었습니다 (내 rev ${current.rev}, 서버 rev ${err.data.server_case.rev}). 변경 내용은 그대로 남아 있습니다.`, 'err', [
          { id: 'toast-conflict-compare', label: '차이 비교', fn: () => selectTab('history') },
          { id: 'toast-conflict-reload', label: '최신 값 불러오기', fn: () => open(current.case_id) },
        ], 0);
      } else {
        toast(`저장 실패: ${esc(err.message)}`, 'err');
      }
    } finally {
      btn.classList.remove('loading');
    }
  }

  function mount(r) {
    root = r;
    const bindField = (sel, field) => $(sel, root).addEventListener('input', (e) => { if (draft) { draft[field] = e.target.value; markDirty(); } });
    bindField('#detail-feature', 'feature');
    bindField('#detail-precondition', 'precondition');
    bindField('#detail-expected', 'expected');
    bindField('#detail-note', 'note');
    [['#detail-priority', 'priority'], ['#detail-auto', 'auto'], ['#detail-result', 'execution_result'], ['#detail-status', 'status']]
      .forEach(([sel, field]) => $(sel, root).addEventListener('change', (e) => { draft[field] = e.target.value; markDirty(); }));
    $('#detail-step-add', root).addEventListener('click', () => {
      draft.steps.push(''); renderSteps(); markDirty();
      $$('#d-steps input', root).at(-1).focus();
    });
    $('#detail-bullet-add', root).addEventListener('click', () => {
      draft.bullets.push({ text: '', verified: false }); renderBullets(); markDirty();
      $$('#d-bullets input', root).at(-1).focus();
    });
    $$('.dtab', root).forEach((t) => t.addEventListener('click', () => selectTab(t.dataset.pane)));
    $('#detail-close', root).addEventListener('click', close);
    $('#detail-revert-edits', root).addEventListener('click', () => { draft = JSON.parse(JSON.stringify(current)); fill(); });
    $('#detail-save', root).addEventListener('click', saveDetail);
    $('#detail-move', root).addEventListener('click', () => NS.library.openMove([state.activeId]));
    $('#detail-delete', root).addEventListener('click', () => NS.library.askDelete([state.activeId]));
    $('#detail-duplicate', root).addEventListener('click', async () => {
      const { case: dup } = await api.duplicate(state.suite, state.activeId);
      toast(`${state.activeId}를 복제했습니다 → ${dup.case_id} (초안)`, 'ok');
      await NS.library.refresh();
      await open(dup.case_id);
    });
    document.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 's' && state.screen === 'library' && state.activeId) {
        e.preventDefault();
        if (!$('#detail-save', root).disabled) saveDetail();
      }
    });
  }
})(window.TCS_NS = window.TCS_NS || {});
```

- [ ] **Step 7: 라이브러리 화면** — `agents/dashboard/static/js/tc-studio/library.js`

목업의 `renderTree`·`renderGrid`·`bindGrid`·`commitCell`·`saveField`·`updateBulk`·`bulk`·`askDelete`를 API 호출로 바꿔 옮긴 것이다. 목업과 다른 점:
- 목업의 메모리 배열(`cases`, `TREE`) 대신 `GET …/tree`와 `GET …?필터`를 쓴다. 필터·검색은 서버가 한다(검색은 250ms 디바운스).
- `saveField`의 가짜 지연·충돌 모드 대신 `PATCH`를 쓴다. 409면 `toast-conflict-compare`·`toast-conflict-reload` 버튼이 있는 토스트를 띄운다.
- 그리드 No.는 현재 목록 순번이다. 엑셀 행 번호는 내보낼 때 수식으로 다시 매긴다.
- 삭제는 소프트 삭제이고, 토스트의 되돌리기가 `restore`를 부른다.
- 목업의 "재검토 필요" 필터 칩·소스 변경 배너는 Phase 3에서 붙인다.

```javascript
// TC 스튜디오 — 라이브러리 화면: 트리·필터·그리드·셀 편집·일괄 편집 (목업 1번 화면, PRD F5.1~F5.4)
(function (NS) {
  'use strict';

  const { state, api, esc, $, $$, toast } = NS;
  const open = new Set();          // 펼친 트리 가지 (path.join('\u0001'))
  let root = null;

  const opt = (v, label, cur) => `<option value="${esc(v)}" ${v === cur ? 'selected' : ''}>${esc(label)}</option>`;

  NS.library = { html, mount, refresh, reloadList };

  function html() {
    return `
  <section class="screen active" id="screen-library" data-screen="library">
    <div class="lib no-detail" id="lib">
      <aside class="tree-pane" aria-label="계층 트리">
        <div class="tree-tools">
          <input class="input" id="tree-search" data-id="tree-search" placeholder="가지 이름 검색" autocomplete="off">
          <div class="row" style="justify-content:space-between">
            <span class="faint" style="font-size:11px">시트 › 대분류 › 중분류 › 소분류 › 기능</span>
            <button class="icon-btn" data-id="tree-collapse-all" id="tree-collapse-all" title="모두 접기" aria-label="모두 접기">⊟</button>
          </div>
        </div>
        <ul class="tree" id="tree" data-id="lib-tree" role="tree"></ul>
        <div class="tree-legend"><span><i class="dot d-draft"></i>초안</span><span><i class="dot d-review"></i>재검토</span><span><i class="dot d-err"></i>검증 오류</span></div>
      </aside>
      <div class="center">
        <div class="filterbar" role="search">
          <div class="search"><input class="input" id="lib-search" data-id="lib-search" placeholder="기능, Step, Expected, UI 문구 검색  ( / )" autocomplete="off"></div>
          <select class="fselect" id="lib-filter-result" data-id="lib-filter-result" aria-label="실행 결과">
            ${opt('', '실행 결과 전체')}${opt('none', '미실행')}${opt('pass', 'Pass')}${opt('fail', 'Fail')}${opt('not_test', 'Not Test')}${opt('na', 'N/A')}</select>
          <select class="fselect" id="lib-filter-status" data-id="lib-filter-status" aria-label="검토 상태">
            ${opt('', '검토 상태 전체')}${Object.entries(NS.STATUS_LABEL).map(([v, l]) => opt(v, l)).join('')}</select>
          <select class="fselect" id="lib-filter-priority" data-id="lib-filter-priority" aria-label="우선순위">
            ${opt('', '우선순위 전체')}${NS.PRIORITIES.map((p) => opt(p, p)).join('')}${opt('-', '미지정')}</select>
          <select class="fselect" id="lib-filter-auto" data-id="lib-filter-auto" aria-label="AUTO">
            ${opt('', 'AUTO 전체')}${NS.AUTO_VALUES.map((a) => opt(a, a)).join('')}${opt('-', '미지정')}</select>
          <select class="fselect" id="lib-filter-source" data-id="lib-filter-source" aria-label="출처">
            ${opt('', '출처 전체')}${opt('xlsx', '엑셀 가져오기')}${opt('conf', 'Confluence')}${opt('figma', 'Figma')}${opt('file', '파일·붙여넣기')}</select>
          <button class="fchip" data-id="lib-filter-invalid" id="lib-filter-invalid" aria-pressed="false">검증 오류 <span class="n" id="n-invalid">0</span></button>
          <button class="btn-sm" data-id="lib-filter-reset" id="lib-filter-reset">초기화</button>
        </div>
        <div class="grid-meta">
          <span class="crumbpath" id="grid-crumb"></span>
          <span id="grid-count" class="num"></span>
          <span class="spacer"></span>
          <span class="faint">더블클릭 또는 Enter로 셀 편집 · <span class="kbd">⌘</span><span class="kbd">↵</span> 저장 · <span class="kbd">Esc</span> 취소</span>
          <button class="btn btn-primary" data-id="btn-add-case" id="btn-add-case">+ 케이스 추가</button>
        </div>
        <div class="grid-wrap" id="grid-wrap">
          <table class="grid" id="grid" data-id="lib-grid" aria-label="케이스 그리드">
            <colgroup><col style="width:34px"><col style="width:20px"><col style="width:44px"><col style="width:110px"><col style="width:88px"><col style="width:120px"><col style="width:80px"><col style="width:130px"><col style="width:170px"><col style="width:200px"><col style="width:260px"><col style="width:74px"><col style="width:150px"></colgroup>
            <thead><tr>
              <th><input type="checkbox" id="grid-check-all" data-id="grid-check-all" aria-label="전체 선택"></th>
              <th></th><th><span class="xl">A</span>No.</th><th>실행 결과</th>
              <th><span class="xl">B</span>대분류</th><th><span class="xl">C</span>중분류</th><th><span class="xl">D</span>소분류</th>
              <th><span class="xl">E</span>기능</th><th><span class="xl">F</span>사전 조건</th><th><span class="xl">G</span>Test Step</th>
              <th><span class="xl">H</span>Expected Result</th><th><span class="xl">I</span>우선순위</th><th><span class="xl">M</span>기타 (id · src)</th>
            </tr></thead>
            <tbody id="grid-body"></tbody>
          </table>
        </div>
        <div class="bulkbar" id="bulkbar" data-id="bulk-bar" hidden>
          <b><span id="bulk-n">0</span>건 선택</b>
          <select class="chip-select" data-id="bulk-priority" id="bulk-priority">${opt('', '우선순위…')}${NS.PRIORITIES.map((p) => opt(p, p)).join('')}</select>
          <select class="chip-select" data-id="bulk-auto" id="bulk-auto">${opt('', 'AUTO…')}${NS.AUTO_VALUES.map((a) => opt(a, a)).join('')}</select>
          <select class="chip-select" data-id="bulk-result" id="bulk-result">${opt('', '실행 결과…')}${opt('none', '미실행')}${opt('pass', 'Pass')}${opt('fail', 'Fail')}${opt('not_test', 'Not Test')}${opt('na', 'N/A')}</select>
          <select class="chip-select" data-id="bulk-status" id="bulk-status">${opt('', '검토 상태…')}${opt('approved', '승인')}${opt('draft', '초안으로')}${opt('rejected', '반려')}</select>
          <button class="btn-sm" data-id="bulk-move" id="bulk-move">계층 이동…</button>
          <button class="btn-sm" data-id="bulk-duplicate" id="bulk-duplicate">복제</button>
          <button class="btn btn-danger" data-id="bulk-delete" id="bulk-delete" style="padding:4px 10px;font-size:11px">삭제</button>
          <span class="spacer"></span>
          <button class="icon-btn" data-id="bulk-clear" id="bulk-clear" aria-label="선택 해제">✕</button>
        </div>
        <div id="lib-empty" hidden>
          <div class="empty" data-id="lib-empty">
            <div class="xl-icon">X</div>
            <h3>라이브러리가 비어 있습니다</h3>
            <p>기존 Full TC 엑셀을 가져오면 시트별 계층 트리와 케이스가 한 번에 들어옵니다. 가져온 케이스는 모두 승인 상태로 시작합니다.</p>
            ${NS.importModal ? '<div class="row" style="justify-content:center"><button class="btn btn-primary" data-id="empty-import-xlsx" id="empty-import-xlsx">엑셀 가져오기</button></div>' : ''}
            <p class="faint" style="font-size:11px">.xlsx · 헤더 행은 자동으로 찾습니다 · 원본 파일은 수정하지 않습니다</p>
          </div>
        </div>
      </div>
      ${NS.detail.html()}
    </div>
  </section>
  <div class="scrim" id="move-modal" data-id="move-modal" hidden>
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="mv-title" style="width:min(440px,100%)">
      <div class="panel-head"><span id="mv-title">계층 이동</span><span class="spacer"></span><button class="icon-btn" data-id="move-close" id="move-close" aria-label="닫기">✕</button></div>
      <div class="panel-body" style="display:grid;gap:10px">
        <div class="field"><span class="label">시트 › 대분류 › 중분류 › 소분류</span><select class="select" id="move-target" data-id="move-target"></select></div>
        <div class="field"><span class="label">기능</span><input class="input" id="move-feature" data-id="move-feature" placeholder="비워 두면 기존 기능명 유지"></div>
        <div class="row"><span class="spacer"></span><button class="btn btn-ghost" id="move-cancel" data-id="move-cancel">취소</button><button class="btn btn-primary" id="move-confirm" data-id="move-confirm">이동</button></div>
      </div>
    </div>
  </div>
  <div class="scrim" id="confirm-modal" data-id="confirm-modal" hidden>
    <div class="modal" role="alertdialog" aria-modal="true" style="width:min(400px,100%)">
      <div class="panel-body" style="display:grid;gap:12px">
        <b id="cf-title"></b>
        <span class="muted">삭제한 케이스는 되돌리기로 복원할 수 있습니다. 엑셀 다음 내보내기부터 빠집니다.</span>
        <div class="row"><span class="spacer"></span><button class="btn btn-ghost" id="cf-cancel" data-id="confirm-cancel">취소</button><button class="btn btn-danger" id="cf-ok" data-id="confirm-ok" style="background:var(--err);color:#fff">삭제</button></div>
      </div>
    </div>
  </div>`;
  }

  // ── 데이터 ───────────────────────────────────────────────────
  async function refresh() {
    const empty = !state.suite;
    $('#lib-empty', root).hidden = !empty;
    ['.filterbar', '.grid-meta', '#grid-wrap', '.tree-tools', '#tree'].forEach((s) => { $(s, root).hidden = empty; });
    if (empty) { state.items = []; state.tree = []; return; }
    const { tree } = await api.tree(state.suite);
    state.tree = tree;
    if (!open.size) tree.forEach((n) => { open.add(key(n.path)); (n.children || []).forEach((c) => open.add(key(c.path))); });
    renderTree();
    await reloadList();
  }

  async function reloadList() {
    const { items, total } = await api.list(state.suite, { ...NS.queryFromFilters(state.filters), limit: 1000 });
    state.items = items;
    state.total = total;
    state.selected.forEach((id) => { if (!items.some((c) => c.case_id === id)) state.selected.delete(id); });
    renderGrid();
    NS.detail.refreshIfOpen();
  }

  const key = (path) => path.join('\u0001');
  const byId = (id) => state.items.find((c) => c.case_id === id);

  // ── 트리 (목업 renderTree 이식) ──────────────────────────────
  const LV = { sheet: 'S', l1: '대', l2: '중', l3: '소', feature: '기' };
  function renderTree() {
    const q = $('#tree-search', root).value.trim();
    const matches = (n) => !q || n.name.includes(q) || (n.children || []).some(matches);
    const node = (n) => {
      if (!matches(n)) return '';
      const has = n.children && n.children.length;
      const isOpen = has && (open.has(key(n.path)) || !!q);
      const sel = state.filters.path === n.path.join('/');
      const dots = `<span class="dots">${n.draft ? `<i class="dot d-draft" title="초안 ${n.draft}"></i>` : ''}${n.needs_review ? '<i class="dot d-review"></i>' : ''}${n.invalid ? `<i class="dot d-err" title="검증 오류 ${n.invalid}"></i>` : ''}</span>`;
      return `<li role="treeitem" aria-expanded="${has ? !!isOpen : ''}">
        <div class="tnode ${isOpen ? 'open' : ''} ${sel ? 'sel' : ''}" data-id="tree-node" tabindex="0" data-path="${esc(n.path.join('/'))}" data-level="${n.level}" data-name="${esc(n.name)}">
          <span class="caret">${has ? '▶' : ''}</span><span class="lvl">${LV[n.level]}</span><span class="nm">${esc(n.name)}</span>${dots}<span class="ct num">${n.count}</span>
        </div>${has && isOpen ? `<ul role="group">${n.children.map(node).join('')}</ul>` : ''}</li>`;
    };
    $('#tree', root).innerHTML = state.tree.map(node).join('');
    $$('#tree .tnode', root).forEach((el) => {
      el.addEventListener('click', () => {
        const path = el.dataset.path.split('/');
        const k = key(path);
        if (open.has(k)) open.delete(k); else open.add(k);
        state.filters.path = state.filters.path === el.dataset.path ? '' : el.dataset.path;
        renderTree();
        reloadList();
      });
      el.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); el.click(); } });
      el.addEventListener('dragover', (e) => { e.preventDefault(); el.classList.add('drop'); });
      el.addEventListener('dragleave', () => el.classList.remove('drop'));
      el.addEventListener('drop', (e) => {
        e.preventDefault();
        el.classList.remove('drop');
        const id = e.dataTransfer.getData('text/case');
        const target = el.dataset.path.split('/');
        // 기능 가지에 떨어뜨리면 그 기능의 부모 가지로 옮기고 기능명은 유지한다
        const parent = el.dataset.level === 'feature' ? target.slice(0, -1) : target;
        if (id && parent.length >= 2) moveCases([id], parent, '');
      });
    });
  }

  // ── 그리드 (목업 renderGrid·bindGrid 이식) ────────────────────
  function resultSelect(c) {
    const v = c.execution_result || '';
    return `<select class="chip-select result-${v ? v.replace('_', '-') : 'none'}" data-id="grid-result" aria-label="${c.case_id} 실행 결과">${
      Object.entries(NS.RESULT_LABEL).map(([k, l]) => opt(k, l, v)).join('')}</select>`;
  }
  function prioritySelect(c) {
    const cls = c.priority ? c.priority.toLowerCase() : 'is-unset';  // 'empty'는 빈 화면 .empty와 충돌
    return `<select class="chip-select ${cls}" data-id="grid-cell-priority" aria-label="${c.case_id} 우선순위">${
      ['', ...NS.PRIORITIES].map((p) => opt(p, p || '—', c.priority)).join('')}</select>`;
  }
  function expHtml(c) {
    return esc(c.expected) + c.bullets.map((b) =>
      `\n<span class="blt ${b.verified ? '' : 'est'}">- ${esc(b.text)}${b.verified ? '' : ' (추정)'}</span>`).join('');
  }
  function renderGrid() {
    let prev = null;
    $('#grid-body', root).innerHTML = state.items.map((c, i) => {
      const hier = [0, 1, 2].map((d) => {
        const rep = prev && prev.sheet === c.sheet && prev.path.slice(0, d + 1).join('/') === c.path.slice(0, d + 1).join('/') && c.path[d];
        return `<td class="${rep ? 'rep' : ''}"><span>${esc(c.path[d])}</span></td>`;
      }).join('');
      const errors = c.issues.filter((x) => x.level === 'error');
      prev = c;
      return `<tr data-case="${c.case_id}" class="${state.selected.has(c.case_id) ? 'sel' : ''} ${state.activeId === c.case_id ? 'active' : ''}">
        <td><input type="checkbox" data-id="grid-row-check" aria-label="${c.case_id} 선택" ${state.selected.has(c.case_id) ? 'checked' : ''}></td>
        <td><span class="drag" draggable="true" data-id="grid-row-drag" title="트리로 끌어 계층 이동">⋮⋮</span></td>
        <td class="no">${i + 1}</td>
        <td>${resultSelect(c)}</td>${hier}
        <td><div class="cell" data-edit="feature" data-id="grid-cell-feature" tabindex="0">${esc(c.feature)}</div></td>
        <td><div class="cell" data-edit="precondition" data-id="grid-cell-precondition" tabindex="0">${esc(c.precondition)}</div></td>
        <td><div class="cell" data-edit="steps" data-id="grid-cell-steps" tabindex="0">${esc(c.steps.map((s, n) => `${n + 1}. ${s}`).join('\n'))}</div></td>
        <td><div class="cell" data-edit="expected" data-id="grid-cell-expected" tabindex="0">${expHtml(c)}</div>${errors.length ? `<span class="vbadge tag err" title="${esc(errors.map((x) => x.message).join(', '))}">검증 오류 ${errors.length}</span>` : ''}${c.bullets.some((b) => !b.verified) ? ' <span class="vbadge tag warn">추정 문구</span>' : ''}</td>
        <td>${prioritySelect(c)}</td>
        <td><div class="etc"><span>id:${c.case_id}</span>${c.status !== 'approved' ? `<span class="pill st-${c.status}" data-id="grid-status-chip">${NS.STATUS_LABEL[c.status]}</span>` : ''}${c.note ? `<span>${esc(c.note)}</span>` : ''}</div></td>
      </tr>`;
    }).join('') || `<tr><td colspan="13" style="text-align:center;padding:40px;color:var(--text3)" data-id="grid-empty-filter">조건에 맞는 케이스가 없습니다.</td></tr>`;
    $('#grid-crumb', root).textContent = state.filters.path.replaceAll('/', ' › ') || state.suite;
    $('#grid-count', root).textContent = `${state.total}건`;
    $('#n-invalid', root).textContent = state.items.filter((c) => c.has_error).length;
    bindGrid();
    updateBulk();
  }

  function bindGrid() {
    $$('#grid-body tr[data-case]', root).forEach((tr) => {
      const id = tr.dataset.case;
      $('[data-id="grid-row-check"]', tr).addEventListener('change', (e) => {
        if (e.target.checked) state.selected.add(id); else state.selected.delete(id);
        tr.classList.toggle('sel', e.target.checked);
        updateBulk();
      });
      tr.addEventListener('click', (e) => {
        if (e.target.closest('input,select,.cell[contenteditable="true"],.drag')) return;
        NS.detail.open(id);
      });
      $('.drag', tr).addEventListener('dragstart', (e) => e.dataTransfer.setData('text/case', id));
      $('[data-id="grid-cell-priority"]', tr).addEventListener('change', (e) => save(id, { priority: e.target.value }));
      $('[data-id="grid-result"]', tr).addEventListener('change', (e) => save(id, { execution_result: e.target.value }));
    });
    $$('#grid-body .cell[data-edit]', root).forEach((cell) => {
      const start = () => {
        if (cell.isContentEditable) return;
        cell.dataset.orig = cell.innerText;
        cell.contentEditable = 'true';
        cell.focus();
      };
      cell.addEventListener('dblclick', start);
      cell.addEventListener('keydown', (e) => {
        if (!cell.isContentEditable) { if (e.key === 'Enter') { e.preventDefault(); start(); } return; }
        if (e.key === 'Escape') { cell.innerText = cell.dataset.orig; cell.contentEditable = 'false'; cell.classList.remove('bad'); }
        if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) { e.preventDefault(); commitCell(cell); }
      });
      cell.addEventListener('blur', () => { if (cell.isContentEditable) commitCell(cell); });
    });
  }

  function commitCell(cell) {
    const id = cell.closest('tr').dataset.case;
    const field = cell.dataset.edit;
    const value = cell.innerText.trim();
    cell.contentEditable = 'false';
    if (value === (cell.dataset.orig || '').trim()) return;
    if (field === 'steps') {
      const lines = value.split('\n').filter(Boolean);
      if (!lines.every((l) => /^\d+\.\s/.test(l))) {
        cell.classList.add('bad');
        toast('Test Step은 줄마다 "1. …" 형식이어야 합니다. 번호를 붙여 다시 저장하세요.', 'err');
        return;
      }
      cell.classList.remove('bad');
      save(id, { steps: lines.map((l) => l.replace(/^\d+\.\s*/, '')) }, cell);
      return;
    }
    if (field === 'expected') {
      const [head, ...rest] = value.split('\n');
      const bullets = rest.filter((x) => x.startsWith('-')).map((x) => ({
        text: x.replace(/^-\s*/, '').replace(/ \(추정\)$/, ''), verified: !x.includes('(추정)') }));
      save(id, { expected: head, bullets }, cell);
      return;
    }
    save(id, { [field]: value }, cell);
  }

  // 목업 saveField 대체: PATCH + 409 충돌 토스트 (명세 1.2 / F5.2)
  async function save(id, changes, el) {
    const c = byId(id);
    if (!c) return;
    if (el) el.classList.add('saving');
    try {
      const { case: updated } = await api.patchCase(state.suite, id, c.rev, changes);
      Object.assign(c, updated);
      toast(`${id} 저장됨 · rev ${updated.rev}`, 'ok', [], 1800);
      await refreshTreeOnly();
      renderGrid();
      NS.detail.refreshIfOpen();
    } catch (err) {
      if (err.status !== 409) { toast(`${id} 저장 실패: ${esc(err.message)}`, 'err'); return; }
      toast(`<b>${id}</b>를 저장하지 못했습니다. 다른 곳에서 먼저 바뀌었습니다 (내 rev ${c.rev}, 서버 rev ${err.data.server_case.rev}). 변경 내용은 그대로 남아 있습니다.`, 'err', [
        { id: 'toast-conflict-compare', label: '차이 비교', fn: () => NS.detail.open(id, 'history') },
        { id: 'toast-conflict-reload', label: '최신 값 불러오기', fn: () => reloadList() },
      ], 0);
    } finally {
      if (el) el.classList.remove('saving');
    }
  }
  NS.library.save = save;

  async function refreshTreeOnly() {
    state.tree = (await api.tree(state.suite)).tree;
    renderTree();
  }

  // ── 일괄 편집 (목업 updateBulk·bulk 이식) ─────────────────────
  function updateBulk() {
    const n = state.selected.size;
    $('#bulkbar', root).hidden = n < 1;
    $('#bulk-n', root).textContent = n;
    $('#grid-check-all', root).checked = n > 0 && state.items.every((c) => state.selected.has(c.case_id));
  }
  const selectedItems = () => state.items.filter((c) => state.selected.has(c.case_id))
    .map((c) => ({ case_id: c.case_id, rev: c.rev }));

  async function bulkSet(field, value, label) {
    const res = await api.bulk(state.suite, selectedItems(), 'set', field, value);
    const skipped = res.conflicts.length ? ` · ${res.conflicts.length}건은 다른 곳에서 바뀌어 건너뜀` : '';
    toast(`${res.updated.length}건의 ${label}을(를) 바꿨습니다${skipped}`, res.conflicts.length ? 'warn' : 'ok');
    await refresh();
  }

  function askDelete(ids) {
    $('#cf-title', root).textContent = `케이스 ${ids.length}건을 삭제할까요?`;
    $('#confirm-modal', root).hidden = false;
    $('#cf-ok', root).onclick = async () => {
      $('#confirm-modal', root).hidden = true;
      const items = state.items.filter((c) => ids.includes(c.case_id)).map((c) => ({ case_id: c.case_id, rev: c.rev }));
      const res = await api.bulk(state.suite, items, 'delete');
      ids.forEach((id) => state.selected.delete(id));
      if (ids.includes(state.activeId)) NS.detail.close();
      toast(`${res.deleted.length}건을 삭제했습니다.`, 'ok', [{
        id: 'delete-undo', label: '되돌리기',
        fn: async () => { for (const id of res.deleted) await api.restore(state.suite, id); await refresh(); },
      }]);
      await refresh();
    };
  }
  NS.library.askDelete = askDelete;

  function openMove(ids) {
    const targets = [];
    const walk = (nodes) => nodes.forEach((n) => {
      if (n.level !== 'feature') { targets.push(n.path); walk(n.children || []); }
    });
    walk(state.tree);
    $('#move-target', root).innerHTML = targets.filter((p) => p.length >= 2)
      .map((p) => `<option value="${esc(p.join('/'))}">${esc(p.join(' › '))}</option>`).join('');
    $('#move-feature', root).value = '';
    $('#move-modal', root).hidden = false;
    $('#move-confirm', root).onclick = async () => {
      $('#move-modal', root).hidden = true;
      await moveCases(ids, $('#move-target', root).value.split('/'), $('#move-feature', root).value.trim());
    };
  }
  NS.library.openMove = openMove;

  async function moveCases(ids, target, feature) {
    const items = state.items.filter((c) => ids.includes(c.case_id)).map((c) => ({ case_id: c.case_id, rev: c.rev }));
    const [sheet, ...path] = target;
    const res = await api.move(state.suite, items, sheet, path.slice(0, 3), feature || undefined);
    toast(`${res.moved.length}건을 ${esc(target.join(' › '))}(으)로 옮겼습니다.`, res.conflicts.length ? 'warn' : 'ok');
    await refresh();
  }

  async function addCase() {
    const base = byId(state.activeId) || state.items[0];
    const fields = base
      ? { sheet: base.sheet, path: base.path, feature: '새 기능', after: base.case_id }
      : { feature: '새 기능' };
    const { case: created } = await api.createCase(state.suite, fields);
    await refresh();
    NS.detail.open(created.case_id);
  }

  // ── 이벤트 연결 ──────────────────────────────────────────────
  function mount(r) {
    root = r;
    const onFilter = (id, k, map = (v) => v) => $(id, root).addEventListener('change', (e) => {
      state.filters[k] = map(e.target.value);
      reloadList();
    });
    onFilter('#lib-filter-result', 'execution_result');
    onFilter('#lib-filter-status', 'status');
    onFilter('#lib-filter-priority', 'priority');
    onFilter('#lib-filter-auto', 'auto');
    onFilter('#lib-filter-source', 'source');
    let t;
    $('#lib-search', root).addEventListener('input', (e) => {
      clearTimeout(t);
      t = setTimeout(() => { state.filters.q = e.target.value.trim(); reloadList(); }, 250);
    });
    $('#lib-filter-invalid', root).addEventListener('click', (e) => {
      const on = e.currentTarget.getAttribute('aria-pressed') !== 'true';
      e.currentTarget.setAttribute('aria-pressed', on);
      state.filters.invalid = on;
      reloadList();
    });
    $('#lib-filter-reset', root).addEventListener('click', () => {
      Object.keys(state.filters).forEach((k) => { state.filters[k] = k === 'invalid' ? false : ''; });
      $$('.filterbar select', root).forEach((s) => { s.value = ''; });
      $('#lib-search', root).value = '';
      $('#lib-filter-invalid', root).setAttribute('aria-pressed', 'false');
      renderTree();
      reloadList();
    });
    $('#tree-search', root).addEventListener('input', renderTree);
    $('#tree-collapse-all', root).addEventListener('click', () => { open.clear(); renderTree(); });
    $('#grid-check-all', root).addEventListener('change', (e) => {
      state.items.forEach((c) => (e.target.checked ? state.selected.add(c.case_id) : state.selected.delete(c.case_id)));
      renderGrid();
    });
    const bulkSelect = (id, field, label, map = (v) => v) => $(id, root).addEventListener('change', async (e) => {
      const v = e.target.value;
      e.target.value = '';
      if (v) await bulkSet(field, map(v), label);
    });
    bulkSelect('#bulk-priority', 'priority', '우선순위');
    bulkSelect('#bulk-auto', 'auto', 'AUTO');
    bulkSelect('#bulk-result', 'execution_result', '실행 결과', (v) => (v === 'none' ? '' : v));
    bulkSelect('#bulk-status', 'status', '검토 상태');
    $('#bulk-clear', root).addEventListener('click', () => { state.selected.clear(); renderGrid(); });
    $('#bulk-move', root).addEventListener('click', () => openMove([...state.selected]));
    $('#bulk-delete', root).addEventListener('click', () => askDelete([...state.selected]));
    $('#bulk-duplicate', root).addEventListener('click', async () => {
      for (const id of state.selected) await api.duplicate(state.suite, id);
      toast(`${state.selected.size}건을 복제했습니다. 새 case_id가 붙고 초안 상태로 들어갑니다.`, 'ok');
      await refresh();
    });
    ['#move-close', '#move-cancel'].forEach((s) => $(s, root).addEventListener('click', () => { $('#move-modal', root).hidden = true; }));
    $('#cf-cancel', root).addEventListener('click', () => { $('#confirm-modal', root).hidden = true; });
    $('#btn-add-case', root).addEventListener('click', addCase);
    if (NS.importModal) $('#empty-import-xlsx', root).addEventListener('click', () => NS.importModal.open());
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') $$('.scrim', root).forEach((s) => { if (s.id !== 'import-modal') s.hidden = true; });
      if (e.key === '/' && state.screen === 'library' && !e.target.closest('input,textarea,[contenteditable="true"]')) {
        e.preventDefault();
        $('#lib-search', root).focus();
      }
    });
    NS.detail.mount(root);
  }
})(window.TCS_NS = window.TCS_NS || {});
```

- [ ] **Step 8: 진입점** — `agents/dashboard/static/js/tc-studio/main.js`

```javascript
// TC 스튜디오 — 진입점: 셸 렌더, 스위트 선택, 화면 전환. 공개 API: window.TCS.init(selector)
(function (NS) {
  'use strict';

  const { state, api, esc, $, $$ } = NS;
  const SUITE_KEY = 'tcs-suite';
  let root = null;

  function shellHtml() {
    return `
<div class="tc-studio">
 <div class="studio" id="studio">
  <header class="page-header">
    <div class="ph-top">
      <div><div class="crumb">QA CONTROL CENTER › 테스트케이스</div><h1 class="page-title">TC 스튜디오</h1></div>
      <select class="suite-select" id="suite-select" data-id="suite-select" aria-label="스위트 선택"></select>
      <span class="spacer"></span>
      ${NS.importModal ? '<button class="btn btn-ghost" data-id="btn-import-xlsx" id="btn-import-xlsx">엑셀 가져오기</button>' : ''}
    </div>
    <nav class="wizard" role="tablist" aria-label="스튜디오 화면">
      <button class="step-item" role="tab" data-id="nav-tab-library" data-screen="library" aria-selected="true"><span class="step-circle">1</span><span class="step-label">TC 라이브러리</span><span class="step-count num" id="cnt-lib">0</span></button>
      ${NS.exportView ? '<div class="step-line"></div><button class="step-item" role="tab" data-id="nav-tab-export" data-screen="export" aria-selected="false"><span class="step-circle">2</span><span class="step-label">내보내기</span></button>' : ''}
    </nav>
  </header>
  ${NS.library.html()}
  ${NS.exportView ? NS.exportView.html() : ''}
 </div>
 ${NS.importModal ? NS.importModal.html() : ''}
 <div class="toasts" id="tcs-toasts" aria-live="polite"></div>
</div>`;
  }

  function show(screen) {
    state.screen = screen;
    $$('.step-item', root).forEach((b) => b.setAttribute('aria-selected', b.dataset.screen === screen));
    $$('.screen', root).forEach((s) => s.classList.toggle('active', s.dataset.screen === screen));
    if (screen === 'export' && NS.exportView) NS.exportView.onShow();
  }

  function renderSuiteSelect() {
    const sel = $('#suite-select', root);
    sel.innerHTML = state.suites.map((s) => `<option value="${esc(s.suite)}" ${s.suite === state.suite ? 'selected' : ''}>${esc(s.suite)} (${s.count})</option>`).join('')
      || '<option value="">스위트 없음</option>';
    sel.disabled = !state.suites.length;
    const cur = state.suites.find((s) => s.suite === state.suite);
    $('#cnt-lib', root).textContent = cur ? cur.count : 0;
  }

  // 가져오기 후에도 호출된다 (import.js)
  NS.reloadSuites = async function (prefer) {
    state.suites = (await api.suites()).suites;
    let saved = prefer || '';
    if (!saved) { try { saved = localStorage.getItem(SUITE_KEY) || ''; } catch (e) { saved = ''; } }
    state.suite = state.suites.some((s) => s.suite === saved) ? saved : (state.suites[0] ? state.suites[0].suite : '');
    try { if (state.suite) localStorage.setItem(SUITE_KEY, state.suite); } catch (e) { /* 저장 불가 환경 */ }
    renderSuiteSelect();
    state.selected.clear();
    await NS.library.refresh();
  };

  // 화면 이벤트에서 시작한 요청이 실패하면(서버 재시작·네트워크 끊김) 처리되지 않은 오류로 남기지 않고
  // 토스트로 알린다. 스튜디오가 화면에 있을 때만 가로챈다 (다른 대시보드 화면의 오류는 건드리지 않는다).
  window.addEventListener('unhandledrejection', (e) => {
    if (!root || !document.body.contains(root)) return;
    e.preventDefault();
    NS.toast(`요청을 처리하지 못했습니다: ${esc((e.reason && e.reason.message) || e.reason)}`, 'err');
  });

  async function init(selector) {
    root = document.querySelector(selector);
    root.innerHTML = shellHtml();
    NS.library.mount(root);
    // 가져오기(W2)·내보내기(W3) 모듈은 스크립트가 로드된 경우에만 붙는다
    if (NS.importModal) NS.importModal.mount(root);
    if (NS.exportView) NS.exportView.mount(root);
    $$('.step-item', root).forEach((b) => b.addEventListener('click', () => show(b.dataset.screen)));
    if (NS.importModal) $('#btn-import-xlsx', root).addEventListener('click', () => NS.importModal.open());
    $('#suite-select', root).addEventListener('change', (e) => NS.reloadSuites(e.target.value));
    show('library');
    await NS.reloadSuites();
  }

  window.TCS = { init };
})(window.TCS_NS = window.TCS_NS || {});
```

- [ ] **Step 9: index.html 연결**

1. 21행 `import-studio.css` 링크 아래:

```html
  <link rel="stylesheet" href="/static/css/tc-studio.css?v=20260929-1">
```

2. 사이드바 "Import Studio" 항목(`id="tab-import_studio"`의 `</div>`) 바로 아래:

```html
          <div class="sidebar-item" id="tab-tc_studio" onclick="selectView('tc_studio')">
            <div class="sidebar-dot-spacer"></div>
            <span class="sidebar-name">TC 스튜디오</span>
          </div>
```

3. `<script src="/static/js/router.js"></script>` 바로 위:

```html
  <script src="/static/js/tc-studio/api.js?v=20260929-1"></script>
  <script src="/static/js/tc-studio/state.js?v=20260929-1"></script>
  <script src="/static/js/tc-studio/detail.js?v=20260929-1"></script>
  <script src="/static/js/tc-studio/library.js?v=20260929-1"></script>
  <script src="/static/js/tc-studio/main.js?v=20260929-1"></script>
```

- [ ] **Step 10: router.js 연결**

1. `const IMPORT_STUDIO_PATH = '/import-studio';` 아래: `const TC_STUDIO_PATH = '/tc-studio';`
2. `_viewToPath`의 import_studio 줄 아래: `  if (viewId === 'tc_studio') return TC_STUDIO_PATH;`
3. `_pathToView`의 import_studio 줄 아래: `  if (window.location.pathname === TC_STUDIO_PATH) return 'tc_studio';`
4. `renderCurrentView`의 `} else if (currentView === 'team_new') {` 바로 앞:

```javascript
  } else if (currentView === 'tc_studio') {
    main.innerHTML = '<div id="tc-studio-root"></div>';
    if (window.TCS) {
      window.TCS.init('#tc-studio-root').catch(console.error);
    } else {
      main.innerHTML = '<div style="padding:40px;color:var(--text-dim);">TC 스튜디오 로딩 실패 — 페이지를 새로고침하세요.</div>';
    }
```

(`/tc-studio` 경로를 index.html로 돌려주는 서버 쪽 처리는 B8 Step 5에서 이미 했다.)

- [ ] **Step 11: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_studio_e2e.py -q`
Expected: `6 passed`

- [ ] **Step 12: 실제 대시보드에서 눈으로 확인**

Run: `.venv/bin/python agents/dashboard/serve.py` → 브라우저에서 `http://localhost:8766/tc-studio`
확인할 것: 사이드바 "TC 스튜디오" 활성, 빈 라이브러리 화면(아직 가져오기 없음 → 버튼 없이 안내 문구), 콘솔 오류 없음. (가져오기는 W2에서 붙는다. 그 전에 데이터를 보려면 B8 API로 가져온다.)

- [ ] **Step 13: 커밋**

```bash
git add agents/dashboard/tools/scope_tc_studio_css.py agents/dashboard/static/css/tc-studio.css agents/dashboard/static/js/tc-studio agents/dashboard/index.html agents/dashboard/static/js/router.js tests/unit/tc_library/test_tc_studio_e2e.py
git commit -m "feat(tc-studio): W1 스튜디오 셸·라이브러리·상세 패널"
```

---

## Task W2: 엑셀 가져오기 모달

PRD 범위: F2.1~F2.4, F2.6, F6.7

**Files:**
- Create: `agents/dashboard/static/js/tc-studio/import.js`
- Modify: `agents/dashboard/index.html` (`library.js` 스크립트 아래 한 줄)
- Modify: `tests/unit/tc_library/test_tc_studio_e2e.py` (파일 끝에 추가)

**Interfaces:**
- Consumes: `api.importPreview(file)`, `api.importCommit({preview_id, suite, sheets, prefixes})`, `TCS_NS.reloadSuites(suite)`
- Produces: `TCS_NS.importModal.{html, mount, open}` — 로드되면 `main.js`가 헤더 "엑셀 가져오기" 버튼과 빈 화면 버튼을 그린다

동작 (목업 852~887행 모달의 Phase 1 범위):
- 파일 고르기(끌어 놓기 포함) → 확장자·25MB 검사 → 미리보기 API → 시트 목록(행 수·헤더 행) + 시트별 접두어 입력 + 경고
- 스위트 이름 기본값: 지금 스위트가 있으면 그 이름, 없으면 파일명에서 `_Full`을 뗀 값
- 접두어는 영문 대문자로 시작하는 8자 이내(서버 규칙과 같다). 어기면 가져오기 버튼을 막는다
- 목업의 "다른 양식 직접 매핑"(매핑 프로필)은 Phase 2 작업 G0으로 미룬다

- [ ] **Step 1: 실패하는 E2E 테스트 추가** — 파일 끝에:

```python

```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_studio_e2e.py -k import_modal -q`
Expected: FAIL — `empty-import-xlsx` 버튼을 찾지 못함

- [ ] **Step 3: 구현** — `agents/dashboard/static/js/tc-studio/import.js`

```javascript
// TC 스튜디오 — 엑셀 가져오기 모달 (PRD F2.1~F2.4, F2.6, F6.7)
(function (NS) {
  'use strict';

  const { state, api, esc, $, $$, toast } = NS;
  let root = null;
  let preview = null;

  NS.importModal = { html, mount, open };

  function html() {
    return `
  <div class="scrim" id="import-modal" data-id="import-modal" hidden>
    <div class="modal" role="dialog" aria-modal="true" aria-labelledby="im-title">
      <div class="panel-head"><span id="im-title">엑셀을 라이브러리로 가져오기</span><span class="spacer"></span>
        <button class="icon-btn" data-id="import-close" id="import-close" aria-label="닫기">✕</button></div>
      <div class="panel-body" style="display:grid;gap:12px">
        <label class="drop" id="import-drop" data-id="import-pick-file" for="import-file">
          <b>엑셀 파일을 끌어다 놓거나 눌러서 선택</b>
          <span class="faint">.xlsx · 최대 25MB · 헤더 행은 자동으로 찾습니다 · 원본 파일은 수정하지 않습니다</span>
        </label>
        <input type="file" id="import-file" data-id="import-file-input" accept=".xlsx" hidden>
        <div id="import-preview" hidden style="display:grid;gap:12px">
          <div class="field"><span class="label">스위트 이름</span>
            <input class="input" id="import-suite" data-id="import-suite" placeholder="예: 야핏무브" autocomplete="off">
            <span class="help">같은 이름이 있으면 case_id가 같은 케이스를 갱신하고, 없는 케이스는 추가합니다.</span></div>
          <div class="field"><span class="label">가져올 시트 · case_id 접두어</span>
            <div class="radio-list" id="import-sheets" data-id="import-sheets"></div></div>
          <ul class="checks" id="import-warnings" data-id="import-warnings"></ul>
        </div>
        <div class="row"><span class="help" id="import-summary"></span><span class="spacer"></span>
          <button class="btn btn-ghost" data-id="import-cancel" id="import-cancel">취소</button>
          <button class="btn btn-primary" data-id="import-confirm" id="import-confirm" disabled>가져오기</button></div>
      </div>
    </div>
  </div>`;
  }

  function open() {
    preview = null;
    $('#import-preview', root).hidden = true;
    $('#import-confirm', root).disabled = true;
    $('#import-summary', root).textContent = '';
    $('#import-file', root).value = '';
    $('#import-modal', root).hidden = false;
  }

  const closeModal = () => { $('#import-modal', root).hidden = true; };

  async function pick(file) {
    if (!file) return;
    if (!/\.xlsx$/i.test(file.name)) { toast(`${esc(file.name)}: .xlsx 파일만 가져올 수 있습니다.`, 'err'); return; }
    if (file.size > 25 * 1024 * 1024) { toast(`${esc(file.name)}: 25MB를 넘습니다.`, 'err'); return; }
    $('#import-summary', root).textContent = '분석 중…';
    try {
      preview = await api.importPreview(file);
    } catch (err) {
      $('#import-summary', root).textContent = '';
      toast(`엑셀을 분석하지 못했습니다: ${esc(err.message)}`, 'err');
      return;
    }
    $('#import-suite', root).value = state.suite || file.name.replace(/\.xlsx$/i, '').replace(/_?Full$/i, '').replace(/[^\w가-힣-]/g, '_');
    $('#import-sheets', root).innerHTML = preview.sheets.map((s, i) => `
      <label class="radio"><input type="checkbox" data-sheet="${esc(s.name)}" checked> ${esc(s.name)}
        <span class="n">${s.cases}행 · 헤더 ${s.header_row}행</span>
        <input class="input mono" data-prefix="${esc(s.name)}" value="S${String(i + 1).padStart(2, '0')}" maxlength="8" style="width:90px" aria-label="${esc(s.name)} 접두어"></label>`).join('');
    const warnings = preview.sheets.flatMap((s) => s.warnings.map((w) => `${s.name}: ${w}`));
    $('#import-warnings', root).innerHTML = warnings.map((w) => `<li><span class="wr">!</span>${esc(w)}</li>`).join('')
      + '<li><span class="faint">·</span> 결과 컬럼(And·iOS)은 실행 결과로 가져옵니다. 두 값이 다르면 Fail > N/A > Pass > NT 순으로 합칩니다</li>';
    $('#import-preview', root).hidden = false;
    updateSummary();
  }

  function selection() {
    const sheets = $$('#import-sheets input[type=checkbox]', root).filter((c) => c.checked).map((c) => c.dataset.sheet);
    const prefixes = {};
    $$('#import-sheets input[data-prefix]', root).forEach((i) => { prefixes[i.dataset.prefix] = i.value.trim().toUpperCase(); });
    return { sheets, prefixes };
  }

  function updateSummary() {
    if (!preview) return;
    const { sheets, prefixes } = selection();
    const count = preview.sheets.filter((s) => sheets.includes(s.name)).reduce((n, s) => n + s.cases, 0);
    const badPrefix = sheets.some((s) => !/^[A-Z][A-Z0-9]{0,7}$/.test(prefixes[s]));
    const suite = $('#import-suite', root).value.trim();
    $('#import-summary', root).textContent = badPrefix ? '접두어는 영문 대문자로 시작하는 8자 이내여야 합니다' : `${count}건 · ${sheets.length}시트`;
    $('#import-confirm', root).disabled = !sheets.length || badPrefix || !/^[\w가-힣-]+$/.test(suite) || suite.startsWith('_');
    $('#import-confirm', root).textContent = `${count}건 가져오기`;
  }

  async function confirm() {
    const btn = $('#import-confirm', root);
    btn.classList.add('loading');
    btn.disabled = true;
    try {
      const suite = $('#import-suite', root).value.trim();
      const res = await api.importCommit({ preview_id: preview.preview_id, suite, ...selection() });
      closeModal();
      toast(`가져왔습니다 · 추가 ${res.created} · 갱신 ${res.updated} · 그대로 ${res.unchanged}`, 'ok');
      await NS.reloadSuites(suite);
    } catch (err) {
      toast(`가져오지 못했습니다: ${esc(err.message)}`, 'err');
      btn.disabled = false;
    } finally {
      btn.classList.remove('loading');
    }
  }

  function mount(r) {
    root = r;
    const drop = $('#import-drop', root);
    ['dragover', 'dragenter'].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add('over'); }));
    ['dragleave', 'drop'].forEach((ev) => drop.addEventListener(ev, () => drop.classList.remove('over')));
    drop.addEventListener('drop', (e) => { e.preventDefault(); pick(e.dataTransfer.files[0]); });
    $('#import-file', root).addEventListener('change', (e) => pick(e.target.files[0]));
    $('#import-sheets', root).addEventListener('input', updateSummary);
    $('#import-suite', root).addEventListener('input', updateSummary);
    ['#import-close', '#import-cancel'].forEach((s) => $(s, root).addEventListener('click', closeModal));
    $('#import-confirm', root).addEventListener('click', confirm);
  }
})(window.TCS_NS = window.TCS_NS || {});
```

- [ ] **Step 4: 스크립트 연결** — index.html의 `tc-studio/library.js` 줄 아래:

```html
  <script src="/static/js/tc-studio/import.js?v=20260929-1"></script>
```

- [ ] **Step 5: 통과 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_studio_e2e.py -q`
Expected: `7 passed`

- [ ] **Step 6: 실제 파일로 확인** — 대시보드에서 `~/Downloads/야핏무브_Full.xlsx`를 가져온다. 시트 6개·926건, 접두어 예: 온보딩 `ONB`, 홈 `HOME`, 혜택 `BEN`, 렛츠두두 `LDD`, 주행 `DRV`, 마일리지 `MIL`. 가져온 뒤 트리 합계가 926인지 본다.

- [ ] **Step 7: 커밋**

```bash
git add agents/dashboard/static/js/tc-studio/import.js agents/dashboard/index.html tests/unit/tc_library/test_tc_studio_e2e.py
git commit -m "feat(tc-studio): W2 엑셀 가져오기 모달"
```

---

## Task W3: 내보내기 화면 (엑셀)

PRD 범위: F6.1~F6.6 (md 카드는 Phase 4)

**Files:**
- Create: `agents/dashboard/static/js/tc-studio/export.js`
- Modify: `agents/dashboard/index.html` (`import.js` 스크립트 아래 한 줄)
- Modify: `tests/unit/tc_library/test_tc_studio_e2e.py` (파일 끝에 추가)

**Interfaces:**
- Consumes: `api.exportXlsx(suite, {scope, sheets?, case_ids?, history_note})`, `api.downloadUrl(exportId)`
- Produces: `TCS_NS.exportView.{html, mount, onShow}` — 로드되면 `main.js`가 "내보내기" 탭을 그린다

동작 (목업 765~812행 엑셀 카드):
- 범위: 전체 / 선택한 시트(다중 선택) / 현재 필터 결과(`case_ids`) / 승인된 케이스만. 범위를 바꾸면 검사 결과를 지우고 내려받기를 막는다
- History 기본 문구: `YY.MM.DD TC 스튜디오 반영` (명세 피드백 #17)
- "검사 실행" → 서버가 사본을 만들고 다시 열어 검사 → 결과 목록 · 파일 이름 · 내려받기 버튼 활성
- 검사에 오류가 있어도 내려받을 수는 있지만 버튼 문구가 "오류가 있지만 내려받기"로 바뀐다

- [ ] **Step 1: 실패하는 E2E 테스트 추가** — 파일 끝에:

```python
# ── W3: 내보내기 화면 ──────────────────────────────────────────────────────────
def test_export_check_and_download(studio):
    _, page = studio
    page.locator('[data-id="nav-tab-export"]').click()
    page.locator('[data-id="xlsx-run-check"]').click()
    expect(page.locator('[data-id="xlsx-integrity"] li .ok')).to_have_count(4)
    expect(page.locator('[data-id="xlsx-download"]')).to_be_enabled()
    with page.expect_download() as info:
        page.locator('[data-id="xlsx-download"]').click()
    assert info.value.suggested_filename.endswith(".xlsx")
```

- [ ] **Step 2: 실패 확인**

Run: `.venv/bin/python -m pytest tests/unit/tc_library/test_tc_studio_e2e.py -k export -q`
Expected: FAIL — `nav-tab-export`를 찾지 못함

- [ ] **Step 3: 구현** — `agents/dashboard/static/js/tc-studio/export.js`

```javascript
// TC 스튜디오 — 내보내기 화면 (Phase 1: 엑셀 카드만. md 카드는 Phase 4) (PRD F6)
(function (NS) {
  'use strict';

  const { state, api, esc, $, $$, toast } = NS;
  let root = null;
  let lastExport = null;

  NS.exportView = { html, mount, onShow };

  function html() {
    return `
  <section class="screen" id="screen-export" data-screen="export">
    <div class="wrap">
      <div class="exp">
        <div class="panel exp-card" style="padding:16px">
          <div class="head"><div class="fmt xl">XLSX</div><div><b style="font-size:14px">엑셀로 내보내기</b>
            <div class="help">가져온 템플릿의 사본에 계층 순서대로 씁니다. 원본 파일은 바꾸지 않습니다.</div></div></div>
          <div class="field"><span class="label">범위</span>
            <div class="radio-list" data-id="xlsx-scope">
              <label class="radio"><input type="radio" name="xscope" value="all" checked> 전체 <span class="n" id="x-all-n"></span></label>
              <label class="radio"><input type="radio" name="xscope" value="sheets"> 선택한 시트
                <select class="fselect" id="xlsx-sheets" data-id="xlsx-sheets" multiple size="3" style="margin-left:6px"></select></label>
              <label class="radio"><input type="radio" name="xscope" value="case_ids"> 현재 필터 결과 <span class="n" id="x-filter-n"></span></label>
              <label class="radio"><input type="radio" name="xscope" value="approved"> 승인된 케이스만</label>
            </div></div>
          <div class="warnbox" data-id="xlsx-openpyxl-warning"><b>다시 저장하면 사라질 수 있는 요소</b>
            <span>이미지·차트와 일부 조건부서식은 사본에서 빠질 수 있습니다. 검사 결과를 확인한 뒤 내려받으세요.</span></div>
          <div class="field"><span class="label">무결성 검사</span>
            <ul class="checks" id="xlsx-checks" data-id="xlsx-integrity"><li class="faint">내보내기 전에 검사를 실행하세요</li></ul>
            <button class="btn btn-ghost" data-id="xlsx-run-check" id="xlsx-run-check" style="justify-self:start">검사 실행</button></div>
          <div class="field"><span class="label">History 시트에 추가할 행</span>
            <textarea class="textarea" id="xlsx-history-note" data-id="xlsx-history-note" rows="3"></textarea></div>
          <div class="field"><span class="label">파일 이름</span><div class="fname" id="xlsx-filename" data-id="xlsx-filename">—</div></div>
          <button class="btn btn-primary" data-id="xlsx-download" id="xlsx-download" disabled style="justify-self:start">검사 후 내려받기</button>
        </div>
      </div>
    </div>
  </section>`;
  }

  function onShow() {
    lastExport = null;
    const suite = state.suites.find((s) => s.suite === state.suite);
    $('#x-all-n', root).textContent = suite ? suite.count : 0;
    $('#x-filter-n', root).textContent = state.items.length;
    $('#xlsx-sheets', root).innerHTML = (suite ? suite.sheets : []).map((s) => `<option selected>${esc(s)}</option>`).join('');
    const d = new Date();
    const yymmdd = `${String(d.getFullYear()).slice(2)}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`;
    if (!$('#xlsx-history-note', root).value) $('#xlsx-history-note', root).value = `${yymmdd} TC 스튜디오 반영\n- `;
    resetCheck('');
  }

  function resetCheck(msg) {
    lastExport = null;
    $('#xlsx-download', root).disabled = true;
    $('#xlsx-download', root).textContent = '검사 후 내려받기';
    $('#xlsx-filename', root).textContent = '—';
    $('#xlsx-checks', root).innerHTML = `<li class="faint">${msg || '내보내기 전에 검사를 실행하세요'}</li>`;
  }

  function payload() {
    const scope = $('input[name="xscope"]:checked', root).value;
    const body = { scope, history_note: $('#xlsx-history-note', root).value.trim() };
    if (scope === 'sheets') body.sheets = $$('#xlsx-sheets option', root).filter((o) => o.selected).map((o) => o.value);
    if (scope === 'case_ids') body.case_ids = state.items.map((c) => c.case_id);
    return body;
  }

  async function runCheck(e) {
    const btn = e.currentTarget;
    btn.classList.add('loading');
    btn.disabled = true;
    $('#xlsx-checks', root).innerHTML = '<li class="faint">사본에 쓰고 다시 여는 중…</li>';
    try {
      lastExport = await api.exportXlsx(state.suite, payload());
      $('#xlsx-checks', root).innerHTML = lastExport.checks.map((c) =>
        `<li><span class="${c.level === 'ok' ? 'ok' : 'bad'}">${c.level === 'ok' ? '✓' : '✕'}</span>${esc(c.message)}</li>`).join('');
      $('#xlsx-filename', root).textContent = lastExport.filename;
      const ok = lastExport.checks.every((c) => c.level === 'ok');
      $('#xlsx-download', root).disabled = false;
      $('#xlsx-download', root).textContent = ok ? `내려받기 (${lastExport.count}건)` : '오류가 있지만 내려받기';
    } catch (err) {
      resetCheck(`검사 실패: ${esc(err.message)}`);
    } finally {
      btn.classList.remove('loading');
      btn.disabled = false;
    }
  }

  function mount(r) {
    root = r;
    $$('input[name="xscope"]', root).forEach((i) => i.addEventListener('change', () => resetCheck('범위가 바뀌었습니다. 검사를 다시 실행하세요')));
    $('#xlsx-sheets', root).addEventListener('change', () => resetCheck('범위가 바뀌었습니다. 검사를 다시 실행하세요'));
    $('#xlsx-run-check', root).addEventListener('click', runCheck);
    $('#xlsx-download', root).addEventListener('click', () => {
      if (!lastExport) return;
      const a = document.createElement('a');
      a.href = api.downloadUrl(lastExport.export_id);
      a.download = lastExport.filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      toast(`${esc(lastExport.filename)} 파일을 내려받습니다.`, 'ok');
    });
  }
})(window.TCS_NS = window.TCS_NS || {});
```

- [ ] **Step 4: 스크립트 연결** — index.html의 `tc-studio/import.js` 줄 아래:

```html
  <script src="/static/js/tc-studio/export.js?v=20260929-1"></script>
```

- [ ] **Step 5: 통과 확인 + 전체 회귀**

Run: `.venv/bin/python -m pytest tests/unit/tc_library -q`
Expected: `40 passed`

Run: `.venv/bin/python -m pytest -q`
Expected: 전체 통과 (기존 677 + 신규 40), 1 skipped

- [ ] **Step 6: 커밋**

```bash
git add agents/dashboard/static/js/tc-studio/export.js agents/dashboard/index.html tests/unit/tc_library/test_tc_studio_e2e.py
git commit -m "feat(tc-studio): W3 엑셀 내보내기 화면"
```

---

## Task W4: 문서 갱신 + Phase 1 완료 확인

**Files:**
- Modify: `doc/API_REFERENCE.md` — "상태 변경 (POST)" 표 아래에 새 절
- Modify: `doc/SCRIPTS_GUIDE.md` — `scripts/_validators.py` 행 아래
- Modify: `scripts/update_directory.py` — `SCRIPT_DESCRIPTIONS`의 `"_validators.py"` 항목 아래
- Modify: `doc/tc-studio/TC_AUTHORING_ELEMENT_SPEC.md` — 8장 케이스 경로 (로드맵 Z2)
- Modify: `doc/tc-studio/TC_AUTHORING_ROADMAP.md` — 상세 계획 표에 완료 표시

- [ ] **Step 1: API 레퍼런스** — `doc/API_REFERENCE.md`의 "#### 리포트 삭제" 절 끝(“…대상 파일을 모두 보존합니다.”) 아래에 추가:

```markdown
### TC 스튜디오 라이브러리 (`/api/tc-library`)

`routes_tc_library.py`가 처리한다. 쓰기 요청은 모두 CSRF 검사를 받고, 케이스 쓰기는 `rev`가 맞아야 한다 (틀리면 409 + `server_case`). JSON 바디 상한 2MB, xlsx 업로드 25MB (초과 시 413 `PAYLOAD_TOO_LARGE`). 스위트 이름에 경로 문자가 있으면 400 `INVALID_SUITE`.

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/tc-library` | 스위트 목록 `{suites:[{suite, sheets, count}]}` |
| POST | `/api/tc-library/import/preview?filename=` | 본문 = xlsx 바이트. 시트별 헤더 행·케이스 수·경고 + `preview_id` |
| POST | `/api/tc-library/import` | `{preview_id, suite, sheets, prefixes}` → `{created, updated, unchanged}` (case_id가 같으면 갱신) |
| GET | `/api/tc-library/{suite}/tree` | 시트 › 대분류 › 중분류 › 소분류 › 기능 트리와 가지별 집계 |
| GET | `/api/tc-library/{suite}` | 케이스 목록. 쿼리: `sheet path status execution_result(빈 값=미실행) priority auto source invalid q offset limit` |
| POST | `/api/tc-library/{suite}/cases` | 케이스 추가 (`after`로 위치 지정), 201 |
| GET · PATCH · DELETE | `/api/tc-library/{suite}/cases/{case_id}` | 조회 · 부분 수정 `{rev, …}` · 소프트 삭제 `?rev=` |
| POST | `/api/tc-library/{suite}/cases/{case_id}/duplicate` · `/restore` · `/revert` | 복제 · 삭제 복원 · 이력 되돌리기 `{history_id, rev}` |
| GET | `/api/tc-library/{suite}/cases/{case_id}/history` | 변경 이력 (최신 먼저) |
| POST | `/api/tc-library/{suite}/bulk` | `{items:[{case_id,rev}], op:"set"|"delete", field, value}` → `{updated|deleted, conflicts}` |
| POST | `/api/tc-library/{suite}/move` | `{items, sheet, path, feature?}` → `{moved, conflicts}` |
| POST | `/api/tc-library/{suite}/export/xlsx` | `{scope, sheets?, case_ids?, history_note}` → `{export_id, filename, checks, count}` |
| GET | `/api/tc-library/exports/{export_id}/download` | 내보낸 xlsx 내려받기 |

저장 위치: `state/tc_library/{suite}/` (`cases.json`, `history.jsonl`, `template.xlsx`, `template_profile.json`), 작업 공간 `state/tc_library/_uploads/`, `_exports/`.
```

- [ ] **Step 2: 스크립트 가이드** — `doc/SCRIPTS_GUIDE.md`의 `scripts/_validators.py` 행 아래에 추가:

```markdown
| `scripts/_tc_model.py` | TC 스튜디오 케이스 모델: 허용 값(P0~P3, 실행 결과), Step·Expected 파싱, 결과 병합, id 발급, 검증 규칙 | ❌ (다른 스크립트가 import) |
| `scripts/_tc_template.py` | 엑셀 TC 템플릿 분석: 헤더·하위 헤더·컬럼·드롭다운·No. 수식 탐지 → `TemplateProfile` | ❌ (다른 스크립트가 import) |
| `scripts/_tc_xlsx_import.py` | 엑셀 시트 → 라이브러리 케이스 (병합·빈 칸 이어받기, 기타 칸의 id·src 분리) | ❌ (다른 스크립트가 import) |
| `scripts/_tc_library.py` | TC 라이브러리 저장소 `state/tc_library/{suite}/`: rev 수정·일괄·생성·삭제·이력·트리·필터 | ❌ (대시보드가 import) |
| `scripts/_tc_xlsx_export.py` | 라이브러리 → 템플릿 사본 xlsx (병합·드롭다운·요약 수식·History) + 무결성 검사 | ❌ (대시보드가 import) |
| `agents/dashboard/tools/scope_tc_studio_css.py` | 목업 CSS → `static/css/tc-studio.css` 생성 (목업을 고친 뒤 다시 실행) | ✅ (`python agents/dashboard/tools/scope_tc_studio_css.py <목업> <출력>`) |
```

- [ ] **Step 3: 디렉토리 설명** — `scripts/update_directory.py`의 `"_validators.py": …` 줄 아래에 추가:

```python
    "_tc_model.py":           "TC 스튜디오 케이스 모델·허용 값·검증 규칙",
    "_tc_template.py":        "엑셀 TC 템플릿 분석 (헤더·컬럼·드롭다운·No. 수식)",
    "_tc_xlsx_import.py":     "엑셀 시트 → TC 라이브러리 케이스",
    "_tc_library.py":         "TC 라이브러리 저장소 (rev·이력·트리·필터)",
    "_tc_xlsx_export.py":     "TC 라이브러리 → 템플릿 사본 xlsx + 무결성 검사",
```

- [ ] **Step 4: 명세서 경로 정리** — `doc/tc-studio/TC_AUTHORING_ELEMENT_SPEC.md` 8장 표에서 `/api/tc-library/cases/{case_id}`로 시작하는 경로를 모두 `/api/tc-library/{suite}/cases/{case_id}`로 바꾸고, 표 위 설명 끝에 한 문장 추가: "케이스 경로에는 스위트가 들어간다 (로드맵 Z2)."

Run: `grep -c "/api/tc-library/cases/" doc/tc-studio/TC_AUTHORING_ELEMENT_SPEC.md`
Expected: `0`

- [ ] **Step 5: 문서 동기화 테스트 + 전체 회귀**

Run: `.venv/bin/python -m pytest tests/unit/core/test_doc_registry_sync.py -q && .venv/bin/python -m pytest -q`
Expected: 전부 통과, 1 skipped

- [ ] **Step 6: Phase 1 완료 기준 확인**

1. 대시보드에서 `야핏무브_Full.xlsx`를 가져온다 → 926건
2. 아무 케이스나 하나 고친 뒤 내보내기 → 검사 12줄 모두 ✓ → 내려받기
3. 내려받은 파일을 다시 가져온다 → `추가 0 · 갱신 0 · 그대로 926`이어야 한다 (고친 내용이 이미 라이브러리에 있으므로)
4. 내려받은 파일을 엑셀에서 열어 요약 표 숫자·드롭다운(P0~P3)·History 마지막 행을 눈으로 확인한다

- [ ] **Step 7: 로드맵 표시 + 커밋** — `doc/tc-studio/TC_AUTHORING_ROADMAP.md` 상단 "상세 계획" 표의 Phase 1 행 끝에 `✅ 완료 (YYYY-MM-DD)`를 붙인다 (실제 날짜)

```bash
git add doc/API_REFERENCE.md doc/SCRIPTS_GUIDE.md scripts/update_directory.py doc/tc-studio/TC_AUTHORING_ELEMENT_SPEC.md doc/tc-studio/TC_AUTHORING_ROADMAP.md
git commit -m "docs(tc-studio): W4 Phase 1 API·스크립트 문서 갱신"
```

---

## Self-Review 결과

- **PRD 대응:** F2.1(B2) · F2.2(B3, B5) · F2.3(B2) · F2.4(B3, W2) · F2.6(B2 경고, W3 안내) · F5.1(B5, W1) · F5.2(B4, B9, W1) · F5.3(B4, B9, W1) · F5.4(B5, W1) · F5.8(B1, B5, W1) · F5.11(B4, B9, W1) · F6.1(B10, W3) · F6.2~F6.4(B6) · F6.5(B6 `note_cell`) · F6.6(B7, B10, W3) · F6.7(B3, B4) · §7 업로드 상한·CSRF(B8)
- **Phase 1에서 뺀 것 (다른 Phase 계획에 있음):** F5.5~F5.7·F5.10 → Phase 2, F5.9 → Phase 3, F7 → Phase 4, 목업의 "다른 양식 직접 매핑" → Phase 2 G0
- **이름 일관성:** `execution_result`(모델·API·필터), `case_id`, `rev`, `TC_LIBRARY_DIR`, `TcLibraryRoutesMixin`, `_tcl_*` 핸들러, `TCS_NS`/`TCS` — 모든 작업에서 같은 이름을 쓴다. 목업의 `result` 필드는 구현에서 `execution_result`로 바뀐다.
