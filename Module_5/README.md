# Module 5: Result Export (Xuất kết quả)

Module cuối cùng của pipeline, chịu trách nhiệm trình bày dữ liệu đã xử lý thành định dạng thân thiện với người đọc và lưu trữ lâu dài.

## 🎯 Mục tiêu
1.  **Trình bày đẹp**: Chuyển đổi JSON khô khan thành văn bản có cấu trúc, dễ đọc.
2.  **Việt hóa**: Hiển thị tên các trường dữ liệu bằng tiếng Việt.
3.  **Lưu trữ**: Tự động quản lý thư mục đầu ra và đặt tên file.

## ⚙️ Cấu trúc File đầu ra (.txt)

File kết quả được chia làm 2 phần chính, ngăn cách rõ ràng:

### Phần 1: Kết quả trích xuất
Chứa thông tin nghiệp vụ của văn bản.
*   Các trường ngắn (Số hiệu, Ngày, Người ký...) được in trên 1 dòng.
*   Các trường dài (Trích yếu, Tóm tắt, Nơi nhận...) được in tách dòng và có đường kẻ phân cách `---` để dễ nhìn.

### Phần 2: Trạng thái kiểm tra
Chứa thông tin kỹ thuật về độ tin cậy của dữ liệu.
*   **Hợp lệ**: CÓ/KHÔNG.
*   **Lỗi/Cảnh báo**: Liệt kê chi tiết nếu có (giúp người dùng biết cần kiểm tra lại phần nào).

## 📝 Logic hoạt động (`exporter.py`)

### Mapping Nhãn (Label Mapping)
Module sử dụng một từ điển để dịch key tiếng Anh sang tiếng Việt:

```python
labels = {
    "so_quyet_dinh": "Số Quyết định",
    "ngay_ban_hanh": "Ngày ban hành",
    "co_quan_ban_hanh": "Cơ quan ban hành",
    "title": "Trích yếu",
    # ...
}
```

### Xử lý tên file
*   Đầu vào: `D:\Projects\AI_HCMUT_PROJECT\test\test_2.pdf`
*   Xử lý: Lấy `test_2` (basename without extension).
*   Đầu ra: `D:\Projects\AI_HCMUT_PROJECT\Result\test_2.txt`

## 📂 Thư mục kết quả
Mặc định, tất cả kết quả sẽ được lưu vào thư mục `Result/` tại thư mục gốc của dự án. Nếu thư mục này chưa tồn tại, Module 5 sẽ tự động tạo nó.
