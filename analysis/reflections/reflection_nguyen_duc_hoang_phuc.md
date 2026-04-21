# Reflection Cá Nhân - Nguyễn Đức Hoàng Phúc

## Vai trò
Trong bài lab Day 14, tôi phụ trách phần **multi-judge evaluation**, bao gồm:
- Thiết kế và triển khai hệ thống **LLM-as-Judge với nhiều model**
- Tính toán **agreement rate** giữa các judge
- Theo dõi **chi phí (cost)** và **hiệu năng (latency, token usage)** của hệ thống đánh giá

---

## Các file phụ trách
- `engine/llm_judge.py`: Triển khai hệ thống multi-judge (OpenAI + Gemini), bao gồm:
  - Gọi API thật từ LLM
  - Xử lý timeout và fallback khi lỗi
  - Tính toán agreement rate và final score
- (liên quan) `engine/runner.py`: Điều chỉnh để hỗ trợ chạy song song (batch parallel) nhằm tăng tốc độ đánh giá

---

## Tóm tắt đóng góp
Tôi đã nâng cấp hệ thống đánh giá từ **rule-based** sang **LLM-based multi-judge**, cụ thể:
- Thay thế scoring đơn giản (token overlap) bằng **2 LLM judges thực (OpenAI + Gemini)**
- Xây dựng cơ chế:
  - **agreement_rate** để đo độ đồng thuận giữa các model
  - **score_delta** để phát hiện conflict
- Triển khai **fallback mechanism** để hệ thống không bị crash khi API lỗi
- Thêm **timeout** để tránh tình trạng treo khi gọi API
- Tối ưu hiệu năng bằng cách:
  - Chạy batch song song (parallel batching)
  - Giảm thời gian chạy xuống ~5–10 lần so với trước

---

## Bài học kỹ thuật
- Hiểu rõ rằng **async không đảm bảo song song** nếu bên trong là blocking call (API sync)
- Multi-judge giúp:
  - Giảm bias của từng model riêng lẻ
  - Tăng độ tin cậy của evaluation
- Agreement rate là một metric quan trọng để:
  - Phát hiện câu trả lời “mơ hồ”
  - Đánh giá độ ổn định của hệ thống
- Khi chuyển từ mock → LLM thật:
  - Score giảm (thực tế hơn)
  - Agreement giảm (do model khác nhau)
  - Cost và latency tăng (trade-off thực tế)
- Hệ thống production cần:
  - Timeout
  - Error handling
  - Cost tracking

---

## Vấn đề gặp phải
- Hệ thống ban đầu bị **treo lâu** do:
  - Gọi LLM blocking trong async pipeline
  - Gemini API có thể bị delay hoặc treo
- Không thấy log khi chạy → khó debug
- LLM trả output không đúng format (ví dụ: "Score: 4") gây lỗi parse
- Thời gian chạy lâu khi dùng multi-judge (do số lượng API call tăng gấp đôi)

---

## Hướng cải thiện tiếp theo
- Chuyển sang **async HTTP client thực sự (httpx)** để tận dụng parallelism tốt hơn
- Thêm **caching** để tránh gọi lại LLM cho các câu hỏi giống nhau
- Sử dụng **LLM judge có reasoning output** để giải thích vì sao chấm điểm
- Thêm judge thứ 3 (nếu có tài nguyên) để tăng độ tin cậy
- Tối ưu cost bằng:
  - batching prompt
  - giảm token
- Xây dựng dashboard monitoring:
  - latency
  - cost
  - agreement distribution