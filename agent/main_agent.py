import asyncio
from typing import Dict, List

from data.sample_kb import SAMPLE_DOCUMENTS


def _normalize(text: str) -> List[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return [token for token in cleaned.split() if token]


class MainAgent:
    """
    Starter RAG-style agent.

    Teams can replace this with their production agent later, but the interface is
    stable enough for the benchmark runner to work immediately.
    """

    def __init__(self, version: str = "Agent_V1_Base"):
        self.version = version

    def _rank_documents(self, question: str) -> List[Dict]:
        question_tokens = set(_normalize(question))
        scored_docs = []
        for doc in SAMPLE_DOCUMENTS:
            keyword_overlap = len(question_tokens.intersection(set(doc["keywords"])))
            title_overlap = len(question_tokens.intersection(set(_normalize(doc["title"]))))
            score = keyword_overlap * 2 + title_overlap
            if score > 0:
                scored_docs.append((score, doc))

        if not scored_docs:
            scored_docs = [(1, SAMPLE_DOCUMENTS[0])]

        scored_docs.sort(key=lambda item: (-item[0], item[1]["id"]))
        return [doc for _, doc in scored_docs[:3]]

    async def query(self, question: str) -> Dict:
        ranked_docs = self._rank_documents(question)
        primary_doc = ranked_docs[0]
        await asyncio.sleep(0.05 if "V2" in self.version else 0.08)

        if "V2" in self.version:
            answer = (
                f"{primary_doc['answer']} "
                f"Supporting docs: {', '.join(doc['id'] for doc in ranked_docs)}."
            )
        else:
            answer = primary_doc["answer"].split(".")[0].strip() + "."

        token_estimate = max(80, len(_normalize(answer)) * 6)
        estimated_cost = round(token_estimate * 0.000002, 6)

        return {
            "answer": answer,
            "contexts": [doc["text"] for doc in ranked_docs],
            "retrieved_ids": [doc["id"] for doc in ranked_docs],
            "metadata": {
                "model": "starter-simulated-rag",
                "version": self.version,
                "tokens_used": token_estimate,
                "estimated_cost_usd": estimated_cost,
                "sources": [doc["title"] for doc in ranked_docs],
            },
        }
