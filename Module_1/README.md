# Module 1: Preprocessing & OCR (Tiền xử lý & Nhận dạng quang học)

Module này là cửa ngõ đầu tiên của hệ thống, chịu trách nhiệm chuyển đổi các tài liệu đầu vào (PDF, DOCX, Hình ảnh) thành văn bản thô (raw text) sạch sẽ, chuẩn hóa để phục vụ cho các bước phân tích NLP và LLM phía sau.

## 🎯 Mục tiêu
1.  **Đa dạng hóa đầu vào**: Xử lý được cả file văn bản điện tử (text-based PDF, Word) và file scan (image-based PDF, ảnh).
2.  **Tối ưu hóa tốc độ**: Ưu tiên trích xuất text trực tiếp nếu có thể, chỉ dùng OCR khi cần thiết.
3.  **Làm sạch dữ liệu**: Khắc phục các lỗi phổ biến của tiếng Việt trong môi trường máy tính (lỗi font, lỗi dấu, lỗi OCR).

## 🛠 Công nghệ & Thư viện

| Thư viện | Phiên bản (Khuyên dùng) | Mục đích sử dụng |
| :--- | :--- | :--- |
| **PyMuPDF (fitz)** | `1.23.x` | Trích xuất văn bản từ PDF text-based. Tốc độ cực nhanh. |
| **EasyOCR** | `1.7.x` | Nhận dạng chữ từ ảnh (OCR). Hỗ trợ tiếng Việt tốt hơn Tesseract trong nhiều trường hợp. |
| **pdf2image** | `1.17.x` | Chuyển đổi trang PDF thành hình ảnh để đưa vào OCR. Yêu cầu cài đặt `Poppler`. |
| **python-docx** | `1.1.x` | Đọc nội dung từ file Microsoft Word (.docx). |
| **Underthesea** | `6.x` | Tách câu (Sentence Segmentation) chuẩn tiếng Việt. |

## ⚙️ Sơ đồ hoạt động (Workflow)

```mermaid
graph TD
    A[Input File] --> B{Kiểm tra định dạng}
    B -- .docx --> C[python-docx]
    B -- .txt --> D[Read File]
    B -- .pdf --> E{Kiểm tra loại PDF}
    
    E -- Text-based --> F[PyMuPDF Extract]
    E -- Image-based/Scan --> G[pdf2image -> Images]
    G --> H[EasyOCR]
    
    C --> I[Raw Text]
    D --> I
    F --> I
    H --> I
    
    I --> J[Clean & Correct]
    J --> K[Normalize Unicode NFC]
    K --> L[Fix Typos (Regex)]
    L --> M[Output: processed_document.txt]
```

## 💡 Chi tiết kỹ thuật & Giải thích Code

### 1. Chiến lược chọn phương pháp đọc PDF (`process_pdf`)
Hệ thống không mặc định dùng OCR cho mọi file PDF vì OCR chậm và tốn tài nguyên.
*   **Bước 1**: Thử đọc bằng `fitz` (PyMuPDF).
*   **Bước 2**: Kiểm tra độ dài văn bản thu được. Nếu văn bản quá ngắn (< 100 ký tự) hoặc rỗng -> Giả định đây là file scan (chỉ chứa ảnh).
*   **Bước 3**: Nếu là file scan, kích hoạt quy trình OCR (`ocr_pdf`).

```python
# Trích đoạn logic trong module1.py
text = ""
with fitz.open(file_path) as doc:
    for page in doc:
        text += page.get_text()

# Nếu text quá ít, chuyển sang OCR
if len(text.strip()) < 100:
    print("Phát hiện PDF dạng ảnh (scan), chuyển sang chế độ OCR...")
    return self.ocr_pdf(file_path)
```

### 2. Cơ chế sửa lỗi chính tả (`clean_and_correct`)
Sau khi OCR, văn bản thường dính các lỗi đặc trưng do nhầm lẫn hình dạng ký tự (ví dụ: `l` thành `1`, `o` thành `0`). Module sử dụng một từ điển `correction_map` và Regex để sửa.

*   **Chuẩn hóa Unicode**: Đưa về dạng **NFC** (Dựng sẵn) để thống nhất bảng mã.
*   **Mapping lỗi thường gặp**:
    *   `hanh phuc` -> `hạnh phúc`
    *   `1onăm` -> `10 năm` (Lỗi số 1 và chữ l, số 0 và chữ o)
    *   `q4-bgdđt` -> `qđ-bgdđt`

```python
# Ví dụ mapping
self.correction_map = {
    'hanh phuc': 'hạnh phúc',
    'kể từngày': 'kể từ ngày', # Lỗi dính chữ
    'trung ưong': 'trung ương', # Lỗi dấu
    # ...
}
```

## ⚠️ Các vấn đề thường gặp (Troubleshooting)

1.  **Lỗi `Poppler not found`**:
    *   `pdf2image` cần bộ thư viện Poppler được cài đặt trong hệ điều hành.
    *   *Windows*: Tải Poppler, giải nén và thêm thư mục `bin` vào biến môi trường PATH.
    *   *Linux*: `sudo apt-get install poppler-utils`.

2.  **OCR chạy chậm**:
    *   EasyOCR mặc định chạy trên CPU. Để nhanh hơn, hãy cài đặt PyTorch bản hỗ trợ CUDA (nếu có GPU NVIDIA) và set `use_gpu=True` khi khởi tạo.

3.  **Cảnh báo `torch`**:
    *   Nếu thấy cảnh báo về `pin_memory` hay `CUDA`, đó là do máy không có GPU. Có thể bỏ qua, module sẽ tự động chạy bằng CPU.
