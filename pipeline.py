import os
import sys
import glob
import json

# Add modules to path
sys.path.append(os.path.join(os.getcwd(), 'Module_1'))
sys.path.append(os.path.join(os.getcwd(), 'Module_2'))
sys.path.append(os.path.join(os.getcwd(), 'Module_3'))
sys.path.append(os.path.join(os.getcwd(), 'Module_4'))
sys.path.append(os.path.join(os.getcwd(), 'Module_5'))

# Import Module 1
try:
    from Module_1.module1 import DocumentPreprocessor
except ImportError as e:
    print(f"Error importing Module 1: {e}")
    sys.exit(1)

# Import Module 2
try:
    from Module_2.analyzer import DocumentAnalyzer
    from Module_2.syntax_parsing import analyze_dependency_parsing
    from Module_2.json_serializer import serialize_full_analysis_to_json, save_json_output
    import spacy
except ImportError as e:
    print(f"Error importing Module 2: {e}")
    sys.exit(1)

# Import Module 3
try:
    from Module_3.gemini import run_gemini
except ImportError as e:
    print(f"Error importing Module 3: {e}")
    sys.exit(1)

def select_test_file():
    """Select a file from the test directory."""
    test_dir = 'test'
    if not os.path.exists(test_dir):
        print(f"Directory '{test_dir}' not found.")
        return None

    files = glob.glob(os.path.join(test_dir, '*.*'))
    # Filter for likely test files (txt, pdf, docx, images)
    valid_extensions = ['.txt', '.pdf', '.docx', '.png', '.jpg', '.jpeg']
    files = [f for f in files if os.path.splitext(f)[1].lower() in valid_extensions]

    if not files:
        print(f"No files found in '{test_dir}'.")
        return None

    print("\n" + "=" * 50)
    print("SELECT TEST FILE")
    print("=" * 50)
    for i, f in enumerate(files):
        print(f"[{i+1}] {os.path.basename(f)}")
    
    while True:
        try:
            choice = input(f"\nSelect [1-{len(files)}] (or 'q' to quit): ").strip()
            if choice.lower() == 'q':
                return None
            idx = int(choice) - 1
            if 0 <= idx < len(files):
                return files[idx]
            print("Invalid selection.")
        except ValueError:
            print("Invalid input.")

# import module 4
from Module_4.post_processor import run_module_4

# Import Module 5
try:
    from Module_5.exporter import export_result
except ImportError as e:
    print(f"Error importing Module 5: {e}")
    sys.exit(1)

def main():
    # 1. Select File
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        if not os.path.exists(input_file):
            print(f"File not found: {input_file}")
            return
    else:
        input_file = select_test_file()
    
    if not input_file:
        print("Exiting.")
        return

    print(f"\nSelected file: {input_file}")
    
    # Output file for Module 1
    processed_text_file = "processed_document.txt"

    # --- RUN MODULE 1 ---
    print("\n" + "=" * 50)
    print("RUNNING MODULE 1 (Preprocessing & OCR)")
    print("=" * 50)
    
    try:
        processor = DocumentPreprocessor(use_gpu=False) # Set use_gpu=True if available
        # Check file type
        ext = os.path.splitext(input_file)[1].lower()
        
        # DocumentPreprocessor.read() handles different types but let's be sure
        processor.read(input_file).clean().segment()
        processor.save_as_official_txt(processed_text_file)
        print(f"Module 1 completed. Output saved to: {processed_text_file}")
        
        # Read the processed text for next steps
        with open(processed_text_file, 'r', encoding='utf-8') as f:
            raw_text = f.read()
            
    except Exception as e:
        print(f"Error in Module 1: {e}")
        return

    # --- RUN MODULE 2 ---
    print("\n" + "=" * 50)
    print("RUNNING MODULE 2 (NLP Analysis)")
    print("=" * 50)
    
    try:
        analyzer = DocumentAnalyzer()
        try:
            nlp = spacy.load("vi_core_news_lg")
        except OSError:
            print("Warning: Model 'vi_core_news_lg' not found. Dependency parsing will be skipped.")
            print("Try installing it or using a different model.")
            nlp = None
        
        # Run analysis
        print("Running POS Tagging...")
        pos_doc, pos_tags = analyzer.analyze_pos(raw_text)
        
        print("Running NER...")
        # analyze_ner returns (doc_hybrid, entities)
        ner_result = analyzer.analyze_ner(raw_text) 
        if isinstance(ner_result, tuple):
            doc_hybrid, entities = ner_result
        else:
            doc_hybrid = ner_result
            entities = [] # Should not happen based on code
        
        dep_doc = None
        # Use analyzer.nlp instead of loading again, as analyzer handles fallback
        if analyzer.nlp and 'parser' in analyzer.nlp.pipe_names:
            print("Running Dependency Parsing...")
            dep_doc = analyze_dependency_parsing(analyzer.nlp, raw_text, output_dir="Module_2")
        else:
            print("Skipping Dependency Parsing...")
            dep_doc = None 
        
        # Export JSON
        print("Exporting JSON...")
        json_data = serialize_full_analysis_to_json(
            pos_doc=pos_doc,
            pos_tags=pos_tags,
            ner_doc=doc_hybrid, # Use doc_hybrid for ner_doc placeholder
            dep_doc=dep_doc,
            hybrid_doc=doc_hybrid,
            raw_text=raw_text,
            stats=analyzer.get_stats(), # analyzer.get_stats() might not exist if not implemented in DocumentAnalyzer
            file_name=os.path.basename(input_file)
        )
        
        module2_output_path = os.path.join("Module_2", "Output", "module_2_output.json")
        save_json_output(json_data, module2_output_path)
        print(f"Module 2 completed. Output saved to: {module2_output_path}")
        
    except Exception as e:
        print(f"Error in Module 2: {e}")
        # Continue to Module 3 even if Module 2 fails? 
        # User said "Module 1 -> 2 -> 3". If 2 fails, maybe 3 can still run on text.
        print("Proceeding to Module 3 with raw text...")

    # --- RUN MODULE 3 ---
    print("\n" + "=" * 50)
    print("RUNNING MODULE 3 (LLM Extraction)")
    print("=" * 50)
    
    try:
        # Module 3 uses the text content
        result = run_gemini(raw_text)
        
        if result:
            print("\n" + "=" * 50)
            print("FINAL RESULT (MODULE 3 OUTPUT)")
            print("=" * 50)
            print(json.dumps(result, indent=4, ensure_ascii=False))
        else:
            print("Module 3 failed to generate result.")
            return
    except Exception as e:
        print(f"Error in Module 3: {e}")
        return
    # --- RUN MODULE 4 ---
    print("\n" + "=" * 50)
    print("RUNNING MODULE 4 (Validation & Post-processing)")
    print("=" * 50)

    final_result = run_module_4(result)

    print("\n" + "=" * 50)
    print("FINAL RESULT (MODULE 4 OUTPUT)")
    print("=" * 50)
    print(json.dumps(final_result, indent=4, ensure_ascii=False))

    # --- RUN MODULE 5 ---
    print("\n" + "=" * 50)
    print("RUNNING MODULE 5 (Export Result)")
    print("=" * 50)
    
    export_result(final_result, input_file)

if __name__ == "__main__":
    main()

