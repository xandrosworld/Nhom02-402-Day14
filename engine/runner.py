import asyncio
import time
from typing import Dict, List


class BenchmarkRunner:
    def __init__(self, agent, evaluator, judge):
        self.agent = agent
        self.evaluator = evaluator
        self.judge = judge

    async def run_single_test(self, test_case: Dict) -> Dict:
        start_time = time.perf_counter()
        response = await self.agent.query(test_case["question"])
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

        retrieval = await self.evaluator.score(test_case, response)
        judge = await self.judge.evaluate_multi_judge(
            question=test_case["question"],
            answer=response["answer"],
            ground_truth=test_case["expected_answer"],
        )

        return {
            "case_id": test_case.get("id"),
            "question": test_case["question"],
            "expected_answer": test_case["expected_answer"],
            "agent_response": response["answer"],
            "retrieval": retrieval,
            "judge": judge,
            "latency_ms": latency_ms,
            "metadata": response.get("metadata", {}),
            "status": "pass" if judge["final_score"] >= 3.0 else "fail",
        }

    async def run_all(self, dataset: List[Dict], concurrency: int = 5) -> List[Dict]:
        semaphore = asyncio.Semaphore(concurrency)

        async def _guarded(case: Dict) -> Dict:
            async with semaphore:
                return await self.run_single_test(case)

        tasks = [_guarded(case) for case in dataset]
        return await asyncio.gather(*tasks)
