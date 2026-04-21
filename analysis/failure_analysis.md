# Báo Cáo Phân Tích Kết Quả Benchmark

**Thời gian chạy cuối**: 2026-04-21 22:35:00  
**Phiên bản so sánh**: `V1` và `V2`  
**Kết luận**: `V2` tốt hơn `V1` và đủ điều kiện sử dụng làm phiên bản nộp cuối.

## 1. Tóm tắt kết quả

Lần chạy benchmark cuối cho thấy phiên bản `V2` đã cải thiện so với `V1` ở các chỉ số quan trọng. Điểm đánh giá trung bình tăng từ `4.7857` lên `4.8482`, mức độ đồng thuận giữa hai mô hình chấm tăng từ `0.9420` lên `0.9911`, trong khi khả năng truy xuất tài liệu đúng vẫn được giữ nguyên ở mức `0.9107`.

Điều này cho thấy phần cải tiến của nhóm không làm giảm chất lượng truy xuất, đồng thời giúp câu trả lời ổn định hơn, ít gây tranh cãi hơn khi được chấm bởi hai mô hình độc lập. Bên cạnh đó, thời gian phản hồi trung bình của `V2` cũng thấp hơn đáng kể so với `V1`.

Tuy vậy, hệ thống vẫn còn `2/56` trường hợp trả lời chưa đúng hoàn toàn. Các lỗi còn lại không phải lỗi nghiêm trọng ở mức toàn hệ thống, nhưng vẫn cần được ghi nhận rõ để hoàn thiện thêm nếu có thời gian.

## 2. So sánh giữa V1 và V2

| Chỉ số | V1 | V2 | Nhận xét |
| --- | ---: | ---: | --- |
| Điểm đánh giá trung bình | 4.7857 | 4.8482 | V2 tốt hơn |
| Tỷ lệ truy xuất đúng | 0.9107 | 0.9107 | Giữ nguyên |
| Mức độ đồng thuận khi chấm | 0.9420 | 0.9911 | V2 ổn định hơn |
| Số câu đạt | 53/56 | 54/56 | V2 giảm số lỗi |
| Tỷ lệ đạt | 0.9464 | 0.9643 | V2 tốt hơn |
| Thời gian phản hồi trung bình | 22.9370 giây | 14.1261 giây | V2 nhanh hơn |
| Số trường hợp chấm còn bất đồng rõ rệt | 4 | 1 | V2 giảm mạnh |

Từ bảng trên có thể thấy:

- `V2` không cải thiện thêm về phần truy xuất, nhưng cải thiện rõ về chất lượng đầu ra.
- `V2` cho câu trả lời ổn định hơn và ít gây bất đồng hơn giữa các mô hình chấm.
- `V2` phản hồi nhanh hơn, phù hợp hơn cho việc sử dụng thực tế.

## 3. Các trường hợp còn lỗi trong V2

### Trường hợp 1: Câu hỏi về quên mật khẩu

- **Câu hỏi**: `Nếu quên mật khẩu thì nên làm gì trước?`
- **Đáp án mong đợi**: `Truy cập https://sso.company.internal/reset hoặc liên hệ Helpdesk qua ext. 9000.`
- **Câu trả lời của V2**: `Có. Mật khẩu phải được thay đổi mỗi 90 ngày. Hệ thống sẽ nhắc nhở 7 ngày trước khi hết hạn.`
- **Điểm chấm**: `1.0`

Phân tích:

- Hệ thống đã truy xuất đúng tài liệu liên quan, nên đây không phải lỗi tìm sai nguồn.
- Sai sót nằm ở bước chọn thông tin để trả lời: thay vì lấy hướng dẫn reset mật khẩu, mô hình lại chọn nhầm nội dung về chu kỳ đổi mật khẩu định kỳ.
- Đây là lỗi chọn sai chi tiết trong cùng một tài liệu có nhiều câu hỏi gần chủ đề với nhau.

### Trường hợp 2: Câu hỏi về ngày áp dụng chính sách hoàn tiền V4

- **Câu hỏi**: `Chính sách hoàn tiền V4 áp dụng cho đơn hàng đặt từ khi nào?`
- **Đáp án mong đợi**: `Áp dụng cho đơn hàng đặt trên hệ thống nội bộ kể từ ngày 01/02/2026.`
- **Câu trả lời của V2**: `Các đơn hàng đặt trước ngày có hiệu lực sẽ áp dụng theo chính sách hoàn tiền phiên bản 3.`
- **Điểm chấm**: `2.0`

Phân tích:

- Hệ thống vẫn truy xuất đúng tài liệu chính sách hoàn tiền V4.
- Tuy nhiên, câu trả lời lại chọn phần quy định chuyển tiếp thay vì mốc thời gian có hiệu lực chính.
- Điều này cho thấy mô hình vẫn còn yếu khi phải ưu tiên một mốc thời gian trung tâm trong tài liệu có nhiều mốc liên quan.

## 4. Mẫu lỗi chính quan sát được

### 4.1. Phần truy xuất tài liệu

