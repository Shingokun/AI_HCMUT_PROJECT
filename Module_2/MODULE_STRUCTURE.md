# Module 2: Feature Extraction - Cấu trúc Module

## 📁 Core Modules (Production)

### 1. **main.py** (Entry Point)
- Điểm vào chính của Module 2
- Menu 6 lựa chọn:
  - [1] POS Tagging
  - [2] Hybrid NER (Statistical + Rule-based)
  - [3] Dependency Parsing
  - [4] Hybrid NER Pipeline (chi tiết)
  - [5] Export JSON only
  - [6] Chạy tất cả + Export JSON
- Orchestrates tất cả modules con

### 2. **analyzer.py** (Document Analyzer)
- Wrapper class chính
- Tích hợp: POS Tagger + Hybrid NER
- Methods:
  - `analyze_pos()` - POS tagging
  - `analyze_ner()` - Hybrid NER (underthesea + EntityRuler)
  - `analyze_full()` - Phân tích toàn diện

### 3. **hybrid_ner.py** (Hybrid NER Pipeline)
- **Luồng A**: Statistical NER với `underthesea.ner()`
- **Luồng B**: Rule-based với spaCy EntityRuler
- **Merging Layer**: Conflict resolution với "Rules-First"
- Entities:
  - Rule-based: `DECISION_ID`, `ISSUE_DATE`
  - Statistical: `PER`, `ORG`, `LOC` (từ underthesea)

### 4. **pos_tagger.py** (POS Tagger)
- POS tagging với spaCy
- Áp dụng correction rules từ `corrections.json`
- Xử lý lowercase text

### 5. **syntax_parsing.py** (Dependency Parser)
- Phân tích cú pháp phụ thuộc
- Tạo visualization HTML với displaCy
- Export: `dependency_parse.html`

### 6. **json_serializer.py** (JSON Exporter)
- Serialize toàn bộ phân tích thành JSON
- Cấu trúc output:
  ```json
  {
    "metadata": {...},
    "raw_text": "...",
    "entities": [...],        // Merged (rule-based + statistical)
    "pos_tagging": [...],
    "dependency_parsing": [...],
    "tokens_detail": [...]
  }
  ```
- Output: `Output/module_2_output.json`

### 7. **pdf_extractor.py** (PDF Extractor)
- Trích xuất text từ PDF
- Dùng thư viện `PyPDF2`

### 8. **text_cleaner.py** (Text Preprocessor)
- `clean_text_preserve_case()` - Cho NER (giữ chữ hoa)
- `clean_text_lowercase()` - Cho POS (lowercase)
- Unicode normalization, khoảng trắng cleanup

### 9. **corrections.json** (Data File)
- Quy tắc sửa lỗi POS tags
- Format: `{"wrong_tag": "correct_tag"}`

---

## 🗑️ Files đã XÓA (không còn dùng)

### ❌ `ner_extractor.py` (DELETED)
- **Lý do**: Không tuân theo báo cáo kỹ thuật
- **Thay thế bằng**: `hybrid_ner.py` (underthesea + EntityRuler)
- **Đã xóa**: 2025-11-14

### ❌ `dependency_parse.html` (Auto-generated output)
- File output tự động tạo, không phải source code

---

## 🔄 Workflow

```
PDF File
  ↓
[pdf_extractor.py] → Raw Text
  ↓
[text_cleaner.py] → Cleaned Text
  ↓
[analyzer.py] orchestrates:
  ├─ [pos_tagger.py] → POS Tags
  ├─ [hybrid_ner.py] → Entities (DECISION_ID, ISSUE_DATE, PER, ORG, LOC)
  └─ [syntax_parsing.py] → Dependency Tree
  ↓
[json_serializer.py] → JSON Output
  ↓
Output/module_2_output.json (Ready for Module 3 - LLM)
```

---

## 🎯 Theo Báo cáo Kỹ thuật

Module 2 triển khai đúng **Hybrid Architecture**:

1. ✅ **Luồng A** (Statistical): `underthesea.ner()`
2. ✅ **Luồng B** (Rule-based): spaCy EntityRuler với Regex patterns
3. ✅ **Merging Layer**: "Rules-First Overwrite" conflict resolution
4. ✅ **JSON Output**: Rich structure với token-level annotations

---

## 📦 Dependencies

```
spacy==3.6.1
underthesea==8.3.0
PyPDF2
```

## 🚀 Usage

```bash
# Activate venv
.\.env\Scripts\Activate.ps1

# Run
python main.py
```
