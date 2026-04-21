import asyncio
import json
import os
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Dict, List, Tuple

from dotenv import load_dotenv

from agent.main_agent import MainAgent
from engine.llm_judge import LLMJudge
from engine.runner import BenchmarkRunner
from engine.retrieval_eval import RetrievalEvaluator

ROOT = Path(__file__).resolve().parent
DATASET_PATH = ROOT / "data" / "golden_set.jsonl"
REPORTS_DIR = ROOT / "reports"


@dataclass
class RuntimeConfig:
    baseline_version: str
    candidate_version: str
    provider: str
    judge_provider: str
    chat_model: str
    judge_models: Tuple[str, str]
    concurrency: int
    min_cases: int
    min_agreement_rate: float
    report_schema_version: str
    dataset_path: str


def _getenv_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def _getenv_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default


def _resolve_chat_model(provider: str) -> str:
    if provider == "gemini":
        return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    return os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")


def _resolve_judge_models(judge_provider: str) -> Tuple[str, str]:
    openai_judge = f"openai:{os.getenv('OPENAI_JUDGE_MODEL', 'gpt-4.1-mini')}"
    gemini_judge = f"gemini:{os.getenv('GEMINI_JUDGE_MODEL', 'gemini-2.5-flash')}"
    if judge_provider == "gemini":
        return gemini_judge, openai_judge
    return openai_judge, gemini_judge


def load_runtime_config() -> RuntimeConfig:
    load_dotenv(ROOT / ".env", override=False)

    provider = os.getenv("PROVIDER", "openai").strip().lower()
    judge_provider = os.getenv("JUDGE_PROVIDER", "openai").strip().lower()

    return RuntimeConfig(
        baseline_version=os.getenv("BASELINE_VERSION", "Agent_V1_Base"),
        candidate_version=os.getenv("CANDIDATE_VERSION", "Agent_V2_Candidate"),
        provider=provider,
        judge_provider=judge_provider,
        chat_model=_resolve_chat_model(provider),
        judge_models=_resolve_judge_models(judge_provider),
        concurrency=_getenv_int("BENCHMARK_CONCURRENCY", 5),
        min_cases=_getenv_int("MIN_GOLDEN_CASES", 50),
        min_agreement_rate=_getenv_float("MIN_AGREEMENT_RATE", 0.60),
        report_schema_version="1.1",
        dataset_path=str(DATASET_PATH.relative_to(ROOT)),
    )


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

    required_fields = {
        "id",
        "question",
        "expected_answer",
        "expected_retrieval_ids",
        "metadata",
    }
    for index, case in enumerate(dataset, start=1):
        missing = required_fields.difference(case.keys())
        if missing:
            missing_fields = ", ".join(sorted(missing))
            raise ValueError(
                f"Case #{index} in data/golden_set.jsonl is missing: {missing_fields}"
            )
        if not isinstance(case["expected_retrieval_ids"], list):
            raise ValueError(
                f"Case #{index} has invalid expected_retrieval_ids. Expected a list."
            )

    return dataset


def build_metrics(results: List[Dict]) -> Dict:
    total = len(results)
    pass_count = sum(1 for item in results if item["status"] == "pass")
    fail_count = sum(1 for item in results if item["status"] == "fail")
    error_count = sum(1 for item in results if item["status"] == "error")

    return {
        "avg_score": round(mean(item["judge"]["final_score"] for item in results), 4),
        "hit_rate": round(mean(item["retrieval"]["hit_rate"] for item in results), 4),
        "mrr": round(mean(item["retrieval"]["mrr"] for item in results), 4),
        "context_precision": round(
            mean(item["retrieval"].get("context_precision", 0.0) for item in results), 4
        ),
        "context_recall": round(
            mean(item["retrieval"].get("context_recall", 0.0) for item in results), 4
        ),
        "faithfulness": round(
            mean(item["retrieval"].get("faithfulness", 0.0) for item in results), 4
        ),
        "answer_relevancy": round(
            mean(item["retrieval"].get("answer_relevancy", 0.0) for item in results), 4
        ),
        "agreement_rate": round(
            mean(item["judge"]["agreement_rate"] for item in results), 4
        ),
        "avg_latency_ms": round(mean(item["latency_ms"] for item in results), 2),
        "pass_rate": round(pass_count / total, 4),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "error_count": error_count,
        "total_tokens": sum(item["metadata"].get("tokens_used", 0) for item in results),
        "total_cost_usd": round(
            sum(item["metadata"].get("estimated_cost_usd", 0.0) for item in results), 6
        ),
    }


def _compact_score(value: float):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def _format_teacher_case(result: Dict) -> Dict:
    judge = result["judge"]
    retrieval = result["retrieval"]
    individual_results = {}

    for model_name, score in judge.get("individual_scores", {}).items():
        individual_results[model_name] = {
            "score": _compact_score(score),
            "reasoning": "Auto-converted from internal judge output.",
        }

    return {
        "test_case": result["question"],
        "agent_response": result["agent_response"],
        "latency": round(result["latency_ms"] / 1000, 6),
        "ragas": {
            "hit_rate": retrieval["hit_rate"],
            "mrr": retrieval["mrr"],
            "faithfulness": retrieval.get("faithfulness", 0.0),
            "relevancy": retrieval.get("answer_relevancy", 0.0),
        },
        "judge": {
            "final_score": judge["final_score"],
            "agreement_rate": judge["agreement_rate"],
            "individual_results": individual_results,
            "status": "conflict" if judge.get("conflict_flag") else "consensus",
        },
        "status": result["status"],
    }


