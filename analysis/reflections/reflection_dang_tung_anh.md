# Reflection Cá Nhân - Đặng Tùng Anh

## Vai trò
Data Owner - Thiết kế Golden Dataset & Script SDG.

## Các file phụ trách
- `data/synthetic_gen.py`
- `data/golden_set.jsonl`

## Tóm tắt đóng góp
- Viết lại script sinh dữ liệu (`data/synthetic_gen.py`) để linh hoạt hơn sơ với bản mẫu, sinh ra được tổng **66 test cases** bám sát Grading Rubric.
- Đảm bảo độ khó và chất lượng bằng cách chia làm 5 loại cases chuyên biệt: `standard` (50), `multi_hop` (4), `adversarial` (4), `out_of_context` (4), và `edge_case` (4).
- Các trường quan trọng như `expected_retrieval_ids` được setup rất cẩn thận và map chính xác với ID của document, để phục vụ việc tính toán `Hit Rate` & `MRR` bên module Retrieval Eval.
- Chủ động phát hiện và khắc phục điểm yếu của bộ dataset mẫu ban đầu (điểm vụ `expected_answer` bị lặp lại y hệt nhau cho nhiều câu hỏi). Bằng cách thiết lập bộ `FOCUSED_ANSWERS`, em đã tinh chỉnh đáp án kỳ vọng chính xác theo từng "ý đồ" câu hỏi thay vì việc sao chép nguyên văn document từ KB, giúp LLM chấm điểm công bằng và khắt khe hơn đối xứng với Agent.

## Bài học kỹ thuật
- **Sự quan trọng của Ground Truth Retrieval ID:** Việc tạo dataset không chỉ là lo về câu hỏi, mà quan trọng là bộ mapping tài liệu để đánh giá được Retrieval Pipeline hoạt động thế nào. Thiếu field này thì metrics Hit Rate sẽ vô nghĩa.
- **Tác động của Expected Answer tới kết quả chấm điểm của Judge:** Nếu để expected_answer là một đoạn văn bản dài, Agent có nguy cơ bị Model Judge chấm điểm thấp nếu trả lời quá súc tích dù đúng trọng tâm. Học được cách thiết kế (Focus) cho đáp án kỳ vọng.

## Vấn đề gặp phải
- **Thiếu sự đa dạng trong expected_answer ở nhóm Standard:** Đối với 50 câu hỏi tiêu chuẩn, mặc dù cách đặt câu hỏi khác nhau (từ tóm tắt, hỏi hành động, đến hỏi số liệu), nhưng expected_answer lại được sao chép/dán y hệt nhau cho toàn bộ 10 câu của cùng một chủ đề.

## Hướng cải thiện tiếp theo
- Dùng thẳng API của LLM (GPT-4o hoặc Gemini) để sinh câu hỏi và nhiễu (noise) một cách đa dạng và tự nhiên hơn dựa trên context có sẵn, thay vì dùng phương pháp điền parameter `{topic}` vào các câu hỏi mẫu cứng nhắc (Templates).
- Mở rộng thêm lượng data `multi-hop` và đo đạc kỹ hơn sự ảnh hưởng của nhiễu lên kết quả retrieval.
