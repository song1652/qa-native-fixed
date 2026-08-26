"""
/api/pipeline_registry 엔드포인트 테스트 (P45).

build_pipeline_registry() 헬퍼를 직접 호출해 검증.
- 단일 파이프라인 steps / step_labels / step_compat 포함 여부
- 병렬 파이프라인 steps / step_labels 포함 여부
- 레지스트리와의 일관성 (Step, ParallelStatus 상수 기반)
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
_DASHBOARD = _ROOT / "agents" / "dashboard"
_SCRIPTS = _ROOT / "scripts"

for _p in (str(_SCRIPTS),):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _load_serve():
    """serve.py를 실제 HTTP 서버 없이 모듈로 로드."""
    spec = importlib.util.spec_from_file_location(
        "serve_mod", str(_DASHBOARD / "serve.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def serve():
    return _load_serve()


@pytest.fixture(scope="module")
def registry(serve):
    return serve.build_pipeline_registry()


# ── 응답 구조 ─────────────────────────────────────────────────────────────────

class TestRegistryShape:
    def test_top_level_keys(self, registry):
        assert "pipeline" in registry
        assert "parallel" in registry

    def test_pipeline_has_required_keys(self, registry):
        p = registry["pipeline"]
        assert "steps" in p
        assert "step_labels" in p
        assert "step_compat" in p

    def test_parallel_has_required_keys(self, registry):
        q = registry["parallel"]
        assert "steps" in q
        assert "step_labels" in q


# ── 단일 파이프라인 ───────────────────────────────────────────────────────────

class TestPipelineSection:
    def test_pipeline_steps_ordered(self, registry):
        steps = registry["pipeline"]["steps"]
        assert isinstance(steps, list)
        assert len(steps) >= 5

    def test_pipeline_steps_contains_core_steps(self, registry):
        steps = registry["pipeline"]["steps"]
        for core in ("init", "analyzed", "generated", "reviewed", "done"):
            assert core in steps, f"'{core}' 누락"

    def test_heal_steps_not_in_pipeline_steps(self, registry):
        """heal_needed / heal_failed 는 스텝바에서 제외된다."""
        steps = registry["pipeline"]["steps"]
        assert "heal_needed" not in steps
        assert "heal_failed" not in steps

    def test_step_labels_covers_all_pipeline_steps(self, registry):
        p = registry["pipeline"]
        for step in p["steps"]:
            assert step in p["step_labels"], f"'{step}' 라벨 누락"

    def test_step_labels_includes_heal_steps(self, registry):
        labels = registry["pipeline"]["step_labels"]
        assert "heal_needed" in labels
        assert "heal_failed" in labels

    def test_step_compat_keys_have_labels(self, registry):
        p = registry["pipeline"]
        for alias in p["step_compat"]:
            assert alias in p["step_labels"], f"compat alias '{alias}' 라벨 누락"

    def test_step_compat_values_are_canonical_steps(self, registry):
        p = registry["pipeline"]
        for alias, canonical in p["step_compat"].items():
            assert canonical in p["step_labels"], (
                f"compat '{alias}' → '{canonical}': canonical step 라벨 누락"
            )

    def test_step_compat_contains_scaffolded_linted_approved(self, registry):
        compat = registry["pipeline"]["step_compat"]
        assert "scaffolded" in compat
        assert "linted" in compat
        assert "approved" in compat


# ── 병렬 파이프라인 ───────────────────────────────────────────────────────────

class TestParallelSection:
    def test_parallel_steps_ordered(self, registry):
        steps = registry["parallel"]["steps"]
        assert isinstance(steps, list)
        assert len(steps) >= 4

    def test_parallel_steps_contains_core_statuses(self, registry):
        steps = registry["parallel"]["steps"]
        for core in ("init", "analyzing", "ready", "testing", "done"):
            assert core in steps, f"'{core}' 누락"

    def test_parallel_step_labels_covers_all_steps(self, registry):
        q = registry["parallel"]
        for step in q["steps"]:
            assert step in q["step_labels"], f"'{step}' 라벨 누락"

    def test_parallel_step_labels_includes_heal(self, registry):
        labels = registry["parallel"]["step_labels"]
        assert "heal_needed" in labels
        assert "heal_failed" in labels


# ── 레지스트리와의 일관성 ─────────────────────────────────────────────────────

class TestRegistryConsistency:
    """_pipeline_registry.py의 Step / ParallelStatus 상수와 일치하는지 검증."""

    def test_step_constants_covered_by_labels(self, registry):
        from _pipeline_registry import Step
        step_values = {
            v for k, v in vars(Step).items()
            if not k.startswith("_") and isinstance(v, str)
        }
        labels = registry["pipeline"]["step_labels"]
        for sv in step_values:
            assert sv in labels, (
                f"Step.{sv!r} 가 step_labels에 없음 — _pipeline_registry 추가 시 API 갱신 필요"
            )

    def test_parallel_status_constants_covered_by_labels(self, registry):
        from _pipeline_registry import ParallelStatus
        ps_values = {
            v for k, v in vars(ParallelStatus).items()
            if not k.startswith("_") and isinstance(v, str) and v  # EMPTY("")는 제외
        }
        labels = registry["parallel"]["step_labels"]
        for pv in ps_values:
            assert pv in labels, (
                f"ParallelStatus.{pv!r} 가 parallel.step_labels에 없음"
            )

    def test_build_pipeline_registry_is_deterministic(self, serve):
        """같은 레지스트리에서 두 번 호출해도 동일한 결과."""
        r1 = serve.build_pipeline_registry()
        r2 = serve.build_pipeline_registry()
        assert r1 == r2
