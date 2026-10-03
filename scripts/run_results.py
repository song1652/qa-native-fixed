"""Run-owned execution summaries; pipeline.json remains a latest-run view."""
import json
import hashlib
import re
from pathlib import Path


def execution_result_path(root: Path, run_id: str) -> Path:
    if not isinstance(run_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', run_id):
        raise ValueError('Invalid run_id')
    return Path(root) / 'state' / 'runs' / run_id / 'execution_result.json'


def read_execution_result(root: Path, run_id: str) -> dict | None:
    try:
        data = json.loads(execution_result_path(root, run_id).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) and data.get('run_id') == run_id else None


def write_execution_result(root: Path, run_id: str, result: dict) -> dict:
    """Atomically publish this owner's result, preserving external terminal stops."""
    from _paths import update_state
    path = execution_result_path(root, run_id)
    if result.get('run_id', run_id) != run_id:
        raise ValueError('Execution result run_id mismatch')
    payload = {**result, 'run_id': run_id}
    return update_state(path, lambda current: current
                        if current.get('status') in ('cancelled', 'interrupted', 'timed_out')
                        else payload)


def worker_run_id(run_id: str, state_path: Path) -> str:
    """Derive a stable worker owner within a workflow, preserving the ID limit."""
    suffix = hashlib.sha256(str(Path(state_path).resolve()).encode()).hexdigest()[:12]
    return f"{run_id[:106]}_worker_{suffix}"
