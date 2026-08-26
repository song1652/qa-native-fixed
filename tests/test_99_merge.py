"""
테스트: parallel/99_merge.py 핵심 경로 커버리지 (P32)

99_merge.py 파일명이 숫자로 시작해 직접 import 불가 → importlib.util로 로드.

커버 대상:
  _natural_sort_key                   — 자연 정렬 (숫자 혼합)
  _detect_repeated_failures_parallel  — 반복 실패 감지 로직
  verify_lessons_learned_updated      — lessons_learned.md 수정 여부 확인
  _scan_generated_groups              — tests/generated/ 그룹 스캔
  build_heal_context                  — heal_context 빌드 (실패 없음 / 있음 / 전체 반복)
  _update_parallel_status             — 병렬 상태 status 필드 업데이트
"""
from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

# ── 모듈 로드 ─────────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
_PARALLEL_DIR = _REPO_ROOT / "parallel"

for _p in (str(_SCRIPTS_DIR), str(_PARALLEL_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_spec = importlib.util.spec_from_file_location(
    "merge_99", str(_PARALLEL_DIR / "99_merge.py")
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

# 함수 별칭
_natural_sort_key = _mod._natural_sort_key
_detect_repeated = _mod._detect_repeated_failures_parallel
verify_lessons = _mod.verify_lessons_learned_updated
_scan_groups = _mod._scan_generated_groups
build_heal_ctx = _mod.build_heal_context
_update_status = _mod._update_parallel_status


# ─── _natural_sort_key ────────────────────────────────────────────────────────


def test_natural_sort_key_numeric_ordering():
    """tc_9 < tc_10 < tc_11 보장 — 문자열 정렬 시 tc_10 < tc_9 오류 방지."""
    paths = [Path(f"tc_{n}_foo.py") for n in [10, 2, 11, 1, 9]]
    result = sorted(paths, key=_natural_sort_key)
    assert [p.name for p in result] == [
        "tc_1_foo.py", "tc_2_foo.py", "tc_9_foo.py",
        "tc_10_foo.py", "tc_11_foo.py",
    ]


def test_natural_sort_key_alpha_before_numeric_prefix():
    """알파벳으로 시작하는 이름이 숫자보다 앞에 정렬되는지 확인."""
    paths = [Path("z_end.py"), Path("a_start.py"), Path("tc_3_mid.py")]
    sorted_paths = sorted(paths, key=_natural_sort_key)
    assert sorted_paths[0].name == "a_start.py"


def test_natural_sort_key_single_digit_vs_double():
    """단일 자리 수와 두 자리 수 경계값 정렬."""
    paths = [Path(f"tc_{n}.py") for n in [20, 3, 100, 9]]
    result = sorted(paths, key=_natural_sort_key)
    assert [p.name for p in result] == [
        "tc_3.py", "tc_9.py", "tc_20.py", "tc_100.py"
    ]


# ─── _detect_repeated_failures_parallel ──────────────────────────────────────


def test_detect_repeated_no_prev_failures_all_healable():
    """이전 실패 없으면 현재 실패 전체가 healable."""
    current = [{"test_name": "test_login", "error_type": "Assertion"}]
    healable, skipped = _detect_repeated(current, {"failures": []})
    assert healable == current
    assert skipped == []


def test_detect_repeated_empty_prev_ctx():
    """prev_ctx 자체가 빈 dict(heal_context.json 없음) → 전부 healable."""
    current = [{"test_name": "test_checkout", "error_type": "Timeout"}]
    healable, skipped = _detect_repeated(current, {})
    assert healable == current
    assert skipped == []


def test_detect_repeated_all_same_signature_skipped():
    """이전과 동일한 (test_name, error_type) → 전부 skip."""
    prev_ctx = {
        "failures": [
            {"test_name": "test_login", "error_type": "Locator", "traceback": ""},
        ]
    }
    current = [{"test_name": "test_login", "error_type": "Locator"}]
    healable, skipped = _detect_repeated(current, prev_ctx)
    assert healable == []
    assert skipped == current


def test_detect_repeated_partial_new_and_old():
    """반복 건(skip) + 신규 건(healable) 혼재."""
    prev_ctx = {
        "failures": [
            {"test_name": "test_old", "error_type": "Timeout", "traceback": ""},
        ]
    }
    current = [
        {"test_name": "test_old", "error_type": "Timeout"},
        {"test_name": "test_new", "error_type": "Assertion"},
    ]
    healable, skipped = _detect_repeated(current, prev_ctx)
    assert len(healable) == 1 and healable[0]["test_name"] == "test_new"
    assert len(skipped) == 1 and skipped[0]["test_name"] == "test_old"


def test_detect_repeated_same_name_different_type_not_skipped():
    """같은 test_name이라도 error_type이 다르면 skip하지 않음."""
    prev_ctx = {
        "failures": [
            {"test_name": "test_a", "error_type": "Timeout", "traceback": ""},
        ]
    }
    current = [{"test_name": "test_a", "error_type": "Assertion"}]
    healable, skipped = _detect_repeated(current, prev_ctx)
    assert healable == current
    assert skipped == []


# ─── verify_lessons_learned_updated ──────────────────────────────────────────


def test_verify_lessons_false_when_file_missing(tmp_path):
    """lessons_learned.md가 없으면 False 반환."""
    with patch.object(_mod, "LESSONS_PATH", tmp_path / "nonexistent.md"):
        assert verify_lessons(datetime.now().isoformat()) is False


def test_verify_lessons_true_when_recently_modified(tmp_path):
    """heal_start_time 이후 파일 수정 → True."""
    lessons = tmp_path / "lessons_learned.md"
    lessons.write_text("# lessons")
    # start_time을 5초 전으로 설정 → 파일 mtime > start_time
    start_iso = (datetime.now() - timedelta(seconds=5)).isoformat()
    with patch.object(_mod, "LESSONS_PATH", lessons):
        assert verify_lessons(start_iso) is True


def test_verify_lessons_false_when_not_modified(tmp_path, capsys):
    """heal_start_time 이후 수정 없으면 False + 경고 출력."""
    lessons = tmp_path / "lessons_learned.md"
    lessons.write_text("# old content")
    # start_time을 미래로 설정 → 파일 mtime < start_time
    start_iso = (datetime.now() + timedelta(hours=1)).isoformat()
    with patch.object(_mod, "LESSONS_PATH", lessons):
        result = verify_lessons(start_iso)
    assert result is False
    captured = capsys.readouterr()
    assert "lessons_learned.md" in captured.out


# ─── _scan_generated_groups ──────────────────────────────────────────────────


def test_scan_generated_groups_empty_when_missing(tmp_path):
    """GENERATED_DIR가 없으면 빈 dict 반환."""
    with patch.object(_mod, "GENERATED_DIR", tmp_path / "no_generated"):
        assert _scan_groups() == {}


def test_scan_generated_groups_collects_py_files(tmp_path):
    """그룹 디렉터리 안의 .py 파일을 수집한다."""
    gen = tmp_path / "generated"
    grp = gen / "login"
    grp.mkdir(parents=True)
    (grp / "tc_01_login.py").write_text("")
    (grp / "tc_02_logout.py").write_text("")
    with patch.object(_mod, "GENERATED_DIR", gen):
        result = _scan_groups()
    assert "login" in result
    assert len(result["login"]) == 2


def test_scan_generated_groups_excludes_conftest(tmp_path):
    """conftest.py와 __init__.py는 결과에서 제외."""
    gen = tmp_path / "generated"
    grp = gen / "shop"
    grp.mkdir(parents=True)
    (grp / "tc_01_cart.py").write_text("")
    (grp / "conftest.py").write_text("")
    (grp / "__init__.py").write_text("")
    with patch.object(_mod, "GENERATED_DIR", gen):
        result = _scan_groups()
    names = [f.name for f in result.get("shop", [])]
    assert "conftest.py" not in names
    assert "__init__.py" not in names
    assert "tc_01_cart.py" in names


def test_scan_generated_groups_skips_hidden(tmp_path):
    """.으로 시작하는 디렉터리는 스킵."""
    gen = tmp_path / "generated"
    (gen / ".git").mkdir(parents=True)
    (gen / ".git" / "tc_01.py").write_text("")
    with patch.object(_mod, "GENERATED_DIR", gen):
        result = _scan_groups()
    assert ".git" not in result


def test_scan_generated_groups_natural_sort_order(tmp_path):
    """그룹 내 파일이 자연 정렬(숫자 순)으로 반환된다."""
    gen = tmp_path / "generated"
    grp = gen / "order"
    grp.mkdir(parents=True)
    for n in [10, 2, 9, 1]:
        (grp / f"tc_{n:02d}_test.py").write_text("")
    with patch.object(_mod, "GENERATED_DIR", gen):
        result = _scan_groups()
    names = [f.name for f in result["order"]]
    nums = [int(n.split("_")[1]) for n in names]
    assert nums == sorted(nums)


# ─── build_heal_context ───────────────────────────────────────────────────────


def test_build_heal_context_none_when_no_failures():
    """실패가 없는 리포트 → None 반환."""
    report = {"tests": [{"outcome": "passed", "nodeid": "t::test_ok", "call": {}}]}
    with patch.object(_mod, "write_state"), \
         patch.object(_mod, "update_state"), \
         patch.object(_mod, "read_state", return_value={}):
        result = build_heal_ctx(report, 0, Path("/fake/state.json"))
    assert result is None


def test_build_heal_context_returns_ctx_with_failures(tmp_path):
    """실패가 있으면 heal_count·failures 포함된 ctx 반환 + write_state 호출."""
    report = {
        "tests": [
            {
                "outcome": "failed",
                "nodeid": "tests/generated/login/tc_01.py::test_login",
                "call": {"longrepr": "AssertionError: expected True"},
            }
        ]
    }
    written = {}

    def fake_write(path, data):
        written.update(data)

    with patch.object(_mod, "write_state", side_effect=fake_write), \
         patch.object(_mod, "update_state"), \
         patch.object(_mod, "read_state", return_value={}), \
         patch.object(_mod, "find_screenshot_for_test", return_value=None), \
         patch.object(_mod, "append_lessons"), \
         patch.object(_mod, "update_heal_stats"), \
         patch.object(_mod, "snapshot_assertions", return_value={}), \
         patch.object(_mod, "LESSONS_PATH", tmp_path / "ll.md"), \
         patch.object(_mod, "LESSONS_AUTO_PATH", tmp_path / "ll_auto.md"), \
         patch.object(_mod, "_check_urls_accessible", return_value=None):
        ctx = build_heal_ctx(report, 1, Path("/fake/state.json"))

    assert ctx is not None
    assert ctx["heal_count"] == 1
    assert ctx["failure_count"] == 1
    assert len(ctx["failures"]) == 1
    # write_state가 HEAL_CONTEXT_STATE에 올바른 데이터를 썼는지 확인
    assert "failures" in written


def test_build_heal_context_site_down_returns_none(tmp_path):
    """사이트 접근 불가 → None 반환 (힐링 중단).

    _check_urls_accessible는 urls가 비어 있으면 호출되지 않는다.
    pages.json에 해당 그룹의 URL을 등록해 urls를 채워야 사이트 체크가 동작한다.
    """
    # pages.json에 shop 그룹 URL 등록 → build_heal_context가 urls를 채움
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "pages.json").write_text(
        '{"shop": {"url": "http://shop.local"}}', encoding="utf-8"
    )

    report = {
        "tests": [
            {
                "outcome": "failed",
                "nodeid": "tests/generated/shop/tc_01.py::test_cart",
                "call": {"longrepr": "TimeoutError: site unreachable"},
            }
        ]
    }
    site_err = {"error": "Connection refused", "url": "http://shop.local", "group": "shop"}

    with patch.object(_mod, "PROJECT_ROOT", tmp_path), \
         patch.object(_mod, "write_state"), \
         patch.object(_mod, "update_state"), \
         patch.object(_mod, "read_state", return_value={}), \
         patch.object(_mod, "find_screenshot_for_test", return_value=None), \
         patch.object(_mod, "_check_urls_accessible", return_value=site_err), \
         patch.object(_mod, "LESSONS_PATH", tmp_path / "ll.md"), \
         patch.object(_mod, "LESSONS_AUTO_PATH", tmp_path / "ll_auto.md"):
        ctx = build_heal_ctx(report, 1, Path("/fake/state.json"))

    assert ctx is None


def test_build_heal_context_all_repeated_returns_none(tmp_path):
    """현재 실패 모두가 이전과 동일 패턴 → None 반환."""
    report = {
        "tests": [
            {
                "outcome": "failed",
                "nodeid": "tests/generated/login/tc_01.py::test_login",
                "call": {"longrepr": "AssertionError"},
            }
        ]
    }
    prev_ctx = {
        "failures": [
            {"test_name": "test_login", "error_type": "Assertion", "traceback": ""}
        ]
    }

    with patch.object(_mod, "write_state"), \
         patch.object(_mod, "update_state"), \
         patch.object(_mod, "read_state", return_value=prev_ctx), \
         patch.object(_mod, "find_screenshot_for_test", return_value=None), \
         patch.object(_mod, "append_lessons"), \
         patch.object(_mod, "update_heal_stats"), \
         patch.object(_mod, "_check_urls_accessible", return_value=None), \
         patch.object(_mod, "LESSONS_PATH", tmp_path / "ll.md"), \
         patch.object(_mod, "LESSONS_AUTO_PATH", tmp_path / "ll_auto.md"):
        ctx = build_heal_ctx(report, 2, Path("/fake/state.json"))

    assert ctx is None


# ─── _update_parallel_status ─────────────────────────────────────────────────


def test_update_parallel_status_sets_status_field():
    """상태 'testing' 설정 시 기존 필드는 보존."""
    captured = []

    def fake_update(path, mutator):
        captured.append(mutator({"heal_count": 1, "groups": ["login"]}))

    with patch.object(_mod, "update_state", side_effect=fake_update):
        _update_status("testing")

    assert len(captured) == 1
    assert captured[0]["status"] == "testing"
    assert captured[0]["heal_count"] == 1      # 기존 필드 보존
    assert captured[0]["groups"] == ["login"]  # 기존 필드 보존


def test_update_parallel_status_with_extra_dict():
    """extra가 상태 dict에 병합된다."""
    captured = []

    def fake_update(path, mutator):
        captured.append(mutator({}))

    with patch.object(_mod, "update_state", side_effect=fake_update):
        _update_status("done", extra={"heal_count": 2, "pass_rate": 100.0})

    assert captured[0]["status"] == "done"
    assert captured[0]["heal_count"] == 2
    assert captured[0]["pass_rate"] == 100.0


def test_update_parallel_status_without_extra():
    """extra 없이 호출해도 status 필드만 업데이트."""
    captured = []

    def fake_update(path, mutator):
        captured.append(mutator({"x": 99}))

    with patch.object(_mod, "update_state", side_effect=fake_update):
        _update_status("heal_needed")

    assert captured[0]["status"] == "heal_needed"
    assert captured[0]["x"] == 99


# ── quick 모드 FSM 크래시 회귀 테스트 (P41) ──────────────────────────────────


class TestQuickModeFsmCrash:
    """P41: quick 파이프라인 재실행 시 ValueError 크래시 회귀 방지.

    quick 모드는 pytest 실행 전 QUICK_STATE에 'testing' 상태를 기록한 뒤
    최종 결과(done|heal_needed|heal_failed)를 쓴다.
    이전에는 'testing' 단계를 건너뛰어, 두 번째 실행에서
    done → heal_needed 같은 FSM 허용 불가 전이가 발생해 크래시했다.
    """

    def test_update_parallel_status_accepts_path_kwarg(self):
        """path 키워드 인자로 quick.json 등 임의 경로를 지정할 수 있다."""
        from pathlib import Path as _Path
        captured_path = []
        captured_data = []

        def fake_update(path, mutator):
            captured_path.append(path)
            captured_data.append(mutator({}))

        fake_path = _Path("/tmp/fake_quick.json")
        with patch.object(_mod, "update_state", side_effect=fake_update):
            _update_status("testing", path=fake_path)

        assert captured_path[0] == fake_path, "path 인자가 update_state에 전달돼야 함"
        assert captured_data[0]["status"] == "testing"

    def test_update_parallel_status_default_path_is_parallel_state(self):
        """path 생략 시 기존처럼 PARALLEL_STATE를 사용한다."""
        captured_path = []

        def fake_update(path, mutator):
            captured_path.append(path)

        with patch.object(_mod, "update_state", side_effect=fake_update):
            _update_status("done")

        assert captured_path[0] == _mod.PARALLEL_STATE

    def test_quick_fsm_done_to_testing_to_heal_needed(self):
        """done → testing → heal_needed 전이 체인이 FSM에서 허용됨 (P41 핵심 경로)."""
        from _pipeline_registry import (
            ParallelStatus,
            assert_valid_parallel_transition,
        )
        # quick 모드 재실행: 이전 상태 done → testing (pytest 시작)
        assert_valid_parallel_transition(ParallelStatus.DONE, ParallelStatus.TESTING)
        # testing → heal_needed (테스트 실패)
        assert_valid_parallel_transition(ParallelStatus.TESTING, ParallelStatus.HEAL_NEEDED)

    def test_quick_fsm_done_to_testing_to_done(self):
        """done → testing → done 전이 체인이 허용됨 (재실행 성공 경로)."""
        from _pipeline_registry import ParallelStatus, assert_valid_parallel_transition
        assert_valid_parallel_transition(ParallelStatus.DONE, ParallelStatus.TESTING)
        assert_valid_parallel_transition(ParallelStatus.TESTING, ParallelStatus.DONE)

    def test_quick_fsm_heal_failed_to_testing_to_done(self):
        """heal_failed → testing → done 전이가 허용됨 (heal_failed 후 재실행 성공)."""
        from _pipeline_registry import ParallelStatus, assert_valid_parallel_transition
        assert_valid_parallel_transition(ParallelStatus.HEAL_FAILED, ParallelStatus.TESTING)
        assert_valid_parallel_transition(ParallelStatus.TESTING, ParallelStatus.DONE)

    def test_quick_fsm_heal_needed_to_testing_to_done(self):
        """heal_needed → testing → done 전이가 허용됨."""
        from _pipeline_registry import ParallelStatus, assert_valid_parallel_transition
        assert_valid_parallel_transition(ParallelStatus.HEAL_NEEDED, ParallelStatus.TESTING)
        assert_valid_parallel_transition(ParallelStatus.TESTING, ParallelStatus.DONE)

    def test_direct_done_to_heal_needed_is_invalid(self):
        """done → heal_needed 직접 전이는 여전히 차단된다 (FSM 무결성 유지)."""
        from _pipeline_registry import ParallelStatus, assert_valid_parallel_transition
        import pytest as _pytest
        with _pytest.raises(ValueError, match="잘못된 parallel status 전이"):
            assert_valid_parallel_transition(ParallelStatus.DONE, ParallelStatus.HEAL_NEEDED)

    def test_update_status_with_extra_and_path(self):
        """extra와 path를 동시에 지정할 수 있다."""
        from pathlib import Path as _Path
        captured = []

        def fake_update(path, mutator):
            captured.append((path, mutator({"existing": True})))

        fake_path = _Path("/tmp/quick.json")
        with patch.object(_mod, "update_state", side_effect=fake_update):
            _update_status("testing", extra={"heal_count": 0}, path=fake_path)

        assert captured[0][0] == fake_path
        assert captured[0][1]["status"] == "testing"
        assert captured[0][1]["heal_count"] == 0
        assert captured[0][1]["existing"] is True
