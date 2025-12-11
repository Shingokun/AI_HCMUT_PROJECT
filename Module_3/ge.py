import os
import json
from google import genai
from google.genai import types

# --- 1. CẤU HÌNH API KEY ---
# Đảm bảo bạn đã cài đặt biến môi trường GEMINI_API_KEY
# Nếu không, bạn có thể thiết lập trực tiếp ở đây, nhưng KHÔNG KHUYẾN KHÍCH TRONG MÔI TRƯỜNG SẢN XUẤT.
api_key = "api_key"
# client = genai.Client(api_key=api_key)

# Lấy API Key từ biến môi trường (Khuyến nghị)
try:
    client = genai.Client(api_key=api_key)
except Exception as e:
    print("LỖI: Không tìm thấy GEMINI_API_KEY hoặc xảy ra lỗi kết nối.")
    print("Vui lòng đảm bảo biến môi trường GEMINI_API_KEY đã được thiết lập.")
    exit()

# --- 2. DỮ LIỆU ĐẦU VÀO (Văn bản hành chính mẫu) ---
input_file_from_module1 = "processed_document.txt"

# --- 3. ĐỊNH NGHĨA CẤU TRÚC ĐẦU RA (SCHEMA) ---
# Sử dụng Pydantic hoặc genai.types.Schema để định nghĩa cấu trúc JSON mong muốn
extraction_schema = types.Schema(
    type=types.Type.OBJECT,
    properties={
        "so_quyet_dinh": types.Schema(
            type=types.Type.STRING,
            description="Số hiệu chính thức của Quyết định, ví dụ: 123/QĐ-BTC"
        ),
        "ngay_ban_hanh": types.Schema(
            type=types.Type.STRING,
            description="Ngày, tháng, năm ban hành Quyết định, định dạng DD/MM/YYYY"
        ),
        "co_quan_ban_hanh": types.Schema(
            type=types.Type.STRING,
            description="Tên cơ quan hoặc tổ chức ban hành, ví dụ: BỘ TÀI CHÍNH"
        ),
        "nguoi_ky": types.Schema(
            type=types.Type.STRING,
            description="Tên người ký Quyết định, ví dụ: Nguyễn Văn A"
        ),
        "chuc_danh_nguoi_ky": types.Schema(
            type=types.Type.STRING,
            description="Chức danh của người ký, ví dụ: THỨ TRƯỞNG"
        ),
        "title": types.Schema(
            type=types.Type.STRING,
            description="Tiêu đề (Trích yếu nội dung), ví dụ: Quyết định Về việc công bố thủ tục hành chính nội bộ được chuẩn hóa thuộc phạm vi, chức năng quản lý của Bộ Giáo dục và Đào tạo"
        ),
        "scope_of_application": types.Schema(
            type=types.Type.STRING,
            description="""Phạm vi áp dụng/Chịu trách nhiệm thi hành (Nơi nhận/Điều 3), ví dụ:
            \"Chánh Văn phòng\",
            \"Thủ trưởng các đơn vị liên quan thuphòng\",
            \"các tổ chức, cá nhân có liênphòng\",
            \"Bộ trưởng (đểphòng\",
            \"Văn phòng Chính phủ (Cục Kiểm soát phòng\",
            \"Các đơn vị thuphòng\",
            \"UBND các tỉnh, TP trực thuphòng\",
            \"Các Sở Giáo dục và Đàphòng\",
            \"Cổng thông tin điện tử Bộ phòng\",
            \"Thủ trưởng các đơn vị liên quan thuphòng\",
            \"các tổ chức, cá nhân có liênphòng\",
            \"Bộ trưởng (đểphòng\",
            \"Văn phòng Chính phủ (Cục Kiểm soát phòng\",
            \"Các đơn vị thuphòng\",
            \"UBND các tỉnh, TP trực thuphòng\",
            \"Các Sở Giáo dục và Đàphòng\",
            \"Cổng thông tin điện tử Bộ GDĐT\"
            """
        ),
        "effective_date_details": types.Schema(
            type=types.Type.STRING,
            description=" Hiệu lực (Thông tin chi tiết về hiệu lực), ví dụ:có hiệu lực thi hành kể từ ngày ký."
        ),
        "main_content_summary": types.Schema(
            type=types.Type.STRING,
            description="Nội dung chính (Tóm tắt các Điều), ví dụ:Công bố kèm theo Quyết định này thủ tục hành chính nội bộ được chuẩn hóa. Quyết định bãi bỏ các nội dung liên quan đến thủ tục hành chính nội bộ đã được công bố tại các Quyết định số 2344/QĐ-BGDDT, 1766/QĐ-BGDĐT, 1195/QĐ-BGDĐT, 1280/QĐ-BGDĐT, 1284/QĐ-BGDĐT và 1709/QĐ-BGDĐT."
        ),
        
    },
    required=[
        "so_quyet_dinh", 
        "ngay_ban_hanh", 
        "co_quan_ban_hanh", 
        "nguoi_ky", 
        "chuc_danh_nguoi_ky","title", 
        "scope_of_application", 
        "effective_date_details", 
        "main_content_summary"],
)

# --- 4. TẠO PROMPT VÀ THIẾT LẬP CẤU TRÚC ĐẦU RA ---
prompt = f"""
Bạn là chuyên gia trích xuất dữ liệu từ văn bản hành chính Việt Nam.
Hãy trích xuất các thông tin cần thiết từ văn bản sau và trả về kết quả chính xác theo định dạng JSON đã được định nghĩa.
Văn bản:
---
{input_file_from_module1}
---
"""

config = types.GenerateContentConfig(
    # Bắt buộc mô hình trả về JSON theo schema đã định nghĩa
    response_mime_type="application/json",
    response_schema=extraction_schema,
)

# --- 5. GỌI API GEMINI ---
print("Đang gọi API Gemini để trích xuất thông tin...")
try:
    response = client.models.generate_content(
        model='gemini-2.5-flash', # Mô hình nhanh và hiệu quả cho trích xuất
        contents=prompt,
        config=config,
    )
    
    # --- 6. XỬ LÝ KẾT QUẢ ---
    # Đầu ra sẽ là một chuỗi JSON hợp lệ
    json_output = response.text.strip()
    
    print("\n✅ Trích xuất thành công! Dữ liệu JSON:")
    print("-" * 30)
    # Định dạng lại JSON cho dễ đọc
    parsed_data = json.loads(json_output)
    print(json.dumps(parsed_data, indent=4, ensure_ascii=False))

    # Ví dụ truy cập dữ liệu đã trích xuất
    print("\n[Kiểm tra Dữ liệu Trích xuất]")
    print(f"Số Quyết định: {parsed_data.get('so_quyet_dinh')}")
    print(f"Người Ký: {parsed_data.get('nguoi_ky')} ({parsed_data.get('chuc_danh_nguoi_ky')})")

except Exception as e:
    print(f"\nLỖI khi gọi API: {e}")