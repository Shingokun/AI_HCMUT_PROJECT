import os
import sys

# Add Module_1 to path
sys.path.append(os.path.join(os.getcwd(), 'Module_1'))

try:
    from Module_1.module1 import DocumentPreprocessor
except ImportError as e:
    print(f"Error importing Module 1: {e}")
    sys.exit(1)

import glob

test_dir = 'test'
pdf_files = sorted(glob.glob(os.path.join(test_dir, '*.pdf')))

processor = DocumentPreprocessor(use_gpu=False)

for pdf_file in pdf_files:
    print(f"\n{'='*20} {os.path.basename(pdf_file)} {'='*20}")
    try:
        # Use the pipeline's OCR capability
        processor.read(pdf_file).clean().segment()
        content = processor.cleaned_text
        if not content:
             content = " ".join(processor.sentences)
        
        print(content[:1000]) 
        print("\n... [END OF FILE] ...\n")
        print(content[-500:])
    except Exception as e:
        print(f"Error processing {pdf_file}: {e}")
