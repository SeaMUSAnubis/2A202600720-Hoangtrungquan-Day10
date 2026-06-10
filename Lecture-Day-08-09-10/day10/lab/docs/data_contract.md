# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| `policy_refund_v4` | File import (`docs/policy_refund_v4.txt`) | Lệch bản version cũ (14 ngày), thiếu chunk_text | Alert khi số lượng lỗi > 0, halt pipeline |
| `sla_p1_2026` | File import (`docs/sla_p1_2026.txt`) | Trùng lặp chunk text, thiếu update SLA | Cảnh báo trùng lặp (warn) |
| `it_helpdesk_faq` | File import (`docs/it_helpdesk_faq.txt`) | Lỗi format, thông tin password quá hạn | Cảnh báo warn/halt tùy theo loại |
| `hr_leave_policy` | File import (`docs/hr_leave_policy.txt`) | Nhầm bản HR 2025 thay vì 2026 | Alert & halt pipeline nếu sai số ngày phép |
| `access_control_sop` | File import (`docs/access_control_sop.txt`) | Thiếu workflow duyệt, format sai | Missing record alert |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | ID định danh độc nhất cho mỗi đoạn text (hash hoặc doc_id + seq) |
| doc_id | string | Có | ID của tài liệu gốc tương ứng (ví dụ: `policy_refund_v4`) |
| chunk_text | string | Có | Nội dung đoạn text đã được xử lý làm sạch (độ dài tối thiểu 8 ký tự) |
| effective_date | date | Có | Ngày có hiệu lực của chính sách |
| exported_at | datetime | Có | Thời gian trích xuất dữ liệu |

---

## 3. Quy tắc quarantine vs drop

> - **Quarantine**: Những record vi phạm lỗi ở mức độ `warn` (như lặp câu, có thể có nhiễu nhẹ) hoặc thiếu dữ liệu không quan trọng sẽ được đẩy vào khu vực *quarantine*. Data Steward / Content Team sẽ định kỳ review khu vực này để sửa thủ công và approve merge lại vào tập cleaned.
> - **Drop**: Những record vi phạm nghiêm trọng mức độ `halt` (ví dụ chứa thông tin chính sách cũ như "hoàn tiền trong 14 ngày" hay "HR 2025" gây hiểu nhầm, rác không thể parse) sẽ bị **drop** trực tiếp khỏi flow chính và log cảnh báo qua hệ thống `#data-quality-alerts` để Data Engineer kiểm tra lại ingestion nguồn.

---

## 4. Phiên bản & canonical

> - **Policy Refund**: Source of truth là file `docs/policy_refund_v4.txt` (Phiên bản v4, hiệu lực 2026-02-01).
> - **HR Leave Policy**: Source of truth là file `docs/hr_leave_policy.txt` (Phiên bản 2026, hiệu lực 2026-01-01).
> - **IT Helpdesk & SLA & Access Control**: Dựa theo các file `.txt` tương ứng trong thư mục `docs/`.
