"""
QA 자동화 진입점.

사용법:
  python run_qa.py --url https://example.com/login --cases config/cases.json

케이스 파일 형식 (두 가지 모두 지원):

  [형식 A] 자연어 문자열 배열 — Claude Code가 DOM 분석 후 steps/assertion 자동 추론
    [
      "정상 로그인이 성공해야 한다",
      "잘못된 비밀번호 입력 시 에러 메시지가 표시되어야 한다"
    ]

  [형식 B] 구조화 객체 배열 — title/steps/expected 직접 지정
    [
      {
        "title": "정상 로그인 성공",
        "steps": [
          "username 필드에 student 입력",
          "password 필드에 Password123 입력",
          "Submit 버튼 클릭"
        ],
        "expected": "Logged In Successfully 텍스트가 표시되어야 한다"
      }
    ]

  [형식 C] 혼합 — 문자열과 객체를 함께 사용 가능
    [
      "잘못된 비밀번호 입력 시 에러 메시지 확인",
      {
        "title": "정상 로그인 성공",
        "steps": ["student 입력", "Password123 입력", "Submit 클릭"],
        "expected": "Logged In Successfully 표시"
      }
    ]
"""
import argparse
import sys
from pathlib import Path

import _bootstrap  # noqa: F401 — scripts/ 경로 설정
from parse_cases import load_cases
from _paths import PIPELINE_STATE, STATE_DIR, PROJECT_ROOT, reset_state
from _pipeline_registry import make_initial_pipeline_state


def init_state(url: str, test_cases: list, cases_path: str) -> dict:
    """pipeline.json 초기 상태 생성 — make_initial_pipeline_state() 에 위임 (P39)."""
    return make_initial_pipeline_state(
        url=url,
        test_cases=test_cases,
        cases_path=str(cases_path),
    )


def print_cases(test_cases: list):
    for i, c in enumerate(test_cases, 1):
        tag = "[구조화]" if c["format"] == "structured" else "[자연어]"
        print(f"    {i}. {tag} {c['title']}")
        if c["format"] == "structured":
            for j, s in enumerate(c["steps"], 1):
                print(f"         step{j}. {s}")
            if c["expected"]:
                print(f"         기대결과: {c['expected']}")


HEADLESS_PROMPT = (
    "CLAUDE.md의 단일 파이프라인으로 state/pipeline.json에 준비된 TC를 끝까지 실행하세요. "
    "01_analyze -> 02a_dialog -> 체크리스트 심의와 plan 저장 -> 02_generate -> scaffold 직접 완성 -> "
    "03_lint -> 03a_dialog -> 체크리스트 리뷰와 review 저장 -> 04_approve -> "
    "05_execute --no-report -> 06_heal 순서로 진행하고, 실패하면 CLAUDE.md의 힐링 절차를 따르세요. "
    "전체 통과를 확인한 뒤 마지막 05_execute로 HTML 리포트를 생성하세요. "
    "모든 Python 명령은 프로젝트 루트의 .venv/bin/python을 사용하세요. "
    "state 변경은 update_state와 레지스트리 상수를 사용하고 step을 수동 덮어쓰지 마세요. "
    "md 하나당 실제 동작과 Expected를 검증하는 테스트 파일·함수 하나를 작성하세요. "
    "사용할 수 없는 MCP·스킬·에이전트 도구는 직접 체크리스트 판단으로 진행하세요. "
    "추가 에이전트를 호출하지 말고, 주어진 TC와 DOM을 근거로 추가 질문 없이 완료하세요. "
    "외부 LLM SDK·API 키·dangerously-skip-permissions 사용, git commit·push는 금지합니다. "
    "완료 시 실제 실행 결과와 리포트 경로를 보고하세요."
)


