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


# ── P43: update_state 원자적 RMW 전환 회귀 테스트 ────────────────────────────


class TestApproveAtomicRmw:
    """04_approve.py가 write_state 대신 update_state를 쓰는지 확인 (P43).

    update_state는 락 보유 중 최신 파일을 읽어 병합·쓰기를 수행하므로
    read_state 이후 다른 프로세스가 쓴 필드를 덮어쓰지 않는다.
    """

    @pytest.fixture
    def _approve(self, tmp_path, monkeypatch):
        """approve_mod + state 파일 세팅 헬퍼."""
        import importlib.util as _ilu
        _ROOT = Path(__file__).resolve().parent.parent
        spec = _ilu.spec_from_file_location(
            "approve_p43", str(_ROOT / "scripts" / "04_approve.py")
        )
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)

        import json
        state_data = {
            "url": "https://example.com", "test_cases": [],
            "step": "reviewed", "review_summary": "OK",
            "lint_result": {"passed": True}, "generated_file_path": "tests/generated/x/",
            "approval_status": None, "rejection_reason": None, "rejection_count": 0,
        }
        state_path = tmp_path / "pipeline.json"
        state_path.write_text(json.dumps(state_data), encoding="utf-8")

        cfg_path = tmp_path / "cfg.json"
        cfg_path.write_text('{"auto_approve": true}', encoding="utf-8")

        monkeypatch.setattr(mod, "PIPELINE_STATE", state_path)
        monkeypatch.setattr(mod, "_PIPELINE_CONFIG", cfg_path)
        monkeypatch.setattr(sys, "argv", ["04_approve.py"])
        return mod, state_path

    def test_auto_approve_uses_update_state_not_write_state(self, _approve, monkeypatch):
        """auto_approve 경로에서 update_state가 호출되고 write_state는 호출 안 됨."""
        mod, _ = _approve
        update_called = []
        write_called = []

        original_update = mod.update_state

        def spy_update(path, mutator):
            update_called.append(True)
            return original_update(path, mutator)

        monkeypatch.setattr(mod, "update_state", spy_update)
        # write_state가 있으면 spy 추가 (없으면 무시)
        if hasattr(mod, "write_state"):
            monkeypatch.setattr(mod, "write_state",
                                lambda *a, **k: write_called.append(True))

        mod.main()

        assert update_called, "update_state가 호출돼야 함"
        assert not write_called, "write_state는 호출되면 안 됨 (P43)"

    def test_auto_approve_sets_correct_field(self, _approve):
        """auto_approve 경로에서 approval_status='approved'가 기록됨."""
        import json
        mod, state_path = _approve
        mod.main()
        after = json.loads(state_path.read_text())
        assert after["approval_status"] == "approved"

    def test_auto_approve_preserves_other_fields(self, _approve):
        """update_state 사용으로 읽기 이후 추가된 필드가 보존됨 (동시성 시뮬레이션)."""
        import json
        mod, state_path = _approve

        # update_state 호출 직전에 외부 프로세스가 필드를 추가했다고 시뮬레이션
        original_update = mod.update_state

        def inject_then_update(path, mutator):
            # mutator 적용 전 파일에 외부 필드 주입
            current = json.loads(path.read_text())
            current["injected_by_external"] = "should_survive"
            path.write_text(json.dumps(current), encoding="utf-8")
            return original_update(path, mutator)

        import importlib.util as _ilu
        _ROOT = Path(__file__).resolve().parent.parent
        spec = _ilu.spec_from_file_location(
            "approve_p43b", str(_ROOT / "scripts" / "04_approve.py")
        )
        mod2 = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod2)

        mod2.PIPELINE_STATE = mod.PIPELINE_STATE
        mod2._PIPELINE_CONFIG = mod._PIPELINE_CONFIG
        import sys as _sys
        _sys.argv = ["04_approve.py"]

        mod2.update_state = inject_then_update
        mod2.main()

        after = json.loads(mod.PIPELINE_STATE.read_text())
        assert after.get("injected_by_external") == "should_survive", (
            "update_state를 쓰면 외부 필드가 보존돼야 함 (write_state를 쓰면 덮어씀)"
        )
        assert after["approval_status"] == "approved"

    def test_rejection_count_incremented_atomically(self, tmp_path, monkeypatch):
        """반려 시 rejection_count가 mutator 안에서 증가해 원자적으로 기록됨."""
        import importlib.util as _ilu, json
        _ROOT = Path(__file__).resolve().parent.parent
        spec = _ilu.spec_from_file_location(
            "approve_p43c", str(_ROOT / "scripts" / "04_approve.py")
        )
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)

        state_data = {
            "url": "https://x.com", "test_cases": [], "step": "reviewed",
            "review_summary": "OK", "lint_result": {"passed": True},
            "generated_file_path": "", "approval_status": None,
            "rejection_reason": None, "rejection_count": 1,  # 이미 1회 반려됨
        }
        state_path = tmp_path / "pipeline.json"
        state_path.write_text(json.dumps(state_data), encoding="utf-8")

        cfg_path = tmp_path / "cfg.json"
        cfg_path.write_text('{"auto_approve": false}', encoding="utf-8")

        monkeypatch.setattr(mod, "PIPELINE_STATE", state_path)
        monkeypatch.setattr(mod, "_PIPELINE_CONFIG", cfg_path)
        monkeypatch.setattr(sys, "argv", ["04_approve.py"])
        # n → 반려 → 사유 입력
        inputs = iter(["n", "테스트 사유"])
        monkeypatch.setattr("builtins.input", lambda *_: next(inputs))

        with pytest.raises(SystemExit) as exc:
            mod.main()
        assert exc.value.code == 4  # 반려 종료코드 (EXIT_REJECTED=4)

        after = json.loads(state_path.read_text())
        assert after["rejection_count"] == 2, "이전 값(1)에서 1 증가해 2여야 함"
        assert after["approval_status"] == "rejected"
        assert after["rejection_reason"] == "테스트 사유"
