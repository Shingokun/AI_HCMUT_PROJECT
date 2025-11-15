"""
Module Hybrid NER Pipeline - PHIÊN BẢN 2 CHÍNH XÁC
Triển khai đúng theo Báo cáo Kỹ thuật - Phần 4: Tầng Hợp nhất

KIẾN TRÚC:
- Luồng A (Statistical): underthesea.ner() → PER, ORG, LOC
- Luồng B (Rule-based): spaCy EntityRuler → DECISION_ID, ISSUE_DATE
- Tầng Hợp nhất: Conflict Resolution với chính sách "Rules-First Overwrite"

LOGIC XỬ LÝ XUNG ĐỘT:
1. Bắt đầu với rule_entities (Luồng B) - luôn được giữ lại
2. Với mỗi stat_entity (Luồng A):
   - Kiểm tra overlap với BẤT KỲ entity nào trong danh sách cuối cùng
   - Nếu overlap → LOẠI BỎ
   - Nếu không overlap → GIỮ LẠI
3. Overlap được định nghĩa: có ít nhất 1 ký tự chung (character-level)
"""

from underthesea import ner as underthesea_ner
from spacy.tokens import Span, Doc


def _has_overlap(span1_start, span1_end, span2_start, span2_end):
    """
    Kiểm tra xem 2 span có overlap không (character-level).
    
    Args:
        span1_start, span1_end: Character offsets của span 1
        span2_start, span2_end: Character offsets của span 2
    
    Returns:
        bool: True nếu có overlap
    
    Example:
        "Hà Nội" (112-118) và "ngày 14..." (120-145) → False (không overlap)
        "Hà Nội" (112-118) và "Nội, ngày" (115-124) → True (có overlap)
    """
    return not (span1_end <= span2_start or span2_end <= span1_start)


def _resolve_conflicts(rule_entities, stat_entities, text):
    """
    Giải quyết xung đột theo chính sách "Rules-First Overwrite".
    
    Thuật toán:
    1. Bắt đầu với danh sách rule_entities (priority cao)
    2. Với mỗi stat_ent trong stat_entities:
       - Nếu overlap với BẤT KỲ entity nào đã có → SKIP
       - Ngược lại → THÊM vào danh sách cuối cùng
    
    Args:
        rule_entities: List[dict] - Entities từ EntityRuler
        stat_entities: List[dict] - Entities từ underthesea
        text: str - Văn bản gốc
    
    Returns:
        List[dict] - Danh sách entities sau khi merge
    """
    # Bắt đầu với rule entities (luôn được giữ)
    merged = list(rule_entities)
    
    # Thử thêm từng statistical entity
    for stat_ent in stat_entities:
        has_conflict = False
        
        # Kiểm tra overlap với TOÀN BỘ entities đã có
        for existing_ent in merged:
            if _has_overlap(
                stat_ent['start'], stat_ent['end'],
                existing_ent['start'], existing_ent['end']
            ):
                has_conflict = True
                break
        
        # Chỉ thêm nếu KHÔNG có conflict
        if not has_conflict:
            merged.append(stat_ent)
    
    # Sắp xếp theo vị trí xuất hiện
    merged.sort(key=lambda x: x['start'])
    
    return merged


