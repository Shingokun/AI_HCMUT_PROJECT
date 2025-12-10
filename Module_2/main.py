"""
Script phân tích tài liệu tiếng Việt.
Bao gồm: POS Tagging, NER, Dependency Parsing, Hybrid NER Pipeline.
"""
import os
import sys
import glob

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from analyzer import DocumentAnalyzer
from syntax_parsing import analyze_dependency_parsing
from json_serializer import serialize_full_analysis_to_json, save_json_output, print_json_preview
import spacy


def select_test_file():
    """Hien thi danh sach file .txt va cho phep chon."""
    print("\n" + "=" * 70)
    print("CHON FILE TEST")
    print("=" * 70)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_folder = os.path.join(script_dir, '..', 'test')
    txt_files = sorted(glob.glob(os.path.join(test_folder, '*.txt')))
    
    if not txt_files:
        print("\nKhong tim thay file .txt trong folder test/")
        sys.exit(1)
    
    print(f"\nCo {len(txt_files)} file .txt:")
    for i, txt_path in enumerate(txt_files, 1):
        filename = os.path.basename(txt_path)
        file_size = os.path.getsize(txt_path) / 1024
        print(f"  [{i}] {filename:<30} ({file_size:.1f} KB)")
    
    while True:
        try:
            choice = input(f"\nChon [1-{len(txt_files)}] hoac 'q' de thoat: ").strip()
            
            if choice.lower() == 'q':
                sys.exit(0)
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(txt_files):
                return txt_files[choice_num - 1]
            else:
                print(f"Vui long nhap so tu 1 den {len(txt_files)}")
        except ValueError:
            print("Vui long nhap so hop le")


def select_section_menu():
    """Hien thi menu chon section."""
    print("\n" + "=" * 70)
    print("CHON PHAN PHAN TICH")
    print("=" * 70)
    print("\n[1] POS Tagging - Gan nhan tu loai")
    print("[2] Hybrid NER - Nhan dien thuc the (Statistical + Rule-based)")
    print("[3] Dependency Parsing - Phan tich cu phap")
    print("[4] Xuat file JSON day du (Chay tat ca)")
    print("[5] Chay tat ca (Hien thi + Xuat JSON)")
    print("[0] Thoat")
    
    while True:
        try:
            choice = input("\nChon [0-5]: ").strip()
            choice_num = int(choice)
            if 0 <= choice_num <= 5:
                return choice_num
            else:
                print("Vui long nhap so tu 0 den 5")
        except ValueError:
            print("Vui long nhap so hop le")


def print_header(title, width=70):
    """In header."""
    print("\n" + "=" * width)
    print(title)
    print("=" * width)


def analyze_pos_tagging(analyzer, raw_text):
    """POS Tagging."""
    print_header("1. GAN NHAN TU LOAI (POS TAGGING)")
    
    pos_doc, pos_tags = analyzer.analyze_pos(raw_text)
    total_tokens = len([t for t in pos_doc if not t.is_space])
    
    print(f"\nTong token: {total_tokens}")
    print(f"Quy tac: {analyzer.get_stats()['pos_correction_rules']}")
    
    print(f"\n{'Token':<30} {'POS':<10}")
    print("-" * 40)
    
    for i, token in enumerate(pos_doc):
        if not token.is_space:
            print(f"{token.text:<30} {pos_tags[i]:<10}")
    
    return pos_doc, pos_tags


def analyze_ner(analyzer, raw_text):
    """Hybrid Named Entity Recognition (underthesea + EntityRuler)."""
    print_header("2. HYBRID NER (Statistical + Rule-based)")
    
    ner_doc, ner_entities = analyzer.analyze_ner(raw_text)
    
    if ner_doc.ents:
        print(f"\nTong thuc the: {len(ner_doc.ents)}")
        
        print(f"\n{'Thuc the':<50} {'Nhan':<20}")
        print("-" * 70)
        
        for ent in ner_doc.ents:
            print(f"{ent.text:<50} {ent.label_:<20}")
        
        print("\nThong ke:")
        entity_counts = {}
        for ent in ner_doc.ents:
            entity_counts[ent.label_] = entity_counts.get(ent.label_, 0) + 1
        
        for label, count in sorted(entity_counts.items()):
            print(f"  {label:<20}: {count}")
    else:
        print("\nKhong tim thay thuc the.")
    
    return ner_doc


