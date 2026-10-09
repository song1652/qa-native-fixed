from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("setup_env", ROOT / "scripts" / "setup_env.py")
setup_env = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup_env)


def test_copy_test_data_creates_missing_and_keeps_existing(tmp_path: Path):
    (tmp_path / "a.example.json").write_text('{"k": "template"}')
    (tmp_path / "b.example.json").write_text('{"k": "template"}')
    (tmp_path / "b.json").write_text('{"k": "real secret"}')

    assert setup_env.copy_test_data(tmp_path) == [tmp_path / "a.json"]
    assert (tmp_path / "a.json").read_text() == '{"k": "template"}'
    assert (tmp_path / "b.json").read_text() == '{"k": "real secret"}'
    assert setup_env.copy_test_data(tmp_path) == []
