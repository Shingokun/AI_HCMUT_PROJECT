import fitz  # PyMuPDF
import docx  # python-docx
import easyocr
import numpy as np
import unicodedata
import re
import os
from pdf2image import convert_from_path
from underthesea import sent_tokenize

class DocumentPreprocessor:
    """
    Bộ xử lý tài liệu toàn diện:
    - Hỗ trợ PDF/DOCX/TXT
    - OCR PDF quét
    - Làm sạch, sửa lỗi tiếng Việt
    - Tách câu
    - Định dạng văn bản hành chính
    """
    # Source - https://stackoverflow.com/a/70095504
# Posted by dataninsight
# Retrieved 2025-12-06, License - CC BY-SA 4.0

    # pages = convert_from_path("D:\Downloads\Release-25.12.0-0.zip", poppler_path=r"actualpoppler_path")
    # Source - https://stackoverflow.com/a/70095504
# Posted by dataninsight
# Retrieved 2025-12-06, License - CC BY-SA 4.0

    

    def __init__(self, use_gpu=False):
        self.raw_text = None
        self.cleaned_text = None
        self.sentences = []

        # Map sửa lỗi OCR và typo
        self.correction_map = {
            'hanh phuc': 'hạnh phúc',
            'đào tao': 'đào tạo',
            'quyên hạn': 'quyền hạn',
            'kể từngày': 'kể từ ngày',
            'q4-bgdđt': 'qđ-bgdđt',
            '1onăm': '10 năm',
            'cuc hợp tác quốc tế': 'cục hợp tác quốc tế',
            'fhứ trưởng': 'thứ trưởng',
            'trung ưong': 'trung ương',
            'số.2750': 'số 2750',
        }

        print("Đang khởi tạo EasyOCR...")
        try:
            self.ocr_reader = easyocr.Reader(['vi', 'en'], gpu=use_gpu)
            print("OCR sẵn sàng.")
        except Exception as e:
            print(f"Lỗi khi khởi tạo EasyOCR: {e}")
            self.ocr_reader = None

    # -------- Public API --------
    def read(self, file_path):
        if not os.path.exists(file_path):
            print(f"Lỗi: Tệp không tồn tại {file_path}")
            self.raw_text = ""
            return self

        self.raw_text = None
        self.cleaned_text = None
        self.sentences = []

        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        try:
            if ext == ".pdf":
                return self._read_pdf(file_path)
            elif ext == ".docx":
                return self._read_docx(file_path)
            elif ext == ".txt":
                return self._read_txt(file_path)
            else:
                print(f"Định dạng không hỗ trợ: {ext}")
                self.raw_text = ""
                return self
        except Exception as e:
            print(f"Lỗi khi đọc {file_path}: {e}")
            self.raw_text = ""
            return self

    def clean(self):
        if not self.raw_text:
            self.cleaned_text = ""
            return self

        text = self.raw_text.lower()
        text = self._handle_hard_line_breaks(text)
        text = self._normalize_unicode(text)
        text = self._remove_noise_and_special_chars(text)
        text = self._apply_vietnamese_corrections(text)
        text = self._normalize_whitespace(text)

        self.cleaned_text = text
        return self

    def segment(self):
        if not self.cleaned_text:
            self.sentences = []
            return self
        try:
            self.sentences = sent_tokenize(self.cleaned_text)
            self.sentences = [s.strip() for s in self.sentences if len(s.strip())>5]
        except:
            self.sentences = [self.cleaned_text]
        return self

    def get_output(self):
        return {
            'raw_text': self.raw_text,
            'cleaned_text': self.cleaned_text,
            'sentences': self.sentences
        }

    def save_as_official_txt(self, output_path):
        formatted_text = self._format_for_official_document(self.sentences)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted_text)
        print(f"✅ Văn bản hành chính đã được lưu tại: {output_path}")

    # -------- Private Helpers --------
    def _read_txt(self, file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            self.raw_text = f.read()
        return self

    def _read_docx(self, file_path):
        doc = docx.Document(file_path)
        self.raw_text = "\n".join([p.text for p in doc.paragraphs])
        return self

    def _read_pdf(self, file_path):
        try:
            doc = fitz.open(file_path)
            text = ""
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text("text")
            if len(text.strip()) < 100:
                return self._read_scanned_pdf(file_path)
            self.raw_text = text
            return self
        except:
            return self._read_scanned_pdf(file_path)

    def _read_scanned_pdf(self, file_path):
        if not self.ocr_reader:
            self.raw_text = ""
            return self
        
        # Use fitz (PyMuPDF) to extract images instead of pdf2image (requires poppler)
        try:
            doc = fitz.open(file_path)
            full_text = []
            
            for page_index in range(len(doc)):
                page = doc[page_index]
                image_list = page.get_images(full=True)
                
                # If page has images, process them
                if image_list:
                    for img_index, img in enumerate(image_list):
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        
                        # Convert bytes to numpy array for EasyOCR
                        # EasyOCR can read from bytes directly or we can convert to PIL/numpy
                        # But EasyOCR readtext accepts bytes
                        result = self.ocr_reader.readtext(image_bytes, detail=0, paragraph=True)
                        full_text.append(" ".join(result))
                else:
                    # If no images found but text extraction failed earlier, 
                    # maybe it's a full page image not detected as 'images' list?
                    # Render page to pixmap (image)
                    pix = page.get_pixmap(dpi=300)
                    # Convert pixmap to bytes
                    img_bytes = pix.tobytes("png")
                    result = self.ocr_reader.readtext(img_bytes, detail=0, paragraph=True)
                    full_text.append(" ".join(result))
                    
            self.raw_text = "\n".join(full_text)
        except Exception as e:
            print(f"Lỗi khi OCR PDF bằng fitz: {e}")
            self.raw_text = ""
            
        return self

    def _handle_hard_line_breaks(self, text):
        text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        text = re.sub(r'[\n\r\t]', ' ', text)
        return text

    def _normalize_unicode(self, text):
        return unicodedata.normalize('NFC', text)

    def _remove_noise_and_special_chars(self, text):
        text = re.sub(r'([.,!?;:()])', r' \1 ', text)
        text = re.sub(r'[^\w\s.,!?;:()-]+', ' ', text, flags=re.UNICODE)
        text = text.replace('_',' ')
        return text

    def _normalize_whitespace(self, text):
        return " ".join(text.split()).strip()

    def _apply_vietnamese_corrections(self, text):
        for old, new in self.correction_map.items():
            text = re.sub(r'\b'+re.escape(old)+r'\b', new, text)
        text = re.sub(r'(độc lập) \d+ (tự do) \d+ (hạnh phúc)', r'\1 \2 \3', text)
        return text

    def _format_for_official_document(self, sentences):
        lines = []
        for s in sentences:
            s = s.replace("kt", "ký thay")
            s = s.replace("y nơi nhân", "nơi nhận")
            s = s.replace("đào tao", "đào tạo")
            s = s.replace("dào tao", "đào tạo")
            s = s.replace("quyết định", "QUYẾT ĐỊNH")
            s = re.sub(r"bộ giáo dục và đào tạo cộng hòa xã hội chủ nghĩa việt nam độc lập\s+2\s+tự do\s+5\s+hanh phúc", "BỘ GIÁO DỤC VÀ ĐÀO TẠO\n CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n Độc lập - Tự do - Hạnh phúc", s, flags=re.IGNORECASE)
            s = re.sub(r'\s*([.,;:()])\s*', r' \1 ', s)
            s = " ".join(s.split())
            lines.append(s)
        return "\n".join(lines)


# -------- Chạy ví dụ --------
if __name__ == "__main__":
    # pages = convert_from_path("test_2.pdf", poppler_path=r"D:\Downloads\Release-25.12.0-0.zip")
    # for i, image in enumerate(images):
    #     fname = 'image'+str(i)+'.png'
    #     image.save(fname, "PNG")
        
    input_file = "test_1.pdf"
    output_file = "processed_document.txt"

    processor = DocumentPreprocessor(use_gpu=True)
    processor.read(input_file).clean().segment()
    processor.save_as_official_txt(output_file)
    