- `V1` và `V2` có cùng tỷ lệ truy xuất đúng là `0.9107`.
- Số trường hợp truy xuất rỗng là `5`, chủ yếu rơi vào các câu hỏi ngoài phạm vi tài liệu hoặc câu hỏi quá mơ hồ.
- Vì vậy, ở lần chạy cuối, truy xuất không phải là điểm yếu lớn nhất của hệ thống.

### 4.2. Phần sinh câu trả lời

- Điểm mạnh của `V2` nằm ở việc câu trả lời ngắn gọn và trực tiếp hơn.
- Ở giai đoạn trước, `V2` từng gặp lỗi trộn thêm đoạn thông tin không liên quan vào câu trả lời, đặc biệt ở các tài liệu dạng FAQ.
- Sau khi chỉnh lại cơ chế chọn đoạn trích, chất lượng đầu ra đã ổn định hơn rõ rệt.
- Hai lỗi còn lại của `V2` đều là lỗi chọn nhầm thông tin gần nghĩa, chứ không phải bịa ra thông tin ngoài tài liệu.

### 4.3. Độ ổn định khi chấm

- `V2` chỉ còn `1` trường hợp mà hai mô hình chấm chưa đồng thuận hoàn toàn, trong khi `V1` có `7` trường hợp.
- Đây là một tín hiệu tốt, vì nó cho thấy đầu ra của `V2` rõ ràng và nhất quán hơn.

## 5. Nguyên nhân của lần kết quả xấu trước đó và cách khắc phục

Trong một lần chạy trước, `V2` từng cho kết quả kém hơn `V1`. Nguyên nhân chính khi đó không nằm ở dữ liệu hay ở phần truy xuất, mà nằm ở cách tạo câu trả lời theo kiểu trích xuất đoạn văn.

Cụ thể:

- Hệ thống từng sinh thêm dạng đoạn ghép giữa câu hỏi và câu trả lời trong tài liệu FAQ.
- Khi chọn đoạn để trả lời, mô hình có thể ghép nhầm hai ý gần nhau nhưng không cùng nội dung trọng tâm.
- Vì vậy, một số câu trả lời bị lẫn thêm thông tin không liên quan, làm giảm điểm và giảm độ đồng thuận khi chấm.

Sau khi sửa:

- bỏ kiểu ghép `Q + A` trong bước tạo đoạn trích,
- chỉ giữ đoạn phù hợp nhất thay vì nối nhiều đoạn,
- chạy lại toàn bộ benchmark để đối chiếu,

thì kết quả cuối cùng cho thấy `V2` đã vượt lại `V1`.

## 6. Đánh giá mức độ tin cậy

Mặc dù `V2` có điểm đánh giá và độ đồng thuận tốt hơn, chỉ số liên quan về mặt từ vựng vẫn thấp hơn nhẹ so với `V1`. Điều này có thể được giải thích bởi hai lý do:

- `V2` có xu hướng trả lời ngắn gọn hơn, nên mức trùng khớp từ ngữ với đáp án mẫu đôi khi thấp hơn.
- Bộ đo dựa trên mức trùng khớp từ ngữ nhạy với cách diễn đạt, trong khi phần chấm bằng mô hình lại phản ánh tốt hơn việc câu trả lời có đúng trọng tâm hay không.

Vì vậy, trong bản đánh giá cuối, nhóm ưu tiên xem xét tổng hợp nhiều chỉ số: độ đúng, độ ổn định khi chấm, số câu đạt và thời gian phản hồi, thay vì chỉ dựa vào một chỉ số đơn lẻ.

## 7. Kiến nghị

Nhóm có thể sử dụng kết quả hiện tại làm bản nộp cuối vì:

- phiên bản `V2` đã tốt hơn `V1` ở các chỉ số quan trọng,
- số lỗi còn lại ít và có thể giải thích rõ trong báo cáo,
- hệ thống phản hồi nhanh hơn và ổn định hơn,
- kết quả tổng thể cho thấy phần cải tiến là có ý nghĩa thực chất.

## 8. Hướng cải thiện tiếp theo

- Bổ sung quy tắc ưu tiên cho các câu hỏi ngắn dạng FAQ, đặc biệt là nhóm hỏi về reset mật khẩu.
- Bổ sung quy tắc nhận diện các câu hỏi hỏi về mốc thời gian hiệu lực, để tránh chọn nhầm thông tin chuyển tiếp.
- Nếu có thêm thời gian, có thể viết thêm các câu trả lời mẫu cố định cho một số trường hợp ngắn nhưng dễ nhầm.

## 9. Kết luận cuối cùng

Phiên bản `V2` đã đạt chất lượng tốt hơn `V1` trong lần đánh giá cuối cùng. Dù vẫn còn hai lỗi nhỏ cần ghi nhận, kết quả chung cho thấy hệ thống đã ổn định hơn, nhanh hơn và cho đầu ra đáng tin cậy hơn. Vì vậy, đây là phiên bản phù hợp để dùng làm kết quả cuối của bài nộp.
