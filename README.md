# AI_HCMUT_PROJECT: Hệ thống Trích xuất Thông tin Văn bản Hành chính

Dự án này là một pipeline xử lý văn bản tự động, chuyên dùng để trích xuất thông tin có cấu trúc từ các văn bản hành chính Việt Nam (Quyết định, Thông tư, Nghị định...). Hệ thống kết hợp giữa OCR, NLP truyền thống và LLM hiện đại.

## 🚀 Tổng quan Kiến trúc

Hệ thống hoạt động theo mô hình Pipeline tuần tự gồm 5 Module:

1.  **Module 1 (Preprocessing & OCR)**: Đọc file (PDF/Image), nhận dạng chữ (OCR) và làm sạch văn bản.
2.  **Module 2 (NLP Analysis)**: Phân tích ngôn ngữ (POS Tagging, NER, Dependency Parsing) để trích xuất đặc trưng.
3.  **Module 3 (LLM Extraction)**: Sử dụng Google Gemini để "đọc hiểu" và trích xuất thông tin chi tiết theo cấu trúc JSON.
4.  **Module 4 (Validation)**: Chuẩn hóa dữ liệu và kiểm tra tính hợp lệ (Logic ngày tháng, định dạng số hiệu...).
5.  **Module 5 (Export)**: Xuất kết quả cuối cùng ra file văn bản (.txt).

## 🛠 Yêu cầu hệ thống

*   **Python**: 3.10 trở lên
*   **Thư viện chính**:
    *   `google-genai`, `python-dotenv` (LLM)
    *   `spacy`, `underthesea` (NLP)
    *   `easyocr`, `pymupdf`, `pdf2image` (OCR)
*   **API Key**: Google Gemini API Key.

## 📦 Cài đặt

1.  **Clone dự án**:
    ```bash
    git clone <repo_url>
    cd AI_HCMUT_PROJECT
    ```

2.  **Cài đặt dependencies**:
    ```bash
    pip install -r requirements.txt
    # (Nếu chưa có requirements.txt, hãy cài các thư viện liệt kê ở trên)
    ```

3.  **Cấu hình môi trường**:
    *   Tạo file `.env` tại thư mục gốc.
    *   Thêm API Key của bạn vào:
        ```properties
        GEMINI_API_KEY=AIzaSy...
        ```

4.  **Cài đặt Model NLP (Optional nhưng khuyến nghị)**:
    ```bash
    python -m spacy download vi_core_news_lg
    # Nếu không cài được, hệ thống sẽ tự động dùng chế độ fallback.
    ```

## ▶️ Cách chạy chương trình

Sử dụng script `pipeline.py` để chạy toàn bộ quy trình:

```bash
# Chạy với file cụ thể
python pipeline.py test/test_2.pdf

# Hoặc chạy không tham số để chọn file từ menu
python pipeline.py
```

## 📂 Cấu trúc thư mục

```
AI_HCMUT_PROJECT/
├── Module_1/           # OCR & Preprocessing
├── Module_2/           # NLP Analysis
├── Module_3/           # LLM Extraction (Gemini)
├── Module_4/           # Validation & Post-processing
├── Module_5/           # Result Export
├── test/               # Thư mục chứa file test đầu vào
├── Result/             # Thư mục chứa kết quả đầu ra (.txt)
├── pipeline.py         # Script chính điều phối toàn bộ hệ thống
├── .env                # File cấu hình API Key
└── README.md           # Tài liệu hướng dẫn này
```

## 📊 Kết quả đầu ra

Kết quả sẽ được lưu trong thư mục `Result/` dưới dạng file `.txt` với cấu trúc dễ đọc, bao gồm:
*   Số hiệu văn bản
*   Ngày ban hành
*   Cơ quan ban hành
*   Người ký & Chức danh
*   Trích yếu & Tóm tắt nội dung
*   Trạng thái kiểm tra (Hợp lệ/Lỗi)
