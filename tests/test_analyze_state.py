"""01_analyze.py 상태 갱신 단위 테스트.

테스트 대상:
- _make_analyze_mutator(dom, url, sub_doms) — 분석 결과를 최신 상태에 병합

analyze_all()이 브라우저로 메인+서브 페이지를 순회하는 동안(수 분) 다른
프로세스가 pipeline.json을 갱신할 수 있으므로, 미리 읽어둔 state를 통째로
되쓰지 않고 소유 필드만 병합하는지 확인한다.
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
from _paths import update_state, url_cache_key  # noqa: E402


@pytest.fixture(scope="module")
def analyze():
    """숫자 프리픽스 모듈이라 importlib으로 로드 (main() 실행 안 됨)."""
    spec = importlib.util.spec_from_file_location(
        "analyze_mod", str(_SCRIPTS_DIR / "01_analyze.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DOM = {"title": "샘플", "inputs": [], "buttons": []}
URL = "https://example.com/"


class TestAnalyzeMutatorFields:
    """이 스크립트가 소유한 필드가 정확히 기록되는지."""

    def test_sets_owned_fields(self, analyze):
        out = analyze._make_analyze_mutator(DOM, URL, {})({})
        assert out["dom_info"] == DOM
        assert out["dom_cache_key"] == url_cache_key(URL)
        assert out["step"] == "analyzed"

    def test_no_sub_dom_keys_when_no_subpages(self, analyze):
        out = analyze._make_analyze_mutator(DOM, URL, {})({})
        assert "sub_dom_keys" not in out

    def test_sub_dom_keys_maps_url_to_cache_key(self, analyze):
        subs = {"https://example.com/a": {}, "https://example.com/b": {}}
        out = analyze._make_analyze_mutator(DOM, URL, subs)({})
        assert out["sub_dom_keys"] == {u: url_cache_key(u) for u in subs}

    def test_outer_url_not_shadowed_by_comprehension(self, analyze):
        """서브페이지 순회 변수가 메인 url의 캐시키를 덮지 않아야 한다."""
        subs = {"https://example.com/other": {}}
        out = analyze._make_analyze_mutator(DOM, URL, subs)({})
        assert out["dom_cache_key"] == url_cache_key(URL)
        assert out["dom_cache_key"] != url_cache_key("https://example.com/other")


class TestAnalyzeMutatorPreservesConcurrentChanges:
    """분석 중(수 분) 다른 프로세스가 쓴 값이 살아남아야 한다."""

    def test_unrelated_fields_survive(self, analyze):
        fresh = {
            "url": URL,
            "test_cases": [{"id": 1}],
            "heal_count": 7,
            "dashboard_flag": "set-during-analysis",
        }
        out = analyze._make_analyze_mutator(DOM, URL, {})(fresh)
        assert out["heal_count"] == 7
        assert out["dashboard_flag"] == "set-during-analysis"
        assert out["test_cases"] == [{"id": 1}]

    def test_stale_snapshot_is_not_written_back(self, analyze, tmp_path, monkeypatch):
        """읽기 → (분석) → 쓰기 사이의 변경이 유실되지 않는지 파일 단위로 확인."""
        p = tmp_path / "pipeline.json"
        p.write_text(json.dumps({"url": URL, "step": "init"}), encoding="utf-8")
        monkeypatch.setattr(_paths, "PIPELINE_STATE", p)

        _stale = json.loads(p.read_text(encoding="utf-8"))  # 분석 전 스냅샷

        # 분석이 도는 동안 다른 프로세스가 갱신
        concurrent = json.loads(p.read_text(encoding="utf-8"))
        concurrent["heal_count"] = 42
        p.write_text(json.dumps(concurrent), encoding="utf-8")

        update_state(p, analyze._make_analyze_mutator(DOM, URL, {}))

        final = json.loads(p.read_text(encoding="utf-8"))
        assert final["heal_count"] == 42          # 동시 변경 보존
        assert final["step"] == "analyzed"        # 자체 갱신 반영
        assert final["dom_info"] == DOM

    def test_step_transition_is_validated(self, analyze, tmp_path, monkeypatch):
        """PIPELINE_STATE 경로이므로 FSM 전이 검증이 적용된다 (init→analyzed 허용)."""
        p = tmp_path / "pipeline.json"
        p.write_text(json.dumps({"step": "init"}), encoding="utf-8")
        monkeypatch.setattr(_paths, "PIPELINE_STATE", p)

        update_state(p, analyze._make_analyze_mutator(DOM, URL, {}))
        assert json.loads(p.read_text(encoding="utf-8"))["step"] == "analyzed"

    def test_invalid_step_transition_is_rejected(self, analyze, tmp_path, monkeypatch):
        """generated→analyzed는 표에 없으므로 거부돼야 한다 (안전장치 연동 확인)."""
        p = tmp_path / "pipeline.json"
        p.write_text(json.dumps({"step": "generated"}), encoding="utf-8")
        monkeypatch.setattr(_paths, "PIPELINE_STATE", p)

        with pytest.raises(ValueError):
            update_state(p, analyze._make_analyze_mutator(DOM, URL, {}))
        assert json.loads(p.read_text(encoding="utf-8"))["step"] == "generated"
