import os
import json

def format_output(data):
    """Formats the dictionary data into a readable string."""
    lines = []
    lines.append("=== KẾT QUẢ TRÍCH XUẤT VĂN BẢN ===")
    lines.append("")
    
    extracted_data = data.get("data", {})
    
    # Define a mapping for readable labels
    labels = {
        "so_quyet_dinh": "Số Quyết định",
        "ngay_ban_hanh": "Ngày ban hành",
        "co_quan_ban_hanh": "Cơ quan ban hành",
        "nguoi_ky": "Người ký",
        "chuc_danh_nguoi_ky": "Chức danh",
        "title": "Trích yếu",
        "scope_of_application": "Phạm vi áp dụng / Nơi nhận",
        "effective_date_details": "Hiệu lực thi hành",
        "main_content_summary": "Tóm tắt nội dung"
    }

    for key, label in labels.items():
        value = extracted_data.get(key, "N/A")
        # Handle multi-line values for better readability
        if isinstance(value, str) and len(value) > 100:
             lines.append(f"{label}:")
             lines.append(f"{value}")
             lines.append("-" * 20)
        else:
            lines.append(f"{label}: {value}")
    
    lines.append("")
    lines.append("=== TRẠNG THÁI KIỂM TRA ===")
    lines.append(f"Hợp lệ: {'CÓ' if data.get('is_valid', False) else 'KHÔNG'}")
    
    errors = data.get("errors", [])
    if errors:
        lines.append("\n[LỖI]:")
        for err in errors:
            lines.append(f"- {err}")
            
    warnings = data.get("warnings", [])
    if warnings:
        lines.append("\n[CẢNH BÁO]:")
        for warn in warnings:
            lines.append(f"- {warn}")

    return "\n".join(lines)

def export_result(data, input_file_path, output_dir="Result"):
    """
    Exports the data to a .txt file in the output_dir.
    The filename is based on the input_file_path.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get filename without extension
    base_name = os.path.splitext(os.path.basename(input_file_path))[0]
    output_filename = f"{base_name}.txt"
    output_path = os.path.join(output_dir, output_filename)

    content = format_output(data)

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path
    except Exception as e:
        print(f"❌ Lỗi khi xuất file kết quả: {e}")
        return None
