# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom

> Agent trả lời sai SLA cho Ticket P1, bị lẫn thông tin sang Ticket P2. Lỗi tương tự: Model trả lời refund trong 14 ngày thay vì 7 ngày.

---

## Detection

> Metric phát hiện: Expectation `refund_no_stale_14d_window` báo FAIL, làm pipeline halt. Ngoài ra Eval script báo `hits_forbidden = yes` và `contains_expected = false`.

---

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|------------------|
| 1 | Kiểm tra log `artifacts/logs/run_*.log` | Thấy log báo Expectation nào đang bị lỗi và số lượng vi phạm. |
| 2 | Kiểm tra `artifacts/manifests/*.json` | Phát hiện lần ingest cuối có stale record hay không thông qua cờ SLA. |
| 3 | Mở `artifacts/quarantine/*.csv` | Xem những mẫu data rác đang được drop (để kiểm chứng rule drop đã đúng chưa). |
| 4 | Chạy `python eval_retrieval.py` | Kiểm tra top k chunks thực tế được truy xuất từ ChromaDB xem có dính doc cũ không. |

---

## Mitigation

> Sửa data bị lỗi, chạy lại ETL script: `python etl_pipeline.py run --run-id fix-run`. Model sẽ làm sạch các chuỗi, và thực hiện prune những ID không còn hợp lệ trên DB, cập nhật đúng thông tin chuẩn.

---

## Prevention

> Bổ sung các rule bắt cụm text cũ (ví dụ: `làm việc làm việc làm việc`, `10 ngày phép năm`) vào `cleaning_rules.py`. Thêm expectation tương ứng kiểm soát gắt gao nội dung text. Tạo cảnh báo khi Freshness quá hạn.
