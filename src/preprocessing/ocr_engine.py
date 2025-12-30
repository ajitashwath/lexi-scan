import pytesseract
from pdf2image import convert_from_path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.preprocessing.image_utils import preprocess_image
import tempfile
from PIL import Image

# Set Tesseract path based on OS
if os.name == 'nt':  # Windows
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    # If not found, try default installation path
    elif os.path.exists(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
# Linux/Docker: tesseract should be in PATH, no need to set

def extract_text_from_pdf(pdf_path, languages="eng"):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")
    full_text = ""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set poppler path only on Windows if custom path exists
        poppler_path = None
        if os.name == 'nt':
            custom_poppler = r"C:\Users\AJIT ASHWATH R\Downloads\poppler-25.12.0\Library\bin"
            if os.path.exists(custom_poppler):
                poppler_path = custom_poppler
        
        convert_kwargs = {
            'dpi': 300,
            'output_folder': temp_dir,
            'paths_only': True
        }
        if poppler_path:
            convert_kwargs['poppler_path'] = poppler_path
        
        image_paths = convert_from_path(pdf_path, **convert_kwargs)
        for i, image_path in enumerate(image_paths):
            print(f"   -> Cleaning and reading page {i + 1}/{len(image_paths)}...")
            try:
                with Image.open(image_path) as page_image:
                    cleaned_image = preprocess_image(page_image)
                    text = pytesseract.image_to_string(
                        cleaned_image,
                        lang=languages,
                        config='--psm 6'
                    )
                    full_text += f"\n--- PAGE {i + 1} ---\n{text}"
            except Exception as e:
                print(f"      Warning: Failed to read page {i+1}. Error: {e}")
                continue
    return full_text

if __name__ == "__main__":
    test_pdf = os.path.join("data", "raw", "sample_contract.pdf")
    if os.path.exists(test_pdf):
        print(extract_text_from_pdf(test_pdf))
    else:
        print("Please place a sample PDF to test.")