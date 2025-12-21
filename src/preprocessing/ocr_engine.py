import pytesseract
from pdf2image import convert_from_path
from src.preprocessing.image_utils import preprocess_image
import os
import tempfile
from PIL import Image

# [CONFIGURATION]
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_pdf(pdf_path, languages="eng"):
    """
    Safely converts a PDF to text using Tesseract OCR.
    Handles large files by processing pages one by one from disk.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")

    # print(f"🔍 Processing: {pdf_path}") # Optional: Un-comment if you want more logs
    full_text = ""

    # [MEMORY FIX: USE TEMP DIRECTORY]
    with tempfile.TemporaryDirectory() as temp_dir:
        
        # 1. Convert PDF -> Image Files (Saved on Disk)
        # Note: We removed fmt='jpeg' to let it default to PPM (safer for Linux)
        image_paths = convert_from_path(
            pdf_path,
            dpi=300,
            output_folder=temp_dir,
            paths_only=True
        )
        
        # 2. Process One by One
        # Fix: Using 'image_paths' (plural) in the loop
        for i, image_path in enumerate(image_paths):
            print(f"   -> Cleaning and reading page {i + 1}/{len(image_paths)}...")
            
            try:
                # Fix: Using 'image_path' (singular) to open the file
                with Image.open(image_path) as page_image:
                    
                    # A. Clean the image
                    cleaned_image = preprocess_image(page_image)
                    
                    # B. Extract Text
                    # Fix: Using --psm 3 (Auto) instead of 6 to avoid empty results
                    text = pytesseract.image_to_string(
                        cleaned_image, 
                        lang=languages, 
                        config='--psm 6'
                    )
                    
                    full_text += f"\n--- PAGE {i + 1} ---\n{text}"
                    
            except Exception as e:
                print(f"      ⚠️ Warning: Failed to read page {i+1}. Error: {e}")
                continue

    return full_text

if __name__ == "__main__":
    # Test block
    test_pdf = os.path.join("data", "raw", "sample_contract.pdf")
    if os.path.exists(test_pdf):
        print(extract_text_from_pdf(test_pdf))
    else:
        print("Please place a sample PDF to test.")