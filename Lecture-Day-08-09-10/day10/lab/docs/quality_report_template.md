# Quality report — Lab Day 10 (nhóm)

**run_id:** _______________  
**Ngày:** _______________

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước | Sau | Ghi chú |
|--------|-------|-----|---------|
| raw_records | 247 | 247 | Tổng dữ liệu raw không đổi |
| cleaned_records | 36 | 36 | (Tuỳ thuộc nội dung bad inject) |
| quarantine_records | 211 | 211 | Bản ghi vi phạm quy tắc |
| Expectation halt? | Có (FAIL refund_no_stale_14d_window) | Không (OK toàn bộ) | Khi inject bad data, expectation báo FAIL và halt. Sau khi fix, pipeline chạy trơn tru. |

---

## 2. Before / after retrieval (bắt buộc)

> Đính kèm hoặc dẫn link tới `artifacts/eval/before_after_eval.csv` (hoặc 2 file before/after).

**Câu hỏi then chốt:** refund window (`q_refund_window`)  
**Trước:** `q_refund_window,Khách hàng có bao nhiêu ngày để yêu cầu hoàn tiền kể từ khi đơn được xác nhận?,policy_refund_v4,Yêu cầu hoàn tiền được chấp nhận trong vòng 14 ngày làm việc kể từ xác nhận đơn.,yes,yes,yes,3` (Bị dính hits_forbidden = yes vì dính 14 ngày)
**Sau:** `q_refund_window,Khách hàng có bao nhiêu ngày để yêu cầu hoàn tiền kể từ khi đơn được xác nhận?,policy_refund_v4,Yêu cầu được gửi trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng.,yes,no,yes,3` (Đã clean, hits_forbidden = no)

**Merit (khuyến nghị):** versioning HR — `q_leave_version` (`contains_expected`, `hits_forbidden`, cột `top1_doc_expected`)

**Trước:** `q_hr_annual_leave_under3,Nhân viên dưới 3 năm kinh nghiệm được bao nhiêu ngày phép năm?,hr_leave_policy,Nhân viên dưới 3 năm kinh nghiệm được 12 ngày phép năm theo chính sách 2026.,yes,no,yes,3`
**Sau:** `q_hr_annual_leave_under3,Nhân viên dưới 3 năm kinh nghiệm được bao nhiêu ngày phép năm?,hr_leave_policy,Nhân viên dưới 3 năm kinh nghiệm được 12 ngày phép năm theo chính sách 2026.,yes,no,yes,3` (Dữ liệu đã được đảm bảo sạch nhờ quy tắc parse ngày >= 2026 và loại bỏ 10 ngày)

---

## 3. Freshness & monitor

> Kết quả `freshness_check`: **FAIL** `{"latest_exported_at": "2026-04-11T00:00:00", "age_hours": 1446.109, "sla_hours": 24.0, "reason": "freshness_sla_exceeded"}`
> **Giải thích SLA:** Dữ liệu có `latest_exported_at` là khoảng 2026-04-11, trong khi ngày hiện tại khi chạy script cách đó khá xa (vượt quá 24h). Do đó hệ thống ném cờ FAIL freshness báo hiệu pipeline quá hạn (stale ingestion).

---

## 4. Corruption inject (Sprint 3)

> **Mô tả inject:** Dùng lệnh `--no-refund-fix --skip-validate` để cố tình không chạy hàm đổi 14 ngày -> 7 ngày, và bỏ qua việc dừng luồng khi expectation FAIL.
> **Cách phát hiện:** Pipeline log báo `expectation[refund_no_stale_14d_window] FAIL (halt) :: violations=1`. Sau khi cố tình embed, chạy eval script trả về lỗi `hits_forbidden = yes` đối với câu hỏi `q_refund_window` do model bốc nhầm policy "14 ngày".

---

## 5. Hạn chế & việc chưa làm

- …
