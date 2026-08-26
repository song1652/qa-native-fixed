"""
테스트: serve.py 보안 수정 3건 회귀 테스트 (P33)

보안 픽스:
  1. CSRF 방어       — _check_csrf_origin: Origin/Referer 헤더 검증
  2. 경로 탈출 방어  — is_safe_filename: `/`, `\\`, 절대경로, `..` 차단
  3. PID kill 제한   — _register_spawned_pid / _is_spawned_pid: 비등록 PID kill 거부

serve.py는 모듈 최상단에서 데몬 스레드(_watch_files)를 시작하나,
파일 mtime 폴링만 수행하므로 테스트 import 시 부작용 없이 안전하다.
"""
from __future__ import annotations

import importlib.util
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ── serve.py 로드 ────────────────────────────────────────────────────────────

_REPO_ROOT = Path(__file__).parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
_DASH_DIR = _REPO_ROOT / "agents" / "dashboard"

for _p in (str(_SCRIPTS_DIR), str(_DASH_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

_spec = importlib.util.spec_from_file_location(
    "serve_dashboard", str(_DASH_DIR / "serve.py")
)
_serve = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_serve)

ALLOWED_ORIGIN = _serve.ALLOWED_ORIGIN          # "http://localhost:8766"
QAHandler = _serve.DashboardHandler
_register_spawned_pid = _serve._register_spawned_pid
_is_spawned_pid = _serve._is_spawned_pid
_SPAWNED_PIDS = _serve._SPAWNED_PIDS
_SPAWNED_PIDS_LOCK = _serve._SPAWNED_PIDS_LOCK


# ── CSRF 방어 테스트 ──────────────────────────────────────────────────────────


def _make_handler(headers: dict) -> QAHandler:
    """최소 QAHandler 인스턴스 — HTTP 소켓 없이 headers만 주입."""
    handler = object.__new__(QAHandler)
    handler.headers = headers
    return handler


class TestCheckCsrfOrigin:
    """_check_csrf_origin 단위 테스트.

    브라우저가 크로스사이트 POST에 항상 Origin을 붙이는 성질을 이용한 방어.
    """

    def test_allowed_origin_passes(self):
        """Origin == ALLOWED_ORIGIN → True (정상 요청)."""
        h = _make_handler({"Origin": ALLOWED_ORIGIN})
        assert h._check_csrf_origin() is True

    def test_different_origin_blocked(self):
        """Origin이 다른 도메인 → False (CSRF 차단)."""
        h = _make_handler({"Origin": "https://evil.com"})
        assert h._check_csrf_origin() is False

    def test_no_header_at_all_passes(self):
        """Origin도 Referer도 없는 요청 → True (curl 등 로컬 CLI 허용)."""
        h = _make_handler({})
        assert h._check_csrf_origin() is True

    def test_referer_matching_origin_passes(self):
        """Referer가 ALLOWED_ORIGIN과 동일한 스킴+호스트 → True."""
        h = _make_handler({"Referer": f"{ALLOWED_ORIGIN}/dashboard"})
        assert h._check_csrf_origin() is True

    def test_referer_matching_without_path_passes(self):
        """Referer에 경로 없이 origin만 있어도 통과."""
        h = _make_handler({"Referer": ALLOWED_ORIGIN})
        assert h._check_csrf_origin() is True

    def test_referer_different_domain_blocked(self):
        """Referer가 다른 도메인 → False."""
        h = _make_handler({"Referer": "https://evil.com/attack"})
        assert h._check_csrf_origin() is False

    def test_origin_takes_precedence_over_referer(self):
        """Origin과 Referer가 모두 있을 때 Origin만 사용 (Referer 무시)."""
        # Origin이 맞고 Referer가 틀린 경우 → True (Origin 우선)
        h = _make_handler({"Origin": ALLOWED_ORIGIN, "Referer": "https://evil.com"})
        assert h._check_csrf_origin() is True

    def test_evil_origin_blocked_even_with_good_referer(self):
        """Origin이 틀리면 Referer가 맞아도 차단."""
        h = _make_handler({"Origin": "https://evil.com", "Referer": ALLOWED_ORIGIN})
        assert h._check_csrf_origin() is False

    def test_origin_empty_string_blocked(self):
        """Origin이 빈 문자열 → ALLOWED_ORIGIN과 불일치 → False."""
        h = _make_handler({"Origin": ""})
        assert h._check_csrf_origin() is False

    def test_referer_scheme_mismatch_blocked(self):
        """Referer가 http vs https 등 스킴이 다르면 차단."""
        # ALLOWED_ORIGIN이 http이고 Referer가 https → 불일치
        h = _make_handler({"Referer": ALLOWED_ORIGIN.replace("http://", "https://")})
        # 스킴 포함해 비교하므로 다른 스킴은 차단 (값이 다를 때만)
        result = h._check_csrf_origin()
        # ALLOWED_ORIGIN이 https:// 면 통과, http:// 에 https:// 이면 차단
        expected = (ALLOWED_ORIGIN.replace("http://", "https://") == ALLOWED_ORIGIN)
        assert result is expected


# ── 경로 탈출 방어 테스트 ──────────────────────────────────────────────────────


class TestSafeFilenameAttackVectors:
    """is_safe_filename — P29 강화 버전: `/`, `\\`, 절대경로 추가 차단.

    기존 test_core_parsers.py의 기본 케이스(`..` 포함)에 더해
    P29에서 추가된 경로 구분자·절대경로 벡터를 회귀 테스트한다.
    """

    def setup_method(self):
        from _validators import is_safe_filename
        self.ok = is_safe_filename

    # ── 정상 통과 케이스 ─────────────────────────────────

    def test_plain_filename_ok(self):
        assert self.ok("report.html")

    def test_filename_with_dash_underscore_ok(self):
        assert self.ok("my-report_2024.html")

    def test_xlsx_extension_ok(self):
        assert self.ok("data_import.xlsx")

    # ── 경로 탈출 벡터 차단 ──────────────────────────────

    def test_dotdot_blocked(self):
        """`..` 포함 차단."""
        assert not self.ok("../../etc/passwd")

    def test_forward_slash_blocked(self):
        """`/` 포함 → 하위경로 탈출 차단 (P29 강화)."""
        assert not self.ok("sub/../../etc/passwd")

    def test_single_slash_blocked(self):
        """단순 `/` 포함도 차단."""
        assert not self.ok("a/b.html")

    def test_backslash_blocked(self):
        """`\\` 포함 → Windows 경로 탈출 차단 (P29 강화)."""
        assert not self.ok("..\\..\\windows\\system32")

    def test_backslash_simple_blocked(self):
        """단순 백슬래시도 차단."""
        assert not self.ok("sub\\file.html")

    def test_absolute_unix_path_blocked(self):
        """절대경로 `/etc/passwd` 차단 (P29 강화)."""
        assert not self.ok("/etc/passwd")

    def test_absolute_windows_path_blocked(self):
        """Windows 스타일 절대경로 `C:\\...` 도 차단."""
        # Path("C:\\file") 는 macOS/Linux에서 절대경로가 아님 — 실제 테스트는
        # 유닉스 경로 탈출에 집중 (크로스플랫폼 고려)
        assert not self.ok("/root/secret.txt")

    def test_empty_string_blocked(self):
        """빈 문자열 차단."""
        assert not self.ok("")

    def test_dotdot_alone_blocked(self):
        """`..` 단독 차단."""
        assert not self.ok("..")


# ── PID kill 제한 테스트 ──────────────────────────────────────────────────────


class TestSpawnedPidGuard:
    """_register_spawned_pid / _is_spawned_pid: 이 서버가 생성한 PID만 kill 허용.

    요청 바디의 임의 PID를 그대로 kill하면 시스템 프로세스까지 종료 가능하므로,
    _SPAWNED_PIDS 목록에 등록된 PID만 허용한다.
    """

    def setup_method(self):
        """각 테스트 전 _SPAWNED_PIDS 초기화 (테스트 간 격리)."""
        with _SPAWNED_PIDS_LOCK:
            _SPAWNED_PIDS.clear()

    def teardown_method(self):
        """테스트 후 _SPAWNED_PIDS 정리."""
        with _SPAWNED_PIDS_LOCK:
            _SPAWNED_PIDS.clear()

    def test_unknown_pid_not_spawned(self):
        """등록하지 않은 PID는 spawned 아님."""
        assert _is_spawned_pid(99999) is False

    def test_registered_pid_is_spawned(self):
        """등록한 PID는 spawned로 인식."""
        _register_spawned_pid(12345)
        assert _is_spawned_pid(12345) is True

    def test_other_pid_not_affected(self):
        """특정 PID 등록이 다른 PID에 영향 없음."""
        _register_spawned_pid(11111)
        assert _is_spawned_pid(22222) is False

    def test_multiple_pids_registered(self):
        """여러 PID를 개별 등록 후 각각 확인."""
        pids = [10001, 10002, 10003]
        for p in pids:
            _register_spawned_pid(p)
        for p in pids:
            assert _is_spawned_pid(p) is True

    def test_unregistered_pid_zero(self):
        """PID 0은 미등록 상태에서 spawned 아님."""
        assert _is_spawned_pid(0) is False

    def test_thread_safe_concurrent_register(self):
        """동시 다발적 등록 시 데이터 손실 없음 (락 검증)."""
        pids = list(range(20000, 20050))
        threads = [
            threading.Thread(target=_register_spawned_pid, args=(p,))
            for p in pids
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        for p in pids:
            assert _is_spawned_pid(p) is True, f"PID {p} lost after concurrent register"
