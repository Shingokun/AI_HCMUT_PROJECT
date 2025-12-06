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
van_ban_mau = """
BỘ GIÁO DỤC VÀ ĐÀO TẠO CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM 
Số: 2827 /QĐ-BGDĐT 
Độc lập - Tự do - Hạnh phúc 
Hà Nội, ngày 14 tháng 10 năm 2025 
QUYẾT ĐỊNH 
Về việc công bố thủ tục hành chính nội bộ được chuẩn hóa thuộc phạm vi, chức năng quản lý của Bộ Giáo dục và Đào tạo 
BỘ TRƯỞNG BỘ GIÁO DỤC VÀ ĐÀO TẠO 
Căn cứ Nghị định số 37/2025/NĐ-CP ngày 26/02/2025 của Chính phủ quy định chức năng, nhiệm vụ, quyền hạn và cơ cấu tổ chức của Bộ Giáo dục và Đào tạo; 
Căn cứ Quyết định số 240/QĐ-TTg ngày 04/02/2025 của Thủ tướng Chính phủ ban hành Kế hoạch thực hiện cải cách thủ tục hành chính trọng tâm năm 2025; Căn cứ Nghị quyết số 66/NQ-CP ngày 26/3/2025 của Chính phủ về Chương trình cắt giảm, đơn giản hóa thủ tục hành chính liên quan đến hoạt động sản xuất, kinh doanh năm 2025 và 2026; 
Theo đề nghị của Chánh Văn phòng. 
QUYẾT ĐỊNH: 
Điều 1. Công bố kèm theo Quyết định này thủ tục hành chính nội bộ dược chuẩn hóa thuộc phạm vi, chức năng quản lý của Bộ Giáo dục và Đào tạo. 
Điều 2. Quyết định này có hiệu lực thi hành kể từ ngày ký. 
Bãi bỏ các nội dung liên quan đến thủ tục hành chính nội bộ tại Quyết định này đã được công bố tại các Quyết định: 
- Quyết định số 2344/QĐ-BGDDT ngày 14/8/2023 của Bộ trưởng Bộ Giáo dục và Đào tạo về việc công bố thủ tục hành chính nội bộ giữa các cơ quan hành chính nhà nước thuộc phạm vi, chức năng quản lý của Bộ Giáo dục và Đào tạo; 
- Quyết định số 1766/QĐ-BGDĐT ngày 01/7/2024 của Bộ trưởng Bộ Giáo dục và Đào tạo về việc công bố thủ tục hành chính nội bộ mới ban hành và thủ tục hành chính được thay thế trong hệ thống hành chính nhà nước nhà nước thuộc phạm vi, chức năng quản lý của Bộ Giáo dục và Đào tạo. 
- Quyết định số 1195/QĐ-BGDĐT ngày 29/4/2025 của Bộ trưởng Bộ Giáo dục và Đào tạo về việc công bố thủ tục hành chính nội bộ trong hệ thống hành chính nhà 
2 
nước lĩnh vực giáo dục và đào tạo; kế hoạch và đầu tư; tài chính thuộc phạm vi, chức năng quản lý của Bộ Giáo dục và Đào tạo; 
- Quyết định số 1280/QĐ-BGDĐT ngày 12/5/2025 của Bộ trưởng Bộ Giáo dục và Đào tạo về việc công bố thủ tục hành chính nội bộ trong hệ thống hành chính nhà nước lĩnh vực chế độ, chính sách đối với nhà giáo thuộc phạm vi, chức năng quản lý của Bộ Giáo dục và Đào tạo. 
- Quyết định số 1284/QĐ-BGDĐT ngày 13/5/2025 của Bộ trưởng Bộ Giáo dục và Đào tạo về việc công bố thủ tục hành chính nội bộ trong hệ thống hành chính nhà nước lĩnh vực giáo dục nghề nghiệp thuộc phạm vi, chức năng quản lý của Bộ Giáo dục và Đào tạo; 
- Quyết định số 1709/QĐ-BGDĐT ngày 27/6/2025 của Bộ trưởng Bộ Giáo dục và Đào tạo về việc công bố thủ tục hành chính nội bộ mới ban hành và thủ tục hành chính nội bộ được sửa đổi, bổ sung hoặc thay thế thuộc phạm vi, chức năng quản lý của Bộ Giáo dục và Đào tạo. 
Điều 3. Chánh Văn phòng, Thủ trưởng các đơn vị liên quan thuộc Bộ và các tổ chức, cá nhân có liên quan chịu trách nhiệm thi hành Quyết định này./. 
Nơi nhận: 
- Như Điều 3; 
- Bộ trưởng (để b/c); 
- Văn phòng Chính phủ (Cục Kiểm soát TTHC); 
- Các đơn vị thuộc Bộ; 
- UBND các tỉnh, TP trực thuộc TW; 
- Các Sở Giáo dục và Đào tạo; 
- Cổng thông tin điện tử Bộ GDĐT; 
- Luru: VT, VP (KSTTHC). 



KT. BỘ TRƯỞNG THỨ TRƯỞNG 

Lê Tấn Dũng 

"""

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
{van_ban_mau}
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