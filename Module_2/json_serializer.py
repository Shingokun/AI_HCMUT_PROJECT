"""
JSON Serializer cho Module 2 Output.
Serialize TAT CA du kien da trich xuat (POS, NER, Dependency, Hybrid NER) thanh JSON.
"""

import json
from datetime import datetime
import re


def _normalize_decision_id(text: str) -> str:
    """Chuan hoa DECISION_ID ve dang chuan: NN[/YYYY]/QĐ-BGDĐT hoac NN[/YYYY]/NĐ-CP.
    Vi du:
      - "số. 2750 qđ-bgdđt" -> "2750/QĐ-BGDĐT"
      - "số 37 2025 nđ-cp" -> "37/2025/NĐ-CP"
    """
    if not text:
        return ""
    s = text.strip().lower()
    # loai bo prefix 'số', 'so' va cac dau phay, dau cham thua
    s = re.sub(r"\b(số|so)\b\s*[.:,-]*\s*", "", s)
    # Thay nhieu khoang trang bang 1 khoang
    s = re.sub(r"\s+", " ", s)
    # Gop cac pattern tach bang dau '-' xung quanh khoang trang
    s = re.sub(r"\s*-\s*", "-", s)

    # Truong hop: num / code (khong co nam), vi du: 2827/qđ-bgdđt
    m0 = re.search(
        r"(?P<num>\d{1,6})\s*/\s*(?P<code>qđ\s*-?\s*bgdđt|nđ\s*-?\s*cp)\b",
        s,
        flags=re.IGNORECASE,
    )
    if m0:
        num = m0.group("num")
        code = m0.group("code").replace(" ", "").replace("-", "-")
        code = code.replace("qđbgdđt", "qđ-bgdđt").replace("nđcp", "nđ-cp")
        return f"{num}/{code.upper()}"

    # Tim num, optional year, code
    # 1) Uu tien match "num (slash hoac space) year code"
    m = re.search(
        r"(?P<num>\d{1,6})\s*(?:/|\s)\s*(?P<year>\d{4})\s*(?P<code>qđ\s*-?\s*bgdđt|nđ\s*-?\s*cp)",
        s,
        flags=re.IGNORECASE,
    )
    if m:
        num = m.group("num")
        year = m.group("year")
        code = m.group("code")
    else:
        # 2) num code (khong year)
        m2 = re.search(r"(?P<num>\d{1,6})\s*(?P<code>qđ\s*-?\s*bgdđt|nđ\s*-?\s*cp)", s, flags=re.IGNORECASE)
        if not m2:
            return text.strip().upper()
        num = m2.group("num")
        year = None
        code = m2.group("code")
    # Chuan hoa code
    code = code.replace(" ", "").replace("-", "-")
    code = code.replace("qđbgdđt", "qđ-bgdđt").replace("nđcp", "nđ-cp")
    code_up = code.upper()

    if year:
        return f"{num}/{year}/{code_up}"
    return f"{num}/{code_up}"


def _parse_issue_date_iso(text: str) -> str:
    """Parse chuoi 'ngày DD tháng M năm YYYY' ve ISO YYYY-MM-DD.
    Tra ve chuoi rong neu khong match.
    """
    if not text:
        return ""
    s = text.strip().lower()
    # Bo cac dau cham phay thua xung quanh
    s = s.replace(",", " ").replace(".", " ")
    s = re.sub(r"\s+", " ", s)
    m = re.search(r"ngày\s*(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4})", s)
    if not m:
        return ""
    d, mth, y = m.group(1), m.group(2), m.group(3)
    try:
        dd = f"{int(d):02d}"
        mm = f"{int(mth):02d}"
        return f"{y}-{mm}-{dd}"
    except Exception:
        return ""


