import asyncio
import time
from typing import Dict, List


class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge

    @staticmethod
    def _normalize_metadata(response: Dict) -> Dict:
        metadata = response.get("metadata") or {}
        return {
            "model": metadata.get("model", "unknown"),
            "version": metadata.get("version", "unknown"),
            "tokens_used": metadata.get("tokens_used", 0),
            "estimated_cost_usd": metadata.get("estimated_cost_usd", 0.0),
            "sources": metadata.get("sources", []),
        }

    @staticmethod
    def _normalize_retrieval(test_case: Dict, response: Dict, retrieval: Dict) -> Dict:
        retrieval = retrieval or {}
        return {
            "hit_rate": retrieval.get("hit_rate", 0.0),
            "mrr": retrieval.get("mrr", 0.0),
            "expected_ids": retrieval.get(
                "expected_ids", test_case.get("expected_retrieval_ids", [])
            ),
            "retrieved_ids": retrieval.get(
                "retrieved_ids", response.get("retrieved_ids", [])
            ),
            "context_precision": retrieval.get("context_precision", 0.0),
            "context_recall": retrieval.get("context_recall", 0.0),
            "faithfulness": retrieval.get("faithfulness", 0.0),
            "answer_relevancy": retrieval.get("answer_relevancy", 0.0),
        }

    @staticmethod
    def _normalize_judge(question: str, judge: Dict) -> Dict:
        judge = judge or {}
        return {
            "question": judge.get("question", question),
            "final_score": judge.get("final_score", 0.0),
            "agreement_rate": judge.get("agreement_rate", 0.0),
            "score_delta": judge.get("score_delta", 0.0),
            "conflict_flag": judge.get("conflict_flag", False),
            "individual_scores": judge.get("individual_scores", {}),
            "judge_metadata": judge.get("judge_metadata", {}),
        }

    async def run_single_test(self, test_case: Dict) -> Dict:
        print(f"→ START: {test_case['question'][:50]}")
        start_time = time.perf_counter()
        response = {
            "answer": "",
            "retrieved_ids": [],
            "metadata": {},
        }
        error_message = None

        try:
            response = await self.agent.query(test_case["question"])
            retrieval_raw = await self.evaluator.score(test_case, response)
            judge_raw = await self.judge.evaluate_multi_judge(
                question=test_case["question"],
                answer=response["answer"],
                ground_truth=test_case["expected_answer"],
            )
            status = "pass" if judge_raw.get("final_score", 0.0) >= 3.0 else "fail"
        except Exception as exc:
            retrieval_raw = {}
            judge_raw = {}
            status = "error"
            error_message = f"{type(exc).__name__}: {exc}"

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        retrieval = self._normalize_retrieval(test_case, response, retrieval_raw)
        judge = self._normalize_judge(test_case["question"], judge_raw)
        metadata = self._normalize_metadata(response)
        print(f"✓ DONE: {test_case['question'][:30]} | score={judge_raw.get('final_score')}")
        return {
            "case_id": test_case.get("id"),
            "question": test_case["question"],
            "expected_answer": test_case["expected_answer"],
            "test_case_metadata": test_case.get("metadata", {}),
            "agent_response": response["answer"],
            "retrieval": retrieval,
            "judge": judge,
            "latency_ms": latency_ms,
            "metadata": metadata,
            "status": status,
            "error": error_message,
        }

    async def run_all(self, dataset: List[Dict], concurrency: int = 10) -> List[Dict]:
        results = []

        # chia batch
        batch_size = concurrency
        batches = [dataset[i:i + batch_size] for i in range(0, len(dataset), batch_size)]

        print(f"Total cases: {len(dataset)} | Batch size: {batch_size} | Batches: {len(batches)}")

        for b_idx, batch in enumerate(batches):
            print(f"\n🚀 Running batch {b_idx+1}/{len(batches)}")

            tasks = []
            for case in batch:
                tasks.append(self.run_single_test(case))

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # xử lý lỗi
            for r in batch_results:
                if isinstance(r, Exception):
                    print(f"[ERROR] {r}")
                else:
                    print(f"✓ {r['case_id']} | score={r['judge']['final_score']}")
                    results.append(r)

        return results
