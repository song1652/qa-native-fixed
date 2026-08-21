"""headless 자동실행 진입점 테스트.

테스트 대상:
- run_qa.py:           _launch_headless_pipeline(), init_state(), --no-auto 분기
- run_qa_parallel.py:  _launch_headless_parallel(), resolve_url(), resolve_page_meta(),
                       _expand_targets(), --no-auto 분기
"""
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 프로젝트 루트를 sys.path에 추가
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))


# ── run_qa.py import ──────────────────────────────────────────────

import importlib.util as _ilu


def _load_run_qa():
    spec = _ilu.spec_from_file_location("run_qa", str(_ROOT / "run_qa.py"))
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_run_qa_parallel():
    spec = _ilu.spec_from_file_location("run_qa_parallel", str(_ROOT / "run_qa_parallel.py"))
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── run_qa.py 테스트 ─────────────────────────────────────────────


class TestRunQaInitState:
    """init_state(): pipeline.json 초기 구조 검증."""

    def setup_method(self):
        self.mod = _load_run_qa()

    def test_required_keys_present(self, tmp_path):
        cases_path = tmp_path / "tc_01.md"
        cases_path.write_text("# test", encoding="utf-8")
        state = self.mod.init_state(
            url="https://example.com/",
            test_cases=[{"format": "natural", "title": "T1"}],
            cases_path=str(cases_path),
        )
        for key in ("url", "step", "test_cases", "heal_count", "created_at",
                    "generated_file_path", "generated_files"):
            assert key in state, f"init_state 결과에 '{key}' 키 없음"

    def test_step_is_init(self, tmp_path):
        cases_path = tmp_path / "tc_01.md"
        cases_path.write_text("# test", encoding="utf-8")
        state = self.mod.init_state("https://x.com", [], str(cases_path))
        assert state["step"] == "init"

    def test_heal_count_zero(self, tmp_path):
        cases_path = tmp_path / "tc_01.md"
        cases_path.write_text("# test", encoding="utf-8")
        state = self.mod.init_state("https://x.com", [], str(cases_path))
        assert state["heal_count"] == 0

    def test_group_dir_from_parent_folder(self, tmp_path):
        folder = tmp_path / "mygroup"
        folder.mkdir()
        cases_path = folder / "tc_01.md"
        cases_path.write_text("# test", encoding="utf-8")
        state = self.mod.init_state("https://x.com", [], str(cases_path))
        assert state["group_dir"] == "mygroup"


class TestRunQaLaunchHeadless:
    """_launch_headless_pipeline(): subprocess 호출 인자 검증."""

    def setup_method(self):
        self.mod = _load_run_qa()

    def test_subprocess_called_with_claude_p(self):
        with patch("subprocess.Popen") as mock_popen, \
             patch("builtins.open", MagicMock()):
            mock_popen.return_value = MagicMock()
            self.mod._launch_headless_pipeline()
            assert mock_popen.called, "subprocess.Popen이 호출되지 않음"
            args = mock_popen.call_args[0][0]  # 첫 번째 위치 인자 (cmd 리스트)
            assert args[0] == "claude"
            assert args[1] == "-p"

    def test_headless_prompt_not_empty(self):
        assert len(self.mod.HEADLESS_PROMPT) > 10

    def test_dangerously_skip_permissions_flag(self):
        with patch("subprocess.Popen") as mock_popen, \
             patch("builtins.open", MagicMock()):
            mock_popen.return_value = MagicMock()
            self.mod._launch_headless_pipeline()
            args = mock_popen.call_args[0][0]
            assert "--dangerously-skip-permissions" in args

    def test_output_format_text(self):
        with patch("subprocess.Popen") as mock_popen, \
             patch("builtins.open", MagicMock()):
            mock_popen.return_value = MagicMock()
            self.mod._launch_headless_pipeline()
            args = mock_popen.call_args[0][0]
            assert "--output-format" in args
            assert "text" in args