def _parse_underthesea_entities(underthesea_result, text):
    """
    Chuyển đổi output của underthesea sang format chuẩn.
    
    CHIẾN LƯỢC (v4 - ĐƠN GIẢN HÓA):
    1. Ghép các chunks liên tiếp có cùng entity type theo BIO tags
    2. Với mỗi entity, tìm vị trí trong text theo thứ tự xuất hiện
    3. Sử dụng search_pos để tìm tuần tự, không bỏ sót
    
    Args:
        underthesea_result: Output từ underthesea.ner()
        text: Văn bản gốc
    
    Returns:
        List[dict] - Danh sách entities
    """
    entities = []
    current_chunks = []
    current_label = None
    search_pos = 0
    
    def add_entity():
        nonlocal search_pos
        if not current_chunks:
            return
        
        # Tìm chunk đầu tiên
        first_word = current_chunks[0][0]
        start = text.find(first_word, search_pos)
        
        if start == -1:
            # Không tìm thấy từ search_pos, thử từ đầu
            start = text.find(first_word, 0)
            if start == -1:
                return
        
        # Tìm các chunks còn lại tuần tự
        pos = start
        for chunk in current_chunks:
            word = chunk[0]
            found_at = text.find(word, pos)
            if found_at != -1:
                pos = found_at + len(word)
            else:
                # Không tìm thấy chunk này, dừng lại
                break
        
        end = pos
        entity_text = text[start:end]
        
        entities.append({
            'text': entity_text,
            'label': current_label.split('-')[1],
            'start': start,
            'end': end,
            'source': 'statistical'
        })
        
        search_pos = end
    
    # Xử lý từng chunk
    for chunk in underthesea_result:
        word, ner_tag = chunk[0], chunk[3]
        
        if ner_tag.startswith('B-'):
            # Bắt đầu entity mới
            add_entity()
            current_chunks = [chunk]
            current_label = ner_tag
            
        elif ner_tag.startswith('I-'):
            if current_chunks:
                # Kiểm tra xem có cùng loại không
                cur_type = current_label.split('-')[1]
                new_type = ner_tag.split('-')[1]
                if cur_type == new_type:
                    # Cùng loại, thêm vào
                    current_chunks.append(chunk)
                else:
                    # Khác loại, kết thúc cũ và bắt đầu mới
                    add_entity()
                    current_chunks = [chunk]
                    current_label = 'B-' + new_type
            else:
                # Orphan I-tag, coi như B-tag
                current_chunks = [chunk]
                current_label = 'B-' + ner_tag.split('-')[1]
                
        else:  # O tag
            add_entity()
            current_chunks = []
            current_label = None
    
    # Xử lý entity cuối cùng
    add_entity()
    
    # Lọc nhiễu
    return _filter_noisy_entities(entities)


