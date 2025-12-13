import re

DATE_REGEX = re.compile(r"\b\d{2}/\d{2}/\d{4}\b")
DECISION_NO_REGEX = re.compile(r"\b\d+/\w+-\w+\b", re.IGNORECASE)

REQUIRED_FIELDS = [
    "so_quyet_dinh",
    "ngay_ban_hanh",
    "co_quan_ban_hanh",
    "nguoi_ky",
    "chuc_danh_nguoi_ky",
    "title",
    "scope_of_application",
    "effective_date_details",
    "main_content_summary"
]

DEFAULT_VALUES = {
    "nguoi_ky": "Không rõ",
    "chuc_danh_nguoi_ky": "Không rõ"
}