class TestRunQaNoAutoFlag:
    """run_qa.py --no-auto: subprocess 미실행, 안내 메시지 출력 확인."""

    def setup_method(self):
        self.mod = _load_run_qa()

    def test_no_auto_skips_subprocess(self, tmp_path, capsys):
        """--no-auto 시 subprocess.Popen이 호출되지 않고, 안내 메시지가 출력되어야 한다."""
        cases_path = tmp_path / "tc_01.md"
        cases_path.write_text("# test", encoding="utf-8")
        test_cases = [{"format": "natural", "title": "T1"}]

        with patch("subprocess.Popen") as mock_popen, \
             patch.object(self.mod, "PIPELINE_STATE", tmp_path / "pipeline.json"), \
             patch.object(self.mod, "STATE_DIR", tmp_path):
            self.mod.run_single("https://x.com", test_cases, str(cases_path), auto=False)
            assert not mock_popen.called, "--no-auto인데 subprocess.Popen이 호출됨"

        out = capsys.readouterr().out
        assert "붙여넣으세요" in out or "HEADLESS" in out or "파이프라인" in out, \
            "--no-auto인데 안내 메시지가 출력되지 않음"

    def test_auto_calls_subprocess(self, tmp_path):
        """--auto(기본)시 subprocess.Popen이 호출되어야 한다."""
        cases_path = tmp_path / "tc_01.md"
        cases_path.write_text("# test", encoding="utf-8")
        test_cases = [{"format": "natural", "title": "T1"}]

        # logs/ 디렉토리를 실제로 생성해야 context manager가 log 파일을 열 수 있음
        (tmp_path / "logs").mkdir()

        with patch("subprocess.Popen") as mock_popen, \
             patch.object(self.mod, "PIPELINE_STATE", tmp_path / "pipeline.json"), \
             patch.object(self.mod, "STATE_DIR", tmp_path), \
             patch.object(self.mod, "PROJECT_ROOT", tmp_path):
            mock_popen.return_value = MagicMock()
            self.mod.run_single("https://x.com", test_cases, str(cases_path), auto=True)
            assert mock_popen.called, "--auto인데 subprocess.Popen이 호출되지 않음"


# ── run_qa_parallel.py 테스트 ─────────────────────────────────────


class TestResolveUrl:
    """resolve_url(): pages.json string/object 형식 모두 처리."""

    def setup_method(self):
        self.mod = _load_run_qa_parallel()

    def test_string_format(self):
        pages = {"login": "https://example.com/login"}
        assert self.mod.resolve_url("login", pages) == "https://example.com/login"

    def test_object_format(self):
        pages = {"login": {"url": "https://example.com/login", "spa": True}}
        assert self.mod.resolve_url("login", pages) == "https://example.com/login"

    def test_missing_key_returns_none(self):
        pages = {"login": "https://example.com/login"}
        assert self.mod.resolve_url("nonexistent", pages) is None

    def test_object_missing_url_returns_none(self):
        pages = {"login": {"spa": True}}
        assert self.mod.resolve_url("login", pages) is None


class TestResolvePageMeta:
    """resolve_page_meta(): url 제외한 메타데이터만 반환."""

    def setup_method(self):
        self.mod = _load_run_qa_parallel()

    def test_extracts_meta_without_url(self):
        pages = {"login": {"url": "https://x.com", "spa": True, "notes": "SPA"}}
        meta = self.mod.resolve_page_meta("login", pages)
        assert "url" not in meta
        assert meta["spa"] is True
        assert meta["notes"] == "SPA"

    def test_string_format_returns_empty(self):
        pages = {"login": "https://x.com"}
        meta = self.mod.resolve_page_meta("login", pages)
        assert meta == {}


