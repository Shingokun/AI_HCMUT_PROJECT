from .rules import REQUIRED_FIELDS, DATE_REGEX, DECISION_NO_REGEX

def validate_fields(data: dict):
    errors = []
    warnings = []

    # 1. Thiếu trường
    for field in REQUIRED_FIELDS:
        if field not in data or not str(data[field]).strip():
            errors.append(f"Thiếu hoặc rỗng trường: {field}")

    # 2. Kiểm tra số quyết định
    so_qd = data.get("so_quyet_dinh", "")
    if so_qd and not DECISION_NO_REGEX.search(so_qd):
        warnings.append(f"Số quyết định có định dạng bất thường: {so_qd}")

    # 3. Kiểm tra ngày ban hành
    ngay = data.get("ngay_ban_hanh", "")
    if ngay and not DATE_REGEX.search(ngay):
        errors.append(f"Ngày ban hành không đúng định dạng DD/MM/YYYY: {ngay}")

    return errors, warnings
