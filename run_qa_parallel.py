"""
QA 병렬 자동화 진입점 (간소화).

testcases/ 폴더를 스캔하고 URL별 DOM 분석 후,
Claude Code subagent에 전달할 컨텍스트를 출력한다.
worker 디렉토리 없이 subagent가 tests/generated/에 직접 저장.

사용법:
  # 전체 자동 스캔 (config/pages.json + testcases/ 폴더)
  python run_qa_parallel.py

  # 특정 폴더만
  python run_qa_parallel.py --folders login saintcore

  # targets.json 지정
  python run_qa_parallel.py --targets testcases/targets_demo.json
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

import _bootstrap  # noqa: F401 — scripts/ 경로 설정
from parse_cases import load_cases
from _paths import PROJECT_ROOT, PARALLEL_STATE, STATE_DIR, HEAL_CONTEXT_STATE, read_state, write_state, reset_state, update_state
from _pipeline_registry import ParallelStatus  # P68: ParallelStatus 상수 사용

# 01_analyze.py의 analyze() 직접 import
from importlib import import_module as _im

PAGES_JSON = PROJECT_ROOT / "config" / "pages.json"
TEST_DATA_JSON = PROJECT_ROOT / "config" / "test_data.json"
PARALLEL_STATE_PATH = PARALLEL_STATE


def _save_state(state: dict) -> None:
    """state/parallel.json에 상태 저장 (원자적 RMW, P50).

    update_state()를 사용해 락 보유 중 read-modify-write를 수행한다.
    기존의 read_state → update → write_state 패턴은 비원자적 RMW 경쟁이
    발생하므로 update_state로 대체.
    """
    update_state(PARALLEL_STATE_PATH, lambda s: {**s, **state})


def load_pages() -> dict:
    if PAGES_JSON.exists():
        return json.loads(PAGES_JSON.read_text(encoding="utf-8"))
    return {}


def load_test_data() -> dict:
    if TEST_DATA_JSON.exists():
        return json.loads(TEST_DATA_JSON.read_text(encoding="utf-8"))
    return {}


def resolve_url(folder_name: str, pages: dict) -> str | None:
    """pages.json에서 URL을 조회. string/object 형식 모두 지원."""
    entry = pages.get(folder_name)
    if entry is None:
        return None
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        return entry.get("url")
    return None


def resolve_page_meta(folder_name: str, pages: dict) -> dict:
    """pages.json에서 메타데이터 조회. string 형식은 빈 메타 반환."""
    entry = pages.get(folder_name)
    if isinstance(entry, dict):
        return {k: v for k, v in entry.items() if k != "url"}
    return {}


def read_file_safe(path: Path) -> str:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def analyze_url(url: str) -> dict:
    """01_analyze.py의 analyze() 함수를 직접 호출해 DOM 분석."""
    spec = _im("importlib.util").find_spec(
        "01_analyze",
        [str(PROJECT_ROOT / "scripts")],
    )
    if spec is None:
        # fallback: 직접 import
        analyze_mod_path = PROJECT_ROOT / "scripts" / "01_analyze.py"
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "analyze_mod", str(analyze_mod_path)
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    else:
        import importlib.util
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    main_dom, _sub_doms = asyncio.run(mod.analyze_all(url, [], skip_dynamic=False))
    return main_dom


def resolve_targets(args, pages: dict) -> list[dict]:
    """실행 대상 목록 생성. 각 항목: {url, cases_paths, group_dir, group_label, batch_info, batch_files}"""
    targets = []

    if args.targets:
        targets_path = Path(args.targets)
        if not targets_path.exists():
            print(f"[오류] targets 파일 없음: {args.targets}")
            sys.exit(1)
        raw = json.loads(targets_path.read_text(encoding="utf-8"))
        for t in raw:
            url = t.get("url")
            cases = t["cases"]
            if not url:
                folder = Path(cases).name
                url = pages.get(folder) or pages.get(Path(cases).parent.name)
            if not url:
                print(f"[건너뜀] URL 없음: {cases}")
                continue
            targets.append({"url": url, "cases": cases})
        return _expand_targets(targets)

    # 폴더 자동 스캔
    testcases_root = PROJECT_ROOT / "testcases"
    if not testcases_root.exists():
        print("[오류] testcases/ 폴더 없음.")
        sys.exit(1)

    folder_filter = args.folders if args.folders else None

    for folder in sorted(testcases_root.iterdir()):
        if not folder.is_dir() or folder.name.startswith("."):
            continue
        if folder_filter and folder.name not in folder_filter:
            continue
        url = resolve_url(folder.name, pages)
        if not url:
            print(f"[건너뜀] '{folder.name}' — config/pages.json에 URL 없음")
            continue
        targets.append({
            "url": url,
            "cases": str(folder),
            "base_group": folder.name,
        })

    if not targets:
        print("[오류] 실행할 대상 없음. config/pages.json에 URL을 등록하세요.")
        sys.exit(1)

    return _expand_targets(targets)


BATCH_SIZE = 8  # 폴더 내 배치 크기 (1 배치 = 1 subagent)


def _expand_targets(targets: list[dict]) -> list[dict]:
    """폴더 내 tc_*.md 파일을 배치 단위 타겟으로 확장.

    각 배치는 최대 BATCH_SIZE개의 tc 파일을 포함하며,
    하나의 subagent가 배치 내 파일들을 동시에 처리한다.
    """
    expanded = []
    for target in targets:
        cases_path = Path(target["cases"])
        if not cases_path.is_absolute():
            cases_path = PROJECT_ROOT / cases_path

        base_group = target.get("base_group")
        if not base_group:
            parent = cases_path.parent.name
            base_group = parent if parent not in ("testcases", "config", ".") else cases_path.stem

        if cases_path.is_dir():
            md_files = sorted(cases_path.glob("tc_*.md"))
            if not md_files:
                md_files = sorted(cases_path.glob("*.md"))
            if not md_files:
                print(f"[경고] 폴더에 .md 파일 없음: {cases_path}")
                continue

            # 배치로 묶기
            for batch_idx in range(0, len(md_files), BATCH_SIZE):
                batch = md_files[batch_idx:batch_idx + BATCH_SIZE]
                batch_num = batch_idx // BATCH_SIZE + 1
                total_batches = (len(md_files) + BATCH_SIZE - 1) // BATCH_SIZE
                expanded.append({
                    "url": target["url"],
                    "cases_paths": [md for md in batch],
                    "group_dir": base_group,
                    "group_label": f"{base_group}_batch{batch_num}",
                    "batch_info": f"{batch_num}/{total_batches}",
                    "batch_files": [md.stem for md in batch],
                })
        else:
            expanded.append({
                "url": target["url"],
                "cases_paths": [cases_path],
                "group_dir": base_group,
                "group_label": cases_path.stem,
                "batch_info": "1/1",
                "batch_files": [cases_path.stem],
            })

    return expanded


PARALLEL_HEADLESS_PROMPT = (
    "CLAUDE.md 병렬 파이프라인 지침대로 QA 자동화를 끝까지 진행해줘. "
    "state/parallel_contexts.json 파일에 subagent 컨텍스트가 준비되어 있어. "
    "다음 순서로 실행해: "
    "1) .venv/bin/python parallel/02a_parallel_dialog.py 실행 → "
    "   DELIBERATION_CONTEXT를 바탕으로 공통 테스트 전략 심의 (사수·부사수 내부 시뮬레이션) → "
    "   결과를 state/parallel_plan.json 에 JSON으로 저장 "
    "   (저장 형식: {common_patterns, common_cautions, group_notes}) "
    "2) state/parallel_contexts.json 읽기 "
    "3) subagents[] 배열의 각 항목을 Agent tool로 동시에 실행 "
    "   (prompts/parallel_subagent.md 지침 참조, shared_context_paths의 파일들 — "
    "   parallel_plan.json 포함 — 각 subagent가 읽도록 지시) "
    "4) 모든 subagent 완료 후 .venv/bin/python parallel/99_merge.py 실행 "
    "5) 실패 케이스가 있으면 doc/HEALING_GUIDE.md를 참조해서 힐링 루프 진행 (최대 3회). "
    "모든 파이썬 명령은 프로젝트 루트의 .venv/bin/python을 사용해서 실행해."
)


def _launch_headless_parallel(output_payload: dict) -> None:
    """parallel_contexts.json을 저장 후 claude -p 헤드리스 세션으로 병렬 파이프라인 자동 실행.

    컨텍스트(DOM, test_cases 등)를 state/parallel_contexts.json에 먼저 기록한 뒤
    claude CLI를 non-interactive 모드로 실행해 subagent 병렬 실행 + 99_merge.py + 힐링까지
    사람 개입 없이 완주시킨다.

    주의: run_qa.py의 _launch_headless_pipeline()과 동일한 이유로
    --dangerously-skip-permissions 사용. 신뢰할 수 없는 환경에서는 재검토 필요.
    """
    import subprocess

    ctx_path = PROJECT_ROOT / "state" / "parallel_contexts.json"
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / "run_qa_parallel_headless.txt"

    # headless Claude가 읽을 컨텍스트 파일 저장
    ctx_path.write_text(
        json.dumps(output_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print()
    print("  [자동 실행] headless Claude Code 세션을 백그라운드로 시작합니다.")
    print(f"  컨텍스트: {ctx_path}")
    print(f"  로그: {log_path}")
    print("  (수동으로 이어받고 싶다면 --no-auto 옵션으로 재실행하세요)")

    # context manager: Popen 예외 시에도 log_file이 반드시 닫힘.
    # POSIX에서 부모가 fd를 닫아도 자식은 dup된 fd로 계속 씀 — 데이터 유실 없음.
    try:
        with open(log_path, "w", encoding="utf-8") as log_file:
            subprocess.Popen(
                [
                    "claude", "-p", PARALLEL_HEADLESS_PROMPT,
                    "--dangerously-skip-permissions",
                    "--output-format", "text",
                ],
                cwd=str(PROJECT_ROOT),
                stdout=log_file, stderr=subprocess.STDOUT,
            )
    except Exception:
        # Popen 실패 시 컨텍스트 파일을 삭제해 stale 상태 방지
        ctx_path.unlink(missing_ok=True)
        raise


def main():
    parser = argparse.ArgumentParser(description="QA 병렬 파이프라인 (간소화)")
    parser.add_argument("--targets", default=None,
                        help="targets.json 경로. 생략 시 testcases/ 폴더 자동 스캔.")
    parser.add_argument("--folders", nargs="*", default=None,
                        help="특정 폴더만 실행 (예: login saintcore)")
    parser.add_argument("--no-auto", action="store_true",
                        help="headless Claude Code 자동 실행을 생략하고 안내 메시지만 출력 (기존 동작)")
    args = parser.parse_args()

    pages = load_pages()
    test_data = load_test_data()

    print("=" * 60)
    print("  QA 병렬 파이프라인 시작 (간소화)")
    print("=" * 60)

    # 상태 파일 초기화
    parallel_dir = PROJECT_ROOT / "parallel"
    parallel_dir.mkdir(exist_ok=True)
    STATE_DIR.mkdir(exist_ok=True)
    # FSM 전이 검증 없이 초기 상태로 리셋 (재실행 시 ValueError 방지, P50)
    reset_state(PARALLEL_STATE_PATH, {"status": ParallelStatus.INIT, "created_at": datetime.now().isoformat()})  # P68: 리터럴 → 상수
    # H-1(P131): 이전 라운드 heal_context 삭제 — 잔존 시 "동일 오류 2회" 로직이
    # 오작동해 첫 힐링부터 즉시 HEAL_FAILED로 전이되는 교착 현상 방지.
    HEAL_CONTEXT_STATE.unlink(missing_ok=True)

    # 등록된 페이지 표시
    active = {k: v for k, v in pages.items() if v}
    print(f"  config/pages.json — {len(active)}개 페이지 등록")
    for name, entry in active.items():
        url = entry.get("url") if isinstance(entry, dict) else entry
        spa = " (SPA)" if isinstance(entry, dict) and entry.get("spa") else ""
        print(f"    [{name}] {url}{spa}")
    print()

    # 1. 대상 목록 생성
    targets = resolve_targets(args, pages)
    print(f"[준비] {len(targets)}개 대상 확인")

    # 2. URL별 DOM 분석 (캐시)
    _save_state({"status": ParallelStatus.ANALYZING,  # P68: 리터럴 → 상수
                 "created_at": datetime.now().isoformat(),
                 "total_count": len(targets)})
    unique_urls = list(dict.fromkeys(t["url"] for t in targets))
    dom_cache: dict[str, dict] = {}

    try:
        for url in unique_urls:
            print(f"[DOM] 분석 중: {url}")
            dom_cache[url] = analyze_url(url)
            dom = dom_cache[url]
            if "error" in dom:
                print(f"  [경고] DOM 분석 실패: {dom['error']}")
            else:
                print(f"  완료 — 입력:{len(dom.get('inputs',[]))} 버튼:{len(dom.get('buttons',[]))}")
    except Exception as e:
        _save_state({"status": ParallelStatus.ERROR, "error": str(e)})  # P68: 리터럴 → 상수
        print(f"[오류] DOM 분석 중 실패: {e}")
        raise

    # 3. 공통 컨텍스트는 파일 경로로 참조 (토큰 절감: 서브에이전트마다 복사하지 않음)
    # parallel_plan: 02a_parallel_dialog.py 심의 후 생성 (사전 심의 전략 공유)
    shared_context_paths = {
        "team_charter": "agents/team_charter.md",
        "lessons_learned": "agents/lessons_learned.md",
        "skill_playwright": ".claude/skills/playwright-best-practices/SKILL.md",
        "parallel_plan": "state/parallel_plan.json",  # 사전 심의 결과 (02a_parallel_dialog 실행 후 생성됨)
    }

    # 4. subagent 컨텍스트 빌드 (배치 단위) — 고유 데이터만 포함
    contexts = []
    for t in targets:
        all_cases = []
        for cp in t["cases_paths"]:
            all_cases.extend(load_cases(str(cp)))

        page_key = t["group_dir"]
        output_dir = PROJECT_ROOT / "tests" / "generated" / t["group_dir"]
        output_dir.mkdir(parents=True, exist_ok=True)

        page_meta = resolve_page_meta(page_key, pages)
        ctx = {
            "group_dir": t["group_dir"],
            "group_label": t["group_label"],
            "batch_info": t.get("batch_info", ""),
            "batch_files": t.get("batch_files", []),
            "url": t["url"],
            "page_meta": page_meta,
            "dom_info": dom_cache.get(t["url"], {}),
            "test_cases": all_cases,
            "test_data": test_data.get(page_key, {}),
            "output_path": f"tests/generated/{t['group_dir']}/",
        }
        contexts.append(ctx)
        files_str = ", ".join(t.get("batch_files", [])[:3])
        if len(t.get("batch_files", [])) > 3:
            files_str += f" 외 {len(t['batch_files']) - 3}개"
        print(f"  [{t['group_label']}] {len(all_cases)}개 케이스 ({files_str}) → {ctx['output_path']}")

    # 5. 상태 파일 저장 (ready = subagent 대기)
    total_cases = sum(len(c["test_cases"]) for c in contexts)
    _save_state({
        "status": ParallelStatus.READY,  # P68: 리터럴 → 상수
        "total_count": len(contexts),
        "total_cases": total_cases,
        "completed_count": 0,
        "targets": [
            {
                "group_dir": c["group_dir"],
                "group_label": c["group_label"],
                "batch_info": c.get("batch_info", ""),
                "url": c["url"],
                "output_path": c["output_path"],
                "case_count": len(c["test_cases"]),
            }
            for c in contexts
        ],
    })

    # 6. subagent 컨텍스트 빌드
    output_payload = {
        "shared_context_paths": shared_context_paths,
        "subagents": contexts,
    }

    # 훅이 로그 파일 없이도 컨텍스트를 읽을 수 있도록 state/parallel.json에 저장 (P89)
    _save_state({"subagent_contexts": output_payload})

    if not args.no_auto:
        # --auto(기본): headless Claude가 state/parallel_contexts.json을 읽으므로
        # 터미널에 대용량 JSON을 출력할 필요 없음
        _launch_headless_parallel(output_payload)
    else:
        # --no-auto: 사람이 직접 Claude에 붙여넣을 수 있도록 전체 컨텍스트 출력
        print()
        print("=== PARALLEL_SUBAGENT_CONTEXTS_START ===")
        print(json.dumps(output_payload, ensure_ascii=False, indent=2))
        print("=== PARALLEL_SUBAGENT_CONTEXTS_END ===")
        print()
        print("=" * 60)
        print("  Claude Code에 아래 지시를 전달하세요:")
        print("=" * 60)
        print()
        print(f"  위 PARALLEL_SUBAGENT_CONTEXTS의 {len(contexts)}개 배치를 Agent tool로 동시에 실행해줘.")
        print(f"  (총 {total_cases}개 케이스, 배치당 최대 {BATCH_SIZE}개)")
        print()
        print("  shared_context_paths의 파일들은 각 subagent가 직접 읽어서 참조합니다.")
        print("  (서브에이전트별 컨텍스트에는 고유 데이터만 포함)")
        print()
        print("  각 subagent는:")
        print("  1. shared_context_paths의 파일들을 먼저 읽기 (lessons_learned, team_charter, SKILL.md)")
        print("  2. 배치 내 모든 test_cases에 대해 dom_info 바탕으로 plan 수립")
        print("  3. plan 기반으로 Playwright 테스트 코드 작성 (tc_*.md 1개 = 파일 1개)")
        print("  4. output_path에 직접 저장")
        print()
        print("  완료 후: python parallel/99_merge.py 실행")
    print("=" * 60)


if __name__ == "__main__":
    main()
