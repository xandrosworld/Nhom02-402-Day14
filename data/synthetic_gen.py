import json
from pathlib import Path
from typing import Dict, List

from sample_kb import SAMPLE_DOCUMENTS

OUTPUT_PATH = Path(__file__).resolve().parent / "golden_set.jsonl"

QUESTION_TEMPLATES = [
    "What does the policy say about {topic}?",
    "Summarize the rule for {topic}.",
    "What is the recommended action for {topic}?",
    "Explain the benchmark expectation around {topic}.",
    "What should the team measure for {topic}?",
    "Give the most important requirement for {topic}.",
    "If the team is struggling with {topic}, what should they check first?",
    "What evidence should appear in the report for {topic}?",
    "What can cause failure in {topic} if the team skips it?",
    "State the practical guideline for {topic}.",
]


def generate_cases() -> List[Dict]:
    cases: List[Dict] = []
    for doc in SAMPLE_DOCUMENTS:
        for index, template in enumerate(QUESTION_TEMPLATES, start=1):
            difficulty = "hard" if index in {7, 8, 9} else "medium"
            case = {
                "id": f"{doc['id']}_{index:02d}",
                "question": template.format(topic=doc["topic"]),
                "expected_answer": doc["answer"],
                "context": doc["text"],
                "expected_retrieval_ids": [doc["id"]],
                "metadata": {
                    "topic": doc["topic"],
                    "difficulty": difficulty,
                    "case_type": "starter_sdg",
                },
            }
            cases.append(case)
    return cases


def main() -> None:
    cases = generate_cases()
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        for case in cases:
            handle.write(json.dumps(case, ensure_ascii=False) + "\n")

    print(f"Wrote {len(cases)} cases to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
