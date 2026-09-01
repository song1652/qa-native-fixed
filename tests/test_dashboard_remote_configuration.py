"""Regression tests for remote dashboard configuration (Notion P0-1/P0-2)."""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


REPO_ROOT = Path(__file__).parent.parent
DASHBOARD_DIR = REPO_ROOT / "agents" / "dashboard"
SERVE_PATH = DASHBOARD_DIR / "serve.py"

for path in (REPO_ROOT / "scripts", DASHBOARD_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

_SPEC = importlib.util.spec_from_file_location("serve_remote_test", SERVE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
SERVE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(SERVE)


def _serve_env_probe(env_overrides: dict[str, str]) -> dict:
    """Import serve.py in a clean process and return env-derived settings."""
    env = os.environ.copy()
    keys = (
        "ALLOWED_HOSTS",
        "ALLOWED_ORIGIN",
        "REMOTE_MODE",
        "REMOTE_API_ALLOWLIST",
    )
    for key in keys:
        env.pop(key, None)
    env.update(env_overrides)
    code = (
        "import importlib.util, json; "
        "spec=importlib.util.spec_from_file_location("
        f"'serve_probe', {str(SERVE_PATH)!r}); "
        "mod=importlib.util.module_from_spec(spec); "
        "spec.loader.exec_module(mod); "
        "print(json.dumps({"
        "'allowed_hosts': sorted(mod.ALLOWED_HOSTS), "
        "'allowed_origin': mod.ALLOWED_ORIGIN, "
        "'remote_mode': mod.REMOTE_MODE, "
        "'remote_allowlist': mod.REMOTE_API_ALLOWLIST}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


def _serve_main_probe(
    arguments: list[str], env_overrides: dict[str, str]
) -> dict:
    """Run main without binding and return CLI-adjusted settings."""
    env = os.environ.copy()
    for key in ("ALLOWED_HOSTS", "ALLOWED_ORIGIN"):
        env.pop(key, None)
    env.update(env_overrides)
    code = (
        "import importlib.util, json, sys; "
        "spec=importlib.util.spec_from_file_location("
        f"'serve_main_probe', {str(SERVE_PATH)!r}); "
        "mod=importlib.util.module_from_spec(spec); "
        "spec.loader.exec_module(mod); "
        f"sys.argv=['serve.py', *{arguments!r}]; "
        "mod._is_port_in_use=lambda *args, **kwargs: True; "
        "mod.webbrowser.open=lambda *args, **kwargs: None; "
        "mod.main(); "
        "print(json.dumps({'allowed_hosts': sorted(mod.ALLOWED_HOSTS), "
        "'allowed_origin': mod.ALLOWED_ORIGIN}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout.strip().splitlines()[-1])


class TestDashboardRemoteConfiguration:
    def test_cli_help_exposes_host_and_port(self):
        result = subprocess.run(
            [sys.executable, str(SERVE_PATH), "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=10,
        )

        assert result.returncode == 0, result.stderr
        assert "--host" in result.stdout
        assert "--port" in result.stdout

    def test_defaults_preserve_local_dashboard_behavior(self):
        settings = _serve_env_probe({})

        assert settings["allowed_hosts"] == [
            "127.0.0.1:8766",
            "localhost:8766",
        ]
        assert settings["allowed_origin"] == "http://localhost:8766"
        assert settings["remote_mode"] is False
        assert settings["remote_allowlist"] == []

    def test_allowed_hosts_accepts_commas_or_whitespace(self):
        settings = _serve_env_probe(
            {
                "ALLOWED_HOSTS": (
                    "localhost:9000  127.0.0.1:9000, "
                    "dashboard.example:9000\nproxy:9000"
                )
            }
        )

        assert settings["allowed_hosts"] == [
            "127.0.0.1:9000",
            "dashboard.example:9000",
            "localhost:9000",
            "proxy:9000",
        ]

    def test_allowed_origin_env_overrides_default(self):
        settings = _serve_env_probe(
            {"ALLOWED_ORIGIN": "https://dashboard.example"}
        )

        assert settings["allowed_origin"] == "https://dashboard.example"

    def test_custom_port_updates_default_csrf_hosts_and_origin(self):
        settings = _serve_main_probe(["--port", "9000"], {})

        assert settings["allowed_hosts"] == [
            "127.0.0.1:9000",
            "localhost:9000",
        ]
        assert settings["allowed_origin"] == "http://localhost:9000"

    def test_custom_port_does_not_replace_explicit_env_overrides(self):
        settings = _serve_main_probe(
            ["--port", "9000"],
            {
                "ALLOWED_HOSTS": "dashboard.example",
                "ALLOWED_ORIGIN": "https://dashboard.example",
            },
        )

        assert settings["allowed_hosts"] == ["dashboard.example"]
        assert settings["allowed_origin"] == "https://dashboard.example"

    @pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
    def test_remote_mode_truthy_values(self, value):
        assert _serve_env_probe({"REMOTE_MODE": value})["remote_mode"] is True

    def test_remote_allowlist_is_comma_separated(self):
        settings = _serve_env_probe(
            {"REMOTE_API_ALLOWLIST": "/api/run_qa, /api/run_quick*,/api/reset"}
        )

        assert settings["remote_allowlist"] == [
            "/api/run_qa",
            "/api/run_quick*",
            "/api/reset",
        ]


def _handler(path: str):
    handler = object.__new__(SERVE.DashboardHandler)
    handler.path = path
    handler.headers = {}
    handler.wfile = MagicMock()
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()
    return handler


class TestRemoteMutationAllowlist:
    @pytest.mark.parametrize(
        "path",
        [
            "/api/run_qa",
            "/api/run_qa_parallel",
            "/api/run_log",
            "/api/run_merge",
            "/api/run_quick",
            "/api/reset",
            "/api/reset/all",
            "/api/pipeline/reset",
            "/api/parallel/reset",
            "/api/quick/reset",
            "/api/heal_stats/reset",
            "/api/run_history/reset",
            "/api/discuss/reset",
        ],
    )
    def test_remote_mode_blocks_run_and_reset_routes_by_default(self, path):
        handler = _handler(path)
        with (
            patch.object(SERVE, "REMOTE_MODE", True),
            patch.object(SERVE, "REMOTE_API_ALLOWLIST", []),
        ):
            assert handler._check_remote_allowlist(path) is False

    @pytest.mark.parametrize(
        "path", ["/api/run_qa", "/api/reset", "/api/pipeline/reset"]
    )
    def test_remote_mode_off_preserves_existing_behavior(self, path):
        handler = _handler(path)
        with (
            patch.object(SERVE, "REMOTE_MODE", False),
            patch.object(SERVE, "REMOTE_API_ALLOWLIST", []),
        ):
            assert handler._check_remote_allowlist(path) is True

    def test_exact_allowlist_entry_does_not_allow_a_longer_route(self):
        handler = _handler("/api/run_qa")
        with (
            patch.object(SERVE, "REMOTE_MODE", True),
            patch.object(SERVE, "REMOTE_API_ALLOWLIST", ["/api/run_qa"]),
        ):
            assert handler._check_remote_allowlist("/api/run_qa") is True
            assert (
                handler._check_remote_allowlist("/api/run_qa_parallel")
                is False
            )

    def test_terminal_star_is_a_literal_prefix_contract(self):
        handler = _handler("/api/run_qa")
        with (
            patch.object(SERVE, "REMOTE_MODE", True),
            patch.object(SERVE, "REMOTE_API_ALLOWLIST", ["/api/run_*"]),
        ):
            assert handler._check_remote_allowlist("/api/run_qa") is True
            assert handler._check_remote_allowlist("/api/run_quick") is True
            assert handler._check_remote_allowlist("/api/reset") is False

    def test_other_glob_metacharacters_are_not_patterns(self):
        handler = _handler("/api/run_qa")
        with (
            patch.object(SERVE, "REMOTE_MODE", True),
            patch.object(SERVE, "REMOTE_API_ALLOWLIST", ["/api/run_[q]*"]),
        ):
            assert handler._check_remote_allowlist("/api/run_qa") is False

    @pytest.mark.parametrize(
        "path",
        [
            "/api/discuss/start",
            "/api/discuss/vote_item",
            "/api/discuss/reject",
        ],
    )
    def test_gate_approval_routes_remain_usable(self, path):
        handler = _handler(path)
        with (
            patch.object(SERVE, "REMOTE_MODE", True),
            patch.object(SERVE, "REMOTE_API_ALLOWLIST", []),
        ):
            assert handler._check_remote_allowlist(path) is True

    def test_blocked_post_returns_403_without_dispatching(self):
        handler = _handler("/api/run_qa")
        handler._post_run_qa = MagicMock()
        handler._check_csrf_origin = MagicMock(return_value=True)

        with (
            patch.object(SERVE, "REMOTE_MODE", True),
            patch.object(SERVE, "REMOTE_API_ALLOWLIST", []),
        ):
            handler.do_POST()

        handler.send_response.assert_called_once_with(403)
        handler._post_run_qa.assert_not_called()
        handler.wfile.write.assert_called_once()
