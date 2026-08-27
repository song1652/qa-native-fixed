"""
Step 2 -- 테스트 코드 뼈대 생성 (파일별 scaffold)
LLM 없음. plan을 읽어 케이스별 개별 파일로 뼈대를 생성.
Claude Code가 각 뼈대를 완성해 tests/generated/{group}/ 에 저장.

뼈대 생성 후 Claude Code에게:
  "02_generate.py가 생성한 뼈대를 기반으로
   tests/generated/{group}/ 아래 각 파일을 완성해줘.
   실제 셀렉터와 assertion을 plan의 내용대로 채워넣어."
"""
import re
import sys
from pathlib import Path
from _paths import PIPELINE_STATE, read_state, update_state
from _pipeline_registry import Step  # P68: Step 상수 사용 — 문자열 리터럴 대신


CONFTEST_TEMPLATE = '''import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright


@pytest.fixture(scope="session")
def browser_instance():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture
def page(browser_instance):
    context = browser_instance.new_context()
    page = context.new_page()
    yield page
    context.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page:
            shot_dir = Path("tests/screenshots")
            shot_dir.mkdir(parents=True, exist_ok=True)
            path = shot_dir / f"{item.name}.png"
            try:
                page.screenshot(path=str(path))
                print(f"\\n스크린샷 저장: {path}")
            except Exception:
                pass
'''

PER_CASE_SCAFFOLD = '''"""
자동 생성된 Playwright 테스트 코드
URL: {url}
케이스: {case_name} ({case_id})

Claude Code가 plan 기반으로 완성한 파일.
수동 편집 가능.
"""
from pathlib import Path

BASE_URL = "{url}"

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEST_DATA_PATH = PROJECT_ROOT / "config" / "test_data.json"


def {func_name}(page):
    """{description}"""
    # TODO: Claude Code가 아래를 완성
    # 케이스 타입: {case_type}
    # data_key: {data_key}
    # 전략: {steps_hint}
    # 검증: {assertion_hint}
    pass
'''


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s_]', '', text)
    text = re.sub(r'[\s]+', '_', text)
    text = text.strip('_')
    return text[:50] if text else "unnamed"


def main():
    state_path = PIPELINE_STATE
    if not state_path.exists():
        print("[오류] state/pipeline.json 없음.")
        sys.exit(1)

    state = read_state(state_path)

    if not state.get("plan"):
        print("[오류] plan 없음. Claude Code가 전략 수립을 먼저 완료해야 합니다.")
        sys.exit(1)

    plan = state["plan"]
    url = state["url"]
    group_dir = state.get("group_dir", "default")

    # conftest.py 생성 (이미 있으면 건너뜀)
    conftest_path = Path("tests/conftest.py")
    if not conftest_path.exists():
        conftest_path.parent.mkdir(parents=True, exist_ok=True)
        conftest_path.write_text(CONFTEST_TEMPLATE, encoding="utf-8")
        print(f"[02] conftest.py 생성: {conftest_path}")
    else:
        print(f"[02] conftest.py 이미 존재 -- 건너뜀: {conftest_path}")

    # 출력 디렉토리: 기존 .py 파일 정리 후 재생성 (잔여 파일 누적 방지)
    out_dir = Path("tests/generated") / group_dir
    if out_dir.exists():
        stale = [f for f in out_dir.glob("tc_*.py")]
        if stale:
            print(f"[02] 잔여 파일 {len(stale)}개 정리: {out_dir}")
            for f in stale:
                f.unlink()
    out_dir.mkdir(parents=True, exist_ok=True)

    # __init__.py (pytest 모듈 충돌 방지)
    for init_dir in [Path("tests/generated"), out_dir]:
        init_file = init_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")

    # 케이스별 scaffold 파일 생성
    generated_files = []
    for idx, case in enumerate(plan):
        raw_name = case.get("case_name", f"case_{idx}")
        func_name = slugify(raw_name)
        # test_ 접두사 중복 방지: case_name이 이미 test_로 시작하면 그대로 사용
        if not func_name.startswith("test_"):
            func_name = f"test_{func_name}"
        case_id = case.get("case_id", f"tc_{idx + 1:02d}")
        case_num = case_id.replace("tc_", "") if case_id.startswith("tc_") else f"{idx + 1:02d}"

        # 파일명: test_ 접두사 + tc_XX_ 접두사 중복 방지
        file_slug = func_name[5:] if func_name.startswith("test_") else func_name
        # case_name이 "tc_01_xxx" 형태면 "tc_01_" 부분 제거
        file_slug = re.sub(r'^tc_\d+_', '', file_slug)
        filename = f"tc_{case_num}_{file_slug}.py"
        out_path = out_dir / filename

        steps_hint = " → ".join(
            f"{s.get('action', '?')}({s.get('selector', '?')})"
            for s in case.get("steps", [])
        )
        assertion = case.get("assertion", {})
        if isinstance(assertion, list):
            assertion_hint = " + ".join(
                f"{a.get('type', '?')}: {a.get('expected', '?')}" for a in assertion
            )
        else:
            assertion_hint = (
                f"{assertion.get('type', '?')}: {assertion.get('expected', '?')}"
            )

        scaffold = PER_CASE_SCAFFOLD.format(
            url=url,
            case_name=case.get("case_name", f"case_{idx}"),
            case_id=case_id,
            func_name=func_name,
            description=case.get("description", case.get("case_name", "")),
            case_type=case.get("case_type", ""),
            data_key=case.get("data_key", "null"),
            steps_hint=steps_hint,
            assertion_hint=assertion_hint,
        )

        out_path.write_text(scaffold, encoding="utf-8")
        generated_files.append(str(out_path))

    # state 업데이트 — 원자적 RMW (P43)
    # read_state 이후 다른 프로세스(대시보드 등)가 쓴 필드를 보존한다.
    _gfp = str(out_dir) + "/"
    update_state(state_path, lambda s: {
        **s,
        "step": Step.GENERATED,  # P68: 리터럴 → 상수
        "generated_file_path": _gfp,
        "generated_files": generated_files,
    })

    print(f"[02] 파일별 뼈대 생성 완료: {out_dir}/  ({len(plan)}개 파일)")
    for f in generated_files:
        print(f"     {f}")
    print()
    print("[다음] Claude Code가 각 뼈대를 완성합니다.")
    print("       실제 셀렉터와 assertion을 plan 내용대로 채워넣습니다.")


if __name__ == "__main__":
    main()
