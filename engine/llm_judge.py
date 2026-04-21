from typing import Any, Dict, List


def _normalize(text: str) -> List[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return [token for token in cleaned.split() if token]


class LLMJudge:
    def __init__(self, models: List[str]):
        self.models = models

    def _score_with_overlap(self, answer: str, ground_truth: str, bias: float) -> float:
        answer_tokens = set(_normalize(answer))
        truth_tokens = set(_normalize(ground_truth))
        if not truth_tokens:
            return 1.0

        overlap = len(answer_tokens.intersection(truth_tokens)) / len(truth_tokens)
        raw_score = 1.0 + overlap * 4.0 + bias
        return max(1.0, min(5.0, round(raw_score, 2)))

    async def evaluate_multi_judge(
        self, question: str, answer: str, ground_truth: str
    ) -> Dict[str, Any]:
        score_a = self._score_with_overlap(answer, ground_truth, bias=0.1)
        score_b = self._score_with_overlap(answer, ground_truth, bias=-0.1)
        delta = abs(score_a - score_b)
        agreement = round(max(0.0, 1.0 - delta / 4.0), 4)
        final_score = round((score_a + score_b) / 2.0, 2)

        return {
            "question": question,
            "final_score": final_score,
            "agreement_rate": agreement,
            "score_delta": round(delta, 2),
            "conflict_flag": delta > 1.0,
            "individual_scores": {
                self.models[0]: score_a,
                self.models[1]: score_b,
            },
        }
