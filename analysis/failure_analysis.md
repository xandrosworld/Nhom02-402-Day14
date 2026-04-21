# Failure Analysis Report - Day 14

## 1. Benchmark Snapshot
- Total cases: 50
- Pass rate: Fill after `python main.py`
- Average judge score: Fill after run
- Retrieval hit rate / MRR: Fill after run
- Agreement rate: Fill after run

## 2. Failure Clusters
| Cluster | Count | Symptom | Suspected layer |
|---|---:|---|---|
| Retrieval miss | 0 | Correct source not retrieved in top-k | Retrieval |
| Partial answer | 0 | Answer is grounded but incomplete | Prompting / synthesis |
| Judge conflict | 0 | Two judge models disagree strongly | Evaluation |
| Slow case | 0 | Latency outlier | Runner / agent |

## 3. Five Whys

### Case A - Worst retrieval miss
1. Symptom:
2. Why 1:
3. Why 2:
4. Why 3:
5. Why 4:
6. Root cause:

### Case B - Worst hallucination or partial answer
1. Symptom:
2. Why 1:
3. Why 2:
4. Why 3:
5. Why 4:
6. Root cause:

### Case C - Worst judge disagreement
1. Symptom:
2. Why 1:
3. Why 2:
4. Why 3:
5. Why 4:
6. Root cause:

## 4. Improvement Plan
- [ ] Tune retrieval or reranking
- [ ] Improve prompt and answer structure
- [ ] Calibrate multi-judge tie-break logic
- [ ] Re-run benchmark and compare deltas
