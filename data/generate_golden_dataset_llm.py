import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from sample_kb import SAMPLE_DOCUMENTS

"""
data/generate_golden_dataset_llm.py

LLM-assisted golden dataset generator for Lab 14. Produces a JSONL dataset with
retrieval ground-truth IDs and adversarial red-team cases.

Usage:
  python data/generate_golden_dataset_llm.py
  python data/generate_golden_dataset_llm.py --output data/golden_set_llm.jsonl --standard 4 --multi-hop 8 --adversarial 8 --out-of-context 6 --edge 4

Requirements:
  - set OPENAI_API_KEY in .env or environment
  - pip install openai python-dotenv
"""

OUTPUT_PATH = Path(__file__).resolve().parent / "golden_set_llm.jsonl"
DEFAULT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")


def _make_case(
    case_id: str,
    question: str,
    expected_answer: str,
    expected_retrieval_ids: List[str],
    difficulty: str,
    case_type: str,
    topic: str,
    context_hint: str = "",
) -> Dict[str, Any]:
    return {
        "id": case_id,
        "question": question,
        "expected_answer": expected_answer,
        "expected_retrieval_ids": expected_retrieval_ids,
        "metadata": {
            "topic": topic,
            "difficulty": difficulty,
            "case_type": case_type,
            "context_hint": context_hint,
        },
    }


def _clean_json_array(raw: str) -> str:
    match = re.search(r"\[(?:.|\n)*\]", raw)
    if not match:
        raise ValueError("Unable to locate a JSON array in the model response.")
    return match.group(0)


def _load_openai():
    try:
        import openai
    except ImportError as exc:
        raise ImportError(
            "openai package is required for this script. Install it with `pip install openai`."
        ) from exc

    load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=False)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY is not set. Please export it or add it to .env."
        )

    if hasattr(openai, "OpenAI"):
        client = openai.OpenAI(api_key=api_key)
        if os.getenv("OPENAI_API_BASE"):
            client.api_base = os.getenv("OPENAI_API_BASE")
        return client

    openai.api_key = api_key
    if os.getenv("OPENAI_API_BASE"):
        openai.api_base = os.getenv("OPENAI_API_BASE")
    return openai


def _call_openai(prompt: str, model: str, temperature: float) -> str:
    client = _load_openai()
    if hasattr(client, "chat"):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a high-quality dataset generation assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=1500,
        )
        return response.choices[0].message.content

    response = client.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a high-quality dataset generation assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        max_tokens=1500,
    )
    return response.choices[0].message.content


def _generate_from_prompt(prompt: str, model: str, temperature: float, retries: int = 3) -> List[Dict[str, Any]]:
    for attempt in range(1, retries + 1):
        raw = _call_openai(prompt, model=model, temperature=temperature)
        try:
            text = _clean_json_array(raw)
            return json.loads(text)
        except Exception as exc:
            print(f"[WARN] Failed to parse JSON on attempt {attempt}: {exc}")
            if attempt == retries:
                raise
            time.sleep(1 + attempt)
    raise RuntimeError("Unable to generate valid JSON from LLM.")


def generate_standard_cases(sample_docs: List[Dict[str, Any]], model: str, temperature: float, cases_per_doc: int = 5) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    for doc in sample_docs:
        prompt = (
            "Create exactly {count} question-answer pairs based on the following knowledge base document. "
            "Each pair must include a question and a concise expected answer grounded in the document. "
            "Use only the document's content, do not add outside facts. "
            "Return a JSON array of objects. Each object should have fields: question, expected_answer.\n\n"
            "Document:\n"
            f"id: {doc['id']}\n"
            f"topic: {doc['topic']}\n"
            f"text: {doc['text']}\n"
            f"answer: {doc['answer']}\n"
        ).format(count=cases_per_doc)
        results = _generate_from_prompt(prompt, model=model, temperature=temperature)
        for index, item in enumerate(results, start=1):
            case_id = f"{doc['id']}_std_{index:02d}"
            cases.append(
                _make_case(
                    case_id=case_id,
                    question=item["question"].strip(),
                    expected_answer=item["expected_answer"].strip(),
                    expected_retrieval_ids=[doc["id"]],
                    difficulty="easy" if index <= 3 else "medium",
                    case_type="standard",
                    topic=doc["topic"],
                    context_hint="Ground the answer in the referenced document.",
                )
            )
    return cases


