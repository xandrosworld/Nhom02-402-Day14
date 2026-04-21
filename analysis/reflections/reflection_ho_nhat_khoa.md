# Reflection Cá Nhân - Hồ Nhất Khoa

## Vai trò

Retrieval Eval Owner — phụ trách module đánh giá chất lượng retrieval trong pipeline benchmark.

## Các file phụ trách

- `engine/retrieval_eval.py`

## Tóm tắt đóng góp

Triển khai 6 metric đánh giá trong `RetrievalEvaluator` — 2 metric cốt lõi theo rubric và 4 metric theo chuẩn RAGAS đầy đủ:

- **Hit Rate@K** (K=3): kiểm tra tài liệu đúng có xuất hiện trong top-K retrieved không
- **MRR (Mean Reciprocal Rank)**: đo vị trí trung bình của tài liệu đúng đầu tiên
- **Context Precision** (RAGAS): precision có trọng số theo vị trí — tài liệu đúng ở vị trí cao được điểm nhiều hơn (Average Precision)
- **Context Recall** (RAGAS, simplified): token overlap giữa expected_answer và retrieved contexts
- **Faithfulness** (RAGAS, simplified): tỷ lệ token trong answer được context hỗ trợ
- **Answer Relevancy** (RAGAS, full): sinh reverse questions qua LLM, tính cosine similarity với Voyage embeddings

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

### Context Recall và Faithfulness (RAGAS simplified)

Token overlap được dùng làm proxy — đủ tín hiệu mà không cần thêm API call:

- **Context Recall**: `len(expected_tokens ∩ context_tokens) / len(expected_tokens)` — keyword trong expected answer có trong retrieved context không?
- **Faithfulness**: `len(answer_tokens ∩ context_tokens) / len(answer_tokens)` — agent trả lời bằng thông tin từ context không?

Lưu ý: Faithfulness có xu hướng cao trong RAG vì agent được thiết kế để dùng ngôn ngữ từ context — metric này không detect được hallucination ở mức claim, chỉ đo token-level overlap.

### Answer Relevancy (RAGAS đầy đủ — LLM + Embeddings)

Đây là metric duy nhất implement đúng theo đặc tả RAGAS gốc, không dùng proxy:

**Thuật toán:**
1. Gọi OpenAI Responses API để sinh n câu hỏi ngược từ answer
2. Dùng Voyage AI embed [câu hỏi gốc] + [n câu hỏi ngược] → vector
3. Tính cosine similarity giữa embedding câu hỏi gốc và từng câu hỏi ngược
4. Score = trung bình similarity

**Kết quả thực tế:**
- Câu trả lời đúng chủ đề → Answer Relevancy ≈ 0.89
- Câu trả lời lạc đề → Answer Relevancy ≈ 0.41

Sự phân biệt rõ ràng chứng minh metric hoạt động đúng hướng.

**Tại sao không dùng token overlap cho metric này:** Token overlap giữa question và answer cho kết quả ngược — LLM thường diễn giải bằng từ ngữ khác câu hỏi nên câu trả lời đúng lại có overlap thấp. Reverse question generation giải quyết đúng bài toán: nếu answer đúng chủ đề, câu hỏi ngược sẽ tương tự câu hỏi gốc trong embedding space.

### Mối liên hệ Retrieval Quality ↔ Answer Quality

Pipeline: `Question → Retriever → Context → Generator → Answer`

- **Context Recall thấp** → retriever bỏ sót evidence → generator thiếu thông tin → answer sai dù LLM tốt đến đâu
- **Context Precision thấp** → context nhiều nhiễu → tăng nguy cơ hallucination
- **Hit Rate = 0** → Faithfulness gần như chắc chắn thấp vì agent không có nguyên liệu để trả lời đúng

Quan sát từ benchmark thực tế: hit_rate = 0.92, mrr = 0.92 — 8% cases agent không retrieve đúng tài liệu. Những cases đó tương quan với judge_score thấp hơn, xác nhận retrieval là bottleneck chính.

### Cohen's Kappa (liên quan multi-judge)

`κ = (P_o - P_e) / (1 - P_e)` — đo đồng thuận giữa các judge vượt qua ngưỡng ngẫu nhiên.

κ > 0.6 là "substantial agreement" — đủ tin tưởng vào final_score từ multi-judge. Nếu không tính Kappa mà chỉ dùng agreement_rate, có thể bị mislead khi hai judge tình cờ đồng ý (P_e cao).

### Trade-off chi phí vs chất lượng

Answer Relevancy thêm 2 API call/case (OpenAI + Voyage). Với 66 cases × 2 versions = 264 call thêm. Quyết định dùng API thật vì accuracy quan trọng hơn chi phí — token overlap cho kết quả sai hướng nên không thể dùng làm proxy.

### Blocking IO trong async context

`urllib_request.urlopen` và `openai.responses.create` là synchronous calls. Nếu gọi thẳng trong async function, chúng block event loop và vô hiệu hóa `asyncio.gather()` trong runner — các case không chạy song song thực sự.

Giải pháp: `asyncio.to_thread()` đẩy blocking call ra thread pool, trả event loop về cho coroutine khác. Đây là pattern chuẩn khi tích hợp sync library vào async pipeline.

## Vấn đề gặp phải

**Backward compatibility:** `runner.py:_normalize_retrieval()` đọc đúng 4 key cố định bằng `.get()`. Phải đọc source để xác nhận extra keys được bỏ qua an toàn.

**Thay đổi signature `calculate_context_recall`:** Chuyển từ ID-based sang text-based. Không ảnh hưởng vì method chỉ được gọi bên trong `score()`.

**Async/sync mismatch:** `_generate_reverse_questions` ban đầu khai báo `async def` nhưng không có `await` bên trong — sai về ngữ nghĩa. Đã sửa thành `def` và dùng `asyncio.to_thread()` ở caller để xử lý đúng blocking IO.

**Pipeline chậm:** Khi thêm 2 API call/case mà không có `asyncio.to_thread()`, blocking IO chặn event loop khiến 66 cases chạy tuần tự thay vì song song. Sau khi fix, pipeline trở về tốc độ bình thường.

## Hướng cải thiện tiếp theo

- **RAGAS library thật** (`ragas` đã có trong requirements.txt): tích hợp để có Context Recall và Faithfulness chính xác theo LLM claim extraction
- **Spearman correlation**: tính tương quan giữa MRR và judge_final_score trên 66 cases
- **NDCG@K**: metric ranking tổng quát hơn, hỗ trợ graded relevance thay vì binary
