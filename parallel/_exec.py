"""
parallel/_exec.py — 병렬 파이프라인 테스트 파일 수집 + pytest 실행 (P84)

99_merge.py에서 분리된 파일 수집·실행 로직.
공개 API: collect_test_files(), run_pytest()
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_SCRIPTS_DIR = str(Path(__file__).parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from _python import PYTHON_EXE
from _constants import MAX_PYTEST_WORKERS  # m3(P95): 병렬 실행 워커 수

PROJECT_ROOT = Path(__file__).parent.parent
GENERATED_DIR = PROJECT_ROOT / "tests" / "generated"
TESTCASES_DIR = PROJECT_ROOT / "testcases"


def _natural_sort_key(p: Path) -> list:
    """파일명을 숫자 기준으로 정렬하는 키 (tc_10 > tc_9 보장)."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", p.name)]


def _valid_py_files(group_dir: Path) -> list[Path]:
    """testcases/{group}/tc_*.md 기준으로 유효한 .py 파일만 반환 (잔여 파일 제외).

    번호 prefix(tc_01_)로 매칭 — 슬러그 명명 차이 무관하게 동작.
    """
    def _tc_num(name: str) -> str | None:
        m = re.match(r"tc_(\d+)_", name)
        return m.group(1) if m else None

    tc_dir = TESTCASES_DIR / group_dir.name
    if tc_dir.exists():
        valid_nums = {_tc_num(f.name) for f in tc_dir.glob("tc_*.md")} - {None}
        all_py = list(group_dir.glob("tc_*.py"))
        files = [f for f in all_py if _tc_num(f.name) in valid_nums]
        stale = [f for f in all_py if _tc_num(f.name) not in valid_nums]
        if stale:
            print(
                f"[99] 잔여 파일 {len(stale)}개 제외 ({group_dir.name}): "
                + ", ".join(f.name for f in stale[:5])
                + ("..." if len(stale) > 5 else "")
            )
    else:
        files = [f for f in group_dir.glob("*.py")
                 if f.name not in ("conftest.py", "__init__.py")]
    return files


def is_spa_group(groups: list[str] | None) -> bool:
    """그룹 이름 목록에 spa: true 항목이 하나라도 있으면 True 반환.

    pages.json 구조: 키 = 그룹명, 값 = URL 문자열 또는 {"url": ..., "spa": true}.
    groups=None(전체 실행)이면 pages.json 전 항목을 검사.
    """
    pages_json = PROJECT_ROOT / "config" / "pages.json"
    if not pages_json.exists():
        return False
    pages: dict = json.loads(pages_json.read_text(encoding="utf-8"))
    check_keys = groups if groups else [k for k in pages if not k.startswith("_")]
    for key in check_keys:
        cfg = pages.get(key, {})
        if isinstance(cfg, dict) and cfg.get("spa", False):
            return True
    return False


def collect_test_files(group: list[str] | None) -> tuple[list[Path], str]:
    """실행 대상 .py 파일을 수집하고 자연 정렬된 목록과 scope 라벨을 반환.

    Args:
        group: 실행할 그룹 이름 목록. None이면 전체 실행.

    Returns:
        (sorted_files, scope_label)
        sorted_files가 빈 리스트이면 호출부에서 에러 처리 후 종료할 것.
    """
    if group:
        target_dirs = [GENERATED_DIR / g for g in group]
        missing = [str(d) for d in target_dirs if not d.exists()]
        if missing:
            print(f"[오류] 존재하지 않는 폴더: {', '.join(missing)}")
            available = [d.name for d in GENERATED_DIR.iterdir() if d.is_dir()] \
                if GENERATED_DIR.exists() else []
            print(f"  사용 가능한 폴더: {', '.join(available) or '없음'}")
            return [], ", ".join(group)
        raw_files: list[Path] = []
        for d in target_dirs:
            raw_files.extend(_valid_py_files(d))
        scope_label = ", ".join(group)
    else:
        raw_files = []
        if GENERATED_DIR.exists():
            for d in GENERATED_DIR.iterdir():
                if d.is_dir() and not d.name.startswith((".", "_")):
                    raw_files.extend(_valid_py_files(d))
        scope_label = "전체"

    sorted_files = sorted(raw_files, key=_natural_sort_key)

    if not sorted_files:
        print("[오류] 실행할 테스트 파일 없음.")
        if GENERATED_DIR.exists():
            available = [d.name for d in GENERATED_DIR.iterdir() if d.is_dir()]
            if available:
                print(f"  사용 가능한 폴더: {', '.join(available)}")
                print(f"  예시: python parallel/99_merge.py --group {available[0]}")

    return sorted_files, scope_label


