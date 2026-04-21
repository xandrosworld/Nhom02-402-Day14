# Phân Công Nhóm - Day 14

## Vai trò nhóm

| Thành viên | Vai trò | Phạm vi chính |
|---|---|---|
| Mai Tấn Thành | Tech Lead / Integration Owner | Tích hợp pipeline, benchmark runner, release gate, merge cuối |
| Đặng Tùng Anh | Data Owner | Golden dataset, synthetic generation, hard cases |
| Hồ Nhất Khoa | Retrieval Eval Owner | Hit Rate, MRR, retrieval metrics |
| Nguyễn Đức Hoàng Phúc | Multi-Judge Owner | Multi-judge, agreement, cost/perf tracking |
| Phạm Lê Hoàng Nam | Analysis & Report Owner | Failure analysis, reflections, checklist nộp bài |

## Quy ước làm việc
1. Mai Tấn Thành chuẩn bị starter repo và giữ merge cuối.
2. Mỗi thành viên tạo một feature branch từ `main`.
3. Không sửa file owner của người khác nếu chưa báo trước.
4. Các artifact sinh ra chỉ commit trong lần final run của integration owner, trừ khi owner file đó cần commit để review logic.
5. Giữ ổn định các interface:
   `MainAgent.query()`
   `RetrievalEvaluator.score()`
   `LLMJudge.evaluate_multi_judge()`
6. Khi bàn giao, mỗi người phải nhắn rõ:
   file đã sửa
   file output đã tạo hoặc đã cập nhật
   phần nào trong repo cần mình pull về merge

## Gợi ý tên branch
- `mtt/integration-gate`
- `anh/golden-dataset`
- `khoa/retrieval-metrics`
- `phuc/multi-judge`
- `nam/failure-analysis`

## Phân công chi tiết theo file

### Mai Tấn Thành

**File chính được sửa**
- `main.py`
- `engine/runner.py`
- nếu cần: `agent/main_agent.py`

**Phải đảm bảo**
- Luồng benchmark chạy end-to-end bằng:
  `python data/synthetic_gen.py`
  `python main.py`
  `python check_lab.py`
- Có release / rollback decision trong `reports/summary.json`
- Final run tạo đủ 2 file:
  `reports/summary.json`
  `reports/benchmark_results.json`

**Bàn giao cuối**
- Code nằm trong:
  `main.py`
  `engine/runner.py`
- Artifact cuối nằm trong:
  `reports/summary.json`
  `reports/benchmark_results.json`

### Đặng Tùng Anh

**File chính được sửa**
- `data/synthetic_gen.py`
- nếu cần thêm tài liệu hỗ trợ hard cases:
  `data/HARD_CASES_GUIDE.md`

**Phải tạo / cập nhật**
- File dataset sinh ra:
  `data/golden_set.jsonl`

**Yêu cầu rõ**
- `data/golden_set.jsonl` phải có ít nhất 50 cases
- Mỗi case phải có:
  `id`
  `question`
  `expected_answer`
  `expected_retrieval_ids`
  `metadata`
- Trong `metadata` nên có tối thiểu:
  `difficulty`
  `case_type`
- Phải có một nhóm hard cases hoặc adversarial cases

**Bàn giao cuối**
- Logic sinh dataset nằm ở:
  `data/synthetic_gen.py`
- Output cần kiểm tra nằm ở:
  `data/golden_set.jsonl`

### Hồ Nhất Khoa

**File chính được sửa**
- `engine/retrieval_eval.py`

**Có thể cần phối hợp với**
- `main.py`
- `engine/runner.py`

**Phải tạo / cập nhật**
- Logic tính:
  `hit_rate`
  `mrr`
- Các field retrieval trong output benchmark:
  `reports/benchmark_results.json`
  `reports/summary.json`

**Yêu cầu rõ**
- Mỗi case trong `reports/benchmark_results.json` phải có block retrieval kiểu:
  `retrieval.hit_rate`
  `retrieval.mrr`
  `retrieval.expected_ids`
  `retrieval.retrieved_ids`
- `reports/summary.json` phải tổng hợp được:
  `metrics.hit_rate`
  `metrics.mrr`

**Bàn giao cuối**
- Code chính nằm ở:
  `engine/retrieval_eval.py`
- Kết quả phải nhìn thấy trong:
  `reports/benchmark_results.json`
  `reports/summary.json`

### Nguyễn Đức Hoàng Phúc

**File chính được sửa**
- `engine/llm_judge.py`

**Có thể cần phối hợp với**
- `main.py`
- `engine/runner.py`

**Phải tạo / cập nhật**
- Logic multi-judge tối thiểu 2 judge
- Agreement rate
- Theo dõi score delta
- Theo dõi cost / token / latency trong output cuối

**Yêu cầu rõ**
- Mỗi case trong `reports/benchmark_results.json` phải có block judge kiểu:
  `judge.final_score`
  `judge.agreement_rate`
  `judge.score_delta`
  `judge.individual_scores`
- `reports/summary.json` phải có tối thiểu:
  `metrics.avg_score`
  `metrics.agreement_rate`
  `metrics.total_tokens`
  `metrics.total_cost_usd`
  `metrics.avg_latency_ms`

**Bàn giao cuối**
- Code chính nằm ở:
  `engine/llm_judge.py`
- Kết quả phải nhìn thấy trong:
  `reports/benchmark_results.json`
  `reports/summary.json`

### Phạm Lê Hoàng Nam

**File chính được sửa**
- `analysis/failure_analysis.md`
- `analysis/reflections/README.md` nếu cần chỉnh guideline
- `analysis/reflections/reflection_template.md` nếu cần chỉnh mẫu

**Phải tạo / cập nhật**
- Báo cáo nhóm:
  `analysis/failure_analysis.md`
- Reflection của từng thành viên:
  `analysis/reflections/reflection_mai_tan_thanh.md`
  `analysis/reflections/reflection_dang_tung_anh.md`
  `analysis/reflections/reflection_ho_nhat_khoa.md`
  `analysis/reflections/reflection_nguyen_duc_hoang_phuc.md`
  `analysis/reflections/reflection_pham_le_hoang_nam.md`

**Yêu cầu rõ**
- `analysis/failure_analysis.md` phải có đủ:
  tổng quan benchmark
  phân nhóm lỗi
  5 Whys cho các case tệ nhất
  kế hoạch cải tiến
- Mỗi file reflection cá nhân phải đặt đúng tên:
  `reflection_<ten_khong_dau_va_cach_bang_gach_duoi>.md`
- Mỗi reflection phải có tối thiểu:
  vai trò
  file phụ trách
  tóm tắt đóng góp
  bài học kỹ thuật
  vấn đề gặp phải
  hướng cải thiện tiếp theo

**Bàn giao cuối**
- Báo cáo nhóm nằm ở:
  `analysis/failure_analysis.md`
- Reflection cá nhân nằm trong:
  `analysis/reflections/`

## Checklist trước khi merge vào main

### Tất cả thành viên
- [ ] Đã tạo branch riêng
- [ ] Chỉ sửa đúng file mình phụ trách hoặc đã báo owner trước
- [ ] Đã chạy phần liên quan của mình và kiểm tra không lỗi
- [ ] Đã nhắn rõ file nào mình đã sửa

### Mai Tấn Thành kiểm tra trước khi merge
- [ ] `data/golden_set.jsonl` sinh được
- [ ] `python main.py` chạy được
- [ ] `python check_lab.py` pass
- [ ] Có đủ:
  `reports/summary.json`
  `reports/benchmark_results.json`
  `analysis/failure_analysis.md`
- [ ] Có đủ reflection trong `analysis/reflections/`
