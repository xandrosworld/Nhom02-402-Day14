# Reflection Cá Nhân - Đặng Tùng Anh

## Vai trò
Data Owner - Phụ trách xây dựng Golden Dataset & chạy SDG script (Synthetic Data Generation) dùng LLM.

## Các file phụ trách
- `data/golden_set.jsonl`
- `data/manual_review_report.md`
- `data/source_docs/` (chuyển đổi từ dữ liệu Lab 8)
- Script gọi LLM sinh dữ liệu.

## Tóm tắt đóng góp
- Thay vì sử dụng văn bản mẫu đơn giản, em đã lấy **thực tế 5 tài liệu nội bộ (HR Policy, IT Helpdesk, v.v...) từ folder của Lab 08** làm Knowledge Base (Source Data) để bộ Dataset có độ khó và tính thực tiễn sát với bài toán doanh nghiệp.
- Ứng dụng LLM với Few-shot Prompting để sinh tự động ra bộ **56 test cases** đa dạng theo đúng yêu cầu từ Checklist Lab 14, bao gồm: Standard, Multi-hop, Adversarial (Prompt Injection / Goal Hijacking), Out-of-context và Edge Case.
- **Tiến hành Manual Review khắt khe**: Sau khi LLM sinh ra JSON, em đã review bằng mắt từng câu một. Bản thân em đã chủ động phát hiện và gọt giũa lại các câu `expected_answer` bị LLM sinh thừa chữ (lỗi Hallucination nhẹ) để đảm bảo ngắn gọn, đúng keyword (Hit Rate, MRR, v.v..), tránh việc LLM Judge chấm oan cho Agent ở phase sau.
- Rà soát chuẩn hóa lại toàn bộ `chunk_id` (`expected_retrieval_ids`) của hệ thống sao cho map 1-1 với Vector DB (Chroma) được xây từ đợt Lab 8.

## Bài học kỹ thuật
- **Kiểm soát Hallucination của LLM trong Data Pipeline:** Kể cả khi LLM đóng vai Data Generator, nó vẫn có thể tóm tắt dông dài hoặc nhầm file đối với các câu Multi-hop. Kinh nghiệm xương máu là luôn phải có bước *Manual Review* (kiểm tra chéo bằng mắt) chứ không thể dựa 100% vào AI.
- **Tầm quan trọng của Ground Truth:** Việc thiết kế ra được 1 bộ `expected_answer` tinh gọn (chỉ bám Keyword chính) khó hơn việc bắt LLM copy lại đoạn văn bản. Nếu đáp án kỳ vọng quá rườm rà, module Generation Relevancy (của Phúc) sẽ bị mâu thuẫn điểm số.

## Vấn đề gặp phải
- Cấu trúc file JSONL của Lab 14 bắt buộc trường ID phải khớp hoàn toàn với IDs trong Vector DB Lab 8. Việc truy xuất ngược lại từ Sqlite của ChromaDB vấp phải cảnh báo charmap tiếng Việt (UnicodeDecodeError trên Terminal Windows) đòi hỏi phải format lại output console.

## Hướng cải thiện tiếp theo
- Xây dựng 1 hàm Feedback Loop tự động: Nhét ngược chính output sinh ra của LLM vào một LLM khác để tự chấm chéo xem câu hỏi này có thực sự "Đánh đố" hệ thống Retrieval hay không trước khi đẩy vào `golden_set`.
