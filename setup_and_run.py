import os
import sys
import subprocess

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def check_dependencies():
    print_header("STEP 0: Checking Dependencies")
    
    required = ['spacy', 'pytesseract', 'pdf2image', 'cv2', 'pandas']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"{package} installed")
        except ImportError:
            print(f"{package} missing")
            missing.append(package)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        print("SpaCy model 'en_core_web_sm' loaded")
    except:
        print("SpaCy model 'en_core_web_sm' not found")
        print("Run: python -m spacy download en_core_web_sm")
        return False
    
    return True

def check_pdf_files():
    print_header("STEP 1: Checking PDF Files")
    
    raw_dir = os.path.join("data", "raw")
    
    if not os.path.exists(raw_dir):
        os.makedirs(raw_dir)
        print(f"Created directory: {raw_dir}")
        print(f"Please add PDF contracts to {raw_dir}")
        return False
    
    pdf_files = [f for f in os.listdir(raw_dir) if f.lower().endswith('.pdf')]
    
    if len(pdf_files) == 0:
        print(f"No PDF files found in {raw_dir}")
        print("Please add at least 10 PDF contracts")
        return False
    
    print(f"Found {len(pdf_files)} PDF files")
    
    if len(pdf_files) < 10:
        print("Warning: Less than 10 PDFs. Results may be poor.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return False
    
    return True

def run_ocr_pipeline():
    print_header("STEP 2: Running OCR Pipeline (Week 1)")
    
    try:
        from src.preprocessing.ocr_engine import extract_text_from_pdf
        exec(open('src/preprocessing/run_batch.py').read())
        print("OCR extraction complete")
        return True
    except Exception as e:
        print(f"OCR failed: {e}")
        print("Check if Tesseract is installed properly")
        return False

def run_annotation():
    print_header("STEP 3: Auto-Annotating Documents (Week 1)")
    
    try:
        exec(open('scripts/auto_annotate.py').read())
        
        train_data = os.path.join("data", "processed", "train_data.jsonl")
        if os.path.exists(train_data):
            with open(train_data, 'r') as f:
                line_count = sum(1 for _ in f)
            
            print(f"Created training data with {line_count} documents")
            
            if line_count < 20:
                print("Warning: Less than 20 training documents")
                print("   Model performance may be limited")
            
            return True
        else:
            print("Training data not created")
            return False
            
    except Exception as e:
        print(f"Annotation failed: {e}")
        return False

def run_training():
    print_header("STEP 4: Training NER Model (Week 2)")
    
    try:
        exec(open('src/models/train_ner.py').read())
        
        model_dir = os.path.join("models", "ner_model_v1")
        if os.path.exists(model_dir):
            print("Model training complete")
            return True
        else:
            print("Model was not saved")
            return False
            
    except Exception as e:
        print(f"Training failed: {e}")
        return False

def run_evaluation():
    print_header("STEP 5: Evaluating Model (Week 2 - F1 Scores)")
    
    try:
        exec(open('src/models/evaluate_model.py').read())
        print("Evaluation complete")
        return True
    except Exception as e:
        print(f"Evaluation failed: {e}")
        return False

def main():
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║         LexiScan Auto - Complete Setup                 ║
    ║         Automated Legal Entity Extractor               ║
    ║         Week 1 & Week 2 Implementation                 ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    if not check_dependencies():
        print("\nSetup failed. Install missing dependencies first.")
        return
    
    if not check_pdf_files():
        print("\nSetup failed. Add PDF files to data/raw/")
        return
    
    if not run_ocr_pipeline():
        print("\nOCR failed. Check troubleshooting guide.")
        return
    
    if not run_annotation():
        print("\nAnnotation failed. Check OCR output quality.")
        return
    
    if not run_training():
        print("\nTraining failed. Check training data format.")
        return
    
    if not run_evaluation():
        print("\nEvaluation failed, but model exists")
        print("   You can still test it manually")
    
    print_header("SETUP COMPLETE!")
    
    print("""
    Week 1: OCR Pipeline & Data Preparation - COMPLETE
    Week 2: NER Model Training & Evaluation - COMPLETE
    
    Your trained model is ready at: models/ner_model_v1/
    
    Next Steps:
       1. Review the evaluation F1-scores above
       2. Test manually: python src/models/test_model.py
       3. If scores are low, add more PDFs and retrain
    
    Need help? Check the implementation guide for troubleshooting.
    """)

if __name__ == "__main__":
    main()