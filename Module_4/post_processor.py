from .validator import validate_fields
from .normalizer import normalize_data
from .rules import DEFAULT_VALUES

def run_module_4(llm_output: dict):
    """
    Input: dict từ Module 3
    Output: dict đã kiểm tra & chuẩn hóa
    """
    if not llm_output:
        return {
            "data": {},
            "errors": ["LLM không trả về dữ liệu"],
            "warnings": []
        }

    # 1. Normalize
    normalized_data = normalize_data(llm_output)

    # 2. Default values
    for k, v in DEFAULT_VALUES.items():
        if k not in normalized_data or not normalized_data[k]:
            normalized_data[k] = v

    # 3. Validate
    errors, warnings = validate_fields(normalized_data)

    return {
        "data": normalized_data,
        "errors": errors,
        "warnings": warnings,
        "is_valid": len(errors) == 0
    }