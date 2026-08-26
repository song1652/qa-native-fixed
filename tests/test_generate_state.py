"""
02_generate.py state 업데이트 원자적 RMW 전환 테스트 (P43).

기존 패턴: read_state → 수정 → write_state (비원자, RMW 경쟁 위험)
수정 후  : update_state(path, mutator) (락 보유 중 병합·쓰기)

테스트 대상:
  - 스캐폴드 생성 후 update_state로 step/generated_file_path/generated_files 기록
  - 기존 필드를 덮어쓰지 않음 (동시성 보존 확인)
  - write_state 미사용 확인
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _ROOT / "scripts"
for _p in (str(_SCRIPTS_DIR),):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _load_generate_mod():
    spec = importlib.util.spec_from_file_location(
        "generate_02", str(_SCRIPTS_DIR / "02_generate.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── 픽스처 ────────────────────────────────────────────────────────────────────


@pytest.fixture
def gen_mod():
    return _load_generate_mod()


@pytest.fixture
def pipeline_state(tmp_path):
    """최소 pipeline.json 상태 파일."""
    data = {
        "url": "https://example.com",
        "step": "planned",
        "group_dir": "login",
        "plan": [
            {
                "case_id": "tc_01",
                "case_name": "login_success",
                "description": "로그인 성공 확인",
                "case_type": "positive",
                "data_key": "null",
                "steps": [{"action": "click", "selector": "#login-btn"}],
                "assertion": {"type": "url_contains", "expected": "/dashboard"},
            }
        ],
        "test_cases": [],
        "generated_file_path": None,
        "generated_files": [],
        "approval_status": None,
        "rejection_count": 0,
    }
    p = tmp_path / "pipeline.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ── RMW 원자성 테스트 ─────────────────────────────────────────────────────────


class TestGenerateAtomicRmw:
    """02_generate.py가 update_state를 사용하는지 확인 (P43)."""

    def test_uses_update_state_not_write_state(self, gen_mod, pipeline_state, tmp_path,
                                               monkeypatch):
        """main()이 update_state를 호출하고 write_state는 호출하지 않음."""
        update_called = []
        write_called = []

        original_update = gen_mod.update_state

        def spy_update(path, mutator):
            update_called.append(True)
            return original_update(path, mutator)

        monkeypatch.setattr(gen_mod, "PIPELINE_STATE", pipeline_state)
        monkeypatch.setattr(gen_mod, "update_state", spy_update)
        if hasattr(gen_mod, "write_state"):
            monkeypatch.setattr(gen_mod, "write_state",
                                lambda *a, **k: write_called.append(True))
        monkeypatch.setattr(sys, "argv", ["02_generate.py"])
        # conftest.py, tests/ 경로를 tmp_path 아래로 리다이렉트
        gen_out = tmp_path / "tests" / "generated" / "login"
        gen_out.mkdir(parents=True)
        conftest = tmp_path / "tests" / "conftest.py"
        monkeypatch.chdir(tmp_path)

        gen_mod.main()

        assert update_called, "update_state가 호출돼야 함"
        assert not write_called, "write_state는 호출되면 안 됨 (P43)"

    def test_state_fields_written_correctly(self, gen_mod, pipeline_state, tmp_path,
                                            monkeypatch):
        """main() 실행 후 step='generated', generated_file_path, generated_files가 기록됨."""
        monkeypatch.setattr(gen_mod, "PIPELINE_STATE", pipeline_state)
        monkeypatch.setattr(sys, "argv", ["02_generate.py"])
        monkeypatch.chdir(tmp_path)

        gen_mod.main()

        after = json.loads(pipeline_state.read_text())
        assert after["step"] == "generated"
        assert after["generated_file_path"].endswith("/")
        assert len(after["generated_files"]) == 1
        assert after["generated_files"][0].endswith(".py")

    def test_concurrent_write_preserved(self, gen_mod, pipeline_state, tmp_path,
                                        monkeypatch):
        """update_state 사용으로, 읽기 이후 외부가 추가한 필드가 보존됨."""
        original_update = gen_mod.update_state

        def inject_then_update(path, mutator):
            # mutator 적용 직전 외부 필드 주입
            current = json.loads(path.read_text())
            current["concurrent_field"] = "must_survive"
            path.write_text(json.dumps(current), encoding="utf-8")
            return original_update(path, mutator)

        monkeypatch.setattr(gen_mod, "PIPELINE_STATE", pipeline_state)
        monkeypatch.setattr(gen_mod, "update_state", inject_then_update)
        monkeypatch.setattr(sys, "argv", ["02_generate.py"])
        monkeypatch.chdir(tmp_path)

        gen_mod.main()

        after = json.loads(pipeline_state.read_text())
        assert after.get("concurrent_field") == "must_survive", (
            "update_state({**s, ...}) 패턴은 외부 필드를 보존해야 함"
        )
        assert after["step"] == "generated"
