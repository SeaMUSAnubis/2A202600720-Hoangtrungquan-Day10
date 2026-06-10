# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Hoàng Trung Quân - 2A202600720  
**Vai trò:** Fullstack Data Pipeline (Ingestion, Cleaning, Embed, Monitoring)  
**Ngày nộp:** 2026-06-10  
**Độ dài yêu cầu:** **400–650 từ**

---

## 1. Tôi phụ trách phần nào?

**File / module:**
- `transform/cleaning_rules.py`: Tái cấu trúc cơ chế làm sạch văn bản, thêm các luật Quarantine (cách ly) để loại bỏ rác và tự code thuật toán cắt đoạn văn bản (Semantic Chunking).
- `quality/expectations.py`: Xây dựng các chốt chặn chất lượng (Quality Gates) để ngăn luồng ETL nạp dữ liệu bẩn vào Vector Database.
- `README.md`: Viết lại toàn bộ tài liệu kiến trúc kỹ thuật để giải trình luồng xử lý.

**Kết nối với thành viên khác:**
Tôi đảm nhận toàn bộ luồng chạy ETL từ lúc nạp dữ liệu thô (Ingestion) đến khi đẩy vector sạch vào ChromaDB (Embed), đảm bảo đầu vào chuẩn xác và không bị rác cho Agent hoạt động trơn tru ở Day 09.

**Bằng chứng (commit / comment trong code):**
Comment chú thích trực tiếp trong source code `cleaning_rules.py`:
`# Semantic Chunking: Tôn trọng ranh giới câu (Sentence Boundary)`

---

## 2. Một quyết định kỹ thuật

Tôi quyết định tự xây dựng lại thuật toán **Sentence-based Semantic Chunking** thay vì sử dụng phương pháp cắt Fixed-size (cắt cứng nhắc theo số lượng từ) hoặc ỷ lại vào dữ liệu cắt sẵn của hệ thống cũ.

Ban đầu, ý tưởng là dùng Sliding Window 50 từ, nhưng tôi nhận ra rủi ro chém đứt đôi câu văn (ví dụ cắt giữa chủ ngữ và vị ngữ) khiến AI mất ngữ cảnh trầm trọng. Tôi đã dùng Regex `re.split(r'(?<=[.!?])\s+', fixed_text)` để tách văn bản theo dấu chấm câu, sau đó mới gom các câu nguyên vẹn vào một chunk (tối đa 70 từ). 

Để đảm bảo tính liền mạch, tôi thiết kế cơ chế **Overlap mềm dẻo**: giữ lại nguyên văn câu cuối cùng của chunk trước làm câu mở đầu cho chunk sau. Quyết định này tốn thêm vài dòng code phức tạp nhưng đã giúp nâng cao đột biến điểm chất lượng của Retrieval.

---

## 3. Một lỗi hoặc anomaly đã xử lý 

**Triệu chứng:** Dù file báo cáo HR có hiệu lực mới nhất (năm 2026), nhưng AI liên tục bị ảo giác (hallucination) và trả lời sai chính sách nghỉ phép là "10 ngày" (quy định cũ) thay vì "12 ngày".

**Xử lý:** Qua rà soát, tôi phát hiện có sự bất đồng bộ (ai đó đã copy-paste nhầm nội dung quy định cũ vào hệ thống mới). Tôi lập tức thêm Rule vào `cleaning_rules.py`:
`if doc_id == "hr_leave_policy" and re.search(r"10\s+ngày\s+phép\s+năm", text, re.IGNORECASE): quarantine.append({...})`

Dữ liệu này không bị drop âm thầm mà bị "bế" thẳng vào mục Quarantine (cách ly) với nhãn `reason: "stale_10d_annual_leave"`. Nhờ đó, data engineer có thể truy vết nguyên nhân từ file logs, đồng thời Vector DB được bảo vệ triệt để khỏi dữ liệu độc hại.

---

## 4. Bằng chứng trước / sau

Sau khi xử lý nhiễu và áp dụng Chunking mới, độ chính xác cải thiện rõ rệt.

**Bằng chứng log chạy ETL (`run_id: 2026-06-10T15-50Z`):**
```text
run_id=2026-06-10T15-50Z
raw_records=152
cleaned_records=163
quarantine_records=8
PIPELINE_OK
```
Số lượng `cleaned_records` tăng lên do các đoạn văn dài được Semantic Chunking chẻ mượt mà thành nhiều chunk nhỏ chuẩn ngữ nghĩa.

**Kết quả đánh giá (Eval):**
- Trước khi fix: `hits_forbidden = true` (AI bị dụ đọc nhầm chính sách cũ).
- Sau khi fix: `hits_forbidden = false`, `contains_expected = true`.

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ tích hợp tính năng **LLM-as-a-judge** vào luồng `expectations.py`. Thay vì dùng Regex khô khan để tìm kiếm chuỗi "Nội dung không rõ ràng", tôi sẽ gọi API GPT-4o-mini duyệt nhanh các chunk để chấm điểm (score) mức độ dễ hiểu của văn bản. Chunk nào quá tối nghĩa sẽ bị đánh `warn` để chuyên viên biên tập lại.
