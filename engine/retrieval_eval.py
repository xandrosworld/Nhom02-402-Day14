from typing import Dict, List


class RetrievalEvaluator:
    def calculate_hit_rate(
        self, expected_ids: List[str], retrieved_ids: List[str], top_k: int = 3
    ) -> float:
        top_retrieved = retrieved_ids[:top_k]
        return 1.0 if any(doc_id in top_retrieved for doc_id in expected_ids) else 0.0

    def calculate_mrr(self, expected_ids: List[str], retrieved_ids: List[str]) -> float:
        for index, doc_id in enumerate(retrieved_ids, start=1):
            if doc_id in expected_ids:
                return 1.0 / index
        return 0.0

    def calculate_context_precision(
        self, expected_ids: List[str], retrieved_ids: List[str], k: int = 3
    ) -> float:
        # Position-weighted precision (RAGAS): CP = (1/K) * sum_{i=1}^{K} (precision@i * rel_i)
        # Equivalent to Average Precision (AP) — relevant chunks ranked higher score more.
        relevant_count = 0
        score = 0.0
        for i, doc_id in enumerate(retrieved_ids[:k], start=1):
            if doc_id in expected_ids:
                relevant_count += 1
                score += relevant_count / i
        denominator = min(len(expected_ids), k)
        return round(score / denominator, 4) if denominator > 0 else 0.0

    def calculate_context_recall(
        self, expected_answer: str, contexts: List[str]
    ) -> float:
        # Fraction of expected_answer tokens present in retrieved contexts (RAGAS simplified).
        # contexts is already the agent's top-k retrieved docs — no need for further slicing.
        # Full RAGAS uses LLM to extract claims; token overlap is the proxy for mock mode.
        expected_tokens = set(expected_answer.lower().split())
        context_tokens = set(t for ctx in contexts for t in ctx.lower().split())
        if not expected_tokens:
            return 0.0
        return round(len(expected_tokens & context_tokens) / len(expected_tokens), 4)

    def calculate_faithfulness(self, answer: str, contexts: List[str]) -> float:
        # Fraction of answer tokens present in retrieved contexts (RAGAS simplified).
        # Full RAGAS uses LLM to verify each claim; token overlap approximates grounding.
        # Note: RAG systems naturally reuse context vocabulary, so this score tends to be
        # high by design — it cannot detect hallucination at the claim level.
        answer_tokens = set(answer.lower().split())
        context_tokens = set(t for ctx in contexts for t in ctx.lower().split())
        if not answer_tokens:
            return 0.0
        return round(len(answer_tokens & context_tokens) / len(answer_tokens), 4)

    async def score(self, test_case: Dict, response: Dict) -> Dict:
        expected_ids    = test_case.get("expected_retrieval_ids", [])
        retrieved_ids   = response.get("retrieved_ids", [])
        expected_answer = test_case.get("expected_answer", "")
        answer          = response.get("answer", "")
        contexts        = response.get("contexts", [])
        return {
            # Required fields — runner.py reads these four keys
            "hit_rate":          self.calculate_hit_rate(expected_ids, retrieved_ids),
            "mrr":               round(self.calculate_mrr(expected_ids, retrieved_ids), 4),
            "expected_ids":      expected_ids,
            "retrieved_ids":     retrieved_ids,
            # RAGAS-aligned metrics (simplified token-overlap proxies)
            "context_precision": self.calculate_context_precision(expected_ids, retrieved_ids),
            "context_recall":    self.calculate_context_recall(expected_answer, contexts),
            "faithfulness":      self.calculate_faithfulness(answer, contexts),
        }