def serialize_full_analysis_to_json(pos_doc, pos_tags, ner_doc, dep_doc, hybrid_doc, raw_text, stats, file_name=None):
    """
    Serialize TAT CA du kien da trich xuat thanh JSON day du
    de cung cap cho Module 3 (LLM).
    
    QUAN TRONG: hybrid_doc chua TAT CA entities (rule-based + statistical merged).
    Module 3 chi can doc "entities" tu hybrid_doc, khong can phan biet nguon goc.
    
    Args:
        pos_doc: spaCy Doc tu POS tagging
        pos_tags: List cac POS tags da chinh sua
        ner_doc: spaCy Doc tu NER (statistical only - for comparison)
        dep_doc: spaCy Doc tu Dependency Parsing
        hybrid_doc: spaCy Doc tu Hybrid NER (FINAL entities - rule overwrite statistical)
        raw_text: Van ban goc
        stats: Dictionary chua cac thong ke
    
    Returns:
        dict: Du lieu JSON day du
    """
    
    # 1. POS TAGGING - Trich xuat tat ca tokens voi POS tags
    pos_tokens = []
    for i, token in enumerate(pos_doc):
        if not token.is_space:
            pos_tokens.append({
                "text": token.text,
                "pos": pos_tags[i],
                "lemma": token.lemma_,
                "is_alpha": token.is_alpha,
                "is_stop": token.is_stop,
                "is_punct": token.is_punct,
                "start_char": token.idx,
                "end_char": token.idx + len(token.text)
            })
    
    # 2. DEPENDENCY PARSING - Trich xuat quan he phu thuoc
    sentences = []
    sentence_spans = []
    for sent in dep_doc.sents:
        sentence_data = {
            "text": sent.text.strip(),
            "start_char": sent.start_char,
            "end_char": sent.end_char,
            "tokens": []
        }
        sentence_spans.append((sent.start_char, sent.end_char))
        
        for token in sent:
            sentence_data["tokens"].append({
                "text": token.text,
                "pos": token.pos_,
                "dep": token.dep_,
                "head": token.head.text,
                "head_pos": token.head.pos_,
                "is_root": token.dep_ == "ROOT",
                "start_char": token.idx,
                "end_char": token.idx + len(token.text)
            })
        
        sentences.append(sentence_data)
    
    # 3. ENTITIES (HYBRID) - Day la danh sach CUOI CUNG cho Module 3
    # Chua TAT CA entities: rule-based (DECISION_ID, ISSUE_DATE) + statistical (PER, ORG, LOC...)
    # EntityRuler da overwrite cac du doan thong ke khi co xung dot
    entities = []
    rule_labels = {'DECISION_ID', 'ISSUE_DATE'}
    
    for ent in hybrid_doc.ents:
        # Xac dinh chi so cau chua entity
        sent_idx = -1
        for idx, (s_start, s_end) in enumerate(sentence_spans):
            if ent.start_char >= s_start and ent.start_char < s_end:
                sent_idx = idx
                break

        ent_obj = {
            "text": ent.text,
            "label": ent.label_,
            "start_char": ent.start_char,
            "end_char": ent.end_char,
            "source": "rule-based" if ent.label_ in rule_labels else "statistical",
            "sentence_idx": sent_idx
        }

        # Bo sung truong chuan hoa/ISO cho cac nhan quan trong
        if ent.label_ == 'DECISION_ID':
            ent_obj["normalized"] = _normalize_decision_id(ent.text)
        elif ent.label_ == 'ISSUE_DATE':
            ent_obj["date_iso"] = _parse_issue_date_iso(ent.text)

        entities.append(ent_obj)
    
    # 4. TOKENS DETAIL - Trich xuat chi tiet toan bo tokens tu hybrid doc
    all_tokens = []
    for token in hybrid_doc:
        if not token.is_space:
            all_tokens.append({
                "text": token.text,
                "lemma": token.lemma_,
                "pos": token.pos_,
                "tag": token.tag_,
                "dep": token.dep_,
                "head": token.head.text,
                "head_pos": token.head.pos_,
                "is_alpha": token.is_alpha,
                "is_stop": token.is_stop,
                "is_punct": token.is_punct,
                "ent_type": token.ent_type_ if token.ent_type_ else "",
                "ent_iob": token.ent_iob_,
                "start_char": token.idx,
                "end_char": token.idx + len(token.text)
            })
    
    # 5. TAO JSON OUTPUT DAY DU
    # Phan "entities" la danh sach DUY NHAT cho Module 3
    output_json_data = {
        "metadata": {
            "source": "Module 2 - Vietnamese Document Analysis",
            "file_name": file_name or "",
            "exported_at": datetime.utcnow().isoformat() + "Z",
            "text_length": len(raw_text),
            # Dong bo voi POS tokens de de doi chieu
            "total_tokens": len(pos_tokens),
            "total_sentences": len(sentences),
            "total_entities": len(entities)
        },
        "raw_text": raw_text,
        "entities": entities,  # DANH SACH DUY NHAT - Hybrid (rule + statistical merged)
        "pos_tagging": {
            "description": "Part-of-Speech tagging voi quy tac chinh sua",
            "total_tokens": len(pos_tokens),
            "correction_rules": stats.get("pos_correction_rules", 0),
            "tokens": pos_tokens
        },
        "dependency_parsing": {
            "description": "Phan tich cau truc cu phap va quan he phu thuoc",
            "total_sentences": len(sentences),
            "sentences": sentences
        },
        "tokens_detail": {
            "description": "Chi tiet day du cua tung token (tu hybrid pipeline)",
            "total_tokens": len(all_tokens),
            "tokens": all_tokens
        }
    }
    
    return output_json_data


