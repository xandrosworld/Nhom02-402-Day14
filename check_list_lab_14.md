## Checklist Lab14 — Các Bước Cần Làm theo hướng dẫn của giáo viên

**Mục tiêu cuối cùng**: Xây dựng hệ thống Benchmark để chứng minh Version 2 tốt hơn Version 1.

---

## PHASE 1 — DATASET (Quan trọng nhất)

### Bước 1: Chuẩn bị source data
* Cần có document gốc.
* Cần có knowledge base.
* Cần có vector DB (nếu đã có).
* Cần có chunk text.
* Cần có chunk ID.
* Nếu đã có vector DB: tiến hành export chunk ra luôn.

### Bước 2: Chunk dữ liệu
* Mỗi đoạn phải có chunk_id.
* Mỗi đoạn phải có chunk_text.
* Mỗi đoạn phải có source_document.
* Ví dụ minh họa: chunk_001 → nội dung văn bản → file policy.pdf.

### Bước 3: Thiết kế prompt tạo dataset
* Prompt phải yêu cầu rõ generate question.
* Prompt phải yêu cầu rõ expected answer.
* Prompt phải yêu cầu rõ correct chunk ID.
* Prompt phải yêu cầu rõ difficulty.
* Prompt phải yêu cầu rõ category.
* Prompt phải yêu cầu rõ metadata đầy đủ.
* Phải cung cấp Good Example và Hard Case Example để LLM học theo.

### Bước 4: Dùng LLM tạo Golden Dataset
* Tạo khoảng 30–50 câu hỏi chuẩn.
* Bao gồm mức độ easy.
* Bao gồm mức độ medium.
* Bao gồm mức độ hard.
* Bao gồm multi-hop reasoning.
* Bao gồm các trường hợp retrieval dễ sai.
* Bao gồm các trường hợp hallucination dễ xảy ra.

### Bước 5: Manual Review Dataset
* Phải kiểm tra câu hỏi đúng chưa.
* Phải kiểm tra answer đúng chưa.
* Phải kiểm tra chunk ID đúng chưa.
* Phải kiểm tra source đúng chưa.
* Đây là bước bắt buộc vì LLM có thể tạo sai.

---

## PHASE 2 — AGENT VERSION

### Bước 6: Tạo Version 1
* Ví dụ: Version 1 có retrieval yếu hơn.
* Ví dụ: Version 1 có logic cũ hơn.
* Ví dụ: Version 1 có prompt chưa tối ưu.

### Bước 7: Tạo Version 2
* Ví dụ: Version 2 có retrieval tốt hơn.
* Ví dụ: Version 2 có reranking tốt hơn.
* Ví dụ: Version 2 có prompt tốt hơn.
* Ví dụ: Version 2 cho final answer tốt hơn.
* Mục tiêu: V2 > V1.

---

## PHASE 3 — TRUST / JUDGE

### Bước 8: Tạo LLM Judge
* Dùng LLM để đánh giá output đúng hay sai.
* Đánh giá partial correct.
* Đánh giá hallucination.
* Đánh giá bias.
* Đánh giá fairness.
* Đánh giá consistency.
* Ví dụ workflow: Question → Expected Answer → System Output → Judge Result.

### Bước 9: Verify lại Judge
* Vì Judge LLM cũng có thể sai nên phải manual spot check để tránh đánh giá sai.

---

## PHASE 4 — BENCHMARK

### Bước 10: Chạy benchmark cho V1
* Chạy toàn bộ dataset với Agent Version 1 và lưu kết quả.

### Bước 11: Chạy benchmark cho V2
* Chạy cùng dataset với Agent Version 2 để so sánh công bằng.

### Bước 12: Tính metric
* Metric tính toán: Retrieval Accuracy.
* Metric tính toán: Hit Rate.
* Metric tính toán: Average Hit Rate.
* Metric tính toán: Final Answer Accuracy.
* Metric tính toán: Hallucination Rate.
* Metric tính toán: Average Score.
* Metric tính toán: Latency.
* Metric tính toán: Cost.
* Metric tính toán: User Satisfaction Score.

---

## PHASE 5 — ANALYSIS

### Bước 13: Phân tích nguyên nhân
* Không chỉ ghi V2 tốt hơn mà phải giải thích rõ ràng: Tại sao tốt hơn, Tốt ở đâu, và Rủi ro còn gì.
* Ví dụ kết quả: retrieval improved.
* Ví dụ kết quả: hallucination giảm.
* Ví dụ kết quả: latency tăng nhẹ.
* Ví dụ kết quả: cost tăng nhưng acceptable.

---

## PHASE 6 — REPORT

### Bước 14: Làm Final Report
* Báo cáo bao gồm Executive Summary.
* Báo cáo bao gồm Benchmark Comparison.
* Báo cáo bao gồm Metric Table.
* Báo cáo bao gồm Trust Analysis.
* Báo cáo bao gồm Risk Analysis.
* Báo cáo bao gồm Recommendation.
* Báo cáo bao gồm Next Action.

---

## FINAL DELIVERABLE
Không phải chỉ là code mà hệ thống cần bàn giao bao gồm các thành phần sau:
* Dataset.
* Agent V1.
* Agent V2.
* LLM Judge.
* Benchmark Result.
* Final Report.