def _filter_noisy_entities(entities):
    """
    Lọc bỏ các thực thể nhiễu/không có giá trị từ statistical NER.
    
    QUY TẮC LỌC:
    1. Loại bỏ các từ khóa pháp lý: "QUYẾT ĐỊNH", "Điều", "Nghị định", "Nghị quyết"
    2. Loại bỏ các mã số pháp lý: "số 37/2025", "NĐ-CP", "QĐ-TTg"
    3. Loại bỏ thời gian đơn thuần: "năm 2025", "ngày"
    4. Loại bỏ chức danh đơn lẻ: "Chánh", "Thủ trưởng", "Bộ trưởng" (nếu không có tên)
    5. Loại bỏ các thực thể chứa ký tự xuống dòng (lỗi parsing)
    6. GIỮ LẠI: Tên người đầy đủ (>= 2 từ), tổ chức cụ thể, địa điểm thực sự
    
    Args:
        entities: List[dict] - Danh sách entities gốc
    
    Returns:
        List[dict] - Danh sách entities đã được lọc
    """
    # Danh sách từ khóa cần loại bỏ (case-insensitive)
    noise_keywords = {
        # Từ khóa pháp lý
        'quyết định', 'điều', 'nghị định', 'nghị quyết', 'căn cứ',
        'theo', 'về việc', 'kèm theo',
        
        # Chức danh đơn lẻ (không có tên người)
        'chánh', 'thủ trưởng', 'bộ trưởng', 'kt.', 'kt', 'thứ trưởng',
        
        # Từ chỉ thời gian
        'năm', 'ngày', 'tháng',
        
        # Từ khóa khác
        'như điều', 'nơi nhận', 'cục', 'văn phòng',
        
        # Thêm các từ nhiễu mới phát hiện (từ module_2_output.json)
        'kstthc', 
        ', vp',
        'vp',
        'vt'
    }
    
    # Danh sách địa danh quan trọng (cho phép ngay cả khi nhãn sai)
    important_locations = {
        'hà nội', 'tp. hồ chí minh', 'hồ chí minh', 'đà nẵng', 'hải phòng',
        'cần thơ', 'huế', 'nha trang', 'vũng tàu', 'buôn ma thuột'
    }
    
    # Pattern mã số pháp lý (regex-like check)
    def is_legal_code(text):
        text_lower = text.lower().strip()
        # Kiểm tra pattern: số + / + chữ cái/số
        if any(pattern in text_lower for pattern in ['số ', '/nđ', '/qđ', '/nq', 'nđ-cp', 'qđ-', 'nq-']):
            return True
        # Kiểm tra chỉ là số
        if text_lower.replace('/', '').replace('-', '').replace(' ', '').isdigit():
            return True
        return False
    
    filtered = []
    for ent in entities:
        text_clean = ent['text'].strip().lower()
        
        # Bỏ qua nếu là rỗng
        if not text_clean:
            continue
        
        # TRƯỚC TIÊN: Kiểm tra xem entity có chứa địa danh quan trọng không
        # Nếu có, tách nó ra
        for loc in important_locations:
            if loc in text_clean and text_clean != loc:
                # Entity chứa địa danh nhưng không phải chỉ là địa danh đó
                # Tách địa danh ra
                loc_start = text_clean.find(loc)
                if loc_start != -1:
                    # Tìm vị trí trong text gốc
                    actual_loc_start = ent['text'].lower().find(loc)
                    if actual_loc_start != -1:
                        actual_start = ent['start'] + actual_loc_start
                        actual_end = actual_start + len(loc)
                        # Thêm địa danh như một entity riêng
                        filtered.append({
                            'text': ent['text'][actual_loc_start:actual_loc_start+len(loc)],
                            'label': 'LOC',
                            'start': actual_start,
                            'end': actual_end,
                            'source': 'statistical'
                        })
                        # Bỏ qua entity gốc (đã tách rồi)
                        continue
        
        # Cho phép các địa danh quan trọng ngay lập tức (bỏ qua tất cả filter)
        if text_clean in important_locations:
            # Sửa nhãn thành LOC nếu bị gán sai
            if ent['label'] != 'LOC':
                ent['label'] = 'LOC'
            filtered.append(ent)
            continue
        
        # Loại bỏ nếu chứa ký tự xuống dòng (lỗi parsing nghiêm trọng)
        if '\n' in ent['text']:
            continue
        
        # Loại bỏ nếu là từ khóa nhiễu (khớp chính xác)
        if text_clean in noise_keywords:
            continue
        
        # Bổ sung: Loại bỏ nếu BẮT ĐẦU bằng từ khóa nhiễu
        # (VD: "Điều 1", "Điều 2" sẽ bị loại bỏ bởi 'điều')
        first_word = text_clean.split()[0] if text_clean.split() else ''
        if first_word in noise_keywords:
            continue
        
        # Loại bỏ nếu là mã số pháp lý
        if is_legal_code(ent['text']):
            continue
        
        # Loại bỏ nếu quá ngắn (< 3 ký tự) VÀ không phải là địa danh/tên riêng có nghĩa
        if len(text_clean) < 3:
            continue
        
        # Cho phép các địa danh ngắn (3-6 ký tự) nếu chúng là LOC
        # Ví dụ: "Hà Nội", "Tokyo", "Paris"
        if len(text_clean) >= 3 and len(text_clean) <= 6 and ent['label'] == 'LOC':
            # Kiểm tra xem có phải là từ khóa nhiễu không
            if text_clean not in noise_keywords:
                filtered.append(ent)
                continue
        
        # Loại bỏ nếu quá ngắn cho các nhãn khác (< 6 ký tự) - tránh lỗi
        if len(text_clean) < 6 and ent['label'] in ['PER', 'ORG']:
            continue
        
        # Loại bỏ nếu kết thúc bằng chức danh đơn lẻ (lỗi gộp)
        if any(text_clean.endswith(' ' + title) for title in ['bộ trưởng', 'thứ trưởng', 'chánh', 'thủ trưởng']):
            continue
        
        # GIỮ LẠI thực thể này
        filtered.append(ent)
    
    return filtered


