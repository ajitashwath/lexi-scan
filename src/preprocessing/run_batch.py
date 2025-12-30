import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.preprocessing.ocr_engine import extract_text_from_pdf

RAW_DIR = os.path.join("data", "raw")
INTERIM_DIR = os.path.join("data", "interim")

os.makedirs(INTERIM_DIR, exist_ok=True)

def is_valid_extraction(text):
    if not text or len(text.strip()) < 50:
        return False
    words = text.split()
    if len(words) < 10:
        return False
    avg_word_length = sum(len(w) for w in words) / len(words)
    if avg_word_length < 2:
        return False
    return True

def process_pdfs():
    pdf_files = [f for f in os.listdir(RAW_DIR) if f.lower().endswith('.pdf')]
    if len(pdf_files) == 0:
        print(f"No PDF files found in {RAW_DIR}")
        print("Please add PDF contracts to the 'data/raw/' folder")
        return
    pdf_files.sort()
    print(f"Found {len(pdf_files)} PDF files to process")
    print("=" * 60)
    success_count = 0
    failed_count = 0
    empty_count = 0
    for index, pdf_file in enumerate(pdf_files, 1):
        input_path = os.path.join(RAW_DIR, pdf_file)
        output_filename = pdf_file.replace('.pdf', '.txt').replace('.PDF', '.txt')
        output_path = os.path.join(INTERIM_DIR, output_filename)
        print(f"\n[{index}/{len(pdf_files)}] Processing: {pdf_file}")
        print("-" * 40)
        try:
            text = extract_text_from_pdf(input_path)
            if is_valid_extraction(text):
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                word_count = len(text.split())
                print(f"   Success: {word_count} words extracted")
                success_count += 1
            else:
                print(f"   Warning: Empty or low-quality extraction")
                print(f"      This PDF may be:")
                print(f"      - Image-only with poor OCR quality")
                print(f"      - Encrypted or password-protected")
                print(f"      - Corrupted")
                empty_count += 1
        except Exception as e:
            print(f"   Failed: {str(e)[:100]}")
            failed_count += 1
    print("\n" + "=" * 60)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Successful: {success_count}/{len(pdf_files)}")
    print(f"Empty/Low Quality: {empty_count}/{len(pdf_files)}")
    print(f"Failed: {failed_count}/{len(pdf_files)}")
    if success_count == 0:
        print("\nTROUBLESHOOTING:")
        print("   1. Check if PDFs are image-based (scanned documents)")
        print("   2. Ensure Tesseract OCR is properly installed")
        print("   3. Try opening PDFs manually to verify they're not corrupted")
        print("   4. For Windows: Set tesseract path in ocr_engine.py")
    elif success_count < len(pdf_files) * 0.5:
        print("\nMANY FILES FAILED:")
        print("   Consider reviewing failed PDFs manually")
        print("   OCR quality may be low for scanned documents")
    else:
        print("\nReady for annotation!")
        print("   Next step: python scripts/auto_annotate.py")

if __name__ == "__main__":
    process_pdfs()