def generate_multi_hop_cases(sample_docs: List[Dict[str, Any]], model: str, temperature: float, count: int = 8) -> List[Dict[str, Any]]:
    doc_pairs = [
        (sample_docs[i], sample_docs[j])
        for i in range(len(sample_docs))
        for j in range(i + 1, len(sample_docs))
    ]
    cases: List[Dict[str, Any]] = []
    for index, (doc_a, doc_b) in enumerate(doc_pairs[:count], start=1):
        prompt = (
            "Create one multi-hop question that requires combining evidence from both documents. "
            "Return a JSON array with a single object containing question and expected_answer.\n\n"
            "Document A:\n"
            f"id: {doc_a['id']}\n"
            f"topic: {doc_a['topic']}\n"
            f"text: {doc_a['text']}\n"
            f"answer: {doc_a['answer']}\n\n"
            "Document B:\n"
            f"id: {doc_b['id']}\n"
            f"topic: {doc_b['topic']}\n"
            f"text: {doc_b['text']}\n"
            f"answer: {doc_b['answer']}\n"
        )
        results = _generate_from_prompt(prompt, model=model, temperature=temperature)
        case_id = f"multihop_{doc_a['id']}_{doc_b['id']}"
        cases.append(
            _make_case(
                case_id=case_id,
                question=results[0]["question"].strip(),
                expected_answer=results[0]["expected_answer"].strip(),
                expected_retrieval_ids=[doc_a["id"], doc_b["id"]],
                difficulty="hard",
                case_type="multi_hop",
                topic=f"{doc_a['topic']} + {doc_b['topic']}",
                context_hint="Combine evidence from both supporting documents.",
            )
        )
    return cases


def generate_adversarial_cases(sample_docs: List[Dict[str, Any]], model: str, temperature: float, count: int = 8) -> List[Dict[str, Any]]:
    cases: List[Dict[str, Any]] = []
    for index, doc in enumerate(sample_docs[:count], start=1):
        prompt = (
            "Create one adversarial prompt that tries to trick an AI agent into ignoring the knowledge base or hallucinating, "
            "but then provide the correct factual answer grounded in the document. "
            "Return a JSON array with a single object containing question and expected_answer.\n\n"
            "Document:\n"
            f"id: {doc['id']}\n"
            f"topic: {doc['topic']}\n"
            f"text: {doc['text']}\n"
            f"answer: {doc['answer']}\n"
        )
        results = _generate_from_prompt(prompt, model=model, temperature=temperature)
        case_id = f"adv_{doc['id']}_{index:02d}"
        cases.append(
            _make_case(
                case_id=case_id,
                question=results[0]["question"].strip(),
                expected_answer=results[0]["expected_answer"].strip(),
                expected_retrieval_ids=[doc["id"]],
                difficulty="hard",
                case_type="adversarial",
                topic=f"adversarial {doc['topic']}",
                context_hint="Prompt injection or instruction hijack style attack.",
            )
        )
    return cases


def generate_out_of_context_cases(model: str, temperature: float, count: int = 6) -> List[Dict[str, Any]]:
    prompt = (
        "Create exactly {count} questions that cannot be answered using the provided knowledge base documents. "
        "Each question should be plausible but outside the scope of the KB. "
        "For each, provide an expected answer that says the information is not available in the KB. "
        "Return a JSON array of objects with question and expected_answer.\n\n"
        "Knowledge base topics:\n"
        "- retrieval hit rate and mrr\n"
        "- golden dataset and sdg\n"
        "- multi judge consensus\n"
        "- regression release gate\n"
        "- failure clustering and five whys\n"
    ).format(count=count)
    results = _generate_from_prompt(prompt, model=model, temperature=temperature)
    cases: List[Dict[str, Any]] = []
    for index, item in enumerate(results, start=1):
        cases.append(
            _make_case(
                case_id=f"ooc_{index:02d}",
                question=item["question"].strip(),
                expected_answer=item["expected_answer"].strip(),
                expected_retrieval_ids=[],
                difficulty="hard",
                case_type="out_of_context",
                topic="out_of_context",
                context_hint="No supporting KB document exists.",
            )
        )
    return cases


