import asyncio
import json
import math
import os
from typing import Dict, List
from urllib import request as urllib_request

from openai import OpenAI


class RetrievalEvaluator:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.voyage_api_key = os.getenv("VOYAGE_API_KEY", "").strip()
        self.voyage_embed_model = os.getenv("VOYAGE_EMBED_MODEL", "voyage-3-large")
        self.openai_model = os.getenv("OPENAI_JUDGE_MODEL", "gpt-4.1-mini")
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

    # ------------------------------------------------------------------ #
    # Core retrieval metrics (required by runner.py)                       #
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    # RAGAS-aligned metrics                                                #
    # ------------------------------------------------------------------ #

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

    async def calculate_answer_relevancy(
        self, question: str, answer: str, n: int = 3
    ) -> float:
        # Full RAGAS implementation: generate n reverse questions from the answer via LLM,
        # then measure cosine similarity between their embeddings and the original question.
        # High similarity → the answer addresses the question → high relevancy.
        # Both IO calls run in thread pool to avoid blocking the event loop.
        reverse_questions = await asyncio.to_thread(self._generate_reverse_questions, answer, n)
        if not reverse_questions:
            return 0.0

        embeddings = await asyncio.to_thread(self._embed, [question] + reverse_questions)
        if len(embeddings) < 2:
            return 0.0

        q_emb = embeddings[0]
        similarities = [
            self._cosine_similarity(q_emb, rq_emb) for rq_emb in embeddings[1:]
        ]
        return round(sum(similarities) / len(similarities), 4)

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _generate_reverse_questions(self, answer: str, n: int) -> List[str]:
        if not self.openai_client:
            return []
        prompt = (
            f"Generate {n} concise questions that the following answer is responding to.\n"
            f"Output only the questions, one per line, with no numbering or extra text.\n\n"
            f"Answer: {answer}"
        )
        try:
            response = self.openai_client.responses.create(
                model=self.openai_model,
                input=prompt,
            )
            lines = [q.strip() for q in response.output_text.strip().split("\n") if q.strip()]
            return lines[:n]
        except Exception:
            return []

    def _embed(self, texts: List[str]) -> List[List[float]]:
        if not self.voyage_api_key or not texts:
            return []
        payload = {"model": self.voyage_embed_model, "input": texts}
        req = urllib_request.Request(
            "https://api.voyageai.com/v1/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.voyage_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib_request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return [item.get("embedding", []) for item in data.get("data", [])]
        except Exception:
            return []

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    # ------------------------------------------------------------------ #
    # Main entry point                                                     #
    # ------------------------------------------------------------------ #

    async def score(self, test_case: Dict, response: Dict) -> Dict:
        expected_ids    = test_case.get("expected_retrieval_ids", [])
        retrieved_ids   = response.get("retrieved_ids", [])
        expected_answer = test_case.get("expected_answer", "")
        question        = test_case.get("question", "")
        answer          = response.get("answer", "")
        contexts        = response.get("contexts", [])
        return {
            # Required fields — runner.py reads these four keys
            "hit_rate":          self.calculate_hit_rate(expected_ids, retrieved_ids),
            "mrr":               round(self.calculate_mrr(expected_ids, retrieved_ids), 4),
            "expected_ids":      expected_ids,
            "retrieved_ids":     retrieved_ids,
            # RAGAS-aligned metrics
            "context_precision": self.calculate_context_precision(expected_ids, retrieved_ids),
            "context_recall":    self.calculate_context_recall(expected_answer, contexts),
            "faithfulness":      self.calculate_faithfulness(answer, contexts),
            "answer_relevancy":  await self.calculate_answer_relevancy(question, answer),
        }
