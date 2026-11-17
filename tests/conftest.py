"""Rebuild generated deliverables before artifact tests on every run."""
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session", autouse=True)
def build_outputs():
    for module in [
        "pipeline.run_model",
        "pipeline.financial_analysis",
        "pipeline.build_backtest",
        "pipeline.build_artifacts",
    ]:
        subprocess.run(
            [sys.executable, "-m", module],
            check=True,
            cwd=ROOT,
        )
