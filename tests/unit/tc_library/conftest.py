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

@pytest.fixture
def fake_claude(tmp_path: Path, monkeypatch):
    """가짜 claude 실행 파일을 만들고 TCS_CLAUDE_BIN으로 가리킨다. 모드는 FAKE_CLAUDE_MODE로 바꾼다."""
    source = (Path(__file__).parent / "fake_claude.py").read_text(encoding="utf-8")
    exe = tmp_path / "bin" / "claude"
    exe.parent.mkdir()
    exe.write_text(f"#!{sys.executable}\n" + source.split("\n", 1)[1], encoding="utf-8")
    exe.chmod(0o755)
    args_file = tmp_path / "claude_args.json"
    monkeypatch.setenv("TCS_CLAUDE_BIN", str(exe))
    monkeypatch.setenv("FAKE_CLAUDE_ARGS", str(args_file))
    monkeypatch.setenv("FAKE_CLAUDE_MODE", "ok")
    return args_file