def _parse_ruler_entities(doc_with_ruler):
    """
    Chuyển đổi entities từ spaCy EntityRuler sang format chuẩn.
    
    Args:
        doc_with_ruler: spaCy Doc đã được xử lý bởi EntityRuler
    
    Returns:
        List[dict] - Danh sách entities với format:
            {
                'text': str,
                'label': str,
                'start': int (char offset),
                'end': int (char offset),
                'source': 'rule-based'
            }
    """
    rule_labels = {'DECISION_ID', 'ISSUE_DATE'}
    
    entities = []
    for ent in doc_with_ruler.ents:
        if ent.label_ in rule_labels:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'source': 'rule-based'
            })
    
    return entities


def _create_spacy_doc_with_entities(nlp, text, merged_entities):
    """
    Tạo spaCy Doc với entities đã merge.
    
    Args:
        nlp: spaCy model
        text: Văn bản gốc
        merged_entities: List[dict] - Entities sau khi merge
    
    Returns:
        spacy.Doc với .ents đã được set
    """
    doc = nlp(text)
    
    # Chuyển entities từ dict sang spaCy Span
    spans = []
    for ent in merged_entities:
        span = doc.char_span(
            ent['start'], 
            ent['end'], 
            label=ent['label'],
            alignment_mode='expand'  # Tự động expand để match token boundaries
        )
        if span:
            spans.append(span)
    
    # Filter overlapping spans (đề phòng)
    from spacy.util import filter_spans
    doc.ents = filter_spans(spans)
    
    return doc


