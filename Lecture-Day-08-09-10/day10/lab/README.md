# Báo Cáo Kỹ Thuật: Hoàn thiện Data Pipeline & Data Observability (Day 10)

Tài liệu này giải trình kiến trúc và các quyết định kỹ thuật được áp dụng để làm sạch dữ liệu, quản lý lỗi và nhúng (embed) vector chuẩn bị cho hệ thống AI Agent (Day 09).

---

## 1. Cấu hình Dữ liệu (Chunking) & Nơi Lưu Trữ

### Chiến lược Cắt dữ liệu (Semantic Sentence Chunking)
Thay vì sử dụng các thuật toán cắt ngốc nghếch theo số lượng ký tự (Fixed-size) vốn dễ làm đứt đôi câu văn (ví dụ: *"Nhân viên được nghỉ..."* - hết chunk - *"...12 ngày"*), hệ thống của chúng tôi được lập trình thuật toán **Sentence-based Semantic Chunking** linh hoạt:

1.  **Tôn trọng ranh giới câu:** Thuật toán dùng Regex tách văn bản dựa trên các dấu chấm câu (`.`, `!`, `?`), đảm bảo không có câu nào bị chẻ đôi.
2.  **Đóng gói (Chunk size):** Gom các câu nguyên vẹn lại với nhau cho đến khi đạt giới hạn **70 từ (words)** mỗi chunk.
3.  **Cầu nối ngữ cảnh (Overlap):** Để AI không bị hẫng nhịp khi đọc nối tiếp 2 chunk, thuật toán tự động giữ lại nguyên văn câu cuối cùng của chunk trước, đem sang làm câu mở đầu cho chunk sau.
4.  **Lọc nhiễu:** Dùng chốt chặn `chunk_min_length_8` để loại bỏ các đoạn quá ngắn hoặc vô nghĩa (ví dụ: *"Xem thêm tại khoản 2."*).

### Kết quả được lưu ở đâu?
Hệ thống tuân thủ nguyên tắc phân loại rõ ràng, kết quả đầu ra được tự động phân bổ vào các thư mục:
1.  **Dữ liệu sạch (Cleaned Data):** Lưu định dạng CSV tại `artifacts/cleaned/policy_cleaned.csv`.
2.  **Dữ liệu bị cách ly (Quarantine Data):** Những đoạn văn bản chứa lỗi không thể sửa tự động được đẩy vào `artifacts/quarantine/` kèm lý do chi tiết.
3.  **Dữ liệu Nhúng (Vector Embeddings):** Văn bản sau khi qua vòng kiểm duyệt được biến đổi thành ma trận số và lưu tại cơ sở dữ liệu nội bộ ở thư mục `chroma_db/`.
4.  **Dữ liệu Giám sát:** Các tệp theo dõi hệ thống (Manifests, logs) nằm trong `artifacts/manifests/` và `artifacts/logs/`.

---

## 2. Kỹ thuật "Biểu Thức Chính Quy" (Regex) 

**Khái niệm đơn giản:** Regex giống như một "siêu công cụ tìm kiếm". Thay vì tìm chính xác từng chữ như `Ctrl + F`, nó tìm theo *quy luật*.

**Cụ thể những chỗ đã thay đổi bằng Regex:**
*   **Chữa lỗi dư khoảng trắng ở Cửa sổ hoàn tiền:** Dùng `r"14\s+ngày\s+làm\s+việc"` để dập tắt mọi biến thể lỗi gõ phím. Dù văn bản thô ghi là `"14 ngày"` hay `"14     ngày"`, hệ thống vẫn nhận diện được và thay thế thành *"7 ngày làm việc"*.
*   **Chữa lỗi "Lặp từ ngữ ngớ ngẩn":** Dùng `r"(làm\s+việc\s*){2,}"` để tự động tìm những chỗ chữ "làm việc" lặp lại liên tiếp 2, 3 hay 100 lần, và nén chúng lại thành 1 chữ "làm việc" duy nhất.

---

## 3. Kỹ thuật "Cách ly dữ liệu" (Data Quarantine)

**Khái niệm đơn giản:** Giống như một phòng khám y tế. Khi phát hiện dữ liệu bẩn, thay vì âm thầm vứt bỏ (drop), hệ thống đưa dữ liệu đó vào "Khu cách ly" và dán nhãn lý do "mắc bệnh". Việc này giúp Data Engineer dễ dàng truy vết (Observability).

**Các "Căn bệnh" bị đem đi cách ly trong bài Lab:**
1.  **Lý do `unclear_content`:** Cách ly những dòng chứa cụm *"Nội dung không rõ ràng"* hoặc có nhiều dấu chấm than `"!!!"`.
2.  **Lý do `stale_10d_annual_leave`:** Nếu nội dung copy nhầm chính sách cũ ghi *"10 ngày phép năm"* (chuẩn mới là 12 ngày), dòng này sẽ bị bế vào phòng cách ly. Nếu không làm việc này, AI sẽ tự tin đọc nhầm và tư vấn sai quyền lợi cho nhân viên.

---

## 4. Kỹ thuật "Chốt chặn Chất Lượng" (Expectation & Quality Gates)

Hệ thống thiết lập các "trạm kiểm soát biên giới" để bảo vệ AI. Tùy mức độ nghiêm trọng, trạm có các quyết định khác nhau:
*   **Mức độ Cảnh cáo (`Severity = "warn"`):** Dùng cho lỗi nhẹ (ví dụ: lặp từ ngữ nhẹ). Ghi vào sổ nhật ký (log) nhưng vẫn cho qua.
*   **Mức độ Cấm cửa (`Severity = "halt"`):** Dùng cho lỗi hủy diệt (ví dụ: chứa ký hiệu rác `"!!!"`). Trạm kiểm soát sẽ báo động đỏ, đánh sập và **dừng toàn bộ Pipeline**, không cho rác lọt vào bộ não của AI gây hiện tượng "ảo giác".

---

## 5. Kỹ thuật "Tính Lũy Đẳng" (Idempotency)

Mỗi đoạn văn được tạo một thẻ căn cước duy nhất (`chunk_id` băm bằng thuật toán SHA-256). 
Khi chạy Pipeline ETL 100 lần, hệ thống sẽ kiểm tra xem thẻ căn cước đó đã có trong Vector DB chưa. Nếu có rồi, nó chỉ **ghi đè (Upsert)** nội dung mới, chứ không bao giờ tạo ra 100 đoạn văn bản nhân bản (duplicate). Nhờ vậy, bộ nhớ Vector của AI luôn chính xác tuyệt đối.
