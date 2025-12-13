# Module 4: Validation & Post-processing (Kiểm tra & Hậu xử lý)

Sau khi LLM trả về kết quả, chúng ta không thể tin tưởng tuyệt đối 100%. Module 4 đóng vai trò là "người gác cổng" (Gatekeeper) để đảm bảo dữ liệu sạch, đúng định dạng và hợp lý trước khi xuất ra.

## 🎯 Mục tiêu
1.  **Chuẩn hóa (Normalize)**: Đưa dữ liệu về định dạng thống nhất (ví dụ: Ngày tháng luôn là DD/MM/YYYY).
2.  **Gán mặc định (Defaulting)**: Điền các giá trị thay thế nếu LLM bỏ sót trường bắt buộc.
3.  **Kiểm tra (Validate)**: Phát hiện các bất thường (số hiệu sai format, ngày tháng vô lý) để cảnh báo người dùng.

## ⚙️ Các quy tắc xử lý (Rules)

### 1. Quy tắc Chuẩn hóa (`normalizer.py`)

| Trường dữ liệu | Input (từ LLM) | Output (Sau chuẩn hóa) | Logic |
| :--- | :--- | :--- | :--- |
| **Tên người** | `nguyễn văn a` | `Nguyễn Văn A` | Title Case (Viết hoa chữ cái đầu). |
| **Ngày tháng** | `2025-10-03` | `03/10/2025` | Chuyển ISO sang DD/MM/YYYY. |
| **Ngày tháng** | `3/10/2025` | `03/10/2025` | Thêm padding số 0 (Zero-padding). |
| **Ngày tháng** | `ngày 03 tháng 10...` | `03/10/2025` | Parse chuỗi tiếng Việt. |

### 2. Quy tắc Kiểm tra (`validator.py`)

Hệ thống kiểm tra dựa trên danh sách `REQUIRED_FIELDS` và các Regex Pattern.

*   **Lỗi (Errors)**: Những sai sót nghiêm trọng khiến dữ liệu không thể sử dụng.
    *   Thiếu trường bắt buộc (`so_quyet_dinh`, `ngay_ban_hanh`...).
    *   Ngày tháng sai định dạng hoàn toàn (không thể parse).
*   **Cảnh báo (Warnings)**: Những điểm đáng ngờ nhưng vẫn có thể chấp nhận.
    *   Số quyết định có định dạng lạ (không khớp pattern `\d+/[A-ZĐƯ-]+`).

### 3. Giá trị mặc định (`rules.py`)

Nếu LLM trả về `null` hoặc chuỗi rỗng cho các trường không quá quan trọng, hệ thống sẽ điền:
*   `nguoi_ky`: "Không rõ"
*   `chuc_danh_nguoi_ky`: "Không rõ"

## 📝 Ví dụ Input/Output

**Input (từ Module 3):**
```json
{
    "so_quyet_dinh": "123/QD-BGDDT",
    "ngay_ban_hanh": "2025-2-26",
    "nguoi_ky": "nguyễn kim sơn",
    "chuc_danh_nguoi_ky": null
}
```

**Output (từ Module 4):**
```json
{
    "data": {
        "so_quyet_dinh": "123/QD-BGDDT",
        "ngay_ban_hanh": "26/02/2025",  // Đã chuẩn hóa
        "nguoi_ky": "Nguyễn Kim Sơn",   // Đã viết hoa
        "chuc_danh_nguoi_ky": "Không rõ" // Gán mặc định
    },
    "errors": [],
    "warnings": [],
    "is_valid": true
}
```
