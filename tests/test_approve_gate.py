"""scripts/04_approve.py 단위 테스트 (#26).

배경: 04_approve.py는 stdin이 없으면(headless) 예전엔 "대시보드 대기"로
빠져 exit 3을 내며 approval_status="pending"을 기록했는데, 대시보드에
그 UI가 실제로 존재하지 않아 파이프라인이 영구 정지하는 데드엔드였다.
그 --auto 플래그와 exit 3 폴백을 제거했다.

테스트 대상:
- --auto 플래그가 더 이상 존재하지 않음 (재도입 방지)
- stdin 없음(EOFError) 시 exit 1로 명확히 실패하고, state를 건드리지 않음
- _auto_approve_enabled()는 그대로 동작 (회귀 없음)
"""
import importlib.util
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))


@pytest.fixture
def approve_mod():
    """숫자 프리픽스 모듈이라 importlib으로 매번 새로 로드 (모듈 전역 오염 방지)."""
    spec = importlib.util.spec_from_file_location(
        "approve_gate", str(_SCRIPTS_DIR / "04_approve.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestAutoFlagRemoved:
    """#26 — --auto 플래그(대시보드 대기 모드)는 존재하지 않아야 한다."""

    def test_source_has_no_auto_flag(self):
        src = (_SCRIPTS_DIR / "04_approve.py").read_text(encoding="utf-8")
        assert "--auto" not in src

    def test_source_has_no_exit_3(self):
        src = (_SCRIPTS_DIR / "04_approve.py").read_text(encoding="utf-8")
        assert "sys.exit(3)" not in src

    def test_argparse_rejects_auto_flag(self, approve_mod, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["04_approve.py", "--auto"])
        with pytest.raises(SystemExit) as exc_info:
            approve_mod._parse_args()
        assert exc_info.value.code == 2  # argparse의 "unrecognized arguments" 종료코드

    def test_argparse_still_accepts_yes_flag(self, approve_mod, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["04_approve.py", "--yes"])
        args = approve_mod._parse_args()
        assert args.yes is True


class TestAutoApproveEnabled:
    """_auto_approve_enabled() 회귀 없음 확인."""

    def test_yes_flag_short_circuits(self, approve_mod):
        assert approve_mod._auto_approve_enabled(yes_flag=True) is True

    def test_reads_config_true(self, approve_mod, tmp_path, monkeypatch):
        cfg = tmp_path / "pipeline.json"
        cfg.write_text('{"auto_approve": true}', encoding="utf-8")
        monkeypatch.setattr(approve_mod, "_PIPELINE_CONFIG", cfg)
        assert approve_mod._auto_approve_enabled(yes_flag=False) is True

    def test_reads_config_false(self, approve_mod, tmp_path, monkeypatch):
        cfg = tmp_path / "pipeline.json"
        cfg.write_text('{"auto_approve": false}', encoding="utf-8")
        monkeypatch.setattr(approve_mod, "_PIPELINE_CONFIG", cfg)
        assert approve_mod._auto_approve_enabled(yes_flag=False) is False

    def test_missing_config_defaults_false(self, approve_mod, tmp_path, monkeypatch):
        monkeypatch.setattr(approve_mod, "_PIPELINE_CONFIG", tmp_path / "no_such_file.json")
        assert approve_mod._auto_approve_enabled(yes_flag=False) is False


class TestEofFallbackFailsClosed:
    """stdin이 없는 headless 환경에서 exit 1로 명확히 실패해야 한다 (죽은 대시보드 대기 아님)."""

    def _make_state_files(self, tmp_path, monkeypatch, approve_mod, *, auto_approve=False):
        state_path = tmp_path / "pipeline.json"
        state_path.write_text(
            '{"url": "https://example.com", "test_cases": [], '
            '"review_summary": "", "lint_result": {}, '
            '"generated_file_path": ""}',
            encoding="utf-8",
        )
        cfg_path = tmp_path / "config_pipeline.json"
        cfg_path.write_text(f'{{"auto_approve": {"true" if auto_approve else "false"}}}',
                             encoding="utf-8")
        monkeypatch.setattr(approve_mod, "PIPELINE_STATE", state_path)
        monkeypatch.setattr(approve_mod, "_PIPELINE_CONFIG", cfg_path)
        return state_path

    def test_eof_exits_1_not_3(self, approve_mod, tmp_path, monkeypatch):
        self._make_state_files(tmp_path, monkeypatch, approve_mod)
        monkeypatch.setattr(sys, "argv", ["04_approve.py"])
        monkeypatch.setattr("builtins.input", lambda *_: (_ for _ in ()).throw(EOFError()))

        with pytest.raises(SystemExit) as exc_info:
            approve_mod.main()
        assert exc_info.value.code == 1

    def test_eof_does_not_mutate_state(self, approve_mod, tmp_path, monkeypatch):
        """예전엔 approval_status="pending"을 기록했다 — 이제는 state를 건드리지 않는다."""
        state_path = self._make_state_files(tmp_path, monkeypatch, approve_mod)
        monkeypatch.setattr(sys, "argv", ["04_approve.py"])
        monkeypatch.setattr("builtins.input", lambda *_: (_ for _ in ()).throw(EOFError()))

        with pytest.raises(SystemExit):
            approve_mod.main()

        import json
        after = json.loads(state_path.read_text(encoding="utf-8"))
        assert "approval_status" not in after
