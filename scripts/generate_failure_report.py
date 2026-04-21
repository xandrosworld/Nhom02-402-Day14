import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = ROOT / "reports"
DATASET_PATH = ROOT / "data" / "golden_set.jsonl"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def _extract_benchmark_results(benchmark_results: Any) -> List[Dict[str, Any]]:
    """Extract list of benchmark results from either old or new JSON format."""
    if isinstance(benchmark_results, dict):
        if "v1" in benchmark_results and "v2" in benchmark_results:
            return benchmark_results["v2"]
        return benchmark_results.get("candidate_results") or benchmark_results.get("results") or []
    return benchmark_results if isinstance(benchmark_results, list) else []


def summarize_reports(summary: Dict[str, Any], benchmark_results: Any) -> Dict[str, Any]:
    """Summarize benchmark reports from new JSON structure."""
    results = _extract_benchmark_results(benchmark_results)

    counts = {"pass": 0, "fail": 0, "error": 0}
    for item in results:
        status = item.get("status", "unknown")
        counts[status] = counts.get(status, 0) + 1

    retrieval_misses = [
        item for item in results
        if item.get("ragas", {}).get("relevancy", 1.0) == 0.0
        or item.get("judge", {}).get("final_score", 5.0) == 0.0
    ]
    worst_retrieval = min(
        retrieval_misses,
        key=lambda item: item.get("judge", {}).get("final_score", 0.0),
        default=None,
    ) if retrieval_misses else None

    fail_cases = [item for item in results if item.get("status") == "fail"]
    worst_partial = min(
        fail_cases,
        key=lambda item: item.get("judge", {}).get("final_score", 5.0),
        default=None,
    ) if fail_cases else None

    disagreement_cases = sorted(
        results,
        key=lambda item: item.get("judge", {}).get("score_delta", 0.0),
        reverse=True,
    )
    worst_disagreement = disagreement_cases[0] if disagreement_cases else None
    disagreement_conflict_count = sum(
        1 for item in results if item.get("judge", {}).get("score_delta", 0.0) > 1.0
    )

    return {
        "counts": counts,
        "total_cases": summary.get("metadata", {}).get("total", len(results)),
        "version": summary.get("metadata", {}).get("version", "unknown"),
        "timestamp": summary.get("metadata", {}).get("timestamp", ""),
        "summary_metrics": summary.get("metrics", {}),
        "regression": summary.get("regression", {}),
        "worst_retrieval_case": worst_retrieval,
        "worst_partial_case": worst_partial,
        "worst_disagreement_case": worst_disagreement,
        "retrieval_miss_count": len(retrieval_misses),
        "disagreement_conflict_count": disagreement_conflict_count,
    }


def validate_dataset() -> Dict[str, Any]:
    dataset = load_jsonl(DATASET_PATH)
    required_fields = {
        "id",
        "question",
        "expected_answer",
        "expected_retrieval_ids",
        "metadata",
    }
    errors: List[str] = []
    for index, case in enumerate(dataset, start=1):
        missing = required_fields.difference(case.keys())
        if missing:
            errors.append(f"Case #{index} missing fields: {sorted(missing)}")
        if not isinstance(case.get("expected_retrieval_ids"), list):
            errors.append(f"Case #{index} expected_retrieval_ids is not a list.")

    return {
        "total_cases": len(dataset),
        "errors": errors,
    }


def format_case_summary(case: Optional[Dict[str, Any]]) -> str:
    if not case:
        return "None"

    return "- test_case: {}\n  status: {}\n  agent_response: {}\n  latency: {}s\n  ragas.relevancy: {}\n  judge.final_score: {}\n  judge.score_delta: {}\n  judge.agreement_rate: {}".format(
        case.get('test_case', 'N/A')[:80],
        case.get('status'),
        case.get('agent_response', 'N/A')[:60],
        case.get('latency'),
        case.get('ragas', {}).get('relevancy'),
        case.get('judge', {}).get('final_score'),
        case.get('judge', {}).get('score_delta'),
        case.get('judge', {}).get('agreement_rate'),
    )


