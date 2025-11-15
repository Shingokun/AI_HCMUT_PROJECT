"""
Module xử lý và làm sạch văn bản.
Cung cấp các hàm tiền xử lý văn bản cho POS tagging và NER.
"""
import re
import unicodedata


def clean_text_preserve_case(text):
    """
    Làm sạch văn bản nhưng giữ nguyên chữ hoa/thường (dùng cho NER).
    
    Args:
        text (str): Văn bản gốc cần làm sạch
    
    Returns:
        str: Văn bản đã được làm sạch
    """
    # 1. Unicode normalize
    text = unicodedata.normalize("NFC", text)
    
    # 2. Loại bỏ ký tự vô hình
    text = text.replace('\u00ad', '')   # soft hyphen
    text = text.replace('\u200b', '')   # zero-width space
    text = text.replace('\ufeff', '')   # BOM
    
    # 3. Ghép các từ bị cắt ở cuối dòng
    text = re.sub(r'-\s*\r?\n\s*', '', text)
    
    # 4. Thay thế xuống dòng bằng dấu cách
    text = re.sub(r'[\r\n]+', ' ', text)
    
    # 5. Xóa khoảng trắng thừa
    text = re.sub(r'[ \t]+', ' ', text).strip()

    # 6. Chuẩn hóa khoảng trắng quanh dấu câu
    # Xóa khoảng trắng trước dấu phẩy, chấm, chấm phẩy, hai chấm
    text = re.sub(r'\s+([,.;:])', r'\1', text)
    # Đảm bảo có một khoảng trắng sau dấu câu (nếu chưa có)
    text = re.sub(r'([,.;:])(?!\s)', r'\1 ', text)
    
    # 7. Xóa khoảng trắng thừa một lần nữa
    text = re.sub(r'[ \t]+', ' ', text).strip()
    
    return text


def clean_text_lowercase(text):
    """
    Làm sạch văn bản và chuyển về chữ thường (dùng cho POS tagging).
    
    Args:
        text (str): Văn bản gốc cần làm sạch
    
    Returns:
        str: Văn bản đã được làm sạch và lowercase
    """
    # Bước 1: Làm sạch giữ nguyên case
    text = clean_text_preserve_case(text)
    
    # Bước 2: Sửa các lỗi dính chữ phổ biến
    fixes = {
        'đềcương': 'đề cương',
        'hệthống': 'hệ thống',
        'đềtài': 'đề tài',
        'ngữlớn': 'ngữ lớn',
        'sẽgồm': 'sẽ gồm',
        'vấnđềvà': 'vấn đề và',
        'kếhoạch': 'kế hoạch',
        'dựkiến': 'dự kiến',
    }
    for wrong, right in fixes.items():
        text = re.sub(r'\b' + re.escape(wrong) + r'\b', right, text, flags=re.IGNORECASE)
    
    # Bước 3: Xóa khoảng trắng thừa lần nữa
    text = re.sub(r' {2,}', ' ', text)
    
    # Bước 4: Chuyển về lowercase
    return text.lower()