def serialize_doc_to_json(doc):
    """
    Chuyen doi doi tuong spaCy Doc thanh dinh dang JSON chi tiet
    (ham nay giu lai de tuong thich nguoc).
    
    Args:
        doc: spaCy Doc object da xu ly (hybrid pipeline)
    
    Returns:
        str: Chuoi JSON da duoc dinh dang
    """
    
    # 1. Trich xuat thong tin thuc the (cap do Span)
    entities = [
        {
            "text": ent.text,
            "label": ent.label_,
            "start_char": ent.start_char,
            "end_char": ent.end_char
        }
        for ent in doc.ents
    ]
    
    # 2. Trich xuat thong tin chi tiet cua tung token (cap do Token)
    tokens = [
        {
            "text": token.text,
            "lemma": token.lemma_,
            "pos": token.pos_,
            "tag": token.tag_,
            "dep": token.dep_,
            "head": token.head.text,
            "head_pos": token.head.pos_,
            "is_alpha": token.is_alpha,
            "is_stop": token.is_stop,
            "is_punct": token.is_punct,
            "ent_type": token.ent_type_ if token.ent_type_ else "",
            "ent_iob": token.ent_iob_,
            "start_char": token.idx,
            "end_char": token.idx + len(token.text)
        }
        for token in doc
        if not token.is_space  # Bo qua khoang trang
    ]
    
    # 3. Tao doi tuong JSON cuoi cung
    output_json_data = {
        "text": doc.text,           # Van ban goc (da lam sach)
        "entities": entities,       # Danh sach thuc the da phat hien
        "tokens": tokens,           # Danh sach chi tiet tung token
        "stats": {
            "total_tokens": len(tokens),
            "total_entities": len(entities),
            "entity_labels": list(set(ent["label"] for ent in entities))
        }
    }
    
    # Tra ve chuoi JSON da duoc dinh dang
    return json.dumps(output_json_data, indent=2, ensure_ascii=False)

def save_json_output(json_data, output_path="Output/module_2_output.json"):
    """
    Luu ket qua JSON ra file.
    
    Args:
        json_data: Dictionary hoac spaCy Doc object
        output_path: Duong dan file output
    
    Returns:
        bool: True neu thanh cong, False neu that bai
    """
    try:
        # Neu la dict thi chi can dumps
        if isinstance(json_data, dict):
            json_output = json.dumps(json_data, indent=2, ensure_ascii=False)
        else:
            # Neu la spaCy Doc thi serialize
            json_output = serialize_doc_to_json(json_data)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_output)
        
        return True
    except Exception as e:
        print(f"\nLoi khi luu file JSON: {e}")
        return False


def print_json_preview(json_data, max_text_length=200):
    """
    In mot phan nho cua JSON de xem truoc.
    
    Args:
        json_data: Dictionary JSON data
        max_text_length: Do dai toi da cua text snippet
    """
    
    if isinstance(json_data, dict):
        data = json_data
    else:
        # Neu la string thi parse
        data = json.loads(json_data)
    
    # Tao preview
    if "entities" in data and "metadata" in data:
        # Format moi (simplified structure)
        
        # Phan loai entities theo source
        rule_entities = [e for e in data["entities"] if e.get("source") == "rule-based"]
        stat_entities = [e for e in data["entities"] if e.get("source") == "statistical"]
        
        preview = {
            "metadata": data["metadata"],
            "text_snippet": data["raw_text"][:max_text_length] + "..." if len(data["raw_text"]) > max_text_length else data["raw_text"],
            "entities_summary": {
                "total": len(data["entities"]),
                "rule_based_count": len(rule_entities),
                "statistical_count": len(stat_entities),
                "all_labels": sorted(set(e["label"] for e in data["entities"])),
                "sample_rule_based": rule_entities[:5],
                "sample_statistical": stat_entities[:5]
            },
            "pos_tagging_summary": {
                "total_tokens": data["pos_tagging"]["total_tokens"],
                "correction_rules": data["pos_tagging"]["correction_rules"],
                "sample_tokens": data["pos_tagging"]["tokens"][:3]
            }
        }
    else:
        # Format cu (backward compatibility)
        preview = {
            "text_snippet": data.get("text", "")[:max_text_length] + "...",
            "stats": data["stats"],
            "entities_preview": data["entities"][:5] if len(data["entities"]) > 5 else data["entities"],
            "tokens_preview": data["tokens"][:10] if len(data["tokens"]) > 10 else data["tokens"]
        }
    
    print(json.dumps(preview, indent=2, ensure_ascii=False))
