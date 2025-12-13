# Module 3: LLM Extraction (Trích xuất thông tin bằng AI tạo sinh)

Đây là "trái tim" của hệ thống, nơi sử dụng sức mạnh của Mô hình Ngôn ngữ Lớn (LLM) để đọc hiểu văn bản như con người và trích xuất thông tin chính xác vào cấu trúc dữ liệu định sẵn.

## 🎯 Mục tiêu
1.  **Đọc hiểu ngữ cảnh**: Hiểu được ý nghĩa của các đoạn văn phức tạp (Trích yếu, Tóm tắt nội dung) mà Regex hay NLP truyền thống khó làm được.
2.  **Suy luận logic**: Tự động sửa lỗi OCR dựa trên ngữ cảnh (ví dụ: ngày ban hành phải sau ngày căn cứ).
3.  **Chuẩn hóa đầu ra**: Trả về dữ liệu dạng JSON tuân thủ nghiêm ngặt Schema.

## 🛠 Công nghệ & Cấu hình

*   **Model**: `gemini-2.5-flash` (Google).
    *   *Lý do chọn*: Tốc độ phản hồi cực nhanh, chi phí thấp (hoặc miễn phí), cửa sổ ngữ cảnh (context window) lớn đủ chứa toàn bộ văn bản hành chính.
*   **SDK**: `google-genai`.
*   **Output Mode**: `JSON Mode` (ép buộc model chỉ trả về JSON hợp lệ).

## ⚙️ Quy trình Prompt Engineering

Module sử dụng kỹ thuật **Few-shot Prompting** (nếu cần) và **Chain-of-Thought** ngầm định trong hướng dẫn hệ thống.

### 1. Cấu trúc Prompt
Prompt gửi đi bao gồm 3 phần chính:

1.  **Role Definition (Vai trò)**:
    > "Bạn là chuyên gia trích xuất dữ liệu từ văn bản hành chính Việt Nam."
2.  **Task Description (Nhiệm vụ)**:
    > "Hãy trích xuất các thông tin... và trả về JSON."
    > "LƯU Ý QUAN TRỌNG VỀ XỬ LÝ LỖI OCR: ..."
3.  **Input Data (Dữ liệu)**:
    > "Văn bản: [Nội dung từ Module 1/2]"

### 2. JSON Schema Definition
Chúng ta định nghĩa rõ ràng kiểu dữ liệu cho từng trường để Gemini không "sáng tạo" lung tung.

```python
# Trích đoạn gemini.py
extraction_schema = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "so_quyet_dinh": types.Schema(type=types.Type.STRING, description="Số hiệu chính thức..."),
        "ngay_ban_hanh": types.Schema(type=types.Type.STRING, description="Định dạng DD/MM/YYYY..."),
        "main_content_summary": types.Schema(type=types.Type.STRING, description="Tóm tắt nội dung chính..."),
        # ...
    },
    required=["so_quyet_dinh", "ngay_ban_hanh", ...]
)
```

## 🔒 Bảo mật & API Key

*   **Tuyệt đối không hardcode API Key** trong code.
*   Sử dụng file `.env` để lưu trữ key. File này đã được thêm vào `.gitignore` để tránh lộ lọt lên Git.

**File `.env` mẫu:**
```properties
GEMINI_API_KEY=AIzaSy...
```

## ⚠️ Xử lý lỗi (Error Handling)

Module xử lý các mã lỗi phổ biến từ Google API:
*   **400 INVALID_ARGUMENT**: Thường do API Key sai hoặc Prompt quá dài.
*   **403 PERMISSION_DENIED**: API Key bị chặn hoặc hết hạn mức.
*   **500 INTERNAL_ERROR**: Lỗi phía server Google (thử lại sau).

Nếu gặp lỗi, Module sẽ in ra thông báo chi tiết và trả về `None` để Pipeline không bị crash, cho phép người dùng kiểm tra lại cấu hình.
