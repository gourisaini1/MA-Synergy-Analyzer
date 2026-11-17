"""Single entry point for reproducible modelling, financial analysis and tests.

The LLM evidence agent is intentionally excluded. Run it manually through the
GitHub Actions 'Manual evidence extraction' workflow after configuring a key.
"""
import subprocess
import sys

STEPS = [
    [sys.executable, "-m", "pipeline.validate_inputs"],
    [sys.executable, "-m", "pipeline.build_source_register"],
    [sys.executable, "-m", "pipeline.run_model"],
    [sys.executable, "-m", "pipeline.sec_companyfacts"],
    [sys.executable, "-m", "pipeline.financial_analysis"],
    [sys.executable, "-m", "pipeline.build_backtest"],
    [sys.executable, "-m", "pipeline.build_deal_comparability"],
    [sys.executable, "-m", "pipeline.build_operational_sensitivities"],
    [sys.executable, "-m", "pipeline.event_study"],
    [sys.executable, "-m", "pipeline.build_artifacts"],
    [sys.executable, "-m", "pytest", "-q"],
]


def main():
    for step in STEPS:
        print("+", " ".join(step), flush=True)
        subprocess.run(step, check=True)


if __name__ == "__main__":
    main()