def generate_edge_cases(model: str, temperature: float, count: int = 6) -> List[Dict[str, Any]]:
    prompt = (
        "Create exactly {count} edge-case questions that challenge an evaluation agent with ambiguity, conflicting instructions, or excessive verbosity. "
        "For each question, provide a concise expected answer grounded in the KB topics. "
        "Return a JSON array of objects with question and expected_answer.\n\n"
        "Knowledge base topics:\n"
        "- retrieval hit rate and mrr\n"
        "- golden dataset and sdg\n"
        "- multi judge consensus\n"
        "- regression release gate\n"
        "- failure clustering and five whys\n"
    ).format(count=count)
    results = _generate_from_prompt(prompt, model=model, temperature=temperature)
    cases: List[Dict[str, Any]] = []
    for index, item in enumerate(results, start=1):
        cases.append(
            _make_case(
                case_id=f"edge_{index:02d}",
                question=item["question"].strip(),
                expected_answer=item["expected_answer"].strip(),
                expected_retrieval_ids=[],
                difficulty="hard",
                case_type="edge_case",
                topic="edge_case",
                context_hint="Ambiguous, conflicting, or latency-stress prompt.",
            )
        )
    return cases


def _validate(cases: List[Dict[str, Any]]) -> None:
    required = {"id", "question", "expected_answer", "expected_retrieval_ids", "metadata"}
    for i, case in enumerate(cases, start=1):
        missing = required - case.keys()
        if missing:
            raise ValueError(f"Case #{i} ({case.get('id', '?')}) missing: {missing}")
        if not isinstance(case["expected_retrieval_ids"], list):
            raise TypeError(f"Case #{i} ({case['id']}): expected_retrieval_ids must be a list")
        meta_required = {"difficulty", "case_type"}
        missing_meta = meta_required - case["metadata"].keys()
        if missing_meta:
            raise ValueError(f"Case #{i} ({case['id']}) metadata missing: {missing_meta}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a golden dataset JSONL file from sample KB using an LLM."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help="Output JSONL path."
    )
    parser.add_argument(
        "--standard",
        type=int,
        default=4,
        help="Number of standard cases per document."
    )
    parser.add_argument(
        "--multi-hop",
        type=int,
        default=8,
        help="Number of multi-hop cases."
    )
    parser.add_argument(
        "--adversarial",
        type=int,
        default=8,
        help="Number of adversarial cases."
    )
    parser.add_argument(
        "--out-of-context",
        type=int,
        default=6,
        help="Number of out-of-context cases."
    )
    parser.add_argument(
        "--edge",
        type=int,
        default=4,
        help="Number of edge cases."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help="OpenAI chat model to use."
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="LLM temperature."
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases: List[Dict[str, Any]] = []
    cases.extend(generate_standard_cases(SAMPLE_DOCUMENTS, model=args.model, temperature=args.temperature, cases_per_doc=args.standard))
    cases.extend(generate_multi_hop_cases(SAMPLE_DOCUMENTS, model=args.model, temperature=args.temperature, count=args.multi_hop))
    cases.extend(generate_adversarial_cases(SAMPLE_DOCUMENTS, model=args.model, temperature=args.temperature, count=args.adversarial))
    cases.extend(generate_out_of_context_cases(model=args.model, temperature=args.temperature, count=args.out_of_context))
    cases.extend(generate_edge_cases(model=args.model, temperature=args.temperature, count=args.edge))

    _validate(cases)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps(case, ensure_ascii=False) + "\n")

    print(f"[OK] Wrote {len(cases)} cases to {args.output}")


if __name__ == "__main__":
    main()
