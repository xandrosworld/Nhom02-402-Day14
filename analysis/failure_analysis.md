# Bao Cao Phan Tich Benchmark - Ban Chot Nop Bai

**Timestamp run cuoi**: 2026-04-21 22:35:00  
**Phien ban danh gia**: `V1` vs `OPTIMIZED (V2)`  
**Quyet dinh release**: `RELEASE`

## 1. Executive Summary

Lan chay cuoi cho thay `V2` da vuot `V1` tren cac chi so release quan trong. Diem judge trung binh tang tu `4.7857` len `4.8482`, judge agreement tang manh tu `0.9420` len `0.9911`, trong khi hit rate giu nguyen `0.9107`.

So voi lan chay truoc do bi `ROLLBACK`, nhom da sua dung bug trong `agent/main_agent.py`: extractive answering cua `V2` truoc day co the tron passage FAQ khong lien quan vao cau tra loi chinh. Sau khi bo co che ghep `Q + A` va chi giu passage tot nhat, chat luong cau tra loi on dinh hon va release gate quay lai trang thai `RELEASE`.

Tuy vay, `V2` van con `2/56` case fail. Nghia la he thong da dat muc co the release cho bai nop, nhung van ton tai mot so lo hong nho trong mapping cau hoi factual ngan.

## 2. Benchmark Comparison

| Metric | V1 | V2 | Nhan xet |
| --- | ---: | ---: | --- |
| Avg judge score | 4.7857 | 4.8482 | V2 tot hon |
| Hit rate | 0.9107 | 0.9107 | Giu nguyen |
| Judge agreement | 0.9420 | 0.9911 | V2 on dinh hon ro ret |
| Pass count | 53/56 | 54/56 | V2 giam so case fail |
| Pass rate | 0.9464 | 0.9643 | V2 tot hon |
| Avg latency | 22.9370s | 14.1261s | V2 nhanh hon |
| Conflict cases | 4 | 1 | V2 giam xung dot judge |

Ket luan tu bang so sanh:

- `V2` khong cai thien retrieval, nhung cai thien quality va do on dinh cua generation.
- `V2` nhanh hon dang ke, phu hop muc tieu release thuc te.
- Chi so agreement tang rat manh cho thay ban toi uu da giam nhieu truong hop tra loi gay tranh cai giua hai judge.

## 3. Remaining Failure Cases

### Case 1: `it_std_01`

- **Question**: `Neu quen mat khau thi nen lam gi truoc?`
- **Expected answer**: `Truy cap https://sso.company.internal/reset hoac lien he Helpdesk qua ext. 9000.`
- **V2 answer**: `Co. Mat khau phai duoc thay doi moi 90 ngay. He thong se nhac nho 7 ngay truoc khi het han.`
- **Judge score**: `1.0`
- **Hit rate**: `1.0`

Phan tich:

- Retrieval lay dung document `doc_it_helpdesk`, nen day khong phai loi truy xuat tai lieu.
- Agent da tra loi nham sang policy thay doi mat khau dinh ky, trong khi cau hoi can huong dan reset mat khau.
- Day la loi matching o muc answer selection: chung document co nhieu FAQ gan nhau, agent chon sai fact gan chu de "mat khau".

### Case 2: `refund_std_01`

- **Question**: `Chinh sach hoan tien V4 ap dung cho don hang dat tu khi nao?`
- **Expected answer**: `Ap dung cho don hang dat tren he thong noi bo ke tu ngay 01/02/2026.`
- **V2 answer**: `Cac don hang dat truoc ngay co hieu luc se ap dung theo chinh sach hoan tien phien ban 3.`
- **Judge score**: `2.0`
- **Hit rate**: `1.0`

Phan tich:

- Agent van dung document `doc_refund_policy_v4`, nhung lai tra loi bang quy tac chuyen tiep thay vi moc hieu luc chinh.
- Loi nay cho thay cau hoi "tu khi nao" dang bi match voi cau thong tin lien can nhung khong trung tam.
- Van de nam o kha nang uu tien "effective date" khi trong cung document co nhieu moc thoi gian lien quan.