def _summary_version_label(candidate_version: str) -> str:
    upper_name = candidate_version.upper()
    if "V2" in upper_name:
        return "OPTIMIZED (V2)"
    return candidate_version


def make_release_gate(
    baseline_metrics: Dict,
    candidate_metrics: Dict,
    total_cases: int,
    runtime_config: RuntimeConfig,
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
    if candidate_metrics["pass_rate"] < baseline_metrics["pass_rate"]:
        decision = "rollback"
        reasons.append("Overall pass rate regressed.")
    if candidate_metrics["error_count"] > 0:
        decision = "rollback"
        reasons.append("Benchmark still has errored cases.")
    if candidate_metrics["agreement_rate"] < runtime_config.min_agreement_rate:
        decision = "rollback"
        reasons.append(
            f"Judge agreement rate is below {runtime_config.min_agreement_rate:.2f}."
        )
    if total_cases < runtime_config.min_cases:
        decision = "rollback"
        reasons.append(
            f"Golden dataset has fewer than {runtime_config.min_cases} cases."
        )

    if decision == "release":
        reasons.append("Candidate passed the starter release gate thresholds.")

    return {
        "decision": decision,
        "score_delta": score_delta,
        "hit_rate_delta": hit_rate_delta,
        "latency_delta_ms": latency_delta_ms,
        "pass_rate_delta": round(
            candidate_metrics["pass_rate"] - baseline_metrics["pass_rate"], 4
        ),
        "thresholds": {
            "min_cases": runtime_config.min_cases,
            "min_agreement_rate": runtime_config.min_agreement_rate,
        },
        "reasons": reasons,
    }


def build_result_samples(results: List[Dict]) -> Dict:
    failed_case_ids = [item["case_id"] for item in results if item["status"] == "fail"]
    error_case_ids = [item["case_id"] for item in results if item["status"] == "error"]
    return {
        "failed_case_ids": failed_case_ids[:10],
        "error_case_ids": error_case_ids[:10],
    }


def write_json(path: Path, payload: Dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


async def run_version(
    agent_version: str, dataset: List[Dict], runtime_config: RuntimeConfig
) -> Tuple[List[Dict], Dict]:
    runner = BenchmarkRunner(
        agent=MainAgent(version=agent_version),
        evaluator=RetrievalEvaluator(),
        judge=LLMJudge(models=list(runtime_config.judge_models)),
    )
    results = await runner.run_all(dataset, concurrency=runtime_config.concurrency)
    return results, build_metrics(results)


async def main() -> None:
    runtime_config = load_runtime_config()
    dataset = load_dataset()

    baseline_results, baseline_metrics = await run_version(
        runtime_config.baseline_version,
        dataset,
        runtime_config,
    )
    candidate_results, candidate_metrics = await run_version(
        runtime_config.candidate_version,
        dataset,
        runtime_config,
    )

    release_gate = make_release_gate(
        baseline_metrics=baseline_metrics,
        candidate_metrics=candidate_metrics,
        total_cases=len(dataset),
        runtime_config=runtime_config,
    )
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    summary = {
        "metadata": {
            "total": len(dataset),
            "version": _summary_version_label(runtime_config.candidate_version),
            "timestamp": timestamp,
            "versions_compared": ["V1", "V2"],
        },
        "metrics": {
            "avg_score": candidate_metrics["avg_score"],
            "hit_rate": candidate_metrics["hit_rate"],
            "mrr": candidate_metrics["mrr"],
            "agreement_rate": candidate_metrics["agreement_rate"],
            "pass_rate": candidate_metrics["pass_rate"],
        },
        "regression": {
            "v1": {
                "score": baseline_metrics["avg_score"],
                "hit_rate": baseline_metrics["hit_rate"],
                "judge_agreement": baseline_metrics["agreement_rate"],
            },
            "v2": {
                "score": candidate_metrics["avg_score"],
                "hit_rate": candidate_metrics["hit_rate"],
                "judge_agreement": candidate_metrics["agreement_rate"],
            },
            "decision": release_gate["decision"].upper(),
        },
    }

    detailed_results = {
        "v1": [_format_teacher_case(item) for item in baseline_results],
        "v2": [_format_teacher_case(item) for item in candidate_results],
    }

    REPORTS_DIR.mkdir(exist_ok=True)
    write_json(REPORTS_DIR / "summary.json", summary)
    write_json(REPORTS_DIR / "benchmark_results.json", detailed_results)

    print("Benchmark complete.")
    print(f"Baseline avg_score:  {baseline_metrics['avg_score']:.2f}")
    print(f"Candidate avg_score: {candidate_metrics['avg_score']:.2f}")
    print(f"Release gate:        {release_gate['decision'].upper()}")


if __name__ == "__main__":
    asyncio.run(main())
