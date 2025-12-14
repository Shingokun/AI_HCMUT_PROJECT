import os
import sys
import glob
import json
import re
import time

# Add modules to path
sys.path.append(os.path.join(os.getcwd(), 'Module_1'))
sys.path.append(os.path.join(os.getcwd(), 'Module_2'))
sys.path.append(os.path.join(os.getcwd(), 'Module_3'))
sys.path.append(os.path.join(os.getcwd(), 'Module_4'))
sys.path.append(os.path.join(os.getcwd(), 'Module_5'))

# Import Modules
try:
    from Module_1.module1 import DocumentPreprocessor
    from Module_3.gemini import run_gemini
    from Module_4.post_processor import run_module_4
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import modules ({e}). Inference will be skipped.")
    MODULES_AVAILABLE = False

def process_file(input_file):
    """Runs the extraction pipeline on a single file."""
    if not MODULES_AVAILABLE:
        return None
        
    print(f"Processing: {input_file}...")
    
    # Module 1: Preprocessing
    try:
        processor = DocumentPreprocessor(use_gpu=False)
        processor.read(input_file).clean().segment()
        raw_text = processor.cleaned_text # Or join sentences
        if not raw_text:
             # Fallback if cleaned_text is empty, try joining sentences
             raw_text = " ".join(processor.sentences)
    except Exception as e:
        print(f"  Module 1 Error: {e}")
        return None

    # Module 3: LLM Extraction
    try:
        # Note: We skip Module 2 here for speed as it's mostly for intermediate analysis
        # unless Module 3 depends on Module 2's output (which it doesn't in pipeline.py)
        llm_result = run_gemini(raw_text)
        if not llm_result:
            print("  Module 3 returned None")
            return None
    except Exception as e:
        print(f"  Module 3 Error: {e}")
        return None

    # Module 4: Validation
    try:
        final_result = run_module_4(llm_result)
        return final_result.get("data", {})
    except Exception as e:
        print(f"  Module 4 Error: {e}")
        return None

def load_ground_truth(gt_path):
    """Loads ground truth data from a JSON file."""
    if os.path.exists(gt_path):
        with open(gt_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def calculate_metrics(predictions, ground_truth):
    """
    Calculates metrics. 
    """
    fields = ["so_quyet_dinh", "ngay_ban_hanh", "co_quan_ban_hanh", "nguoi_ky"]
    
    y_true_all = []
    y_pred_all = []
    
    print("\n=== DETAILED RESULTS PER FILE ===")
    print(f"{'File':<15} | {'Accuracy':<10} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10}")
    print("-" * 70)

    sorted_files = sorted(ground_truth.keys(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)

    for file_name in sorted_files:
        true_data = ground_truth[file_name]
        if file_name in predictions:
            pred_data = predictions[file_name]
            
            tp = 0
            fp = 0
            fn = 0
            tn = 0
            
            for field in fields:
                val_true = true_data.get(field, "").strip().lower()
                val_pred = pred_data.get(field, "").strip().lower()
                
                # Normalize "unknown" values to empty to distinguish Miss vs Hallucination
                if val_pred in ["không rõ", "n/a", "unknown", "none", ""]:
                    val_pred = ""
                
                y_true_all.append(val_true)
                y_pred_all.append(val_pred)
                
                if val_true == val_pred:
                    if val_true != "":
                        tp += 1
                    else:
                        tn += 1
                else:
                    if val_pred != "" and val_true != "":
                        fp += 1 # Wrong value
                        fn += 1 # Missed correct value
                    elif val_pred != "" and val_true == "":
                        fp += 1 # Hallucination
                    elif val_pred == "" and val_true != "":
                        fn += 1 # Missed
            
            # Calculate per-file metrics
            total_fields = len(fields)
            accuracy = (tp + tn) / total_fields
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            
            print(f"{file_name:<15} | {accuracy:.2f}       | {precision:.2f}       | {recall:.2f}       | {f1:.2f}")

    print("\n=== ERROR ANALYSIS (MISMATCHES) ===")
    print(f"{'File':<15} | {'Field':<20} | {'Ground Truth':<30} | {'Prediction':<30}")
    print("-" * 100)
    
    for file_name in sorted_files:
        true_data = ground_truth[file_name]
        if file_name in predictions:
            pred_data = predictions[file_name]
            for field in fields:
                val_true = true_data.get(field, "").strip().lower()
                val_pred = pred_data.get(field, "").strip().lower()
                
                if val_true != val_pred:
                    # Truncate for display
                    vt_disp = (val_true[:27] + '...') if len(val_true) > 27 else val_true
                    vp_disp = (val_pred[:27] + '...') if len(val_pred) > 27 else val_pred
                    print(f"{file_name:<15} | {field:<20} | {vt_disp:<30} | {vp_disp:<30}")

    if not y_true_all:
        return None

    # Re-calculating global based on TP/FP/FN logic for consistency
    tp_total = 0
    fp_total = 0
    fn_total = 0
    tn_total = 0
    
    for i in range(len(y_true_all)):
        vt = y_true_all[i]
        vp = y_pred_all[i]
        if vt == vp:
            if vt != "": tp_total += 1
            else: tn_total += 1
        else:
            if vp != "" and vt != "":
                fp_total += 1
                fn_total += 1
            elif vp != "" and vt == "":
                fp_total += 1
            elif vp == "" and vt != "":
                fn_total += 1
                
    global_acc = (tp_total + tn_total) / len(y_true_all)
    global_prec = tp_total / (tp_total + fp_total) if (tp_total + fp_total) > 0 else 0
    global_rec = tp_total / (tp_total + fn_total) if (tp_total + fn_total) > 0 else 0
    global_f1 = 2 * global_prec * global_rec / (global_prec + global_rec) if (global_prec + global_rec) > 0 else 0

    return {
        "Accuracy": global_acc,
        "Precision": global_prec,
        "Recall": global_rec,
        "F1": global_f1
    }

def main():
    test_dir = 'test'
    files = glob.glob(os.path.join(test_dir, '*.*'))
    valid_extensions = ['.txt', '.pdf', '.docx', '.png', '.jpg']
    files = [f for f in files if os.path.splitext(f)[1].lower() in valid_extensions]
    
    if not files:
        print("No test files found.")
        return

    print(f"Found {len(files)} test files.")
    
    results = {}
    
    # 1. Run Inference
    # Check if predictions.json exists to save time, or run fresh?
    if os.path.exists('predictions.json'):
        print("Loading existing predictions from predictions.json...")
        with open('predictions.json', 'r', encoding='utf-8') as f:
            results = json.load(f)
    elif MODULES_AVAILABLE:
        for f in files:
            file_name = os.path.basename(f)
            extracted_data = process_file(f)
            if extracted_data:
                results[file_name] = extracted_data
            time.sleep(1) # Avoid rate limits
        
        # 2. Save Predictions
        with open('predictions.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        print("\nPredictions saved to 'predictions.json'.")
    else:
        print("Modules not available and no predictions.json found. Cannot run inference.")
        return

    # 3. Compare with Ground Truth (if exists)
    gt_file = 'ground_truth.json'
    if os.path.exists(gt_file):
        print("\nCalculating metrics against ground_truth.json...")
        ground_truth = load_ground_truth(gt_file)
        metrics = calculate_metrics(results, ground_truth)
        
        if metrics:
            print("\n=== OVERALL PERFORMANCE ===")
            for k, v in metrics.items():
                print(f"{k}: {v:.4f}")
    else:
        print(f"\n[INFO] '{gt_file}' not found.")

if __name__ == "__main__":
    main()
