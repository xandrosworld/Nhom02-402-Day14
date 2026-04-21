# Báo Cáo Phân Tích Thất Bại - Day 14

## 1. Tổng quan benchmark

- Tổng số cases: 66
- Tỷ lệ pass: 0.8485
- Điểm judge trung bình: 4.0379
- Retrieval hit rate: 0.9242
- MRR: 0.9167
- Agreement rate: 0.8561
- Pass/fail/error: 56 / 10 / 0
- Release gate: release

## 2. Phân nhóm lỗi

| Nhóm lỗi       | Số lượng | Triệu chứng                                                          | Tầng nghi ngờ         |
| -------------- | -------: | -------------------------------------------------------------------- | --------------------- |
| Retrieval miss |        0 | Không có case candidate với expected_retrieval_ids và hit_rate 0.0   | Retrieval             |
| Partial answer |        1 | Câu trả lời đúng nhưng điểm judge thấp, thiếu chiều sâu nội dung     | Prompting / synthesis |
| Judge conflict |        1 | Một case có score delta rất cao giữa hai judge model                 | Evaluation            |
| Slow case      |        0 | Không phát hiện case có latency bất thường quá lớn so với trung bình | Runner / agent        |

> Lưu ý: các case out-of-context có `hit_rate == 0` là do dataset không có document tương ứng, nên không tính là retrieval failure thực tế.

## 3. Phân tích 5 Whys

### Case A - Lỗi retrieval tệ nhất

1. Triệu chứng: `ooc_weather_01` trả về `hit_rate=0.0`, `mrr=0.0` trong khi agent vẫn cần xử lý câu hỏi ngoài KB.
2. Why 1: Không có document phù hợp trong KB cho câu hỏi về dự báo thời tiết.
3. Why 2: Dataset thiết kế case out-of-context để kiểm tra khả năng từ chối thông minh.
4. Why 3: Retrieval engine vẫn trả về các document không liên quan thay vì trả về kết quả “không tìm thấy”.
5. Why 4: Prompt/agent chưa được ép rõ ràng vào hành vi từ chối khi không tìm được tài liệu.
6. Nguyên nhân gốc: Thiếu cơ chế xử lý out-of-domain trong pipeline retrieval/generation, nên agent có thể bị lẫn giữa “không có dữ liệu” và “trả lời sai”.

### Case B - Lỗi partial answer tệ nhất

1. Triệu chứng: `kb_golden_dataset_std_08` đạt `final_score=2.0` dù status vẫn là pass.
2. Why 1: Câu trả lời nêu được ý chung nhưng không đi sâu vào bằng chứng cụ thể từ KB.
3. Why 2: Model trả lời quá khái quát, thiếu ví dụ và chi tiết chứng minh.
4. Why 3: Prompt generation chưa buộc agent trích dẫn hoặc tập trung vào cấu trúc “evidence-based answer”.
5. Why 4: Thang chấm judge dựa trên overlap token không đủ mạnh để đòn bẩy cho câu trả lời cô đọng, có thể khiến model chọn câu trả lời hơi lỏng.
6. Nguyên nhân gốc: Generation stage cần một prompt grounded hơn, hướng dẫn agent đưa ra câu trả lời chú ý đến nội dung KB và khía cạnh cụ thể của câu hỏi.

### Case C - Lỗi judge disagreement tệ nhất

1. Triệu chứng: `kb_retrieval_metrics_std_02` có `score_delta=3.0`, `final_score=1.75`, `agreement_rate=0.25`.
2. Why 1: Hai judge model đưa ra đánh giá rất khác nhau (5.0 vs 1.0).
3. Why 2: Một model đánh giá câu trả lời là gần đúng, trong khi model kia xem nó thiếu độ chính xác cần thiết.
4. Why 3: Logic đánh giá hiện tại chỉ dùng overlap token và bias cố định, dễ bị lệch khi thông tin đúng nhưng phrasing khác nhau.
5. Why 4: Thiếu cơ chế “tie-break” hoặc hiệu chỉnh đồng thuận khi score delta lớn.
6. Nguyên nhân gốc: Hệ thống multi-judge chưa đủ robust để xử lý trường hợp partial correctness; cần thêm quy tắc xếp ưu tiên khi disagreement cao.

## 4. Kế hoạch cải tiến

- [ ] Tăng cường prompt cho generation, yêu cầu câu trả lời grounded và trích dẫn nội dung KB.
- [ ] Hoàn thiện cơ chế xử lý out-of-context để agent có thể từ chối chính xác khi không có document tương ứng.
- [ ] Bổ sung logic tie-break cho multi-judge hoặc thêm judge thứ ba khi score delta lớn.
- [ ] Chạy lại benchmark sau khi sửa prompt và đánh giá xem pass/fail delta có cải thiện hay không.
