"""
Step 3 -- 코드 lint 검사
LLM 없음. flake8 실행 후 결과를 state.json에 저장.
Claude Code는 결과를 보고 QA 리드용 요약을 직접 작성한다.
"""
import json
import subprocess
import sys
from pathlib import Path
from _python import PYTHON_EXE
from _paths import PIPELINE_STATE, read_state, update_state
from _constants import DEFAULT_GENERATED_FILE
from _pipeline_registry import Step  # P68: Step 상수 사용 — 문자열 리터럴 대신


def _make_lint_mutator(lint_result: dict):
    """lint 결과 필드만 최신 상태 위에 병합하는 mutator를 만든다.

    state를 읽은 뒤 flake8 서브프로세스를 거쳐 쓰기까지 시간이 벌어지므로,
    미리 읽어둔 state를 통째로 되쓰면 그 사이 다른 프로세스가 쓴 값이 유실된다.
    이 스크립트가 소유한 필드만 갱신한다.
    """
    def _mutator(fresh: dict) -> dict:
        return {**fresh, "lint_result": lint_result, "step": Step.REVIEWED}  # P68: 리터럴 → 상수

    return _mutator


def main():
    state_path = PIPELINE_STATE
    if not state_path.exists():
        print("[오류] state/pipeline.json 없음.")
        sys.exit(1)

    state = read_state(state_path)
    file_path = state.get("generated_file_path", DEFAULT_GENERATED_FILE)

    p = Path(file_path)
    if not p.exists():
        print(f"[오류] 테스트 경로 없음: {file_path}")
        sys.exit(1)

    # 디렉토리면 내부 *.py 파일 전체 lint
    if p.is_dir():
        target_files = [
            str(f) for f in sorted(p.glob("*.py"))
            if f.name not in ("__init__.py", "conftest.py")
        ]
    else:
        target_files = [file_path]

    if not target_files:
        print(f"[오류] lint 대상 파일 없음: {file_path}")
        sys.exit(1)

    print(f"[03] lint 검사 중: {len(target_files)}개 파일")

    result = subprocess.run(
        [PYTHON_EXE, "-m", "flake8"] + target_files
        + ["--max-line-length=120", "--statistics"],
        capture_output=True, text=True
    )

    issues_raw = result.stdout.strip()
    issue_lines = [l for l in issues_raw.splitlines() if l.strip()]

    lint_result = {
        "passed":      result.returncode == 0,
        "issue_count": len(issue_lines),
        "issues":      issues_raw if issues_raw else "이슈 없음",
        "file":        file_path,
    }

    update_state(state_path, _make_lint_mutator(lint_result))

    status = "통과" if lint_result["passed"] else f"이슈 {lint_result['issue_count']}건"
    print(f"[03] lint {status}")
    if not lint_result["passed"]:
        print(lint_result["issues"])

    print()
    print("[다음] Claude Code가 코드 + lint 결과를 보고 QA 리드용 요약을 작성합니다.")


if __name__ == "__main__":
    main()
