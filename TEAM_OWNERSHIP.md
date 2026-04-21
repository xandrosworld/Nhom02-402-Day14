# Team Ownership - Day 14

## Team roles

| Member | Role | Main ownership |
|---|---|---|
| Mai Tan Thanh | Tech Lead / Eval Integration Owner | `main.py`, `engine/runner.py`, release gate, final merge |
| Dang Tung Anh | Data Owner | `data/synthetic_gen.py`, golden dataset quality, hard cases |
| Ho Nhat Khoa | Retrieval Eval Owner | `engine/retrieval_eval.py`, retrieval metrics, retrieval evidence |
| Nguyen Duc Hoang Phuc | Multi-Judge Owner | `engine/llm_judge.py`, agreement calibration, benchmark cost/perf |
| Pham Le Hoang Nam | Analysis & Report Owner | `analysis/failure_analysis.md`, reflections checklist, final report assembly |

## Working rules
1. Mai Tan Thanh prepares the starter repo and does the final merge.
2. Each member creates one feature branch from `main`.
3. Do not edit someone else's owned file without telling the owner first.
4. Commit generated artifacts only in the final run by the integration owner.
5. Keep interfaces stable: `MainAgent.query()`, `RetrievalEvaluator.score()`, `LLMJudge.evaluate_multi_judge()`.

## Suggested branches
- `mtt/integration-gate`
- `anh/golden-dataset`
- `khoa/retrieval-metrics`
- `phuc/multi-judge`
- `nam/failure-analysis`

## Expected handoff

### Mai Tan Thanh
- main benchmark flow runs end-to-end
- reports are generated in `reports/`
- release / rollback decision is visible in `summary.json`

### Dang Tung Anh
- `golden_set.jsonl` can be generated with 50+ cases
- each case has `expected_retrieval_ids`
- hard cases are included

### Ho Nhat Khoa
- hit rate and MRR are correct
- retrieval evidence can explain top-k misses

### Nguyen Duc Hoang Phuc
- at least two judges are wired
- agreement logic is visible in output
- latency, token, and cost fields are tracked

### Pham Le Hoang Nam
- `analysis/failure_analysis.md` is completed
- reflections are collected in `analysis/reflections/`
- final submission checklist is reviewed
