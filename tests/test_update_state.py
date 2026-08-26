"""update_state() 단위 테스트.

테스트 대상 (_paths.py):
- update_state(path, mutator) — 락 보유 중 read-modify-write를 원자적으로 수행

update_state의 존재 이유가 "read_state + write_state 사이에 끼어든 다른 프로세스의
변경을 덮어쓰지 않는 것"이므로, 단순 동작뿐 아니라 스레드/프로세스 동시 호출에서
갱신이 유실되지 않는지까지 확인한다.
"""
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

# scripts/ 모듈 import 준비
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import _paths  # noqa: E402
from _paths import (  # noqa: E402
    LOCK_TIMEOUT_SECS,
    update_state,
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ── 기본 동작 ────────────────────────────────────────────────────


class TestUpdateStateBasics:
    """mutator 계약과 반환값."""

    def test_mutator_receives_current_state(self, tmp_path):
        p = tmp_path / "s.json"
        p.write_text(json.dumps({"a": 1}), encoding="utf-8")

        seen = {}

        def mutator(current):
            seen.update(current)
            return {**current, "b": 2}

        update_state(p, mutator)
        assert seen == {"a": 1}
        assert _read(p) == {"a": 1, "b": 2}

    def test_returns_written_data(self, tmp_path):
        p = tmp_path / "s.json"
        result = update_state(p, lambda c: {**c, "x": 1})
        assert result == {"x": 1}
        assert _read(p) == result

    def test_missing_file_yields_empty_dict(self, tmp_path):
        p = tmp_path / "nope.json"
        update_state(p, lambda c: {**c, "created": True})
        assert _read(p) == {"created": True}

    def test_corrupt_json_raises_and_backs_up(self, tmp_path):
        """손상 JSON은 ValueError를 발생시키고 .corrupt.* 백업을 생성 (P51).

        조용히 빈 dict로 덮어쓰면 사용자 데이터가 소실되므로,
        예외 발생 + 백업 파일 생성으로 동작을 변경함.
        """
        p = tmp_path / "s.json"
        p.write_text("{ not json", encoding="utf-8")
        import pytest as _pytest
        with _pytest.raises((ValueError, Exception)):
            update_state(p, lambda c: {**c, "recovered": True})
        # 백업 파일이 생성됐는지 확인
        backups = list(tmp_path.glob("s.corrupt.*.json"))
        assert backups, "손상 JSON 백업 파일이 생성되어야 함"

    def test_creates_parent_directory(self, tmp_path):
        p = tmp_path / "deep" / "nested" / "s.json"
        update_state(p, lambda c: {**c, "ok": True})
        assert _read(p) == {"ok": True}

    def test_unicode_is_preserved_not_escaped(self, tmp_path):
        p = tmp_path / "s.json"
        update_state(p, lambda c: {**c, "msg": "힐링 필요"})
        assert "힐링 필요" in p.read_text(encoding="utf-8")
        assert _read(p)["msg"] == "힐링 필요"


# ── 원자성 / 실패 처리 ───────────────────────────────────────────


class TestUpdateStateAtomicity:
    """쓰기 실패나 mutator 예외가 상태를 오염시키지 않아야 한다."""

    def test_no_temp_files_left_behind(self, tmp_path):
        p = tmp_path / "s.json"
        update_state(p, lambda c: {**c, "x": 1})
        assert list(tmp_path.glob("*.tmp")) == []

    def test_lock_released_after_success(self, tmp_path):
        p = tmp_path / "s.json"
        update_state(p, lambda c: {**c, "x": 1})
        assert not p.with_suffix(".lock").exists()

    def test_mutator_exception_propagates(self, tmp_path):
        p = tmp_path / "s.json"
        p.write_text(json.dumps({"keep": "me"}), encoding="utf-8")

        def boom(_current):
            raise RuntimeError("mutator 실패")

        with pytest.raises(RuntimeError, match="mutator 실패"):
            update_state(p, boom)

        # 원본 보존 + 락 해제 (finally)
        assert _read(p) == {"keep": "me"}
        assert not p.with_suffix(".lock").exists()

    def test_lock_released_even_when_mutator_fails(self, tmp_path):
        """예외 후에도 다음 호출이 정상 동작해야 한다 (락 누수 없음)."""
        p = tmp_path / "s.json"
        with pytest.raises(ValueError):
            update_state(p, lambda c: (_ for _ in ()).throw(ValueError("x")))
        update_state(p, lambda c: {**c, "after": True})
        assert _read(p) == {"after": True}


# ── 동시 호출 / 락 경합 ──────────────────────────────────────────


_WORKER = """\
import json, sys
sys.path.insert(0, {scripts!r})
from _paths import update_state
from pathlib import Path
p = Path({path!r})
for _ in range({iters}):
    update_state(p, lambda c: {{**c, "counter": c.get("counter", 0) + 1}})
"""


class TestUpdateStateConcurrency:
    """update_state의 존재 이유 — 갱신 유실 방지."""

    def test_threads_do_not_lose_updates(self, tmp_path):
        """20 스레드 × 5회 증가 = 정확히 100. 하나라도 유실되면 실패."""
        p = tmp_path / "s.json"
        p.write_text(json.dumps({"counter": 0}), encoding="utf-8")
        n_threads, iters = 20, 5

        def bump(current):
            # RMW 창을 넓혀 경합을 실제로 유발
            value = current.get("counter", 0)
            time.sleep(0.001)
            return {**current, "counter": value + 1}

        errors = []

        def worker():
            try:
                for _ in range(iters):
                    update_state(p, bump)
            except Exception as e:  # pragma: no cover - 실패 시 진단용
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"동시 호출 중 예외: {errors}"
        assert _read(p)["counter"] == n_threads * iters

    def test_threads_preserve_each_others_keys(self, tmp_path):
        """서로 다른 키를 쓰는 동시 호출에서 모든 키가 살아남아야 한다."""
        p = tmp_path / "s.json"
        p.write_text(json.dumps({}), encoding="utf-8")
        n = 25

        def worker(i):
            update_state(p, lambda c: {**c, f"k{i}": i})

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        final = _read(p)
        assert final == {f"k{i}": i for i in range(n)}

    def test_processes_do_not_lose_updates(self, tmp_path):
        """별도 프로세스 간에도 락이 동작해야 한다 (실제 파이프라인 구성)."""
        p = tmp_path / "s.json"
        p.write_text(json.dumps({"counter": 0}), encoding="utf-8")
        n_procs, iters = 5, 4

        script = tmp_path / "worker.py"
        script.write_text(
            _WORKER.format(scripts=_SCRIPTS_DIR, path=str(p), iters=iters),
            encoding="utf-8",
        )

        procs = [
            subprocess.Popen([sys.executable, str(script)],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for _ in range(n_procs)
        ]
        for proc in procs:
            _, err = proc.communicate(timeout=120)
            assert proc.returncode == 0, f"worker 실패: {err.decode(errors='replace')}"

        assert _read(p)["counter"] == n_procs * iters


class TestUpdateStateLocking:
    """락 획득 실패와 스테일 락 처리."""

    def test_timeout_error_when_lock_cannot_be_acquired(self, tmp_path, monkeypatch):
        """락 획득 실패는 조용히 넘어가지 않고 TimeoutError로 승격된다."""
        p = tmp_path / "s.json"
        p.write_text(json.dumps({"keep": "me"}), encoding="utf-8")
        monkeypatch.setattr(_paths, "_acquire_file_lock", lambda *a, **kw: False)

        with pytest.raises(TimeoutError):
            update_state(p, lambda c: {**c, "never": True})

        # 락을 못 잡았으면 파일은 그대로여야 한다
        assert _read(p) == {"keep": "me"}

    def test_held_lock_is_not_stolen_before_stale_threshold(self, tmp_path):
        """살아 있는 보유자의 락을 대기 측이 강탈하면 안 된다 (상호 배제 유지)."""
        lock = tmp_path / "s.lock"
        lock.touch()
        acquired = _paths._acquire_file_lock(lock, timeout_secs=0.2)
        assert acquired is False
        assert lock.exists()  # 강탈되지 않고 그대로
        lock.unlink()

    def test_stale_lock_is_reclaimed(self, tmp_path):
        """비정상 종료 잔재(스테일 락)는 회수되어야 한다."""
        lock = tmp_path / "s.lock"
        lock.touch()
        # 스테일 임계값을 확실히 넘긴 시각으로 mtime 조작
        old = time.time() - (_paths.LOCK_STALE_SECS * 10)
        os.utime(lock, (old, old))

        assert _paths._acquire_file_lock(lock, timeout_secs=1.0) is True
        lock.unlink()

    def test_stale_threshold_exceeds_acquire_timeout(self):
        """스테일 임계값이 획득 타임아웃보다 커야 조기 강탈이 없다."""
        assert _paths.LOCK_STALE_SECS > LOCK_TIMEOUT_SECS


# ── FSM 전이 검증 연동 ───────────────────────────────────────────


class TestUpdateStateFsmIntegration:
    """update_state는 pipeline/parallel 상태 파일에 한해 전이를 검증한다."""

    def test_invalid_step_transition_raises_and_leaves_file_untouched(
        self, tmp_path, monkeypatch
    ):
        p = tmp_path / "pipeline.json"
        p.write_text(json.dumps({"step": "init"}), encoding="utf-8")
        monkeypatch.setattr(_paths, "PIPELINE_STATE", p)

        with pytest.raises(ValueError):
            update_state(p, lambda c: {**c, "step": "done"})  # init→done 미허용

        assert _read(p) == {"step": "init"}
        assert not p.with_suffix(".lock").exists()

    def test_valid_step_transition_passes(self, tmp_path, monkeypatch):
        p = tmp_path / "pipeline.json"
        p.write_text(json.dumps({"step": "init"}), encoding="utf-8")
        monkeypatch.setattr(_paths, "PIPELINE_STATE", p)

        update_state(p, lambda c: {**c, "step": "analyzed"})
        assert _read(p)["step"] == "analyzed"

    def test_unchanged_step_is_not_validated(self, tmp_path, monkeypatch):
        """같은 step 재기록은 전이가 아니므로 통과해야 한다."""
        p = tmp_path / "pipeline.json"
        p.write_text(json.dumps({"step": "init"}), encoding="utf-8")
        monkeypatch.setattr(_paths, "PIPELINE_STATE", p)

        update_state(p, lambda c: {**c, "step": "init", "extra": 1})
        assert _read(p) == {"step": "init", "extra": 1}

    def test_non_state_file_is_not_validated(self, tmp_path):
        """pipeline/parallel/quick 이외 경로는 전이 검증 대상이 아니다."""
        p = tmp_path / "random.json"
        p.write_text(json.dumps({"step": "init"}), encoding="utf-8")
        update_state(p, lambda c: {**c, "step": "done"})  # 예외 없이 통과
        assert _read(p)["step"] == "done"

    def test_first_status_write_is_not_validated(self, tmp_path, monkeypatch):
        """현재 status가 빈 문자열이면 전이 검증이 건너뛰어진다 (의도된 설계).

        근거: 같은 역할의 _validate_transition_locked(write_state 경로)에
        "초기 상태(파일 없음 or 필드 없음)에서는 검증 건너뜀"이라는 주석과 함께
        동일한 `if not current_val: return` 가드가 명시돼 있다. 두 검증 함수가
        같은 규칙을 공유하므로 누락이 아니라 합의된 계약이다.

        current.get(field, "")는 "필드 없음"과 "빈 문자열"을 구분하지 못하므로,
        최초 기록을 검증하면 상태 파일이 갓 생성된 시점의 정상 기록까지 막힌다.

        부작용: VALID_PARALLEL_TRANSITIONS의 "": ["init", "testing"] 규칙은
        이 경로로는 절대 발동하지 않는 죽은 설정이 된다(함수 자체는 검증함).
        """
        p = tmp_path / "parallel.json"
        p.write_text(json.dumps({"status": ""}), encoding="utf-8")
        monkeypatch.setattr(_paths, "PARALLEL_STATE", p)

        # ""→"done"은 표상 미허용이지만 조기 return 때문에 통과한다
        update_state(p, lambda c: {**c, "status": "done"})
        assert _read(p)["status"] == "done"