def _launch_headless_pipeline() -> None:
    """claude -p(헤드리스) 세션을 백그라운드로 띄워 파이프라인을 끝까지 자동 실행한다.

    기존에는 state/pipeline.json만 써두고 "다른 데서 Claude Code 세션이 훅으로
    우연히 감지하기"를 기다렸는데, 그 방식은 실제로 이어받는 세션이 없으면
    영원히 멈춰있는 문제가 있었다. --auto(기본값)에서는 이 스크립트가 직접
    claude CLI를 non-interactive 모드로 실행해 파이프라인을 완결시킨다.

    파일 편집은 acceptEdits, 실행은 프로젝트 .venv/bin/python 패턴만 허용한다.
    MCP 설정과 사용 도구를 제한하여 대시보드에서도 같은 권한으로 자동 실행한다.
    """
    import subprocess

    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_path = logs_dir / "run_qa_headless.txt"

    print()
    print("  [자동 실행] headless Claude Code 세션을 백그라운드로 시작합니다.")
    print(f"  로그: {log_path}")
    print("  (수동으로 이어받고 싶다면 --no-auto 옵션으로 재실행하세요)")

    # context manager: Popen 예외 시에도 log_file이 반드시 닫힘.
    # POSIX에서 부모가 fd를 닫아도 자식은 dup된 fd로 계속 씀 — 데이터 유실 없음.
    with open(log_path, "w", encoding="utf-8") as log_file:
        subprocess.Popen(
            [
                "claude", "-p", HEADLESS_PROMPT,
                "--settings", '{"disableAllHooks":true}',
                "--strict-mcp-config",
                "--tools", "Read,Write,Edit,Glob,Grep,Bash",
                "--permission-mode", "acceptEdits",
                "--allowedTools", "Read", "Write", "Edit", "Glob", "Grep",
                "Bash(.venv/bin/python *)",
                "--output-format", "text",
            ],
            cwd=str(PROJECT_ROOT),
            stdout=log_file, stderr=subprocess.STDOUT,
        )


def run_single(url: str, test_cases: list, cases_path: str, auto: bool = True):
    """단일 파이프라인: state/pipeline.json 생성 후 자동 실행(기본) 또는 안내만 출력(--no-auto)."""
    natural_count    = sum(1 for c in test_cases if c["format"] == "natural")
    structured_count = sum(1 for c in test_cases if c["format"] == "structured")

    state = init_state(url, test_cases, cases_path)
    STATE_DIR.mkdir(exist_ok=True)
    # reset_state()로 FSM 검증 없이 초기화 (step="init"은 전이 규칙 시작점이므로 우회 허용)
    reset_state(PIPELINE_STATE, state)

    print("=" * 55)
    print("  QA 자동화 파이프라인 초기화 완료 [단일 모드]")
    print("=" * 55)
    print(f"  URL   : {url}")
    print(f"  케이스 : {len(test_cases)}개  (자연어 {natural_count} / 구조화 {structured_count})")
    print_cases(test_cases)
    print()
    print("  state/pipeline.json 생성 완료.")

    if auto:
        _launch_headless_pipeline()
    else:
        print()
        print("  -- Claude Code에 아래 메시지를 붙여넣으세요 --")
        print()
        print("  " + HEADLESS_PROMPT.replace(". ", ".\n  "))
    print("=" * 55)


def main():
    parser = argparse.ArgumentParser(description="QA 자동화 파이프라인 시작 (단일 모드)")
    parser.add_argument("--url",   required=True, help="테스트 대상 URL")
    parser.add_argument("--cases", default=None,  help="테스트 케이스 파일 경로 (.md 또는 .json)")
    parser.add_argument("--no-auto", action="store_true",
                         help="headless Claude Code 자동 실행을 생략하고 안내 메시지만 출력 (기존 동작)")
    args = parser.parse_args()

    if args.cases and Path(args.cases).exists():
        test_cases = load_cases(args.cases)
    else:
        print("[오류] --cases 옵션으로 케이스 파일을 지정하세요. (.md 또는 .json)")
        sys.exit(1)

    run_single(args.url, test_cases, args.cases, auto=not args.no_auto)


if __name__ == "__main__":
    main()
