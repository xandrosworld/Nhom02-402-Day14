import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def validate_lab() -> None:
    print("Checking Day 14 submission starter...")

    required_files = [
        ROOT / "reports" / "summary.json",
        ROOT / "reports" / "benchmark_results.json",
        ROOT / "analysis" / "failure_analysis.md",
    ]

    missing = [path for path in required_files if not path.exists()]
    for path in required_files:
        print(f"[{'OK' if path.exists() else 'MISSING'}] {path.relative_to(ROOT)}")

    if missing:
        raise SystemExit(
            f"Missing {len(missing)} required file(s). Generate reports before submission."
        )

    summary = json.loads((ROOT / "reports" / "summary.json").read_text(encoding="utf-8"))

    if "metadata" not in summary or "metrics" not in summary:
        raise SystemExit("summary.json must contain both `metadata` and `metrics`.")

    metrics = summary["metrics"]
    for field in ["avg_score", "hit_rate", "mrr", "agreement_rate", "pass_rate"]:
        if field not in metrics:
            raise SystemExit(f"summary.json is missing metrics.{field}")

    if "regression" not in summary or "decision" not in summary["regression"]:
        raise SystemExit("summary.json must contain regression.decision")

    print("Summary metrics found:")
    print(f"  total cases:      {summary['metadata'].get('total')}")
    print(f"  avg score:        {metrics['avg_score']}")
    print(f"  hit rate:         {metrics['hit_rate']}")
    print(f"  mrr:              {metrics['mrr']}")
    print(f"  agreement rate:   {metrics['agreement_rate']}")
    print(f"  release decision: {summary['regression']['decision']}")
    print("Starter validation passed.")


if __name__ == "__main__":
    validate_lab()
