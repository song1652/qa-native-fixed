"""agents/dashboard/serve.py 상태 쓰기 배선 테스트 (#25).

이 파일은 940문장짜리 serve.py 전체 커버리지(#33, 별도 트래커 항목)가
아니라, #25가 고친 정확한 문제 — "대시보드가 상태 프리미티브를 포크해서
락/FSM 검증을 우회한다" — 가 재발하지 않는지만 좁게 고정한다.

테스트 대상:
- serve.py가 자체 _safe_write_json/_safe_update_json을 재구현하지 않고
  _paths.write_state/update_state를 그대로 쓰는지 (identity)
- state/pipeline.json·parallel.json·quick.json 경로가 _paths.py와
  동일한 객체인지 (경로 재선언 재발 방지)
- 리셋 핸들러(_post_reset_all/_post_pipeline_reset/_post_parallel_reset)가
  FSM 검증을 받는 write_state가 아니라 reset_state를 쓰는지
  (아니면 진행 중인 파이프라인을 리셋할 때 ValueError로 깨진다)
"""
import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
_DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "agents" / "dashboard"
for _d in (_SCRIPTS_DIR, _DASHBOARD_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import _paths  # noqa: E402


@pytest.fixture(scope="module")
def serve_mod():
    spec = importlib.util.spec_from_file_location(
        "serve", str(_DASHBOARD_DIR / "serve.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def serve_src():
    return (_DASHBOARD_DIR / "serve.py").read_text(encoding="utf-8")


class TestNoForkedPrimitives:
    """serve.py가 더 이상 자체 락/원자쓰기 구현을 갖지 않는지."""

    def test_no_own_write_impl_in_source(self, serve_src):
        assert "def _safe_write_json" not in serve_src
        assert "def _safe_update_json" not in serve_src

    def test_no_direct_lock_calls(self, serve_src):
        """_acquire_file_lock을 직접 호출하면 락 실패 무시 버그가 재발할 수 있다."""
        assert "_acquire_file_lock(" not in serve_src
        assert "_release_file_lock(" not in serve_src

    def test_safe_write_json_is_paths_write_state(self, serve_mod):
        assert serve_mod._safe_write_json is _paths.write_state

    def test_safe_update_json_is_paths_update_state(self, serve_mod):
        assert serve_mod._safe_update_json is _paths.update_state

    def test_reset_state_is_paths_reset_state(self, serve_mod):
        assert serve_mod.reset_state is _paths.reset_state


class TestPathsMatchSingleSource:
    """경로 상수가 _paths.py와 동일 객체인지 (재선언 재발 방지)."""

    def test_pipeline_state_path(self, serve_mod):
        assert serve_mod.STATE_PATH == _paths.PIPELINE_STATE

    def test_parallel_state_path(self, serve_mod):
        assert serve_mod.PARALLEL_STATE_PATH == _paths.PARALLEL_STATE

    def test_quick_state_path(self, serve_mod):
        assert serve_mod.QUICK_STATE_PATH == _paths.QUICK_STATE

    def test_run_history_path(self, serve_mod):
        assert serve_mod.RUN_HISTORY_PATH == _paths.RUN_HISTORY

    def test_discuss_path(self, serve_mod):
        assert serve_mod.DISCUSS_PATH == _paths.DISCUSS_STATE


class TestResetHandlersBypassFsmValidation:
    """리셋 핸들러는 reset_state를 써야 한다 (write_state를 쓰면 FSM 위반으로 깨짐).

    예: pipeline.json이 step="generated"인 도중 대시보드에서 "전체 리셋"을
    누르면 step="init"을 쓰게 되는데, VALID_TRANSITIONS["generated"]에는
    "init"이 없다. write_state를 썼다면 이 시나리오에서 리셋 버튼 자체가
    ValueError로 실패한다 — reset_state는 검증을 건너뛰므로 안전하다.
    """

    @pytest.mark.parametrize("handler", [
        "_post_reset_all", "_post_pipeline_reset", "_post_parallel_reset",
    ])
    def test_handler_uses_reset_state_for_pipeline_or_parallel(self, serve_src, handler):
        import re
        m = re.search(rf"def {handler}\(self\):(.*?)(?=\n    def |\Z)", serve_src, re.S)
        assert m, f"{handler} 정의를 못 찾음"
        body = m.group(1)
        # STATE_PATH/PARALLEL_STATE_PATH에 쓰는 줄은 reset_state(...)여야 한다
        for line in body.splitlines():
            if "STATE_PATH" in line and ("_safe_write_json(" in line or "write_state(" in line):
                pytest.fail(
                    f"{handler}가 write_state 계열로 STATE_PATH를 쓰고 있음 "
                    f"(FSM 검증 우회하는 reset_state여야 함): {line.strip()}"
                )

    def test_pipeline_fsm_has_no_universal_init_edge(self):
        """전제 확인: 실제로 모든 상태에서 init으로 못 돌아간다 (그래서 reset_state가 필요).

        VALID_TRANSITIONS 자체가 바뀌어 모든 상태에 "init" 전이가 생기면
        이 가정이 깨지므로, 그때는 이 테스트가 실패로 알려준다.
        """
        from _constants import VALID_TRANSITIONS
        missing_init_edge = [
            step for step, allowed in VALID_TRANSITIONS.items()
            if "init" not in allowed
        ]
        assert missing_init_edge, (
            "모든 step에 init 전이가 허용되면 reset_state 대신 write_state를 "
            "써도 안전해지므로, 이 테스트가 가정하는 전제가 바뀐 것입니다."
        )
