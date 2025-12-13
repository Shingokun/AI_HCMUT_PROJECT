"""
Module Document Analyzer - Tích hợp POS Tagging và Hybrid NER.
Lớp chính để phân tích toàn diện văn bản tiếng Việt.
Theo báo cáo kỹ thuật: Hybrid Architecture với underthesea + EntityRuler.
"""
import spacy
import sys

# from text_cleaner import clean_text_preserve_case, clean_text_lowercase # Removed redundant cleaning
from pos_tagger import POSTagger
from hybrid_ner import analyze_hybrid_ner


class DocumentAnalyzer:
    """
    Lớp phân tích tài liệu toàn diện.
    Kết hợp trích xuất PDF, POS Tagging và NER.
    """
    
    def __init__(self, model_name='vi_core_news_lg', corrections_path=None):
        """
        Khởi tạo Document Analyzer.
        
        Args:
            model_name (str): Tên mô hình spaCy cần load
            corrections_path (str, optional): Đường dẫn đến file corrections.json
        """
        self.nlp = self._load_model(model_name)
        self.pos_tagger = POSTagger(self.nlp, corrections_path)
    
    def _load_model(self, model_name):
        """
        Tải mô hình spaCy.
        
        Args:
            model_name (str): Tên mô hình cần load
        
        Returns:
            spacy.Language: Mô hình spaCy đã load
        """
        nlp = None
        try:
            nlp = spacy.load(model_name)
        except OSError:
            print(f"Loi: Khong tim thay mo hinh '{model_name}'")
            fallback_model = 'xx_ent_wiki_sm'
            print(f"Dang thu load fallback model '{fallback_model}'...")
            try:
                nlp = spacy.load(fallback_model)
            except OSError:
                print(f"Loi: Khong tim thay ca fallback model '{fallback_model}'")
                print(f"Chay: python -m spacy download {model_name}")
                print(f"Hoac: python -m spacy download {fallback_model}")
                sys.exit()
        
        # Add sentencizer if parser is missing (required for sentence segmentation)
        if 'parser' not in nlp.pipe_names:
            try:
                nlp.add_pipe('sentencizer')
            except Exception:
                pass # sentencizer might already exist or be incompatible
                
        return nlp
    
    def analyze_pos(self, text):
        """
        Phân tích POS tagging cho văn bản.
        
        Args:
            text (str): Văn bản gốc (đã được làm sạch từ Module 1)
        
        Returns:
            tuple: (doc, corrected_tags)
        """
        # cleaned_text = clean_text_lowercase(text) # Redundant
        return self.pos_tagger.tag(text)
    
    def analyze_ner(self, text):
        """
        Phân tích Hybrid NER cho văn bản (theo báo cáo kỹ thuật).
        Kết hợp underthesea (statistical) + EntityRuler (rule-based).
        
        Args:
            text (str): Văn bản gốc (đã được làm sạch từ Module 1)
        
        Returns:
            tuple: (doc_hybrid, entities) - Document và danh sách entities
        """
        # cleaned_text = clean_text_preserve_case(text) # Redundant
        return analyze_hybrid_ner(self.nlp, text)
    
    def analyze_full(self, text):
        """
        Phân tích toàn diện: cả POS và Hybrid NER.
        
        Args:
            text (str): Văn bản gốc
        
        Returns:
            dict: Kết quả phân tích
                - 'pos_doc': spaCy Doc cho POS
                - 'pos_tags': List POS tags đã sửa lỗi
                - 'ner_doc': spaCy Doc cho Hybrid NER
                - 'ner_entities': List entities đã merge
        """
        # Phân tích POS
        pos_doc, pos_tags = self.analyze_pos(text)
        
        # Phân tích Hybrid NER
        ner_doc, ner_entities = self.analyze_ner(text)
        
        return {
            'pos_doc': pos_doc,
            'pos_tags': pos_tags,
            'ner_doc': ner_doc,
            'ner_entities': ner_entities
        }
    
    def analyze_txt_file(self, txt_path):
        """
        Phân tích văn bản từ file .txt.
        
        Args:
            txt_path (str): Đường dẫn đến file .txt
        
        Returns:
            dict hoặc None: Kết quả phân tích, hoặc None nếu có lỗi
        """
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            if not text:
                print(f"Loi: File {txt_path} rong")
                return None
            
            # Phân tích toàn diện
            return self.analyze_full(text)
        except Exception as e:
            print(f"Loi khi doc file {txt_path}: {e}")
            return None
    
    def get_stats(self):
        """
        Lấy thông tin thống kê về analyzer.
        
        Returns:
            dict: Thông tin thống kê
        """
        return {
            'model': self.nlp.meta['name'],
            'pos_correction_rules': self.pos_tagger.get_stats()['total_rules']
        }
