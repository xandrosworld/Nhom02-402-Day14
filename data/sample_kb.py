SAMPLE_DOCUMENTS = [
    {
        "id": "kb_retrieval_metrics",
        "title": "Retrieval Quality Metrics",
        "topic": "retrieval hit rate and mrr",
        "keywords": ["retrieval", "hit", "rate", "mrr", "ranking", "documents"],
        "answer": (
            "Teams should measure retrieval quality with Hit Rate and Mean Reciprocal Rank. "
            "These metrics show whether the right document was found and how early it appeared."
        ),
        "text": (
            "Retrieval quality must be validated before judging generation. "
            "Use Hit Rate to check whether at least one ground-truth document appears in the top-k list. "
            "Use Mean Reciprocal Rank to reward systems that surface the correct document earlier in the ranking."
        ),
    },
    {
        "id": "kb_golden_dataset",
        "title": "Golden Dataset Design",
        "topic": "golden dataset and sdg",
        "keywords": ["golden", "dataset", "sdg", "cases", "ground", "truth"],
        "answer": (
            "The golden dataset should contain at least 50 high-quality test cases with ground-truth retrieval IDs. "
            "At least a few hard or adversarial questions should be included."
        ),
        "text": (
            "Synthetic data generation should create a benchmark set with at least 50 cases. "
            "Every case should map to the correct supporting document IDs so retrieval can be scored. "
            "A strong dataset also includes red-team style prompts that stress failure modes."
        ),
    },
    {
        "id": "kb_multi_judge",
        "title": "Multi Judge Consensus",
        "topic": "multi judge consensus",
        "keywords": ["judge", "consensus", "agreement", "calibration", "models"],
        "answer": (
            "The evaluation system should use at least two judge models and track agreement rate. "
            "When scores disagree sharply, the pipeline should flag the conflict or apply a tie-break rule."
        ),
        "text": (
            "A single judge can be unreliable in production evaluation. "
            "Use at least two independent judge models, compare their scores, and compute an agreement metric. "
            "Large disagreement should trigger calibration logic instead of silently averaging everything."
        ),
    },
    {
        "id": "kb_regression_gate",
        "title": "Regression Release Gate",
        "topic": "regression release gate",
        "keywords": ["regression", "release", "gate", "rollback", "delta", "version"],
        "answer": (
            "Teams should compare the candidate agent against a baseline and compute deltas for quality, cost, and latency. "
            "The release gate should output a clear release or rollback decision."
        ),
        "text": (
            "Regression analysis compares Agent V2 with Agent V1 across quality, performance, and cost. "
            "A practical release gate should automatically say release or rollback when thresholds are crossed."
        ),
    },
    {
        "id": "kb_failure_analysis",
        "title": "Failure Analysis and Five Whys",
        "topic": "failure clustering and five whys",
        "keywords": ["failure", "cluster", "five", "whys", "root", "cause"],
        "answer": (
            "Benchmarking should end with failure clustering and a Five Whys analysis on the worst cases. "
            "The report should identify whether the root cause comes from ingestion, chunking, retrieval, or prompting."
        ),
        "text": (
            "The benchmark report should not stop at scores. "
            "Teams should cluster failures, pick the worst cases, and run a Five Whys analysis to isolate the real system bottleneck."
        ),
    },
]
