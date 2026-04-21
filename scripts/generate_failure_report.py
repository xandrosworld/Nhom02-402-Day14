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


def summarize_reports(summary: Dict[str, Any], benchmark_results: Any) -> Dict[str, Any]:
    if isinstance(benchmark_results, dict):
        benchmark_results = benchmark_results.get("candidate_results") or benchmark_results.get("results") or benchmark_results.get("baseline_results") or []

    counts = {"pass": 0, "fail": 0, "error": 0}
    for item in benchmark_results:
        counts[item.get("status", "unknown")] = counts.get(item.get("status", "unknown"), 0) + 1

    retrieval_misses = [
        item for item in benchmark_results if item.get("retrieval", {}).get("hit_rate", 0.0) == 0.0
    ]
    worst_retrieval = min(
        retrieval_misses,
        key=lambda item: item.get("retrieval", {}).get("mrr", 0.0),
        default=None,
    )

    passed_cases = [item for item in benchmark_results if item.get("status") == "pass"]
    worst_partial = min(
        passed_cases,
        key=lambda item: item.get("judge", {}).get("final_score", 5.0),
        default=None,
    )

    disagreement_cases = sorted(
        benchmark_results,
        key=lambda item: item.get("judge", {}).get("score_delta", 0.0),
        reverse=True,
    )
    worst_disagreement = disagreement_cases[0] if disagreement_cases else None
    disagreement_conflict_count = sum(
        1 for item in benchmark_results if item.get("judge", {}).get("score_delta", 0.0) > 1.0
    )

    return {
        "counts": counts,
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

    return (
        f"- case_id: {case.get('case_id') or case.get('id')}\n"
        f"  status: {case.get('status')}\n"
        f"  retrieval.hit_rate: {case.get('retrieval', {}).get('hit_rate')}\n"
        f"  retrieval.mrr: {case.get('retrieval', {}).get('mrr')}\n"
        f"  judge.final_score: {case.get('judge', {}).get('final_score')}\n"
        f"  judge.score_delta: {case.get('judge', {}).get('score_delta')}\n"
        f"  agreement_rate: {case.get('judge', {}).get('agreement_rate')}\n"
    )


def generate_failure_analysis_markdown(summary: Dict[str, Any], report_data: Dict[str, Any]) -> str:
    metrics = report_data["summary_metrics"]
    counts = report_data["counts"]
    regression = report_data["regression"]

    return f"""# Báo cáo phân tích failure tự động

## 1. Tổng quan benchmark
- total cases: {counts.get('pass', 0) + counts.get('fail', 0) + counts.get('error', 0)}
- pass_count: {counts.get('pass', 0)}
- fail_count: {counts.get('fail', 0)}
- error_count: {counts.get('error', 0)}
- avg_score: {metrics.get('avg_score')}
- hit_rate: {metrics.get('hit_rate')}
- mrr: {metrics.get('mrr')}
- agreement_rate: {metrics.get('agreement_rate')}
- pass_rate: {metrics.get('pass_rate')}
- regression decision: {regression.get('decision')}
- regression reasons: {regression.get('reasons')}

## 2. Phân nhóm lỗi
- Retrieval miss cases (hit_rate == 0): {report_data['retrieval_miss_count']}
- Fail cases (partial / wrong answer): {report_data['counts'].get('fail', 0)}
- Judge disagreement cases (score_delta > 1.0): {report_data['disagreement_conflict_count']}
- Top judge disagreement delta: {report_data['worst_disagreement_case'].get('judge', {}).get('score_delta') if report_data['worst_disagreement_case'] else 'N/A'}

## 3. Worst cases
### Retrieval miss
{format_case_summary(report_data['worst_retrieval_case'])}

### Partial answer
{format_case_summary(report_data['worst_partial_case'])}

### Judge disagreement
{format_case_summary(report_data['worst_disagreement_case'])}

## 4. Gợi ý cải tiến
- Kiểm tra lại pipeline retrieval khi `hit_rate == 0`.
- Xem lại prompt và generator cho các case có `final_score` thấp.
- Điều chỉnh logic `agreement_rate` / `score_delta` để xử lý conflict tốt hơn.
- Chuẩn hoá schema `reports/summary.json` để hỗ trợ tự động hoá báo cáo.

## 5. Hướng tiếp theo
- Sử dụng script này để tự động ghi `analysis/failure_analysis.md` khi benchmark hoàn tất.
"""  # noqa: E501


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

        print("Benchmark summary:")
        print(f"  pass: {report_data['counts'].get('pass', 0)}")
        print(f"  fail: {report_data['counts'].get('fail', 0)}")
        print(f"  error: {report_data['counts'].get('error', 0)}")
        print(f"  avg_score: {report_data['summary_metrics'].get('avg_score')}")
        print(f"  hit_rate: {report_data['summary_metrics'].get('hit_rate')}")
        print(f"  mrr: {report_data['summary_metrics'].get('mrr')}")
        print(f"  agreement_rate: {report_data['summary_metrics'].get('agreement_rate')}")
        print("\nWorst cases:")
        print("  Retrieval miss:")
        print(format_case_summary(report_data["worst_retrieval_case"]))
        print("  Partial answer:")
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
