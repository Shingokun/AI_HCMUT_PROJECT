"""
Module phân tích cú pháp phụ thuộc (Dependency Parsing).
"""
import os
from spacy import displacy


def analyze_dependency_parsing(nlp, raw_text, output_dir="."):
    """
    Phan tich cu phap phu thuoc.
    
    Args:
        nlp: spaCy model
        raw_text: Van ban goc
        output_dir: Thu muc luu HTML
    
    Returns:
        str: Duong dan file HTML
    """
    print("\n" + "=" * 70)
    print("3. PHAN TICH CU PHAP PHU THUOC")
    print("=" * 70)
    
    if 'parser' not in nlp.pipe_names:
        print("Warning: Model does not support dependency parsing (no 'parser' component).")
        return None

    doc = nlp(raw_text)
    sentences = list(doc.sents)
    
    if not sentences:
        print("\nKhong tim thay cau")
        return None
    
    print(f"\nPhan tich {len(sentences)} cau:")
    
    for idx, sentence in enumerate(sentences, 1):
        text = sentence.text.strip()
        
        print(f"\nCau {idx}: \"{text}\"")
        print(f"\n{'Token':<20} {'Dep':<15} {'Head':<20}")
        print("-" * 55)
        
        for token in sentence:
            print(f"{token.text:<20} {token.dep_:<15} {token.head.text:<20}")
    
    print("\nTruc quan hoa cau dau tien:")
    output_path = os.path.join(output_dir, "dependency_parse.html")
    
    # Use first sentence if available, handle index error
    sent_to_viz = sentences[0] if len(sentences) > 0 else None
    if sent_to_viz:
        try:
            html = displacy.render(sent_to_viz, style="dep", 
                                options={"compact": True, "distance": 100})
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)
        except Exception as e:
            print(f"Loi khi tao visualization: {e}")
    
    print(f"Luu: {output_path}")
    return doc  # Tra ve doc de serialize
