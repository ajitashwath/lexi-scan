import os
from src.preprocessing.ocr_engine import extract_text_from_pdf

# PATHS
RAW_DIR = os.path.join("data", "raw")
INTERIM_DIR = os.path.join("data", "interim")

# Ensure output directory exists
os.makedirs(INTERIM_DIR, exist_ok=True)

# Get all PDF files
pdf_files = [f for f in os.listdir(RAW_DIR) if f.endswith('.pdf')]
pdf_files.sort() # Optional: Sorts them alphabetically

print(f"Found {len(pdf_files)} PDFs to process...")

for index, pdf_file in enumerate(pdf_files):
    input_path = os.path.join(RAW_DIR, pdf_file)
    output_filename = pdf_file.replace('.pdf', '.txt')
    output_path = os.path.join(INTERIM_DIR, output_filename)
    
    # [DISABLED SKIP LOGIC]
    # We commented this out so it ALWAYS runs, fixing the "skipped empty files" issue.
    # if os.path.exists(output_path):
    #     print(f"Skipping {pdf_file} (already done)")
    #     continue

    try:
        print(f"[{index+1}/{len(pdf_files)}] Processing {pdf_file}...")
        
        # Call the engine
        text = extract_text_from_pdf(input_path)
        
        # Save output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
            
    except Exception as e:
        print(f"❌ Failed on {pdf_file}: {e}")

print("✅ Batch processing complete!")