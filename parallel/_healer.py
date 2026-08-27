"""
parallel/_healer.py — 병렬 파이프라인 힐링 판단·실행 (P84)

99_merge.py에서 분리된 힐링 로직.
공개 API:
  - should_heal()        힐링 여부/종류 결정
  - run_heal_cycle()     heal_context 생성 + auto_heal 시도
  - verify_lessons_learned_updated()  패치 후 lessons_learned 기록 확인
  - print_heal_instructions()         힐링 배치 출력 (하위 호환)
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from _paths import (
    HEAL_CONTEXT_STATE, read_state, write_state, update_state,
)
from _python import PYTHON_EXE
from _constants import MAX_HEAL
from _pipeline_registry import ParallelStatus
from heal_utils import (
    classify_error, find_screenshot_for_test,
    append_lessons, update_heal_stats,
    build_heal_batches, print_heal_batches,
    LESSONS_PATH, LESSONS_AUTO_PATH,
    snapshot_assertions, compare_assertions,
)
from structured_log import slog

PROJECT_ROOT = Path(__file__).parent.parent


# ── 내부 헬퍼 ────────────────────────────────────────────────────────────────


def _check_urls_accessible(urls: dict) -> dict | None:
    """힐링 전 사이트 접근 가능 여부를 사전 체크. 접근 불가 시 에러 dict 반환."""
    import urllib.request
    import urllib.error
    for group, url in urls.items():
        if not url:
            continue
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.getcode()
            if status >= 400:
                return {"error": f"사이트 접근 불가 HTTP {status}", "url": url, "group": group}
        except (urllib.error.URLError, OSError) as e:
            return {"error": f"사이트 접근 불가: {e}", "url": url, "group": group}
    return None


def _detect_repeated_failures_parallel(
    current_failures: list[dict], prev_ctx: dict
) -> tuple[list[dict], list[dict]]:
    """이전 heal_context와 비교하여 동일 (test_name, error_type) 반복 감지.

    M-3(P101): prev_failures(안정 스냅샷) 우선 사용.
    auto_heal이 heal_context["failures"]를 잔여 목록으로 덮어쓰므로
    "failures"만 보면 다음 라운드의 반복 감지 기준선이 어긋난다.

    Returns:
        (healable, skipped)
    """
    prev_failures = (
        prev_ctx.get("prev_failures")
        or prev_ctx.get("failures", [])
    )
    if not prev_failures:
        return current_failures, []

    prev_signatures = {
        (f.get("test_name", ""),
         f.get("error_type") or classify_error(f.get("traceback", "")))
        for f in prev_failures
    }

    healable, skipped = [], []
    for f in current_failures:
        sig = (f.get("test_name", ""), f.get("error_type", ""))
        if sig in prev_signatures:
            skipped.append(f)
        else:
            healable.append(f)
    return healable, skipped


def _build_heal_context(report: dict, heal_count: int, state_path: Path) -> dict | None:
    """실패 테스트의 traceback을 모아 heal_context.json 생성. 실패 없으면 None 반환.

    단일 파이프라인(06_heal.py)과 동일한 플로우:
    1. 실패 수집 + 스크린샷 연결
    2. classify_error로 에러 분류 + failure_groups 구성
    3. 사이트 사전 접근 체크
    4. 반복 실패 감지
    5. append_lessons + update_heal_stats
    6. 힐링 전 assertion 스냅샷 저장
    """
    failures = []
    for t in report.get("tests", []):
        if t.get("outcome") in ("failed", "error"):
            call = t.get("call") or {}
            longrepr = call.get("longrepr", "")
            if isinstance(longrepr, dict):
                longrepr = longrepr.get("reprcrash", {}).get("message", str(longrepr))
            test_name = t.get("nodeid", "").split("::")[-1]
            traceback_str = str(longrepr)
            failures.append({
                "test_id":    t.get("nodeid", ""),
                "test_name":  test_name,
                "file":       t.get("nodeid", "").split("::")[0],
                "traceback":  traceback_str,
                "error_type": classify_error(traceback_str),
                "screenshot": find_screenshot_for_test(test_name),
            })
    if not failures:
        return None

    # 실패 그룹의 URL 수집 (pages.json에서)
    urls: dict[str, str] = {}
    pages_path = PROJECT_ROOT / "config" / "pages.json"
    if pages_path.exists():
        try:
            pages_data = json.loads(pages_path.read_text(encoding="utf-8"))
            for f in failures:
                group = f["file"].split("/")[-2] if "/" in f["file"] else None
                if group and group in pages_data and group not in urls:
                    entry = pages_data[group]
                    urls[group] = entry.get("url") if isinstance(entry, dict) else entry
        except Exception:
            pass

    # 사이트 접근 가능성 사전 체크
    if urls:
        site_err = _check_urls_accessible(urls)
        if site_err:
            print(f"\n[99] 사이트 접근 불가: {site_err['url']} ({site_err['error']})")
            print("     사이트가 다운되었거나 네트워크 문제입니다. 힐링을 건너뜁니다.")
            ctx = {
                "heal_count":  heal_count,
                "error":       site_err["error"],
                "url":         site_err["url"],
                "analyzed_at": datetime.now().isoformat(),
            }
            write_state(HEAL_CONTEXT_STATE, ctx)
            return None

    # 에러 타입별 그룹핑
    failure_groups: dict[str, list[str]] = defaultdict(list)
    for f in failures:
        failure_groups[f["error_type"]].append(f["test_name"])

    # 반복 실패 감지
    prev_ctx = read_state(HEAL_CONTEXT_STATE)
    healable, skipped = _detect_repeated_failures_parallel(failures, prev_ctx)

    if skipped:
        skipped_names = [f["test_name"] for f in skipped]
        print(f"\n[99] 동일 오류 2회 연속 반복 → {len(skipped)}건 스킵:")
        for name in skipped_names:
            print(f"     - {name}")
        for s in skipped:
            slog("heal_skip_repeated", test_name=s["test_name"],
                 error_type=s.get("error_type", ""), pipeline="parallel")

    # 모든 실패가 반복 → 힐링 중단
    if not healable and skipped:
        print("[99] 모든 실패가 반복 패턴 -- 수동 수정이 필요합니다.")
        ctx = {
            "heal_count":      heal_count,
            "skipped_repeated": [f["test_name"] for f in skipped],
            "error":           "모든 실패가 동일 오류 2회 반복. 수동 수정 필요.",
            "analyzed_at":     datetime.now().isoformat(),
        }
        write_state(HEAL_CONTEXT_STATE, ctx)
        append_lessons(failures)
        update_heal_stats(failures)
        return None

    # 최신 lessons_learned 스냅샷 (subagent 간 학습 공유)
    lessons_snapshot = ""
    for lpath in [LESSONS_PATH, LESSONS_AUTO_PATH]:
        if lpath.exists():
            try:
                lessons_snapshot += lpath.read_text(encoding="utf-8") + "\n"
            except Exception:
                pass

    ctx = {
        "heal_count":      heal_count,
        "failure_count":   len(healable),
        "failures":        healable,
        # M-3(P101): 다음 라운드 반복 감지용 안정 스냅샷.
        # auto_heal이 "failures"를 잔여 목록으로 덮어써도 이 키는 유지된다.
        "prev_failures":   [
            {"test_name": f.get("test_name", ""), "test_id": f.get("test_id", ""),
             "error_type": f.get("error_type", ""), "traceback": f.get("traceback", "")}
            for f in healable
        ],
        "failure_groups":  dict(failure_groups),
        "skipped_repeated": [f["test_name"] for f in skipped],
        "urls":            urls,
        "lessons_snapshot": lessons_snapshot[-3000:] if lessons_snapshot else "",
        "analyzed_at":     datetime.now().isoformat(),
    }
    write_state(HEAL_CONTEXT_STATE, ctx)
    print(
        f"\n[99] heal_context 저장됨: {HEAL_CONTEXT_STATE}  "
        f"(힐링 대상 {len(healable)}건"
        + (f", 반복 스킵 {len(skipped)}건" if skipped else "") + ")"
    )

    # 실수 패턴 자동 기록 + heal_stats 빈도 업데이트
    append_lessons(healable + skipped)
    update_heal_stats(healable + skipped)

    # M-1(P100): auto-append 완료 직후 타임스탬프 저장.
    # verify_lessons_learned_updated가 이 시각 이후의 갱신만 "Agent 기록"으로 인정한다.
    # (analyzed_at 직후 append_lessons()가 auto.md를 갱신하므로 analyzed_at 기준은 항상 통과)
    _post_auto_at = datetime.now().isoformat()
    write_state(HEAL_CONTEXT_STATE, {**ctx, "post_auto_lessons_at": _post_auto_at})

    # 힐링 전 assertion 스냅샷 저장 (06_heal.py와 동일한 정책)
    failing_files = sorted({
        str(f["file"]) if Path(f["file"]).is_absolute() else str(PROJECT_ROOT / f["file"])
        for f in healable if f.get("file")
    })
    pre_snap = snapshot_assertions(failing_files)

    def _snap_mutator(fresh: dict) -> dict:
        updated = {
            **fresh,
            "pre_heal_assertions": pre_snap,
            "pre_heal_files":      failing_files,
        }
        if not fresh.get("original_assertions"):
            updated["original_assertions"] = pre_snap
        return updated

    update_state(state_path, _snap_mutator)
    return ctx


def _try_auto_heal(state_path: Path | None = None) -> bool:
    """06_auto_heal.py를 subprocess로 호출하여 deterministic 패치 시도 (P53).

    Returns:
        True: auto_heal이 일부/전부 패치 성공 (재실행 필요)
        False: 자동 패치 가능한 패턴 없음 (Agent 힐링 필요)
    """
    auto_heal_script = PROJECT_ROOT / "scripts" / "06_auto_heal.py"
    if not auto_heal_script.exists():
        return False
    cmd = [PYTHON_EXE, str(auto_heal_script)]
    if state_path is not None:
        cmd += ["--state-path", str(state_path)]
        if state_path.name in ("parallel.json", "quick.json"):
            cmd += ["--state-key", "status"]
    # P65: 병렬 파이프라인은 heal_context를 HEAL_CONTEXT_STATE에 별도 저장
    if HEAL_CONTEXT_STATE.exists():
        cmd += ["--heal-context-path", str(HEAL_CONTEXT_STATE)]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True,
            timeout=120,
        )
        if result.stdout.strip():
            for line in result.stdout.strip().splitlines():
                print(f"  {line}")
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception) as e:
        print(f"  [auto_heal] 실행 실패 (무시): {e}")
        return False


# ── 공개 API ─────────────────────────────────────────────────────────────────


# should_heal 반환값 리터럴 타입
_HealDecision = str  # 'skip' | 'over_limit' | 'heal' | 'ok'


def should_heal(
    pytest_exit_code: int,
    failed_count: int,
    no_heal: bool,
    heal_count: int,
) -> _HealDecision:
    """힐링이 필요한지, 가능한지 결정.

    Returns:
        'ok'         실패 없음 — 힐링 불필요
        'skip'       실패 있지만 --no-heal 플래그
        'over_limit' 최대 힐링 횟수(MAX_HEAL) 초과
        'heal'       힐링 진행 가능
    """
    has_issues = pytest_exit_code != 0 or failed_count > 0
    if not has_issues:
        return "ok"
    if no_heal:
        return "skip"
    if heal_count >= MAX_HEAL:
        return "over_limit"
    return "heal"


def run_heal_cycle(
    report: dict,
    heal_count: int,
    state_path: Path,
    quick_mode: bool,
) -> tuple[bool, bool]:
    """heal_context 생성 + auto_heal 시도.

    Args:
        report:     pytest JSON 리포트 dict
        heal_count: 현재까지의 힐링 횟수 (이미 +1 증가된 값)
        state_path: 상태 파일 경로 (PARALLEL_STATE or QUICK_STATE)
        quick_mode: True이면 quick 파이프라인

    Returns:
        (heal_applied, heal_impossible)
        heal_applied:    True이면 auto_heal이 패치 성공 (재실행 필요)
        heal_impossible: True이면 사이트 불가·전체 반복으로 힐링 불가
    """
    heal_ctx = _build_heal_context(report, heal_count, state_path)
    if not heal_ctx:
        # build_heal_context가 None = 사이트 불가 또는 전체 반복 (P67)
        return False, True

    # auto_heal 시도 (deterministic 패치)
    auto_heal_applied = _try_auto_heal(state_path=state_path)
    # H-2(P105): auto_heal 후 heal_ctx 재로드 — 06_auto_heal이 HEAL_CONTEXT_STATE를 갱신했을 수 있음.
    # (--heal-context-path 지정 시 H-2 수정으로 해당 파일에도 동기화됨)
    if HEAL_CONTEXT_STATE.exists():
        _reloaded = read_state(HEAL_CONTEXT_STATE)
        if _reloaded:
            heal_ctx = _reloaded
    pipeline_label = "quick" if quick_mode else "parallel"
    if auto_heal_applied:
        print("[99] auto_heal 성공 -- Agent 힐링 불필요할 수 있습니다.")
        print("     python parallel/99_merge.py 를 다시 실행하여 확인하세요.")
        # H-3(P106): auto_heal이 모든 실패를 수정한 경우 힐링 지시 스킵.
        # heal_ctx.failures=[] 이면 subagent에게 전달할 작업이 없음.
        if not heal_ctx.get("failures"):
            # H-1(P116): stale heal_subagent_contexts 소거 — P106(H-3) 조기 반환 시
            # 이전 라운드 배치가 훅(check_pending_quick_heal.py)에 재주입되는 것을 방지한다.
            update_state(state_path, lambda fresh: {
                k: v for k, v in fresh.items() if k != "heal_subagent_contexts"
            })
            return auto_heal_applied, False
    print_heal_instructions(heal_ctx, pipeline=pipeline_label, state_path=state_path)
    return auto_heal_applied, False


def print_heal_instructions(heal_context: dict, pipeline: str = "parallel",
                            state_path: "Path | None" = None) -> None:
    """배치 분할 병렬 힐링 지시를 출력."""
    failures = heal_context.get("failures", [])
    urls = heal_context.get("urls", {})
    url = next(iter(urls.values()), "") if urls else ""
    batches = build_heal_batches(failures)
    print_heal_batches(batches, url=url, pipeline=pipeline, state_path=state_path)


def verify_lessons_learned_updated(heal_start_time: str) -> bool:
    """힐링 후 lessons_learned.md 또는 lessons_learned_auto.md가 업데이트되었는지 검증.

    M-1(P100): 기준 시각으로 heal_context의 post_auto_lessons_at을 우선 사용한다.
    _build_heal_context()가 append_lessons() 직후 이 타임스탬프를 저장하므로,
    auto-append 이전에 기록된 변경만 통과 → "Agent가 직접 기록했는가"를 올바르게 감지.
    post_auto_lessons_at 없으면 heal_start_time(analyzed_at)을 fallback으로 사용.
    """
    # post_auto_lessons_at: _build_heal_context()가 append_lessons() 직후 저장
    _ctx = read_state(HEAL_CONTEXT_STATE) if HEAL_CONTEXT_STATE.exists() else {}
    effective_start = _ctx.get("post_auto_lessons_at") or heal_start_time

    if not LESSONS_PATH.exists() and not LESSONS_AUTO_PATH.exists():
        return False
    try:
        from datetime import datetime as dt
        start = dt.fromisoformat(effective_start)
        mtimes = []
        for lpath in [LESSONS_PATH, LESSONS_AUTO_PATH]:
            if lpath.exists():
                mtimes.append(dt.fromtimestamp(lpath.stat().st_mtime))
        if mtimes and max(mtimes) > start:
            return True
    except Exception:
        pass
    print()
    print("⚠ [경고] lessons_learned.md 기록이 누락되었습니다!")
    print("  힐링 패치 후 반드시 agents/lessons_learned.md에 기록해야 합니다.")
    print("  형식: ### [힐링] {날짜} -- {파일명}")
    print("        - **문제**: {traceback 요약}")
    print("        - **수정**: {적용한 패치 내용}")
    print("        - **재발 방지**: {동일 실수 방지 규칙}")
    print()
    return False


def check_assertion_integrity(heal_count: int, state_path: Path) -> None:
    """힐링을 거쳐 통과한 경우 패치 전/후 assertion 무결성 확인 (경고만 출력).

    단일 파이프라인의 assert_guard.py와 동일한 방식.
    """
    prior_run_state = read_state(state_path)
    pre_heal = prior_run_state.get("pre_heal_assertions")
    if not pre_heal:
        return
    baseline = prior_run_state.get("original_assertions") or pre_heal
    post_files = prior_run_state.get("pre_heal_files") or list(pre_heal.keys())
    post_snap = snapshot_assertions(post_files)
    integrity = compare_assertions(baseline, post_snap)
    integrity["baseline"] = (
        "최초 생성 기준" if prior_run_state.get("original_assertions") else "직전 패치 기준"
    )
    integrity["heal_round"] = heal_count
    if integrity["has_warnings"]:
        print()
        print("=" * 60)
        print(
            f"  ⚠️  [assertion 무결성 경고] 힐링 중 assertion이 약화되었을 수 있습니다"
            f" ({integrity['baseline']}, {heal_count}회차)"
        )
        print("=" * 60)
        for w in integrity["warnings"]:
            print(f"  - {w}")
        print("=" * 60)
        print()
    else:
        print(f"[99] assertion 품질 이상 없음 ({integrity['baseline']}).")
    update_state(state_path, lambda fresh: {**fresh, "assertion_integrity": integrity})
