# Legal AI System: Kiến trúc Tích hợp Data Pipeline & Multi-Agent

Dự án này là kết quả tổng hợp toàn diện của hệ thống **Legal AI** (Trợ lý ảo pháp lý và quy định nội bộ). Hệ thống là sự kết hợp chặt chẽ giữa tầng xử lý dữ liệu (Data Pipeline) và tầng suy luận trí tuệ nhân tạo (Agent Orchestrator), đảm bảo AI luôn trả lời dựa trên kho kiến thức sạch sẽ, cập nhật và chính xác nhất.

---

## 1. Tổng quan Kiến trúc

Hệ thống được chia thành hai phân hệ độc lập nhưng liên kết mật thiết với nhau:

1. **Data Pipeline (`day10/lab`):**
   - Đảm nhiệm việc thu thập (Ingestion) văn bản thô từ nhiều nguồn.
   - Làm sạch, cách ly rác (Quarantine) và kiểm soát chất lượng (Quality Gates).
   - Tự động cắt theo ngữ nghĩa (Semantic Sentence Chunking) và nhúng thành Vector lưu vào ChromaDB.

2. **Web Application (`day10/web_app`):**
   - **Backend API:** Hệ thống Supervisor định tuyến câu hỏi tới các AI Worker chuyên trách (Legal, Tax, Compliance). Worker sử dụng RAG để móc nối với cơ sở dữ liệu ChromaDB.
   - **Frontend UI:** Giao diện React mượt mà giúp người dùng tương tác trực tiếp với các Agent.

---

## 2. Công nghệ sử dụng

- **LLM & RAG:** GPT-4o-mini, LangChain, SentenceTransformers.
- **Vector Database:** ChromaDB.
- **Backend:** FastAPI, Uvicorn, Pydantic.
- **Frontend:** React, Vite, Tailwind CSS.
- **Data Engineering:** Python thuần túy với kiến trúc Idempotency và Regex Rules.

---

## 3. Cấu trúc Thư mục

```text
day10/
├── lab/                             # Tầng Data Pipeline (ETL)
│   ├── data/                        # Chứa dữ liệu đầu vào (raw data)
│   ├── transform/
│   │   └── cleaning_rules.py        # Luật làm sạch, Chunking & Quarantine
│   ├── quality/
│   │   └── expectations.py          # Chốt chặn chất lượng (Quality Gates)
│   ├── chroma_db/                   # Cơ sở dữ liệu Vector tự động sinh ra
│   └── etl_pipeline.py              # Script điều phối luồng ETL
│
└── web_app/                         # Tầng Multi-Agent Application
    ├── backend/                     # API Server
    │   ├── workers/                 # Chứa các Agent phụ trách mảng riêng lẻ
    │   │   ├── legal_worker.py      # Truy vấn RAG qua ChromaDB
    │   │   ├── tax_worker.py
    │   │   └── compliance_worker.py
    │   ├── agent_orchestrator.py    # Supervisor AI (Pure Python Routing)
    │   └── main.py                  # FastAPI App
    └── frontend/                    # Giao diện người dùng React/Vite
        └── src/
```

---

## 4. Hướng dẫn Khởi chạy Toàn Hệ Thống

Hãy thực hiện tuần tự 3 bước sau để đưa toàn bộ kiến trúc vào hoạt động.

### Bước 1: Khởi tạo Dữ liệu (ETL Pipeline)
Thực thi luồng ETL để hệ thống đọc các file văn bản mới nhất, làm sạch và tạo Vector Database.
```bash
cd day10/lab
python etl_pipeline.py run
```

### Bước 2: Bật Backend API (Agent Orchestrator)
Khởi động máy chủ định tuyến Agent. Backend đã được cấu hình để tự động đọc dữ liệu từ thư mục `chroma_db` vừa tạo ở Bước 1.
```bash
cd day10/web_app/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Bước 3: Bật Giao diện Frontend (Web UI)
Mở một terminal mới và khởi động giao diện người dùng để tương tác.
```bash
cd day10/web_app/frontend
npm install
npm run dev
```

Sau khi hoàn tất, bạn có thể truy cập `http://localhost:5173` trên trình duyệt và đặt câu hỏi cho AI (ví dụ: *"Theo quy định mới năm 2026, nhân viên được nghỉ phép bao nhiêu ngày?"*). Hệ thống sẽ ngay lập tức truy vấn RAG qua ChromaDB và trả về kết quả chuẩn xác.
