"""update_heal_stats() 단위 테스트.

테스트 대상 (heal_utils.py):
- update_heal_stats(failures) — heal_stats.json의 오류 패턴별 빈도 갱신

병렬 파이프라인(99_merge.py)에서 여러 그룹이 동시에 호출하므로,
집계 로직뿐 아니라 동시 호출에서 카운트가 유실되지 않는지까지 확인한다.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

# scripts/ 모듈 import 준비
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import heal_utils  # noqa: E402


TB_LOCATOR = "Error: Element not found"
TB_TIMEOUT = "TimeoutError: Timeout 5000ms exceeded"


@pytest.fixture
def stats_path(tmp_path, monkeypatch):
    """heal_stats.json 경로를 임시 파일로 격리."""
    p = tmp_path / "heal_stats.json"
    monkeypatch.setattr(heal_utils, "HEAL_STATS_PATH", p)
    return p


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _total_count(path: Path) -> int:
    return sum(v["count"] for v in _load(path)["patterns"].values())


class TestUpdateHealStatsBasics:
    """집계 로직 (전환 전후 동일해야 하는 부분)."""

    def test_noop_when_no_failures(self, stats_path):
        heal_utils.update_heal_stats([])
        assert not stats_path.exists()

    def test_creates_file_with_version_and_patterns(self, stats_path):
        heal_utils.update_heal_stats([{"traceback": TB_LOCATOR, "test_name": "a"}])
        data = _load(stats_path)
        assert data["version"] == 1
        assert len(data["patterns"]) == 1

    def test_same_pattern_increments_count(self, stats_path):
        f = [{"traceback": TB_LOCATOR, "test_name": "a"}]
        heal_utils.update_heal_stats(f)
        heal_utils.update_heal_stats(f)
        heal_utils.update_heal_stats(f)
        assert _total_count(stats_path) == 3
        assert len(_load(stats_path)["patterns"]) == 1

    def test_distinct_patterns_are_separate_entries(self, stats_path):
        heal_utils.update_heal_stats([
            {"traceback": TB_LOCATOR, "test_name": "a"},
            {"traceback": TB_TIMEOUT, "test_name": "b"},
        ])
        assert len(_load(stats_path)["patterns"]) == 2
        assert _total_count(stats_path) == 2

    def test_duplicate_failures_in_one_call_are_counted(self, stats_path):
        heal_utils.update_heal_stats([
            {"traceback": TB_LOCATOR, "test_name": "a"},
            {"traceback": TB_LOCATOR, "test_name": "b"},
        ])
        assert _total_count(stats_path) == 2

    def test_entry_has_expected_fields(self, stats_path):
        heal_utils.update_heal_stats([{"traceback": TB_LOCATOR, "test_name": "a"}])
        entry = next(iter(_load(stats_path)["patterns"].values()))
        assert set(entry) == {"count", "error_type", "summary", "first_seen", "last_seen"}

    def test_first_seen_is_stable_across_updates(self, stats_path):
        """재발 시 first_seen은 고정, last_seen만 갱신."""
        f = [{"traceback": TB_LOCATOR, "test_name": "a"}]
        heal_utils.update_heal_stats(f)
        first = next(iter(_load(stats_path)["patterns"].values()))["first_seen"]
        heal_utils.update_heal_stats(f)
        entry = next(iter(_load(stats_path)["patterns"].values()))
        assert entry["first_seen"] == first
        assert entry["count"] == 2

    def test_empty_traceback_uses_fallback_summary(self, stats_path):
        heal_utils.update_heal_stats([{"traceback": "", "test_name": "solo"}])
        summary = next(iter(_load(stats_path)["patterns"].values()))["summary"]
        assert "no_traceback::solo" in summary

    def test_existing_unrelated_keys_are_preserved(self, stats_path):
        stats_path.write_text(
            json.dumps({"version": 1, "patterns": {}, "custom": "keep"}),
            encoding="utf-8",
        )
        heal_utils.update_heal_stats([{"traceback": TB_LOCATOR, "test_name": "a"}])
        assert _load(stats_path)["custom"] == "keep"

    def test_failure_is_advisory_not_fatal(self, stats_path, monkeypatch, capsys):
        """통계 갱신 실패가 파이프라인을 중단시키면 안 된다."""
        def boom(*_a, **_kw):
            raise TimeoutError("락 실패")

        monkeypatch.setattr(heal_utils, "update_state", boom)
        heal_utils.update_heal_stats([{"traceback": TB_LOCATOR, "test_name": "a"}])
        assert "실패 (무시)" in capsys.readouterr().out


_WORKER = """\
import sys
sys.path.insert(0, {scripts!r})
from pathlib import Path
import heal_utils
heal_utils.HEAL_STATS_PATH = Path({path!r})
F = [{{"traceback": {tb!r}, "test_name": "t"}}]
for _ in range({iters}):
    heal_utils.update_heal_stats(F)
"""


class TestUpdateHealStatsConcurrency:
    """전환의 목적 — 동시 호출에서 카운트 유실 없음."""

    def test_concurrent_processes_do_not_lose_counts(self, tmp_path):
        """6 프로세스 × 5회 = 정확히 30. 전환 전에는 대부분 유실됐다."""
        path = tmp_path / "heal_stats.json"
        n_procs, iters = 6, 5

        script = tmp_path / "worker.py"
        script.write_text(
            _WORKER.format(scripts=_SCRIPTS_DIR, path=str(path),
                           tb=TB_LOCATOR, iters=iters),
            encoding="utf-8",
        )

        procs = [
            subprocess.Popen([sys.executable, str(script)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for _ in range(n_procs)
        ]
        for proc in procs:
            _, err = proc.communicate(timeout=180)
            assert proc.returncode == 0, f"worker 실패: {err.decode(errors='replace')}"

        assert _total_count(path) == n_procs * iters
