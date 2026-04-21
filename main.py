import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Dict, List, Tuple

from agent.main_agent import MainAgent
from engine.llm_judge import LLMJudge
from engine.runner import BenchmarkRunner
from engine.retrieval_eval import RetrievalEvaluator

ROOT = Path(__file__).resolve().parent
DATASET_PATH = ROOT / "data" / "golden_set.jsonl"
REPORTS_DIR = ROOT / "reports"


def load_dataset() -> List[Dict]:
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            "Missing data/golden_set.jsonl. Run `python data/synthetic_gen.py` first."
        )

    dataset: List[Dict] = []
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                dataset.append(json.loads(line))

    if not dataset:
        raise ValueError("data/golden_set.jsonl is empty.")

    return dataset


def build_metrics(results: List[Dict]) -> Dict:
    return {
        "avg_score": round(mean(item["judge"]["final_score"] for item in results), 4),
        "hit_rate": round(mean(item["retrieval"]["hit_rate"] for item in results), 4),
        "mrr": round(mean(item["retrieval"]["mrr"] for item in results), 4),
        "agreement_rate": round(
            mean(item["judge"]["agreement_rate"] for item in results), 4
        ),
        "avg_latency_ms": round(mean(item["latency_ms"] for item in results), 2),
        "pass_rate": round(
            sum(1 for item in results if item["status"] == "pass") / len(results), 4
        ),
        "total_tokens": sum(item["metadata"]["tokens_used"] for item in results),
        "total_cost_usd": round(
            sum(item["metadata"]["estimated_cost_usd"] for item in results), 6
        ),
    }


def make_release_gate(
    baseline_metrics: Dict, candidate_metrics: Dict, total_cases: int
) -> Dict:
    score_delta = round(
        candidate_metrics["avg_score"] - baseline_metrics["avg_score"], 4
    )
    hit_rate_delta = round(
        candidate_metrics["hit_rate"] - baseline_metrics["hit_rate"], 4
    )
    latency_delta_ms = round(
        candidate_metrics["avg_latency_ms"] - baseline_metrics["avg_latency_ms"], 2
    )

    decision = "release"
    reasons: List[str] = []

    if candidate_metrics["avg_score"] < baseline_metrics["avg_score"]:
        decision = "rollback"
        reasons.append("Average judge score regressed.")
    if candidate_metrics["hit_rate"] < baseline_metrics["hit_rate"]:
        decision = "rollback"
        reasons.append("Retrieval hit rate regressed.")
    if candidate_metrics["agreement_rate"] < 0.6:
        decision = "rollback"
        reasons.append("Judge agreement rate is below 0.60.")
    if total_cases < 50:
        decision = "rollback"
        reasons.append("Golden dataset has fewer than 50 cases.")

    if decision == "release":
        reasons.append("Candidate passed the starter release gate thresholds.")

    return {
        "decision": decision,
        "score_delta": score_delta,
        "hit_rate_delta": hit_rate_delta,
        "latency_delta_ms": latency_delta_ms,
        "reasons": reasons,
    }


async def run_version(agent_version: str, dataset: List[Dict]) -> Tuple[List[Dict], Dict]:
    runner = BenchmarkRunner(
        agent=MainAgent(version=agent_version),
        evaluator=RetrievalEvaluator(),
        judge=LLMJudge(models=["gpt-4o-mini", "claude-3-5-sonnet"]),
    )
    results = await runner.run_all(dataset, concurrency=5)
    return results, build_metrics(results)


async def main() -> None:
    dataset = load_dataset()

    baseline_results, baseline_metrics = await run_version("Agent_V1_Base", dataset)
    candidate_results, candidate_metrics = await run_version(
        "Agent_V2_Candidate", dataset
    )

    release_gate = make_release_gate(
        baseline_metrics=baseline_metrics,
        candidate_metrics=candidate_metrics,
        total_cases=len(dataset),
    )

    summary = {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total": len(dataset),
            "baseline_version": "Agent_V1_Base",
            "candidate_version": "Agent_V2_Candidate",
        },
        "metrics": candidate_metrics,
        "baseline": baseline_metrics,
        "candidate": candidate_metrics,
        "regression": release_gate,
    }

    detailed_results = {
        "baseline_results": baseline_results,
        "candidate_results": candidate_results,
    }

    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (REPORTS_DIR / "benchmark_results.json").write_text(
        json.dumps(detailed_results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Benchmark complete.")
    print(f"Baseline avg_score:  {baseline_metrics['avg_score']:.2f}")
    print(f"Candidate avg_score: {candidate_metrics['avg_score']:.2f}")
    print(f"Release gate:        {release_gate['decision'].upper()}")


if __name__ == "__main__":
    asyncio.run(main())