def run_pytest(sorted_files: list[Path], *, single_session: bool = False) -> tuple[int, dict]:
    """정렬된 파일 목록으로 pytest를 실행하고 결과를 반환.

    Args:
        sorted_files: 실행할 .py 파일 목록 (자연 정렬 완료 상태).
        single_session: True이면 SPA/세션 충돌 방지를 위해 -n 플래그 생략 (순차 실행).

    Returns:
        (pytest_exit_code, report)
        report: JSON 리포트 dict. pytest가 리포트를 못 만들었으면 {}.

    Notes:
        - Windows 커맨드라인 길이 제한(~32KB) 초과 시 runner 스크립트 방식으로 우회.
        - 타임아웃: 7200초.
    """
    ts = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
    json_report_path = Path(tempfile.gettempdir()) / f"qa_report_{ts}.json"
    _runner_script: Path | None = None

    try:
        file_args = [str(f) for f in sorted_files]
        cmd_len = sum(len(f) + 1 for f in file_args)

        if cmd_len > 20000:
            # 커맨드라인 길이 제한 우회: 임시 runner 스크립트로 pytest.main() 직접 호출
            _json_report_str = str(json_report_path).replace("\\", "\\\\")
            if single_session:
                # spa: true — -n 생략하여 순차 실행 (세션 충돌 방지)
                n_line = ""
            else:
                n_line = f"    '-n', '{MAX_PYTEST_WORKERS}',\n"  # m3(P95): 병렬 실행
            runner_code = (
                "import sys, pytest\n"
                f"files = {file_args!r}\n"
                "args = files + [\n"
                "    '--json-report',\n"
                f"    '--json-report-file={_json_report_str}',\n"
                f"{n_line}"
                "    '--tb=short', '-v',\n"
                "]\n"
                "sys.exit(pytest.main(args))\n"
            )
            af = tempfile.NamedTemporaryFile(
                mode="w", suffix="_pytest_runner.py", delete=False, encoding="utf-8"
            )
            af.write(runner_code)
            af.close()
            _runner_script = Path(af.name)
            cmd = [PYTHON_EXE, str(_runner_script)]
            print(f"[99] 파일 수 {len(sorted_files)}개 — runner 스크립트 방식으로 pytest 실행")
        else:
            _parallel_flags = (
                [] if single_session
                else ["-n", str(MAX_PYTEST_WORKERS)]  # m3(P95): 병렬 실행
            )
            cmd = [PYTHON_EXE, "-m", "pytest"] + file_args + [
                "--json-report",
                f"--json-report-file={json_report_path}",
                *_parallel_flags,
                "--tb=short", "-v",
            ]

        proc = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=False,
            timeout=7200,
        )
        pytest_exit_code = proc.returncode

    except subprocess.TimeoutExpired:
        print("\n[99] pytest 실행 타임아웃 (7200초 초과)")
        pytest_exit_code = -1

    finally:
        if _runner_script and _runner_script.exists():
            _runner_script.unlink(missing_ok=True)

    report: dict = {}
    if json_report_path.exists():
        report = json.loads(json_report_path.read_text(encoding="utf-8"))
        json_report_path.unlink()

    return pytest_exit_code, report
