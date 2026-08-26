"""03_lint.py 상태 갱신 단위 테스트.

테스트 대상:
- _make_lint_mutator(lint_result) — lint 결과를 최신 상태에 병합

state를 읽고 flake8 서브프로세스를 거쳐 쓰기까지 시간이 벌어지므로,
미리 읽어둔 state를 통째로 되쓰지 않고 소유 필드만 병합하는지 확인한다.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import _paths  # noqa: E402
from _paths import update_state  # noqa: E402


@pytest.fixture(scope="module")
def lint():
    """숫자 프리픽스 모듈이라 importlib으로 로드 (main() 실행 안 됨)."""
    spec = importlib.util.spec_from_file_location(
        "lint_mod", str(_SCRIPTS_DIR / "03_lint.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PASSED = {"passed": True, "issue_count": 0, "issues": "이슈 없음",
          "file": "tests/generated/"}
FAILED = {"passed": False, "issue_count": 2, "issues": "E501 line too long",
          "file": "tests/generated/"}


class TestLintMutatorFields:
    def test_sets_owned_fields(self, lint):
        out = lint._make_lint_mutator(PASSED)({})
        assert out["lint_result"] == PASSED
        assert out["step"] == "reviewed"

    def test_failed_result_is_stored_verbatim(self, lint):
        out = lint._make_lint_mutator(FAILED)({})
        assert out["lint_result"] == FAILED
        assert out["step"] == "reviewed"

    def test_replaces_previous_lint_result(self, lint):
        """이전 라운드의 lint_result는 새 결과로 대체돼야 한다."""
        out = lint._make_lint_mutator(PASSED)({"lint_result": FAILED})
        assert out["lint_result"] == PASSED


class TestLintMutatorPreservesConcurrentChanges:
    def test_unrelated_fields_survive(self, lint):
        fresh = {
            "url": "https://example.com/",
            "heal_count": 3,
            "dom_info": {"title": "t"},
            "dashboard_flag": "set-during-lint",
        }
        out = lint._make_lint_mutator(PASSED)(fresh)
        assert out["heal_count"] == 3
        assert out["dom_info"] == {"title": "t"}
        assert out["dashboard_flag"] == "set-during-lint"

    def test_stale_snapshot_is_not_written_back(self, lint, tmp_path, monkeypatch):
        """읽기 → (flake8) → 쓰기 사이의 변경이 유실되지 않는지 파일 단위로 확인."""
        p = tmp_path / "pipeline.json"
        p.write_text(json.dumps({"step": "generated"}), encoding="utf-8")
        monkeypatch.setattr(_paths, "PIPELINE_STATE", p)

        # flake8이 도는 동안 다른 프로세스가 갱신
        concurrent = json.loads(p.read_text(encoding="utf-8"))
        concurrent["heal_count"] = 11
        p.write_text(json.dumps(concurrent), encoding="utf-8")

        update_state(p, lint._make_lint_mutator(PASSED))

        final = json.loads(p.read_text(encoding="utf-8"))
        assert final["heal_count"] == 11           # 동시 변경 보존
        assert final["step"] == "reviewed"         # 자체 갱신 반영
        assert final["lint_result"] == PASSED


class TestLintStepTransition:
    def test_generated_to_reviewed_is_allowed(self, lint, tmp_path, monkeypatch):
        """파이프라인 정상 경로: generated → reviewed."""
        p = tmp_path / "pipeline.json"
        p.write_text(json.dumps({"step": "generated"}), encoding="utf-8")
        monkeypatch.setattr(_paths, "PIPELINE_STATE", p)

        update_state(p, lint._make_lint_mutator(PASSED))
        assert json.loads(p.read_text(encoding="utf-8"))["step"] == "reviewed"

    def test_invalid_transition_is_rejected(self, lint, tmp_path, monkeypatch):
        """init → reviewed는 표에 없으므로 거부 + 파일 무변경."""
        p = tmp_path / "pipeline.json"
        p.write_text(json.dumps({"step": "init"}), encoding="utf-8")
        monkeypatch.setattr(_paths, "PIPELINE_STATE", p)

        with pytest.raises(ValueError):
            update_state(p, lint._make_lint_mutator(PASSED))

        final = json.loads(p.read_text(encoding="utf-8"))
        assert final["step"] == "init"
        assert "lint_result" not in final