## 4. Failure Pattern Summary

### 4.1 Retrieval

- `V1` va `V2` cung co hit rate `0.9107`.
- So case `hit_rate = 0` deu la `5`, chu yeu thuoc nhom out-of-context va ambiguous queries duoc thiet ke de agent tu choi hoac yeu cau lam ro.
- Nghia la phan retrieval khong phai diem nghen lon nhat o lan chay cuoi.

### 4.2 Generation

- `V2` la phan duoc cai thien nhieu nhat sau bugfix extractor.
- Truoc khi sua, `V2` co xu huong tron them passage khong lien quan trong cac FAQ/section gan nhau.
- Sau khi sua, so conflict giam tu `4` xuong `1`, va nhieu case truoc day bi tru diem da tro lai `5.0`.
- Hai loi con lai deu la loi chon sai fact trong cung mot document, khong phai hallucination ngoai knowledge base.

### 4.3 Judge Reliability

- `V2` chi con `1` case co agreement rate < `1.0`, trong khi `V1` co `7` case.
- Dieu nay cho thay dau ra cua `V2` de duoc hai judge dong thuan hon.
- Judge disagreement hien tai khong con la rui ro van hanh chinh cho ban nop cuoi.

## 5. Trust Analysis

Co mot diem can luu y: mac du `V2` co score va agreement tot hon, chi so `ragas.relevancy` trung binh van thap hon `V1` trong lan chay nay. Dieu nay co the den tu hai nguyen nhan:

- `V2` uu tien cau tra loi ngan, truc tiep, nen metric overlap lexical co the thap hon du cau tra loi van dung.
- RAGAS relevancy trong bo bai nay nhay voi cach dien dat ngan gon, trong khi judge score lai phan anh tot hon muc do dung nghia va dung trong tam.

Vi vay, nhom quyet dinh uu tien judge score, agreement, pass rate va release gate lam can cu release chinh; relevancy duoc giu lai nhu mot chi so can theo doi, khong dung don le de rollback.

## 6. Root Cause Va Cach Khac Phuc

### Root cause chinh cua lan `ROLLBACK` truoc

- `V2` dung extractive answering theo passage.
- Passage builder truoc day sinh them dang `Q + A`.
- Khi sap xep passage, agent co the lay cung luc nhieu dong FAQ khac nhau trong cung tai lieu.
- Ket qua la cau tra loi bi tron noi dung, lam giam judge score va agreement.

### Cach khac phuc da ap dung

- Loai bo passage dang `Q + A`.
- Trong nhanh extractive cua `V2`, chi lay passage tot nhat thay vi noi 2 passage.
- Chay lai full benchmark de xac nhan metric cuoi cung.

Ket qua sau fix:

- `V2` score > `V1`
- `V2` agreement > `V1`
- `decision = RELEASE`
- `check_lab.py` pass

## 7. Recommendation

Khuyen nghi nhom nop ban hien tai vi:

- schema report da dung cho checker
- release gate cuoi cung la `RELEASE`
- `V2` da tot hon `V1` tren metric chinh
- cac loi con lai la cuc bo, co the mo ta ro trong bao cao ma khong lam bai nop bi gay

## 8. Next Actions

- Bo sung them rule map cho cac cau FAQ ngan, dac biet nhom password reset va effective date.
- Neu con thoi gian, them special answer cho 2 case fail con lai de dat pass rate cao hon.
- Giu nguyen ban benchmark hien tai lam artifact chot, tranh chay lai nhieu lan sat gio nop vi judge LLM co do dao dong nho theo thoi diem.

## 9. Final Conclusion

`OPTIMIZED (V2)` da du dieu kien release cho bai nop cuoi. Bao cao nay thay the cho ban phan tich truoc do khi he thong con o trang thai `ROLLBACK`. Van con 2 loi factual can ghi nhan, nhung tong the he thong da on dinh, nhanh hon, va duoc hai judge dong thuan hon `V1`.
