import os
import json
import time
import re
import random
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# --- 1. CẤU HÌNH API KEY ---
# Đảm bảo bạn đã cài đặt biến môi trường GEMINI_API_KEY
api_key = os.environ.get("GEMINI_API_KEY")

def run_gemini(text_content):
    """
    Hàm thực thi Gemini để trích xuất thông tin từ văn bản.
    Args:
        text_content (str): Nội dung văn bản cần trích xuất.
    Returns:
        dict: Kết quả trích xuất dưới dạng JSON.
    """
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        print("LỖI: GEMINI_API_KEY chưa được cấu hình đúng.")
        print("Vui lòng mở file .env và thay thế 'YOUR_API_KEY_HERE' bằng API Key thực của bạn.")
        return None

    try:
        client = genai.Client(api_key=api_key)
    except Exception as e:
        print(f"LỖI: Không thể khởi tạo Gemini Client: {e}")
        return None

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
                description="Ngày, tháng, năm ban hành Quyết định, định dạng DD/MM/YYYY. Lưu ý: Nếu OCR bị lỗi (ví dụ 'tháng ionăm'), hãy suy luận ngày hợp lý dựa trên các văn bản căn cứ (ngày ban hành phải sau ngày của các văn bản căn cứ)."
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
    
    LƯU Ý QUAN TRỌNG VỀ XỬ LÝ LỖI OCR:
    1. Ngày tháng: Văn bản đầu vào là kết quả OCR nên có thể bị lỗi (ví dụ: "tháng ionăm" thường là "tháng 10 năm", "tháng 0i" là "tháng 01"). 
       - Hãy kiểm tra logic thời gian: Ngày ban hành quyết định PHẢI SAU ngày của các văn bản pháp luật được trích dẫn trong phần "Căn cứ".
       - Ví dụ: Nếu căn cứ Nghị định ngày 26/02/2025, thì ngày ban hành quyết định KHÔNG THỂ là tháng 01/2025. Hãy sửa lại cho hợp lý (ví dụ 03/10/2025).
    2. Người ký: Nếu không tìm thấy tên người ký rõ ràng, hãy để "Không rõ".

    Văn bản:
    ---
    {text_content}
    ---
    """

    config = types.GenerateContentConfig(
        # Bắt buộc mô hình trả về JSON theo schema đã định nghĩa
        response_mime_type="application/json",
        response_schema=extraction_schema,
    )

    # --- 5. GỌI API GEMINI ---
    print("Đang gọi API Gemini để trích xuất thông tin...")
    
    # Danh sách các model để thử (ưu tiên model nhanh/rẻ trước)
    # Dựa trên danh sách model khả dụng: gemini-2.5-flash, gemini-2.0-flash, gemini-2.0-flash-lite, etc.
    models_to_try = [
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite',
        'gemini-2.5-flash',
        'gemini-2.5-pro',
        'gemini-flash-latest',
        'gemini-pro-latest'
    ]
    
    max_retries_per_model = 3
    base_delay = 2

    for model_name in models_to_try:
        print(f"Trying model: {model_name}")
        for attempt in range(max_retries_per_model):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )
                
                # --- 6. XỬ LÝ KẾT QUẢ ---
                # Đầu ra sẽ là một chuỗi JSON hợp lệ
                json_output = response.text.strip()
                parsed_data = json.loads(json_output)
                return parsed_data

            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    print(f"LỖI: Quota exceeded (429) for {model_name}. Attempt {attempt + 1}/{max_retries_per_model}")
                    
                    # If it's the last attempt for this model, break to try next model
                    if attempt == max_retries_per_model - 1:
                        print(f"Switching to next model after {max_retries_per_model} failed attempts...")
                        break

                    # Try to extract retry delay from error message
                    retry_match = re.search(r"Please retry in (\d+(\.\d+)?)s", error_str)
                    
                    if retry_match:
                        wait_time = float(retry_match.group(1)) + 1.0 # Add 1s buffer
                        print(f"Waiting for {wait_time:.2f} seconds as requested by API...")
                        time.sleep(wait_time)
                    else:
                        # Exponential backoff
                        wait_time = (base_delay * (2 ** attempt)) + random.uniform(0, 1)
                        print(f"Waiting for {wait_time:.2f} seconds (exponential backoff)...")
                        time.sleep(wait_time)
                    
                    continue
                else:
                    print(f"\\nLỖI khi gọi API với model {model_name}: {e}")
                    # Nếu lỗi không phải 429 (ví dụ 404 Not Found, 400 Bad Request), 
                    # chúng ta nên thử model tiếp theo trong danh sách thay vì dừng hẳn.
                    print(f"Switching to next model due to error...")
                    break # Break inner loop to go to next model
    
    print(f"\\nLỖI: Đã thử tất cả các models {models_to_try} nhưng đều thất bại.")
    return None

if __name__ == "__main__":
    input_file_from_module1 = "processed_document.txt"
    # Đọc file nếu chạy trực tiếp
    try:
        with open(input_file_from_module1, "r", encoding="utf-8") as f:
            content = f.read()
            result = run_gemini(content)
            if result:
                print(json.dumps(result, indent=4, ensure_ascii=False))
    except FileNotFoundError:
        print(f"Không tìm thấy file {input_file_from_module1}")