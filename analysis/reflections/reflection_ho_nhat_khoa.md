# Reflection Cá Nhân - Hồ Nhất Khoa

## Vai trò

Retrieval Eval Owner — phụ trách module đánh giá chất lượng retrieval trong pipeline benchmark.

## Các file phụ trách

- `engine/retrieval_eval.py`

## Tóm tắt đóng góp

Triển khai 6 metric đánh giá trong `RetrievalEvaluator`, bao gồm 2 metric cốt lõi theo rubric và 4 metric theo chuẩn RAGAS:

- **Hit Rate@K** (K=3): kiểm tra tài liệu đúng có xuất hiện trong top-K retrieved không
- **MRR (Mean Reciprocal Rank)**: đo vị trí trung bình của tài liệu đúng đầu tiên
- **Context Precision** (RAGAS): precision có trọng số theo vị trí — tài liệu đúng ở vị trí cao được điểm nhiều hơn
- **Context Recall** (RAGAS, simplified): tỷ lệ token trong expected_answer xuất hiện trong context retrieved
- **Faithfulness** (RAGAS, simplified): tỷ lệ token trong answer được context hỗ trợ — đo mức độ grounded
- **Answer Relevancy** (RAGAS, simplified): token overlap giữa question và answer — proxy của mức độ liên quan

4 field gốc mà `runner.py` đọc (`hit_rate`, `mrr`, `expected_ids`, `retrieved_ids`) được giữ nguyên. 4 RAGAS field là bonus, bỏ qua an toàn bởi runner.

## Bài học kỹ thuật

### Hit Rate

Hit Rate = 1 nếu ít nhất một tài liệu đúng xuất hiện trong top-K retrieved, ngược lại = 0. Metric nhị phân — trả lời "có tìm được hay không" nhưng không phân biệt tài liệu đúng ở vị trí 1 hay vị trí 3.

K=3 vì agent trả về top-3 documents. Tăng K không thay đổi giá trị khi tập retrieved cố định ở 3 phần tử.

### MRR (Mean Reciprocal Rank)

`MRR = (1/|Q|) × Σ(1/rank_i)` — trung bình nghịch đảo vị trí của tài liệu đúng đầu tiên.

- MRR = 1.0: tài liệu đúng luôn ở vị trí 1
- MRR = 0.5: tài liệu đúng trung bình ở vị trí 2
- MRR = 0.0: không tìm thấy tài liệu đúng

MRR bổ sung cho Hit Rate: hai hệ thống cùng Hit Rate = 1.0 nhưng một hệ thống trả về tài liệu đúng ở vị trí 1 (MRR = 1.0), hệ thống kia ở vị trí 3 (MRR = 0.33) — rõ ràng hệ thống đầu tốt hơn.

### Context Precision (RAGAS — position-weighted)

Bài giảng định nghĩa: `CP = (1/K) × Σ_{k=1}^{K} [Precision@k × rel_k]`

Đây là **Average Precision (AP)** trong Information Retrieval — tài liệu đúng ở vị trí cao được điểm nhiều hơn. Với 1 expected doc:

| Vị trí tài liệu đúng | Simple Precision | Context Precision |
|---|---|---|
| Vị trí 1 | 0.33 | 1.0 |
| Vị trí 2 | 0.33 | 0.5 |
| Vị trí 3 | 0.33 | 0.33 |

Simple precision không phân biệt vị trí — Context Precision phản ánh thực tế rằng LLM xử lý tốt hơn khi tài liệu liên quan ở đầu context window (Position Bias).

### Context Recall, Faithfulness, Answer Relevancy (RAGAS simplified)

RAGAS thực sự dùng LLM để extract claims và tính semantic similarity. Trong pipeline này, token overlap được dùng làm proxy khi không muốn tốn thêm API cost cho bước evaluation:

- **Context Recall**: `len(expected_tokens ∩ context_tokens) / len(expected_tokens)` — câu trả lời đúng có keyword trong context không?
- **Faithfulness**: `len(answer_tokens ∩ context_tokens) / len(answer_tokens)` — agent có trả lời bằng thông tin từ context không, hay hallucinate?
- **Answer Relevancy**: `len(q_tokens ∩ a_tokens) / len(q_tokens)` — answer có đề cập đến các keyword trong question không?

Những metric này là **simplified proxies** — không thay thế RAGAS thật nhưng cung cấp tín hiệu hữu ích với chi phí $0.

### Mối liên hệ Retrieval Quality ↔ Answer Quality

Pipeline: `Question → Retriever → Context → Generator → Answer`

- **Context Recall thấp** → retriever bỏ sót evidence → generator thiếu thông tin → answer sai dù LLM tốt đến đâu
- **Context Precision thấp** → context nhiều nhiễu → tăng nguy cơ hallucination (Faithfulness thấp)
- **Hit Rate = 0** → Faithfulness gần như chắc chắn thấp vì agent không có nguyên liệu để trả lời đúng

Quan sát từ benchmark thực tế: hit_rate = 0.92, mrr = 0.92 — 8% cases agent không retrieve đúng tài liệu. Những cases đó tương quan với judge_score thấp hơn, xác nhận retrieval là bottleneck chính.

### Cohen's Kappa (liên quan multi-judge)

`κ = (P_o - P_e) / (1 - P_e)` — đo đồng thuận giữa các judge vượt qua ngưỡng ngẫu nhiên.

κ > 0.6 là "substantial agreement" — đủ tin tưởng vào final_score từ multi-judge. Nếu không tính Kappa mà chỉ dùng agreement_rate, có thể bị mislead khi hai judge tình cờ đồng ý (P_e cao).

### Trade-off chi phí vs chất lượng

Dùng token overlap thay LLM để tính RAGAS metrics: tiết kiệm ~4 API calls/case × 66 cases = ~264 calls ≈ $1-3. Với benchmark chạy nhiều lần mỗi ngày, đây là quyết định có cân nhắc. Khi cần độ chính xác cao (trước release quan trọng), nên dùng RAGAS library thật.

## Vấn đề gặp phải

**Backward compatibility:** `runner.py:_normalize_retrieval()` đọc đúng 4 key cố định bằng `.get()`. Phải đọc source để xác nhận extra keys được bỏ qua an toàn — runner không iterate qua toàn bộ dict.

**Thay đổi signature `calculate_context_recall`:** Chuyển từ ID-based (`expected_ids`, `retrieved_ids`) sang text-based (`expected_answer`, `contexts`). Không ảnh hưởng vì method chỉ được gọi bên trong `score()`, không có external caller.

**Phân biệt RAGAS thật vs simplified:** Answer Relevancy dùng token overlap là proxy rất thô — RAGAS thật generate reverse questions qua LLM và dùng embedding cosine similarity. Điều này được ghi rõ trong comment code để không gây hiểu nhầm.

## Hướng cải thiện tiếp theo

- **RAGAS library thật**: tích hợp `ragas` package (đã có trong requirements.txt) khi có API key để có kết quả chính xác hơn
- **Spearman correlation**: tính tương quan giữa MRR và judge_final_score trên 66 cases — định lượng mức độ retrieval quality ảnh hưởng answer quality
- **NDCG@K**: metric ranking tổng quát hơn, hỗ trợ graded relevance thay vì binary