def main():
    """Ham chinh."""
    print("=" * 70)
    print("PHAN TICH TAI LIEU TIENG VIET")
    print("=" * 70)
    
    # Chon file .txt
    txt_path = select_test_file()
    
    print_header("DOC FILE VAN BAN")
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            raw_text = f.read()
    except Exception as e:
        print(f"\nLoi: Khong the doc file .txt - {e}")
        sys.exit(1)
    
    if not raw_text:
        print("\nLoi: File rong")
        sys.exit(1)
    
    print(f"\nFile: {os.path.basename(txt_path)}")
    print(f"Ky tu: {len(raw_text)}")
    print(f"Dong: {len(raw_text.splitlines())}")
    print(f"Tu: {len(raw_text.split())}")
    
    print("\nDang tai mo hinh spaCy...")
    analyzer = DocumentAnalyzer(model_name='vi_core_news_lg')
    nlp = spacy.load('vi_core_news_lg')
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Chon section de hien thi
    section_choice = select_section_menu()
    
    if section_choice == 0:
        print("\nThoat chuong trinh.")
        sys.exit(0)
    
    # Khoi tao cac bien luu ket qua
    pos_doc = None
    pos_tags = None
    ner_doc = None
    dep_doc = None
    
    # Chay theo lua chon
    if section_choice == 1:
        pos_doc, pos_tags = analyze_pos_tagging(analyzer, raw_text)
    
    elif section_choice == 2:
        ner_doc = analyze_ner(analyzer, raw_text)
    
    elif section_choice == 3:
        dep_doc = analyze_dependency_parsing(nlp, raw_text, output_dir=script_dir)
    
    elif section_choice == 4:
        # Chi xuat JSON (can chay tat ca truoc)
        print("\nDang xu ly tat ca section de tao JSON...")
        pos_doc, pos_tags = analyze_pos_tagging(analyzer, raw_text)
        ner_doc = analyze_ner(analyzer, raw_text)
        dep_doc = analyze_dependency_parsing(nlp, raw_text, output_dir=script_dir)
        
        # Xuat JSON
        # ner_doc tu analyze_ner chinh la doc_hybrid
        export_json(pos_doc, pos_tags, ner_doc, dep_doc, ner_doc, raw_text, analyzer, script_dir, file_name=os.path.basename(txt_path))
    
    elif section_choice == 5:
        # Chay tat ca + Xuat JSON
        pos_doc, pos_tags = analyze_pos_tagging(analyzer, raw_text)
        ner_doc = analyze_ner(analyzer, raw_text)
        dep_doc = analyze_dependency_parsing(nlp, raw_text, output_dir=script_dir)
        
        # Xuat JSON
        # ner_doc tu analyze_ner chinh la doc_hybrid
        export_json(pos_doc, pos_tags, ner_doc, dep_doc, ner_doc, raw_text, analyzer, script_dir, file_name=os.path.basename(txt_path))
        
        # Tong ket
        print_summary(txt_path, raw_text, pos_doc, ner_doc, analyzer)
    
    print("\n" + "=" * 70)


def export_json(pos_doc, pos_tags, ner_doc_for_comparison, dep_doc, doc_hybrid, raw_text, analyzer, script_dir, file_name=""):
    """Xuat file JSON."""
    print_header("JSON OUTPUT CHO MODULE 3 (LLM)")
    
    # Tao JSON day du tu TAT CA cac phan phan tich
    json_data = serialize_full_analysis_to_json(
        pos_doc=pos_doc,
        pos_tags=pos_tags,
        ner_doc=ner_doc_for_comparison,  # Day la ner_doc tu analyze_ner
        dep_doc=dep_doc,
        hybrid_doc=doc_hybrid,  # Day cung la ner_doc tu analyze_ner
        raw_text=raw_text,
        stats=analyzer.get_stats(),
        file_name=file_name
    )
    
    json_file = os.path.join(script_dir, "Output", "module_2_output.json")
    if save_json_output(json_data, json_file):
        print(f"\nDa luu: {json_file}")
        
        # Thong ke JSON
        print(f"\nThong ke JSON Output:")
        print(f"  Tong tokens: {json_data['metadata']['total_tokens']}")
        print(f"  Tong cau: {json_data['metadata']['total_sentences']}")
        print(f"  Tong entities: {json_data['metadata']['total_entities']}")
        
        # Phan loai entities
        rule_entities = [e for e in json_data['entities'] if e.get('source') == 'rule-based']
        stat_entities = [e for e in json_data['entities'] if e.get('source') == 'statistical']
        
        print(f"    - Rule-based: {len(rule_entities)}")
        print(f"    - Statistical: {len(stat_entities)}")
        print(f"  Quy tac POS: {json_data['pos_tagging']['correction_rules']}")
        
        print(f"\nXem truoc JSON:")
        print_json_preview(json_data, max_text_length=150)


def print_summary(txt_path, raw_text, pos_doc, ner_doc, analyzer):
    """In tong ket."""
    print_header("TONG KET")
    print(f"\nFile: {os.path.basename(txt_path)}")
    print(f"Ky tu xu ly: {len(raw_text)}")
    print(f"Token (POS): {len([t for t in pos_doc if not t.is_space])}")
    print(f"Thuc the (NER): {len(ner_doc.ents)}")
    print(f"Quy tac POS: {analyzer.get_stats()['pos_correction_rules']}")
    print(f"File HTML: dependency_parse.html")
    print(f"File JSON: Output/module_2_output.json")


if __name__ == "__main__":
    main()
