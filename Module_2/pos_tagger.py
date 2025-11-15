"""
Module POS Tagging cho văn bản tiếng Việt.
Sử dụng spaCy và các quy tắc sửa lỗi tùy chỉnh.
"""
import json
import os


class POSTagger:
    """
    Lớp xử lý POS (Part-of-Speech) tagging cho văn bản tiếng Việt.
    """
    
    def __init__(self, nlp, corrections_path=None):
        """
        Khởi tạo POS Tagger.
        
        Args:
            nlp: spaCy language model đã load
            corrections_path (str, optional): Đường dẫn đến file corrections.json
        """
        self.nlp = nlp
        self.correction_rules = self._load_correction_rules(corrections_path)
    
    def _load_correction_rules(self, corrections_path):
        """
        Tải các quy tắc sửa lỗi POS từ file JSON.
        
        Args:
            corrections_path (str): Đường dẫn đến file corrections.json
        
        Returns:
            dict: Dictionary chứa các quy tắc sửa lỗi
        """
        if corrections_path is None:
            # Mặc định tìm file corrections.json trong cùng thư mục
            script_dir = os.path.dirname(os.path.abspath(__file__))
            corrections_path = os.path.join(script_dir, "corrections.json")
        
        try:
            with open(corrections_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('simple_tag_rules', {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"⚠ Cảnh báo: Không thể tải file '{corrections_path}': {e}")
            return {}
    
    def tag(self, text):
        """
        Thực hiện POS tagging cho văn bản.
        
        Args:
            text (str): Văn bản đã được làm sạch (lowercase)
        
        Returns:
            tuple: (doc, corrected_tags)
                - doc: spaCy Doc object
                - corrected_tags: List các POS tags đã được sửa lỗi
        """
        doc = self.nlp(text)
        corrected_tags = self._apply_corrections(doc)
        return doc, corrected_tags
    
    def _apply_corrections(self, doc):
        """
        Áp dụng các quy tắc sửa lỗi POS cho document.
        
        Args:
            doc: spaCy Doc object
        
        Returns:
            list: Danh sách POS tags đã được sửa lỗi
        """
        tags = [token.tag_ for token in doc]
        
        i = 0
        while i < len(doc):
            token = doc[i]
            
            # Ưu tiên kiểm tra cụm 2 từ
            if i + 1 < len(doc):
                next_token_index = i + 1
                
                # Bỏ qua các token là khoảng trắng
                while next_token_index < len(doc) and doc[next_token_index].is_space:
                    next_token_index += 1
                
                if next_token_index < len(doc):
                    # Tạo cụm 2 từ
                    phrase = f"{token.lower_.strip()} {doc[next_token_index].lower_.strip()}"
                    
                    # Kiểm tra xem cụm này có trong rules không
                    if phrase in self.correction_rules:
                        # Sửa cả 2 tokens
                        tags[i] = tags[next_token_index] = self.correction_rules[phrase]
                        i = next_token_index + 1
                        continue
            
            # Xử lý từ đơn
            current_token_lower = token.lower_.strip()
            if current_token_lower in self.correction_rules:
                tags[i] = self.correction_rules[current_token_lower]
            
            i += 1
        
        return tags
    
    def get_stats(self):
        """
        Lấy thông tin thống kê về các quy tắc sửa lỗi.
        
        Returns:
            dict: Thông tin thống kê
        """
        return {
            'total_rules': len(self.correction_rules),
            'rules': list(self.correction_rules.keys())
        }
