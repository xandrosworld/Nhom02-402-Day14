# Phân Công Nhóm - Day 14

## Vai trò nhóm

| Thành viên | Vai trò | Phạm vi chính |
|---|---|---|
| Mai Tan Thanh | Tech Lead / Integration Owner | `main.py`, `engine/runner.py`, release gate, merge cuối |
| Dang Tung Anh | Data Owner | `data/synthetic_gen.py`, chất lượng golden dataset, hard cases |
| Ho Nhat Khoa | Retrieval Eval Owner | `engine/retrieval_eval.py`, retrieval metrics, retrieval evidence |
| Nguyen Duc Hoang Phuc | Multi-Judge Owner | `engine/llm_judge.py`, agreement calibration, cost/perf benchmark |
| Pham Le Hoang Nam | Analysis & Report Owner | `analysis/failure_analysis.md`, checklist reflection, tổng hợp báo cáo cuối |

## Quy ước làm việc
1. Mai Tan Thanh chuẩn bị starter repo và giữ merge cuối.
2. Mỗi thành viên tạo một feature branch từ `main`.
3. Không sửa file owner của người khác nếu chưa báo trước.
4. Các artifact sinh ra chỉ commit trong lần final run của integration owner.
5. Giữ ổn định interface: `MainAgent.query()`, `RetrievalEvaluator.score()`, `LLMJudge.evaluate_multi_judge()`.

## Gợi ý tên branch
- `mtt/integration-gate`
- `anh/golden-dataset`
- `khoa/retrieval-metrics`
- `phuc/multi-judge`
- `nam/failure-analysis`

## Bàn giao mong đợi

### Mai Tan Thanh
- Luồng benchmark chạy end-to-end
- Report được tạo trong `reports/`
- Quyết định release / rollback hiện trong `summary.json`

### Dang Tung Anh
- `golden_set.jsonl` tạo được 50+ cases
- Mỗi case có `expected_retrieval_ids`
- Có các hard case

### Ho Nhat Khoa
- Hit Rate và MRR tính đúng
- Có evidence giải thích các top-k miss

### Nguyen Duc Hoang Phuc
- Có ít nhất hai judge được nối vào pipeline
- Logic agreement hiện rõ trong output
- Có theo dõi latency, token, và cost

### Pham Le Hoang Nam
- `analysis/failure_analysis.md` được điền đầy đủ
- Các file reflection được gom trong `analysis/reflections/`
- Checklist nộp bài cuối được review
