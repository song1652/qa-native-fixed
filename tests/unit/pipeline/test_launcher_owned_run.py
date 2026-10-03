"""The headless controller preserves dashboard identity and failure status."""
import importlib.util
from pathlib import Path
import sys
from unittest.mock import MagicMock
import pytest

ROOT = Path(__file__).resolve().parents[3]
for folder in (ROOT, ROOT / 'scripts'):
    sys.path.insert(0, str(folder))


def test_single_initialization_keeps_dashboard_run_identity(monkeypatch):
    spec = importlib.util.spec_from_file_location('single_owned', ROOT / 'run_qa.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setenv('QA_RUN_ID', 'owned-workflow')
    result = module.init_state('https://example.org', [], 'testcases/demo')
    assert result['run_id'] == 'owned-workflow'


@pytest.mark.parametrize('parallel', [False, True])
def test_failed_claude_exit_does_not_report_launcher_success(tmp_path, monkeypatch, parallel):
    filename = 'run_qa_parallel.py' if parallel else 'run_qa.py'
    spec = importlib.util.spec_from_file_location('owned_launcher', ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(module, 'STATE_DIR', tmp_path / 'state')
    (tmp_path / 'state').mkdir()
    monkeypatch.setenv('QA_RUN_ID', 'owned-workflow')
    process = MagicMock()
    process.wait.return_value = 7
    monkeypatch.setattr('subprocess.Popen', lambda *args, **kwargs: process)
    with pytest.raises(SystemExit) as error:
        if parallel: module._launch_headless_parallel({'subagents': []})
        else: module._launch_headless_pipeline()
    assert error.value.code == 7
    assert (tmp_path / 'logs/runs/owned-workflow-headless.txt').exists()
