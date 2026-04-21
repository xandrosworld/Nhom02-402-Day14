# Reflection Cá Nhân - Phạm Lê Hoàng Nam

## Vai trò

Analysis & Report Owner

## Các file phụ trách

- `analysis/failure_analysis.md`
- `analysis/reflections/reflection_pham_le_hoang_nam.md`

## Tóm tắt đóng góp

- Chuẩn bị cấu trúc báo cáo `analysis/failure_analysis.md` và xác định các chỉ số chính cần điền.
- Tạo và mở rộng script `scripts/generate_failure_report.py` để tự động trích xuất số liệu benchmark từ `reports/*`, tính toán số lượng retrieval miss và judge disagreement, và xuất file markdown hỗ trợ điền `analysis/failure_analysis.md`.
- Kiểm tra dataset `data/golden_set.jsonl` về schema và xác nhận phần `expected_retrieval_ids`.
- Đọc và đánh giá logic tính toán metric trong `engine/runner.py`, `engine/retrieval_eval.py`, `engine/llm_judge.py`.
- Dùng `reports/summary.json` và `reports/benchmark_results.json` để chọn worst-case thực tế và hoàn thiện `analysis/failure_analysis.md`.
- Soạn khung phân tích 5 Whys và checklist cải tiến.
- Tạo script `data/generate_golden_dataset_llm.py` với CLI help và hướng dẫn sử dụng để sinh golden dataset tự động, bao gồm mapping ground truth retrieval IDs và các bộ red-team adversarial.

## Bài học kỹ thuật

- Hiểu rõ cách hệ thống tính toán: `hit_rate`, `mrr`, `final_score`, `agreement_rate` và phân loại `status`.
- Nhận diện được trade-off giữa chi phí và chất lượng: `total_tokens`, `estimated_cost_usd` và ảnh hưởng của hit rate lên điểm đánh giá.
- Nâng cao kỹ thuật đánh giá đồng thuận: hiện tại sử dụng `agreement_rate` với score delta, tương đương với một dạng đánh giá đáng tin cậy khi thiếu Cohen's Kappa thực thụ.
- Biết ý nghĩa của `Position Bias` trong retrieval: tài liệu đúng càng xuất hiện càng sớm thì MRR càng cao.
- Quy chuẩn hoá schema `reports/summary.json` giúp tự động hoá báo cáo và giảm sai sót trong bước nộp bài.

## Vấn đề gặp phải

- Khi tạo dataset bằng LLM, đầu ra JSON đôi khi không chuẩn, nên cần bổ sung bước kiểm tra và làm sạch để tránh lỗi parse.
- Thiếu tài liệu schema rõ ràng cho `reports/summary.json` và `reports/benchmark_results.json`, cần phải đọc `check_lab.py` và `main.py` để suy ra định dạng đúng.
- Logic `status` chỉ phân biệt `pass` / `fail` / `error`, nên khó xác định ngay đâu là lỗi retrieval, đâu là lỗi generation khi chưa có thêm metadata chi tiết.
- Cần một cách tái sử dụng và dễ chạy cho team, nên tôi đã thêm CLI help vào script dataset generation.

## Hướng cải thiện tiếp theo

- Xây dựng script tạo thẳng `analysis/failure_analysis.md` từ kết quả benchmark.
- Chuẩn hóa schema `reports/summary.json` và `reports/benchmark_results.json` để hỗ trợ tự động hóa tốt hơn.
- Mở rộng dataset và thêm kiểm tra chất lượng case trước khi benchmark.
- Thêm logic score threshold hoặc weight cho judge nếu `score_delta` lớn, tương tự cách khai thác Cohen's Kappa để xử lý xung đột.
