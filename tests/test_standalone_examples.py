"""Test that all standalone CLI example scripts run to completion without errors."""

import runpy
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "examples"))
STANDALONE_EXAMPLES = sorted(p for p in (ROOT / "examples").glob("example_*.py") if not p.name.endswith("_well.py"))


@pytest.mark.parametrize("script_path", STANDALONE_EXAMPLES, ids=lambda p: p.name)
def test_standalone_example_runs(script_path):
    # Execute script in isolated module namespace
    namespace = runpy.run_path(str(script_path), run_name="__main__")
    assert namespace is not None
