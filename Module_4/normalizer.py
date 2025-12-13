from datetime import datetime
import re

def normalize_name(name: str):
    return " ".join(w.capitalize() for w in name.split())

def normalize_date(date_str: str):
    date_str = date_str.strip()

    # Trường hợp đã đúng chuẩn DD/MM/YYYY → giữ nguyên
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", date_str):
        return date_str

    # Trường hợp thiếu padding: 1/1/2025 → 01/01/2025
    try:
        d = datetime.strptime(date_str, "%d/%m/%Y")
        return d.strftime("%d/%m/%Y")
    except:
        pass

    # Trường hợp ISO: 2025-10-14 → 14/10/2025
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%d/%m/%Y")
    except:
        return date_str  # giữ nguyên nếu không parse được

def normalize_data(data: dict):
    normalized = data.copy()

    if "nguoi_ky" in normalized and normalized["nguoi_ky"]:
        normalized["nguoi_ky"] = normalize_name(normalized["nguoi_ky"])

    if "ngay_ban_hanh" in normalized and normalized["ngay_ban_hanh"]:
        normalized["ngay_ban_hanh"] = normalize_date(normalized["ngay_ban_hanh"])

    return normalized