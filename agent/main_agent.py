import asyncio
import json
import math
import os
from pathlib import Path
from typing import Dict, List, Optional
from urllib import error, request

from dotenv import load_dotenv
from openai import OpenAI

from data.sample_kb import SAMPLE_DOCUMENTS

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=False)


def _normalize(text: str) -> List[str]:
    cleaned = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    return [token for token in cleaned.split() if token]


def _sentence_split(text: str) -> List[str]:
    return [sentence.strip() for sentence in text.split(".") if sentence.strip()]


def _cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    if not vector_a or not vector_b or len(vector_a) != len(vector_b):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    norm_a = math.sqrt(sum(a * a for a in vector_a))
    norm_b = math.sqrt(sum(b * b for b in vector_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


class MainAgent:
    """
    Benchmark agent used by the evaluation runner.

    Current behavior:
    1. Retrieve documents from the local KB using hybrid lexical scoring.
    2. If a Voyage API key is available, blend in embedding similarity.
    3. Generate the final answer with OpenAI or Gemini when keys are present.
    4. Fall back to grounded local answer generation if any external call fails.
    """

    _document_embeddings: Dict[str, List[float]] = {}

    def __init__(self, version: str = "Agent_V1_Base"):
        self.version = version
        self.provider = os.getenv("PROVIDER", "openai").strip().lower()
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.voyage_api_key = os.getenv("VOYAGE_API_KEY", "").strip()
        self.voyage_embed_model = os.getenv("VOYAGE_EMBED_MODEL", "voyage-3-large")
        self.chat_model = self._resolve_chat_model()
        self.documents = self._build_document_store()
        self.openai_client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None

    def _resolve_chat_model(self) -> str:
        if self.provider == "gemini":
            return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        return os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")

    def _build_document_store(self) -> List[Dict]:
        documents: List[Dict] = []
        for doc in SAMPLE_DOCUMENTS:
            searchable_text = " ".join(
                [
                    doc.get("title", ""),
                    doc.get("topic", ""),
                    " ".join(doc.get("keywords", [])),
                    doc.get("text", ""),
                    doc.get("answer", ""),
                ]
            )
            documents.append(
                {
                    "id": doc["id"],
                    "title": doc["title"],
                    "topic": doc.get("topic", ""),
                    "keywords": doc.get("keywords", []),
                    "text": doc["text"],
                    "answer": doc.get("answer", ""),
                    "search_tokens": set(_normalize(searchable_text)),
                }
            )
        return documents

    def _score_document_lexical(self, question: str, doc: Dict) -> float:
        question_tokens = set(_normalize(question))
        if not question_tokens:
            return 0.0

        overlap = question_tokens.intersection(doc["search_tokens"])
        keyword_overlap = question_tokens.intersection(set(doc["keywords"]))
        topic_overlap = question_tokens.intersection(set(_normalize(doc["topic"])))
        title_overlap = question_tokens.intersection(set(_normalize(doc["title"])))

        score = (
            len(overlap)
            + len(keyword_overlap) * 2.0
            + len(topic_overlap) * 1.5
            + len(title_overlap) * 1.5
        )

        if "V2" in self.version:
            score += len(keyword_overlap) * 0.75 + len(topic_overlap) * 0.5

        return score

    def _voyage_embed(self, texts: List[str]) -> List[List[float]]:
        if not self.voyage_api_key:
            return []

        payload = {
            "model": self.voyage_embed_model,
            "input": texts,
        }
        http_request = request.Request(
            "https://api.voyageai.com/v1/embeddings",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.voyage_api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with request.urlopen(http_request, timeout=30) as response:
            response_payload = json.loads(response.read().decode("utf-8"))

        data_items = response_payload.get("data", [])
        return [item.get("embedding", []) for item in data_items]

    def _ensure_document_embeddings(self) -> None:
        missing_docs = [
            doc for doc in self.documents if doc["id"] not in self._document_embeddings
        ]
        if not missing_docs or not self.voyage_api_key:
            return

        texts = [doc["text"] for doc in missing_docs]
        embeddings = self._voyage_embed(texts)
        for doc, embedding in zip(missing_docs, embeddings):
            self._document_embeddings[doc["id"]] = embedding

    def _rank_documents(self, question: str, top_k: int = 3) -> List[Dict]:
        lexical_scores = {
            doc["id"]: self._score_document_lexical(question, doc) for doc in self.documents
        }

        embedding_scores: Dict[str, float] = {}
        if self.voyage_api_key:
            try:
                self._ensure_document_embeddings()
                query_embedding = self._voyage_embed([question])[0]
                for doc in self.documents:
                    doc_embedding = self._document_embeddings.get(doc["id"], [])
                    embedding_scores[doc["id"]] = _cosine_similarity(
                        query_embedding, doc_embedding
                    )
            except (error.URLError, TimeoutError, IndexError, KeyError, json.JSONDecodeError):
                embedding_scores = {}

        scored_docs = []
        for doc in self.documents:
            lexical_score = lexical_scores.get(doc["id"], 0.0)
            semantic_score = embedding_scores.get(doc["id"], 0.0)
            combined_score = lexical_score + semantic_score * 5.0
            if combined_score > 0:
                scored_docs.append((combined_score, doc))

        if not scored_docs:
            scored_docs = [(1.0, self.documents[0])]

        scored_docs.sort(key=lambda item: (-item[0], item[1]["id"]))
        return [doc for _, doc in scored_docs[:top_k]]

    def _build_fallback_answer(self, ranked_docs: List[Dict]) -> str:
        primary_doc = ranked_docs[0]
        fallback_answer = primary_doc.get("answer") or primary_doc["text"]
        primary_sentences = _sentence_split(fallback_answer)
        if not primary_sentences:
            primary_sentences = _sentence_split(primary_doc["text"])

        if "V2" in self.version:
            answer = primary_sentences[0]
            if len(primary_sentences) > 1:
                answer += ". " + primary_sentences[1]
            return answer if answer.endswith(".") else answer + "."

        answer = primary_sentences[0]
        return answer if answer.endswith(".") else answer + "."

    def _build_prompt(self, question: str, ranked_docs: List[Dict]) -> str:
        context_blocks = []
        for doc in ranked_docs:
            context_blocks.append(
                f"[{doc['id']}] {doc['title']}\n{doc['text']}"
            )

        instruction = (
            "Answer only from the provided knowledge base context. "
            "If the answer is not supported by the context, say clearly that the knowledge base does not contain that information. "
            "Do not invent facts."
        )
        if "V2" in self.version:
            instruction += " Keep the answer concise but include the most important supporting detail."

        return (
            f"{instruction}\n\n"
            f"Question:\n{question}\n\n"
            f"Knowledge base context:\n" + "\n\n".join(context_blocks)
        )

    def _generate_with_openai(self, prompt: str) -> Dict:
        response = self.openai_client.responses.create(
            model=self.chat_model,
            input=prompt,
        )
        usage = getattr(response, "usage", None)
        output_text = response.output_text.strip()
        total_tokens = getattr(usage, "total_tokens", 0) if usage else 0
        return {
            "answer": output_text,
            "tokens_used": total_tokens,
        }

    def _generate_with_gemini(self, prompt: str) -> Dict:
        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}],
                }
            ]
        }
        http_request = request.Request(
            (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.chat_model}:generateContent?key={self.gemini_api_key}"
            ),
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with request.urlopen(http_request, timeout=30) as response:
            response_payload = json.loads(response.read().decode("utf-8"))

        candidates = response_payload.get("candidates", [])
        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
            if candidates
            else []
        )
        answer = "\n".join(part.get("text", "") for part in parts).strip()
        usage = response_payload.get("usageMetadata", {})
        tokens_used = int(usage.get("totalTokenCount", 0))
        return {
            "answer": answer,
            "tokens_used": tokens_used,
        }

    def _generate_answer(self, question: str, ranked_docs: List[Dict]) -> Dict:
        fallback_answer = self._build_fallback_answer(ranked_docs)
        prompt = self._build_prompt(question, ranked_docs)

        try:
            if self.provider == "gemini" and self.gemini_api_key:
                generated = self._generate_with_gemini(prompt)
                if generated["answer"]:
                    return generated
            if self.provider == "openai" and self.openai_client:
                generated = self._generate_with_openai(prompt)
                if generated["answer"]:
                    return generated
        except Exception:
            pass

        return {
            "answer": fallback_answer,
            "tokens_used": max(80, len(_normalize(question + " " + fallback_answer)) * 4),
        }

    async def query(self, question: str) -> Dict:
        ranked_docs = await asyncio.to_thread(self._rank_documents, question, 3)
        generated = await asyncio.to_thread(self._generate_answer, question, ranked_docs)
        answer = generated["answer"]
        token_estimate = max(
            generated.get("tokens_used", 0),
            len(_normalize(question + " " + answer)) * 4,
        )
        estimated_cost = round(token_estimate * 0.000002, 6)

        return {
            "answer": answer,
            "contexts": [doc["text"] for doc in ranked_docs],
            "retrieved_ids": [doc["id"] for doc in ranked_docs],
            "metadata": {
                "model": self.chat_model,
                "provider": self.provider,
                "version": self.version,
                "tokens_used": token_estimate,
                "estimated_cost_usd": estimated_cost,
                "sources": [doc["title"] for doc in ranked_docs],
            },
        }
