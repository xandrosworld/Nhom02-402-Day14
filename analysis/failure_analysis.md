# Bao Cao Phan Tich That Bai - Toi uu hoa OPTIMIZED (V2)

**Timestamp**: 2026-04-21 17:57:59
**Quyet dinh Release**: ROLLBACK

## 1. Tong quan benchmark

| Metrics         | V1     | V2     | Thay doi |
| --------------- | ------ | ------ | -------- |
| Judge Score     | 4.9018 | 4.8259 | -0.08    |
| Hit Rate        | 0.9107 | 0.9107 | 0.00     |
| Judge Agreement | 0.9732 | 0.9554 | -0.02    |

**Metrics hien tai (V2)**:

- Tong cases: 56
- Pass: 55 (98.2%)
- Fail: 1
- Error: 0
- Avg Score: 4.8259
- Hit Rate: 0.9107
- Agreement Rate: 0.9554

## 2. Phan nhom loi

- Retrieval failures (relevancy == 0): 0
- Failed cases: 1
- Judge disagreement (delta > 1.0): 3
- Max disagreement delta: 3.0

## 3. Worst cases

### Case A - Retrieval failure

None

### Case B - Partial/Wrong answer

- test_case: Sau khi khac phuc xong, incident report phai duoc viet trong bao lau?
  status: fail
  agent_response: Sau khi khac phuc, viet incident report trong vong 24 gio. Laptop moi duoc cap sau bao lau khi vao cong ty? Laptop duoc cap trong ngay onboarding dau tien.
  latency: 32.46131s
  ragas.relevancy: 0.5391
  judge.final_score: 2.75
  judge.score_delta: 3.0
  judge.agreement_rate: 0.25

### Case C - Judge disagreement

- test_case: IT Security thuc hien access review dinh ky bao lau mot lan?
  status: pass
  agent_response: IT Security thuc hien access review moi 6 thang. Laptop moi duoc cap sau bao lau khi vao cong ty? Laptop duoc cap trong ngay onboarding dau tien.
  latency: 19.04855s
  ragas.relevancy: 0.4979
  judge.final_score: 3.5
  judge.score_delta: 2.0
  judge.agreement_rate: 0.5

## 4. Goi y cai tien

- Toi uu retrieval pipeline de cai thien hit_rate.
- Dieu chinh generation prompt cho cac case co score thap.
- Xem xet tie-break logic khi judge disagreement cao.
- Tiep tuc monitoring sau khi release quyet dinh ROLLBACK.

## 5. Giai thich vi sao V2 khong bang V1

- Retrieval khong giam nhung chat luong tra loi giam: Hit Rate giu nguyen 0.9107, trong khi Judge Score giam tu 4.9018 xuong 4.8259 va Judge Agreement giam tu 0.9732 xuong 0.9554.
- Dau hieu regression nam o generation/consistency: mot so cau tra loi bi tron noi dung khong lien quan vao dap an chinh, khien diem judge giam manh du retrieval van trung tai lieu.
- Regression kieu "soft" nhung co y nghia van hanh: Pass rate van cao, nhung do tin cay giam do disagreement tang va chat luong khong on dinh o mot nhom case.
- Quyet dinh ROLLBACK la hop ly: khi score va agreement cung giam, rui ro release tang; rollback giup bao toan chat luong truoc khi tiep tuc toi uu V2.
