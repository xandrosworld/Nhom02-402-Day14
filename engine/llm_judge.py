import os
import time
import asyncio
import re
import concurrent.futures
from typing import Any, Dict, List

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
import google.generativeai as genai


# ===== INIT CLIENT =====
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class LLMJudge:
    def __init__(self, models: List[str]):
        if len(models) < 2:
            raise ValueError("Need at least 2 judge models")
        self.models = models[:2]

    # ===== PROMPT =====
    def _build_prompt(self, question: str, answer: str, ground_truth: str) -> str:
        return f"""
You are an evaluation judge.

Score the answer from 1 to 5 based on correctness compared to ground truth.

Question:
{question}

Ground Truth:
{ground_truth}

Answer:
{answer}

Return ONLY a number between 1 and 5.
"""

    # ===== PARSE SCORE (ROBUST) =====
    def _parse_score(self, text: str) -> float:
        try:
            match = re.search(r"\d+(\.\d+)?", text)
            if match:
                return float(match.group())
        except:
            pass
        return 3.0

    # ===== OPENAI JUDGE =====
    async def _judge_openai(self, prompt: str) -> Dict:
        start = time.perf_counter()

        try:
            response = openai_client.chat.completions.create(
                model=os.getenv("OPENAI_JUDGE_MODEL", "gpt-4.1-mini"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                timeout=20,  # 🔥 timeout
            )

            latency = (time.perf_counter() - start) * 1000

            content = response.choices[0].message.content.strip()
            score = self._parse_score(content)

            tokens = response.usage.total_tokens if response.usage else 0
            cost = tokens * 0.0000025

            return {
                "score": max(1.0, min(5.0, score)),
                "tokens": tokens,
                "cost": cost,
                "latency": latency,
            }

        except Exception as e:
            print(f"[OpenAI ERROR] {e}")
            return {
                "score": 3.0,
                "tokens": 0,
                "cost": 0,
                "latency": 0,
            }

    # ===== GEMINI JUDGE (WITH TIMEOUT FIX) =====
    async def _judge_gemini(self, prompt: str) -> Dict:
        start = time.perf_counter()

        def call_gemini():
            model = genai.GenerativeModel(
                os.getenv("GEMINI_JUDGE_MODEL", "gemini-2.5-flash")
            )
            return model.generate_content(prompt)

        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(call_gemini)
                response = future.result(timeout=20)  # 🔥 timeout

            latency = (time.perf_counter() - start) * 1000

            text = response.text.strip()
            score = self._parse_score(text)

            # estimate token
            tokens = len(prompt.split()) * 4
            cost = tokens * 0.000002

            return {
                "score": max(1.0, min(5.0, score)),
                "tokens": tokens,
                "cost": cost,
                "latency": latency,
            }

        except Exception as e:
            print(f"[Gemini ERROR] {e}")
            return {
                "score": 3.0,
                "tokens": 0,
                "cost": 0,
                "latency": 0,
            }

    # ===== MAIN MULTI-JUDGE =====
    async def evaluate_multi_judge(
        self,
        question: str,
        answer: str,
        ground_truth: str,
    ) -> Dict[str, Any]:

        prompt = self._build_prompt(question, answer, ground_truth)

        # chạy song song 2 judge
        res_a, res_b = await asyncio.gather(
            self._judge_openai(prompt),
            self._judge_gemini(prompt),
        )

        score_a = res_a["score"]
        score_b = res_b["score"]

        delta = abs(score_a - score_b)
        agreement_rate = round(max(0.0, 1 - delta / 4), 4)

        final_score = round((score_a + score_b) / 2, 2)

        conflict_flag = delta > 1.0
        if conflict_flag:
            final_score = round(min(score_a, score_b) + delta * 0.25, 2)

        total_tokens = res_a["tokens"] + res_b["tokens"]
        total_cost = res_a["cost"] + res_b["cost"]
        avg_latency = (res_a["latency"] + res_b["latency"]) / 2

        return {
            "question": question,
            "final_score": final_score,
            "agreement_rate": agreement_rate,
            "score_delta": round(delta, 2),
            "conflict_flag": conflict_flag,
            "individual_scores": {
                self.models[0]: score_a,
                self.models[1]: score_b,
            },
            "judge_metadata": {
                "judge_models": self.models,
                "tokens_used": int(total_tokens),
                "estimated_cost_usd": round(total_cost, 6),
                "latency_ms": round(avg_latency, 2),
            },
        }