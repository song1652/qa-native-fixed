"""Terminal workflows must not be restarted by stale prompt-submit hooks."""
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts'))
from hook_utils import check_state


@pytest.mark.parametrize('status', ['failed', 'cancelled', 'interrupted', 'timed_out', 'incomplete'])
def test_terminal_workflow_cannot_trigger_a_pending_hook(tmp_path, status):
    path = tmp_path / 'pipeline.json'
    path.write_text(json.dumps({'step': 'init', 'workflow_status': status, 'url': 'https://example.org'}))
    assert check_state(path, 'step', 'init') is None


def test_running_and_manual_workflows_keep_pending_hooks(tmp_path):
    path = tmp_path / 'pipeline.json'
    for state in [{'step': 'init'}, {'step': 'init', 'workflow_status': 'running'}]:
        path.write_text(json.dumps(state))
        assert check_state(path, 'step', 'init') == state
