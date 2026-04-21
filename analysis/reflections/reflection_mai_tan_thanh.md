# Reflection Cá Nhân - Mai Tan Thanh

## Vai trò
Tech Lead / Eval Integration Owner

## Các file phụ trách
- `main.py`
- `engine/runner.py`
- `agent/main_agent.py`
- phần integration và final release gate

## Tóm tắt đóng góp
- Chuẩn bị skeleton benchmark pipeline ban đầu để nhóm có thể chạy end-to-end với cùng một interface chung giữa agent, retrieval evaluator và judge.
- Thiết kế phần integration trong `main.py` để gom các bước load dataset, chạy baseline/candidate, tổng hợp metrics, quyết định release gate, và xuất ra `reports/summary.json` cùng `reports/benchmark_results.json`.
- Tích hợp `engine/runner.py` vào luồng benchmark chung để mỗi test case đều có format output thống nhất gồm câu hỏi, answer, retrieval block, judge block, latency và metadata.
- Điều chỉnh `agent/main_agent.py` để agent có thể làm việc với knowledge base mới, truy xuất đúng nguồn tài liệu nội bộ, và tạo câu trả lời ổn định hơn cho benchmark cuối.
- Giữ vai trò merge cuối và đồng bộ artifact, bảo đảm các phần do từng owner bàn giao có thể ghép lại thành một pipeline chạy được với các lệnh:
  `python data/synthetic_gen.py`
  `python main.py`
  `python check_lab.py`
- Sửa log trong runner về ASCII để tránh lỗi console encoding khi chạy benchmark trên Windows terminal, nhờ đó quá trình final run không bị dừng giữa chừng chỉ vì vấn đề hiển thị.

## Bài học kỹ thuật
- Khi nhiều thành viên làm song song, phần khó nhất không nằm ở từng module riêng lẻ mà ở chỗ giữ interface ổn định. Việc khóa sớm các contract như `MainAgent.query()`, `RetrievalEvaluator.score()` và `LLMJudge.evaluate_multi_judge()` giúp integration về cuối nhẹ hơn rất nhiều.
- Một benchmark pipeline tốt không chỉ chạy được mà còn phải xuất artifact nhất quán. Nếu report schema thay đổi liên tục hoặc thiếu field, việc merge giữa data, retrieval, judge và analysis sẽ rất dễ gãy.
- Release gate cần dựa trên số liệu tổng hợp rõ ràng thay vì cảm giác. Việc đặt logic so sánh baseline/candidate bằng score delta, hit rate delta, pass rate và agreement threshold giúp quyết định release/rollback minh bạch hơn.
- Khi chạy benchmark trên Windows, các chi tiết tưởng nhỏ như encoding console cũng có thể làm hỏng cả pipeline. Việc thay log Unicode bằng log ASCII trong runner là một bài học thực tế về độ bền của công cụ.
- Integration owner cần nhìn bài toán ở mức hệ thống: dataset mới, agent mới và report mới phải đồng bộ với nhau. Chỉ cần một mắt xích cũ còn sót lại thì kết quả benchmark sẽ mất ý nghĩa.

## Vấn đề gặp phải
- Các nhánh của nhóm được đẩy lên không cùng thời điểm nên nhiều lúc remote `main` thay đổi liên tục, dẫn đến phải fetch/rebase thường xuyên trước khi push phần integration cuối.
- Có giai đoạn dataset đã đổi sang bộ tài liệu mới nhưng reports vẫn còn ghi kết quả từ bộ demo cũ. Việc phát hiện và xử lý độ lệch giữa dataset và benchmark artifact là một trong những vấn đề integration quan trọng nhất.
- Trong lúc phối hợp theo ownership, một vài file ngoài scope của mình bị chạm vào trong quá trình debug. Điều này buộc mình phải quay lại rà `TEAM_OWNERSHIP.md`, khôi phục file không đúng owner, và chỉ giữ các thay đổi đúng trách nhiệm của mình.
- Benchmark full có lúc chạy lâu hoặc bị chặn bởi lỗi runtime không đến từ logic cốt lõi, ví dụ lỗi in ký tự Unicode ra terminal. Những lỗi kiểu này mất thời gian vì không nằm trong bài toán học thuật nhưng vẫn phải xử lý để pipeline chạy được thật.
- Việc vừa đảm bảo benchmark pass, vừa giữ worktree sạch để bàn giao/push đúng phần của từng người đòi hỏi kiểm soát Git khá chặt, đặc biệt khi cần stash, rebase và khôi phục local changes an toàn.

## Hướng cải thiện tiếp theo
- Tách rõ hơn cấu hình giữa baseline và candidate trong pipeline để việc so sánh V1/V2 minh bạch hơn và không phụ thuộc quá nhiều vào logic cài cứng trong agent.
- Thêm bước kiểm tra đồng bộ trước khi xuất report, ví dụ xác nhận `reports/*` đang được tạo từ đúng dataset hiện hành thay vì từ artifact cũ.
- Bổ sung một lệnh hoặc script tổng hợp cho final run, ví dụ một script duy nhất chạy dataset generation, benchmark, validation và in checklist trạng thái nộp bài.
- Chuẩn hóa logging và error handling trong toàn pipeline để khi benchmark lỗi có thể xác định ngay đang hỏng ở dataset, retrieval, judge hay report writing.
- Nếu làm lại, mình sẽ yêu cầu từng owner bàn giao kèm “definition of done” rõ hơn: file đã sửa, output mong đợi, cách test cục bộ và rủi ro merge, để pha integration cuối nhanh và ít hồi quy hơn.
