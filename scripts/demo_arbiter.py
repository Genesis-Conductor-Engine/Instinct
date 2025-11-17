import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pipelines.arbiter_demo import run_demo


def main() -> None:
    """Entry point retained for backward-compatible demos."""
    summary = run_demo()
    for case in summary["cases"]:
        print(f"\n--- Results ({case['label']}) ---")
        for name, score in case["scores"]:
            print(f"  {name}: {score:.4f}")

    print("\n--- Pareto Frontier ---")
    for plan in summary["pareto"]["pareto_plans"]:
        print(f"  -> {plan}")
    knee = summary["pareto"].get("knee_plan")
    if knee:
        print(f"Recommended 'Knee' Plan: {knee}")


if __name__ == "__main__":
    main()