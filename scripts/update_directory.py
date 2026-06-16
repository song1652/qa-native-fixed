"""
doc/DIRECTORY.md 자동 생성 스크립트.

파일시스템을 실시간 스캔하여 현재 상태를 반영한 DIRECTORY.md를 덮어씁니다.

실행:
    python scripts/update_directory.py

자동 호출 시점 (권장):
    - run_qa.py / run_qa_parallel.py 완료 후
    - git pre-commit hook
    - 파이프라인 step=done 도달 시

수동 수정이 필요한 부분:
    - FOLDER_DESCRIPTIONS: 폴더/파일 역할 설명 (아키텍처 변경 시만 수정)
    - SCRIPT_DESCRIPTIONS: scripts/ 하위 파일별 설명
    - SKILL_DESCRIPTIONS: .claude/skills/ 하위 스킬 설명
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# ── 경로 설정 ──────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _paths import PROJECT_ROOT

DOC_PATH = PROJECT_ROOT / "doc" / "DIRECTORY.md"

# ── 역할 설명 맵 (아키텍처 변경 시만 수정) ────────────────────────

FOLDER_DESCRIPTIONS: dict[str, str] = {
    "scripts":       "단계별 실행 스크립트 (LLM 없음, 순수 Python)",
    "agents":        "사수-부사수 에이전트 시스템 (페르소나·교훈·대시보드)",
    "prompts":       "심의 Agent 프롬프트 템플릿",
    "state":         "런타임 상태 파일 (파이프라인 실행 중 자동 생성·갱신)",
    "logs":          "실행 로그 (런타임 자동 생성)",
    "parallel":      "병렬 파이프라인 스크립트",
    "tests":         "테스트 산출물 (생성 코드·리포트·스크린샷)",
    "testcases":     "케이스 파일 (tc_*.md) — 그룹별 서브폴더",
    "config":        "설정 파일 (URL 매핑·테스트 입력값)",
    "doc":           "문서 (사람용·에이전트 on-demand 참조)",
    "knowledge":     "QA 지식 베이스 (체크리스트·팀 내규)",
    "templates":     "문서 템플릿 (TC·리포트·이슈)",
    ".claude/skills": "스킬 프레임워크 (SKILL.md 표준, Claude Code 참조용)",
}

SCRIPT_DESCRIPTIONS: dict[str, str] = {
    "01_analyze.py":          "DOM 추출 (서브페이지 병렬, 동적 UI·우클릭 메뉴 캡처, 정적 TTL 7일·동적 TTL 24h)",
    "02a_dialog.py":          "Plan 심의 컨텍스트 초기화",
    "02_generate.py":         "테스트 코드 scaffold 생성",
    "03_lint.py":             "flake8 검사 → step=reviewed 설정",
    "03a_dialog.py":          "코드 리뷰 심의 컨텍스트 초기화",
    "04_approve.py":          "lint 리뷰 승인/반려 (종료코드 0=승인, 2=반려, 3=대기)",
    "05_execute.py":          "pytest 실행 (--only-failed, --no-report 플래그, 최대 8 workers)",
    "06_heal.py":             "실패 분석 (최대 3회 자동 패치)",
    "06_auto_heal.py":        "자동 힐링 패치 (8개 정적 패턴 + heal_stats 빈출 패턴)",
    "06a_dialog.py":          "힐링 심의 컨텍스트 초기화",
    "heal_utils.py":          "힐링 공용 유틸 (classify_error 7분류, append_lessons)",
    "result_parser.py":       "pytest JSON 리포트 파싱 (단일/병렬 공유)",
    "report_html.py":         "HTML 리포트 생성 (단일/병렬 공통)",
    "parse_cases.py":         "tc_*.md 파싱",
    "hook_utils.py":          "훅 스크립트 공통 유틸 (check_state)",
    "structured_log.py":      "구조화 로그 (JSON Lines → logs/structured.jsonl)",
    "_paths.py":              "중앙 경로 상수 + read_state/write_state 원자적 I/O (FSM 전이 검증 내장)",
    "_constants.py":          "파이프라인 종료코드 + VALID_TRANSITIONS + assert_valid_transition",
    "_python.py":             ".venv 경로 자동 감지",
    "_generate_plan.py":      "테스트케이스별 실행 계획 생성",
    "dom_helpers.js":         "JS 공통 유틸 (isVisible·esc·getSelectorsSimple) — _js()가 자동 주입",
    "team_discuss.py":        "팀 토론 초기화",
    "team_approve.py":        "팀 토론 승인 (터미널용)",
    "sync_test_data.py":      "test_data.json 동기화",
    "coverage_matrix.py":     "커버리지 매트릭스 생성 (→ state/coverage.json)",
    "flaky_detector.py":      "Flaky Test 감지기 (run_history.json 분석 → state/flaky_tests.json)",
    "update_directory.py":    "doc/DIRECTORY.md 자동 생성 (이 파일)",
    # check_pending_*.py 그룹
    "check_pending_approve.py":   "훅: 승인 대기 상태 확인 (hook_utils.check_state)",
    "check_pending_discuss.py":   "훅: 토론 대기 상태 확인",
    "check_pending_impl.py":      "훅: 구현 대기 상태 확인",
    "check_pending_parallel.py":  "훅: 병렬 파이프라인 대기 상태 확인",
    "check_pending_pipeline.py":  "훅: 단일 파이프라인 대기 상태 확인",
    "check_pending_quick_heal.py":"훅: 빠른 힐링 대기 상태 확인",
    # 일회성 유틸 스크립트 (레거시 — 정리 예정)
    "_add_login_retry.py":    "일회성: 생성 테스트에 로그인 retry 로직 일괄 추가 (레거시)",
    "_complete_scaffolds.py": "일회성: scaffold 파일 완성 보조 (레거시)",
    "_fix_final_lint.py":     "일회성: lint 최종 패치 (레거시)",
    "_fix_login_wait.py":     "일회성: 로그인 대기 패치 (레거시)",
    "_fix_string_split.py":   "일회성: 문자열 분리 패치 (레거시)",
    "_revert_login.py":       "일회성: 로그인 패치 롤백 (레거시)",
}

SKILL_DESCRIPTIONS: dict[str, str] = {
    "playwright-best-practices": "Python Playwright 정적 베스트프랙티스 (qa-native)",
    "heal-patterns":             "힐링 오류 유형별 패치 전략 가이드라인 (qa-native)",
    "verify":                    "패치 후 05_execute 기반 3단계 증거 검증 (qa-native)",
    "skillify":                  "반복 패턴 → heal-patterns/lessons_learned 공식 등록 (qa-native)",
    "browser-qa":                "배포 후 시각 검증, 4단계 QA 플로우 (ECC)",
    "python-testing":            "pytest 픽스처·파라미터화·mocking 전략 (ECC)",
}

STATE_FILE_DESCRIPTIONS: dict[str, str] = {
    "pipeline.json":    "단일 파이프라인 상태 (FSM step 전이 검증 포함)",
    "parallel.json":    "병렬 파이프라인 상태",
    "quick.json":       "빠른 실행 상태",
    "discuss.json":     "팀 토론 상태",
    "heal_context.json":"병렬 힐링 컨텍스트 (failure_groups, lessons_snapshot 포함)",
    "heal_stats.json":  "힐링 오류 패턴별 빈도 카운터 (06_heal.py 자동 갱신)",
    "run_history.json": "실행 이력 (매 실행 시 자동 append)",
    "coverage.json":    "커버리지 매트릭스 (coverage_matrix.py 생성)",
    "flaky_tests.json": "Flaky Test 목록 (flaky_detector.py 생성)",
}

# ── 헬퍼 함수 ────────────────────────────────────────────────────

def _count_md_files(path: Path) -> int:
    if not path.exists():
        return 0
    return len(list(path.glob("tc_*.md")))


def _count_py_files(path: Path) -> int:
    if not path.exists():
        return 0
    return len([f for f in path.glob("tc_*.py") if f.is_file()])


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _last_run_summary() -> str:
    """run_history.json에서 최근 실행 요약 반환."""
    history_path = PROJECT_ROOT / "state" / "run_history.json"
    if not history_path.exists():
        return "이력 없음"
    history = _load_json(history_path)
    if not isinstance(history, list) or not history:
        return "이력 없음"
    last = history[-1]
    ts = last.get("timestamp", "")[:16]
    pipeline = last.get("pipeline", "")
    group = last.get("group") or "/".join(last.get("groups", []))
    passed = last.get("passed", 0)
    total = last.get("total", 0)
    heal = last.get("heal_count", 0)
    return f"{ts} | {pipeline} | {group} | {passed}/{total} | heal:{heal}"


def _group_status(group: str) -> str:
    """run_history.json에서 특정 그룹의 최근 통과율 반환."""
    history_path = PROJECT_ROOT / "state" / "run_history.json"
    if not history_path.exists():
        return ""
    history = _load_json(history_path)
    if not isinstance(history, list):
        return ""
    for entry in reversed(history):
        grp = entry.get("group") or ""
        grps = entry.get("groups") or []
        if group == grp or group in grps:
            p = entry.get("passed", 0)
            t = entry.get("total", 0)
            rate = entry.get("pass_rate", 0)
            return f"{p}/{t} ({rate:.0f}%)"
    return ""


def _scan_testcase_groups() -> list[tuple[str, int, str]]:
    """testcases/ 하위 그룹 스캔. (group_name, tc_count, last_status) 반환."""
    tc_root = PROJECT_ROOT / "testcases"
    if not tc_root.exists():
        return []
    groups = []
    for d in sorted(tc_root.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            count = _count_md_files(d)
            status = _group_status(d.name)
            groups.append((d.name, count, status))
    return groups


def _scan_generated_groups() -> list[tuple[str, int, str]]:
    """tests/generated/ 하위 그룹 스캔. (group_name, py_count, last_status) 반환."""
    gen_root = PROJECT_ROOT / "tests" / "generated"
    if not gen_root.exists():
        return []
    groups = []
    for d in sorted(gen_root.iterdir()):
        if d.is_dir() and not d.name.startswith((".", "__")):
            count = _count_py_files(d)
            status = _group_status(d.name)
            groups.append((d.name, count, status))
    return groups


def _scan_scripts() -> list[tuple[str, str]]:
    """scripts/ 하위 .py/.js 파일 스캔. (filename, description) 반환."""
    scripts_dir = PROJECT_ROOT / "scripts"
    files = []
    for f in sorted(scripts_dir.iterdir()):
        if f.suffix in (".py", ".js") and not f.name.startswith("__"):
            desc = SCRIPT_DESCRIPTIONS.get(f.name, "")
            files.append((f.name, desc))
    return files


def _scan_state_files() -> list[tuple[str, str]]:
    """state/ 하위 파일 스캔."""
    state_dir = PROJECT_ROOT / "state"
    files = []
    for f in sorted(state_dir.iterdir()):
        if f.is_file() and f.suffix == ".json":
            desc = STATE_FILE_DESCRIPTIONS.get(f.name, "런타임 생성")
            files.append((f.name, desc))
    return files


def _scan_skills() -> list[tuple[str, str]]:
    """.claude/skills/ 하위 스킬 스캔."""
    skills_dir = PROJECT_ROOT / ".claude" / "skills"
    skills = []
    for d in sorted(skills_dir.iterdir()):
        if d.is_dir() and (d / "SKILL.md").exists():
            desc = SKILL_DESCRIPTIONS.get(d.name, "")
            skills.append((d.name, desc))
    return skills


# ── Markdown 생성 ────────────────────────────────────────────────

def build_markdown() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    last_run = _last_run_summary()
    tc_groups = _scan_testcase_groups()
    gen_groups = _scan_generated_groups()
    scripts = _scan_scripts()
    state_files = _scan_state_files()
    skills = _scan_skills()

    lines: list[str] = []

    lines += [
        "# 디렉토리 구조",
        "",
        f"> **자동 생성** — `python scripts/update_directory.py` | 마지막 갱신: {now}",
        f"> 최근 실행: {last_run}",
        "",
        "> 역할 설명 수정: `scripts/update_directory.py` 내 `SCRIPT_DESCRIPTIONS` / `FOLDER_DESCRIPTIONS` 편집.",
        "",
        "---",
        "",
    ]

    # ── 루트 파일 ──
    lines += [
        "## 루트",
        "",
        "| 파일 | 역할 |",
        "|------|------|",
        "| `_bootstrap.py` | 프로젝트 진입점 공통 경로 설정 (루트 스크립트가 import) |",
        "| `run_qa.py` | 단일 파이프라인 실행 엔트리포인트 |",
        "| `run_qa_parallel.py` | 병렬 파이프라인 실행 엔트리포인트 |",
        "| `run_team.py` | 팀 토론 실행 엔트리포인트 |",
        "",
    ]

    # ── scripts/ ──
    lines += [
        "## scripts/ — " + FOLDER_DESCRIPTIONS.get("scripts", ""),
        "",
        "| 파일 | 역할 |",
        "|------|------|",
    ]
    for fname, desc in scripts:
        lines.append(f"| `{fname}` | {desc} |")
    lines.append("")

    # ── parallel/ ──
    lines += [
        "## parallel/ — " + FOLDER_DESCRIPTIONS.get("parallel", ""),
        "",
        "| 파일 | 역할 |",
        "|------|------|",
        "| `00_split.py` | URL별 worker 환경 초기화 (workers/ 디렉토리 생성) |",
        "| `99_merge.py` | pytest 실행 + 통합 리포트 + 힐링 루프 |",
        "",
    ]

    # ── testcases/ ──
    lines += [
        "## testcases/ — " + FOLDER_DESCRIPTIONS.get("testcases", ""),
        "",
        "| 그룹 | TC 수 | 최근 실행 결과 |",
        "|------|-------|---------------|",
    ]
    for group, count, status in tc_groups:
        lines.append(f"| `{group}/` | {count}개 | {status or '-'} |")
    if not tc_groups:
        lines.append("| (그룹 없음) | - | - |")
    lines.append("")

    # ── tests/ ──
    lines += [
        "## tests/ — " + FOLDER_DESCRIPTIONS.get("tests", ""),
        "",
        "### tests/generated/ — Claude Code가 작성한 테스트 코드",
        "",
        "| 그룹 | 생성 파일 수 | 최근 실행 결과 |",
        "|------|------------|---------------|",
    ]
    for group, count, status in gen_groups:
        lines.append(f"| `{group}/` | {count}개 | {status or '-'} |")
    if not gen_groups:
        lines.append("| (그룹 없음) | - | - |")
    lines += [
        "",
        "| 경로 | 역할 |",
        "|------|------|",
        "| `tests/reports/` | HTML 리포트 (pytest 실행 결과) |",
        "| `tests/screenshots/` | 실패 시 스크린샷 (conftest.py 기반 자동 캡처) |",
        "| `tests/conftest.py` | pytest 전역 픽스처 |",
        "| `tests/test_core_parsers.py` | 핵심 파서 유닛 테스트 |",
        "",
    ]

    # ── agents/ ──
    lines += [
        "## agents/ — " + FOLDER_DESCRIPTIONS.get("agents", ""),
        "",
        "| 파일/폴더 | 역할 |",
        "|-----------|------|",
        "| `IDENTITY.md` | 사수/부사수 페르소나 (말투·성격) |",
        "| `SOUL.md` | 팀 원칙과 가치관 |",
        "| `team_charter.md` | 팀 헌장 (협업 규칙·역할 정의) |",
        "| `team_notes.md` | 승인된 팀 결정사항 |",
        "| `lessons_learned.md` | 큐레이션된 실수 패턴 (수동 관리, 힐링 전 참조) |",
        "| `lessons_learned_auto.md` | 자동 기록 힐링 로그 (heal_utils.py 자동 추가) |",
        "| `dialog.json` | 팀 토론 대화 로그 |",
        "| `roles/senior.md` | 사수 행동 지침 (상세) |",
        "| `roles/junior.md` | 부사수 행동 지침 (상세) |",
        "| `dashboard/serve.py` | 대시보드 로컬 서버 (포트 8766) |",
        "| `dashboard/index.html` | 파이프라인 모니터링 대시보드 UI |",
        "",
    ]

    # ── state/ ──
    lines += [
        "## state/ — " + FOLDER_DESCRIPTIONS.get("state", ""),
        "",
        "| 파일 | 역할 |",
        "|------|------|",
    ]
    for fname, desc in state_files:
        lines.append(f"| `{fname}` | {desc} |")
    lines += [
        "| `dom_cache/` | 서브페이지 DOM 스냅샷 캐시 (URL MD5 해시 키) |",
        "",
    ]

    # ── config/ ──
    lines += [
        "## config/ — " + FOLDER_DESCRIPTIONS.get("config", ""),
        "",
        "| 파일 | 역할 |",
        "|------|------|",
        "| `pages.json` | 페이지명 → URL 매핑 (키 = testcases/ 하위 폴더명) |",
        "| `test_data.json` | 테스트 입력값 (하드코딩 금지, 키 = 그룹명) |",
        "",
    ]

    # ── prompts/ ──
    lines += [
        "## prompts/ — " + FOLDER_DESCRIPTIONS.get("prompts", ""),
        "",
        "| 파일 | 역할 |",
        "|------|------|",
        "| `plan_deliberation.md` | 02a 심의 — plan 수립 |",
        "| `review_deliberation.md` | 03a 심의 — 코드 리뷰 |",
        "| `heal_deliberation.md` | 06a 심의 — 힐링 패치 |",
        "| `parallel_subagent.md` | 병렬 subagent 코드 생성 |",
        "| `team_discussion.md` | 팀 토론 멀티라운드 |",
        "| `examples/` | few-shot 예시 JSON (plan_good, plan_bad, heal_patch) |",
        "",
    ]

    # ── .claude/skills/ ──
    lines += [
        "## .claude/skills/ — " + FOLDER_DESCRIPTIONS.get(".claude/skills", ""),
        "",
        "| 스킬 | 역할 |",
        "|------|------|",
    ]
    for skill, desc in skills:
        lines.append(f"| `{skill}/` | {desc} |")
    lines.append("")

    # ── doc/ ──
    lines += [
        "## doc/ — " + FOLDER_DESCRIPTIONS.get("doc", ""),
        "",
        "| 파일 | 역할 |",
        "|------|------|",
        "| `DIRECTORY.md` | 디렉토리 구조 (이 파일, 자동 생성) |",
        "| `PIPELINE_STATE.md` | state/pipeline.json 스키마 상세 |",
        "| `HEALING_GUIDE.md` | 힐링 완료 체크리스트 + MCP 시각 검증 절차 |",
        "| `SCRIPTS_GUIDE.md` | 스크립트 CLI 옵션·실행 방법 |",
        "| `TEAM_DISCUSSION.md` | 팀 토론 파이프라인 상세 |",
        "| `API_REFERENCE.md` | CLI 옵션 + 대시보드 API 엔드포인트 |",
        "| `PROMPTS_REFERENCE.md` | prompts/ 템플릿 입출력 스키마 |",
        "| `PROJECT_OVERVIEW.md` | 아키텍처 설계 문서 |",
        "",
    ]

    # ── 기타 ──
    lines += [
        "## 기타",
        "",
        "| 경로 | 역할 |",
        "|------|------|",
        "| `knowledge/` | QA 지식 베이스 (체크리스트·팀 내규) |",
        "| `templates/` | 문서 템플릿 (TC·리포트·이슈) |",
        "| `logs/` | 실행 로그 (run_qa.txt, run_parallel.txt, structured.jsonl 등) |",
        "| `reports/issues/` | 이슈 추적 파일 (ISSUE-{날짜}-{번호}.md) |",
        "",
    ]

    return "\n".join(lines)


# ── 실행 ─────────────────────────────────────────────────────────

def main() -> None:
    md = build_markdown()
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOC_PATH.write_text(md, encoding="utf-8")
    print(f"[update_directory] doc/DIRECTORY.md 갱신 완료 ({len(md.splitlines())}줄)")


if __name__ == "__main__":
    main()