def analyze_hybrid_ner(nlp, raw_text):
    """
    Phân tích Hybrid NER với Conflict Resolution đúng chuẩn.
    
    PIPELINE:
    1. Luồng A: underthesea.ner() → statistical entities
    2. Luồng B: spaCy EntityRuler → rule-based entities
    3. Tầng Hợp nhất: _resolve_conflicts() → merged entities
    4. Tạo spaCy Doc với entities đã merge
    
    Args:
        nlp: spaCy model (có pipeline: tok2vec, tagger, parser)
        raw_text: Văn bản gốc
    
    Returns:
        tuple: (doc_hybrid, merged_entities)
            - doc_hybrid: spaCy Doc với .ents là merged entities
            - merged_entities: List[dict] - Chi tiết các entities
    """
    print("\n" + "=" * 70)
    print("HYBRID NER PIPELINE v2 (WITH CONFLICT RESOLUTION)")
    print("=" * 70)
    
    # ==================== LUỒNG A: STATISTICAL NER ====================
    print("\n[LUỒNG A] Statistical NER (underthesea)...")
    underthesea_result = underthesea_ner(raw_text)
    stat_entities = _parse_underthesea_entities(underthesea_result, raw_text)
    
    print(f"  → Tìm thấy {len(stat_entities)} statistical entities")
    
    # Hiển thị thống kê
    stat_labels = {}
    for ent in stat_entities:
        label = ent['label']
        stat_labels[label] = stat_labels.get(label, 0) + 1
    
    print("  Thống kê nhãn:")
    for label in sorted(stat_labels.keys()):
        print(f"    {label}: {stat_labels[label]}")
    
    # ==================== LUỒNG B: RULE-BASED NER ====================
    print("\n[LUỒNG B] Rule-based NER (EntityRuler)...")
    
    # Xóa EntityRuler cũ nếu có
    if "entity_ruler" in nlp.pipe_names:
        nlp.remove_pipe("entity_ruler")
    
    # Định nghĩa patterns
    patterns = [
        # DECISION_ID - Số Quyết định (hỗ trợ cả "2827 /QĐ-BGDĐT" và "2827/QĐ-BGDĐT")
        {
            "label": "DECISION_ID",
            "pattern": [
                {"TEXT": {"REGEX": r"^\d+$"}},
                {"TEXT": {"REGEX": r"^\s*/?\s*$"}},
                {"TEXT": {"REGEX": r"^QĐ$|^QD$"}, "OP": "?"},
                {"TEXT": "-", "OP": "?"},
                {"TEXT": {"REGEX": r"^BGD[ĐD]T$"}}
            ]
        },
        # ISSUE_DATE - Ngày ban hành
        {
            "label": "ISSUE_DATE",
            "pattern": [
                {"LOWER": "ngày"},
                {"TEXT": {"REGEX": r"^\d{1,2}$"}},
                {"LOWER": "tháng"},
                {"TEXT": {"REGEX": r"^\d{1,2}$"}},
                {"LOWER": "năm"},
                {"TEXT": {"REGEX": r"^\d{4}$"}}
            ]
        }
    ]
    
    # Thêm EntityRuler SAU parser với overwrite_ents=True
    ruler = nlp.add_pipe("entity_ruler", after="parser", 
                        config={"overwrite_ents": True})
    ruler.add_patterns(patterns)
    
    # Xử lý văn bản
    doc_with_ruler = nlp(raw_text)
    rule_entities = _parse_ruler_entities(doc_with_ruler)
    
    print(f"  → Tìm thấy {len(rule_entities)} rule-based entities")
    
    # Hiển thị chi tiết
    if rule_entities:
        print("\n  Chi tiết:")
        for ent in rule_entities:
            print(f"    [{ent['label']}] {ent['text']}")
    
    # ==================== TẦNG HỢP NHẤT ====================
    print("\n[TẦNG HỢP NHẤT] Conflict Resolution (Rules-First)...")
    
    merged_entities = _resolve_conflicts(rule_entities, stat_entities, raw_text)
    
    print(f"  → Tổng entities sau merge: {len(merged_entities)}")
    print(f"    • Rule-based: {len(rule_entities)}")
    print(f"    • Statistical (kept): {len(merged_entities) - len(rule_entities)}")
    print(f"    • Statistical (rejected): {len(stat_entities) - (len(merged_entities) - len(rule_entities))}")
    
    # ==================== TẠO SPACY DOC ====================
    print("\n[XUẤT KẾT QUẢ] Tạo spaCy Doc với entities merged...")
    
    doc_hybrid = _create_spacy_doc_with_entities(nlp, raw_text, merged_entities)
    
    # Xóa EntityRuler sau khi xử lý
    nlp.remove_pipe("entity_ruler")
    
    # ==================== HIỂN THỊ TỔNG HỢP ====================
    print("\n" + "=" * 70)
    print("KẾT QUẢ CUỐI CÙNG")
    print("=" * 70)
    
    # Nhóm theo source
    rule_ents = [e for e in merged_entities if e['source'] == 'rule-based']
    stat_ents = [e for e in merged_entities if e['source'] == 'statistical']
    
    if rule_ents:
        print(f"\n{'RULE-BASED ENTITIES':<70}")
        print(f"{'Text':<40} {'Label':<20} {'Char Range'}")
        print("-" * 70)
        for ent in rule_ents:
            print(f"{ent['text']:<40} {ent['label']:<20} ({ent['start']}-{ent['end']})")
    
    if stat_ents:
        print(f"\n{'STATISTICAL ENTITIES (TOP 20)':<70}")
        print(f"{'Text':<40} {'Label':<20} {'Char Range'}")
        print("-" * 70)
        for ent in stat_ents[:20]:
            print(f"{ent['text']:<40} {ent['label']:<20} ({ent['start']}-{ent['end']})")
        
        if len(stat_ents) > 20:
            print(f"\n... và {len(stat_ents) - 20} entities khác")
    
    return doc_hybrid, merged_entities
