# Báo Cáo Phân Tích Thất Bại - Day 14

## 1. Tổng quan benchmark
- Tổng số cases: 50
- Tỷ lệ pass: Điền sau khi chạy `python main.py`
- Điểm judge trung bình: Điền sau khi chạy
- Retrieval hit rate / MRR: Điền sau khi chạy
- Agreement rate: Điền sau khi chạy

## 2. Phân nhóm lỗi
| Nhóm lỗi | Số lượng | Triệu chứng | Tầng nghi ngờ |
|---|---:|---|---|
| Retrieval miss | 0 | Không retrieve được tài liệu đúng trong top-k | Retrieval |
| Partial answer | 0 | Câu trả lời có ground nhưng chưa đầy đủ | Prompting / synthesis |
| Judge conflict | 0 | Hai model judge chấm lệch nhau nhiều | Evaluation |
| Slow case | 0 | Case có độ trễ bất thường | Runner / agent |

## 3. Phân tích 5 Whys

### Case A - Lỗi retrieval tệ nhất
1. Triệu chứng:
2. Why 1:
3. Why 2:
4. Why 3:
5. Why 4:
6. Nguyên nhân gốc:

### Case B - Lỗi hallucination hoặc partial answer tệ nhất
1. Triệu chứng:
2. Why 1:
3. Why 2:
4. Why 3:
5. Why 4:
6. Nguyên nhân gốc:

### Case C - Lỗi judge disagreement tệ nhất
1. Triệu chứng:
2. Why 1:
3. Why 2:
4. Why 3:
5. Why 4:
6. Nguyên nhân gốc:

## 4. Kế hoạch cải tiến
- [ ] Tinh chỉnh retrieval hoặc reranking
- [ ] Cải thiện prompt và cấu trúc câu trả lời
- [ ] Hiệu chỉnh logic tie-break cho multi-judge
- [ ] Chạy lại benchmark và so sánh delta