def generate_failure_analysis_markdown(summary: Dict[str, Any], report_data: Dict[str, Any]) -> str:
    """Generate markdown failure analysis from new JSON report structure."""
    metrics = report_data["summary_metrics"]
    counts = report_data["counts"]
    regression = report_data["regression"]
    total = report_data["total_cases"]
    version = report_data["version"]
    timestamp = report_data["timestamp"]
    pass_rate = (counts.get('pass', 0) / total * 100) if total > 0 else 0.0

    v1_metrics = regression.get("v1", {})
    v2_metrics = regression.get("v2", {})
    regression_decision = regression.get("decision", "N/A")

    v1_score = v1_metrics.get('score', 'N/A')
    v2_score = v2_metrics.get('score', 'N/A')
    score_delta = v2_score - v1_score if isinstance(v1_score, (int, float)) and isinstance(v2_score, (int, float)) else 0

    lines = [
        "# Bao Cao Phan Tich That Bai - Toi uu hoa " + str(version),
        "",
        "**Timestamp**: " + str(timestamp),
        "**Quyet dinh Release**: " + str(regression_decision),
        "",
        "## 1. Tong quan benchmark",
        "",
        "| Metrics | V1 | V2 | Thay doi |",
        "| --- | --- | --- | --- |",
        "| Judge Score | {} | {} | {:.2f} |".format(v1_score, v2_score, score_delta),
        "| Hit Rate | {} | {} | {:.2f} |".format(
            v1_metrics.get('hit_rate', 'N/A'),
            v2_metrics.get('hit_rate', 'N/A'),
            (v2_metrics.get('hit_rate', 0) - v1_metrics.get('hit_rate', 0)) if isinstance(v1_metrics.get('hit_rate'), (int, float)) and isinstance(v2_metrics.get('hit_rate'), (int, float)) else 0
        ),
        "| Judge Agreement | {} | {} | {:.2f} |".format(
            v1_metrics.get('judge_agreement', 'N/A'),
            v2_metrics.get('judge_agreement', 'N/A'),
            (v2_metrics.get('judge_agreement', 0) - v1_metrics.get('judge_agreement', 0)) if isinstance(v1_metrics.get('judge_agreement'), (int, float)) and isinstance(v2_metrics.get('judge_agreement'), (int, float)) else 0
        ),
        "",
        "**Metrics hien tai (V2)**:",
        "- Tong cases: {}".format(total),
        "- Pass: {} ({:.1f}%)".format(counts.get('pass', 0), pass_rate),
        "- Fail: {}".format(counts.get('fail', 0)),
        "- Error: {}".format(counts.get('error', 0)),
        "- Avg Score: {}".format(metrics.get('avg_score')),
        "- Hit Rate: {}".format(metrics.get('hit_rate')),
        "- Agreement Rate: {}".format(metrics.get('agreement_rate')),
        "",
        "## 2. Phan nhom loi",
        "",
        "- Retrieval failures (relevancy == 0): {}".format(report_data['retrieval_miss_count']),
        "- Failed cases: {}".format(report_data['counts'].get('fail', 0)),
        "- Judge disagreement (delta > 1.0): {}".format(report_data['disagreement_conflict_count']),
        "- Max disagreement delta: {}".format(
            report_data['worst_disagreement_case'].get('judge', {}).get('score_delta')
            if report_data['worst_disagreement_case'] else 'N/A'
        ),
        "",
        "## 3. Worst cases",
        "",
        "### Case A - Retrieval failure",
        format_case_summary(report_data['worst_retrieval_case']),
        "",
        "### Case B - Partial/Wrong answer",
        format_case_summary(report_data['worst_partial_case']),
        "",
        "### Case C - Judge disagreement",
        format_case_summary(report_data['worst_disagreement_case']),
        "",
        "## 4. Goi y cai tien",
        "",
        "- Toi uu retrieval pipeline de cai thien hit_rate.".format(),
        "- Dieu chinh generation prompt cho cac case co score thap.",
        "- Xem xet tie-break logic khi judge disagreement cao.",
        "- Tiep tuc monitoring sau khi release quyet dinh {}.".format(regression_decision),
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate quick benchmark summary and dataset validation for Lab 14."
    )
    parser.add_argument(
        "--check-dataset",
        action="store_true",
        help="Validate data/golden_set.jsonl for required fields.",
    )
    parser.add_argument(
        "--report-summary",
        action="store_true",
        help="Summarize reports/summary.json and reports/benchmark_results.json.",
    )
    parser.add_argument(
        "--output-md",
        type=str,
        default=None,
        help="Write a markdown failure analysis report to the given path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.check_dataset:
        dataset_result = validate_dataset()
        print("Dataset validation result:")
        print(f"  total cases: {dataset_result['total_cases']}")
        if dataset_result["errors"]:
            print("  errors:")
            for error in dataset_result["errors"]:
                print(f"    - {error}")
        else:
            print("  dataset schema looks good.")

    if args.report_summary:
        summary_path = REPORTS_DIR / "summary.json"
        results_path = REPORTS_DIR / "benchmark_results.json"

        if not summary_path.exists() or not results_path.exists():
            print("Missing reports/summary.json or reports/benchmark_results.json.")
            return 1

        summary = load_json(summary_path)
        benchmark_results = load_json(results_path)
        report_data = summarize_reports(summary, benchmark_results)

        print(f"Benchmark summary (version: {report_data['version']}, timestamp: {report_data['timestamp']}):")
        print(f"  total: {report_data['total_cases']}")
        print(f"  pass: {report_data['counts'].get('pass', 0)}")
        print(f"  fail: {report_data['counts'].get('fail', 0)}")
        print(f"  error: {report_data['counts'].get('error', 0)}")
        print(f"  avg_score: {report_data['summary_metrics'].get('avg_score')}")
        print(f"  hit_rate: {report_data['summary_metrics'].get('hit_rate')}")
        print(f"  agreement_rate: {report_data['summary_metrics'].get('agreement_rate')}")
        regression = report_data.get('regression', {})
        if regression.get('v1') and regression.get('v2'):
            print("\nRegression V1 -> V2:")
            print(f"  v1.score: {regression['v1'].get('score')}")
            print(f"  v2.score: {regression['v2'].get('score')}")
            print(f"  decision: {regression.get('decision')}")
        print("\nWorst cases:")
        print("  Retrieval failure:")
        print(format_case_summary(report_data["worst_retrieval_case"]))
        print("  Partial/Wrong answer:")
        print(format_case_summary(report_data["worst_partial_case"]))
        print("  Judge disagreement:")
        print(format_case_summary(report_data["worst_disagreement_case"]))

        if args.output_md:
            output_path = Path(args.output_md)
            output_path.write_text(generate_failure_analysis_markdown(summary, report_data), encoding="utf-8")
            print(f"Wrote markdown failure analysis report to {output_path}")

    if not args.check_dataset and not args.report_summary:
        print("No action specified. Use --check-dataset or --report-summary.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