class TestExpandTargets:
    """_expand_targets(): 배치 단위 분할 검증."""

    def setup_method(self):
        self.mod = _load_run_qa_parallel()

    def test_single_file_target(self, tmp_path):
        md = tmp_path / "tc_01_login.md"
        md.write_text("# TC", encoding="utf-8")
        targets = [{"url": "https://x.com", "cases": str(md)}]
        result = self.mod._expand_targets(targets)
        assert len(result) == 1
        assert result[0]["batch_info"] == "1/1"
        assert result[0]["url"] == "https://x.com"

    def test_folder_target_batched(self, tmp_path):
        folder = tmp_path / "login"
        folder.mkdir()
        # BATCH_SIZE(8)보다 많은 파일 생성 → 2배치
        for i in range(10):
            (folder / f"tc_{i:02d}_test.md").write_text("# TC", encoding="utf-8")
        targets = [{"url": "https://x.com", "cases": str(folder), "base_group": "login"}]
        result = self.mod._expand_targets(targets)
        assert len(result) == 2, f"10개 파일은 2배치여야 하는데 {len(result)}배치"
        assert result[0]["batch_info"] == "1/2"
        assert result[1]["batch_info"] == "2/2"

    def test_empty_folder_skipped(self, tmp_path):
        folder = tmp_path / "empty"
        folder.mkdir()
        targets = [{"url": "https://x.com", "cases": str(folder), "base_group": "empty"}]
        result = self.mod._expand_targets(targets)
        assert result == []

    def test_group_label_includes_batch_number(self, tmp_path):
        folder = tmp_path / "site"
        folder.mkdir()
        for i in range(3):
            (folder / f"tc_{i:02d}_t.md").write_text("# TC", encoding="utf-8")
        targets = [{"url": "https://x.com", "cases": str(folder), "base_group": "site"}]
        result = self.mod._expand_targets(targets)
        assert result[0]["group_label"] == "site_batch1"


class TestLaunchHeadlessParallel:
    """_launch_headless_parallel(): parallel_contexts.json 저장 + subprocess 호출 검증."""

    def setup_method(self):
        self.mod = _load_run_qa_parallel()

    def _make_env(self, tmp_path):
        """테스트용 디렉토리 구조 생성 (state/, logs/ 필수)."""
        (tmp_path / "state").mkdir(exist_ok=True)
        (tmp_path / "logs").mkdir(exist_ok=True)
        return tmp_path

    def test_saves_parallel_contexts_json(self, tmp_path):
        """state/parallel_contexts.json이 올바른 구조로 저장되어야 한다."""
        payload = {
            "shared_context_paths": {"lessons_learned": "agents/lessons_learned.md"},
            "subagents": [{"group_dir": "login", "url": "https://x.com", "test_cases": []}],
        }
        self._make_env(tmp_path)

        # builtins.open을 mock하지 않음 — Path.write_text가 실제 파일을 쓰고,
        # log file도 실제로 생성됨 (logs/ 디렉토리 미리 생성해야 함)
        with patch("subprocess.Popen") as mock_popen, \
             patch.object(self.mod, "PROJECT_ROOT", tmp_path):
            mock_popen.return_value = MagicMock()
            self.mod._launch_headless_parallel(payload)

        saved = json.loads(
            (tmp_path / "state" / "parallel_contexts.json").read_text(encoding="utf-8")
        )
        assert "shared_context_paths" in saved
        assert "subagents" in saved
        assert saved["subagents"][0]["group_dir"] == "login"

    def test_subprocess_called_with_claude_p(self, tmp_path):
        payload = {"shared_context_paths": {}, "subagents": []}
        self._make_env(tmp_path)

        with patch("subprocess.Popen") as mock_popen, \
             patch.object(self.mod, "PROJECT_ROOT", tmp_path):
            mock_popen.return_value = MagicMock()
            self.mod._launch_headless_parallel(payload)
            assert mock_popen.called
            args = mock_popen.call_args[0][0]
            assert args[0] == "claude"
            assert args[1] == "-p"

    def test_dangerously_skip_permissions_in_args(self, tmp_path):
        payload = {"shared_context_paths": {}, "subagents": []}
        self._make_env(tmp_path)

        with patch("subprocess.Popen") as mock_popen, \
             patch.object(self.mod, "PROJECT_ROOT", tmp_path):
            mock_popen.return_value = MagicMock()
            self.mod._launch_headless_parallel(payload)
            args = mock_popen.call_args[0][0]
            assert "--dangerously-skip-permissions" in args

    def test_parallel_headless_prompt_references_99_merge(self):
        """PARALLEL_HEADLESS_PROMPT에 99_merge.py 언급이 있어야 한다."""
        assert "99_merge" in self.mod.PARALLEL_HEADLESS_PROMPT

    def test_parallel_headless_prompt_references_parallel_contexts(self):
        """PARALLEL_HEADLESS_PROMPT에 parallel_contexts.json 언급이 있어야 한다."""
        assert "parallel_contexts.json" in self.mod.PARALLEL_HEADLESS_PROMPT
