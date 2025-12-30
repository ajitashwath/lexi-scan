import pytesseract
from pdf2image import convert_from_path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.preprocessing.image_utils import preprocess_image
import tempfile
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text_from_pdf(pdf_path, languages="eng"):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at: {pdf_path}")
    full_text = ""
    with tempfile.TemporaryDirectory() as temp_dir:
        image_paths = convert_from_path(
            pdf_path,
            dpi=300,
            output_folder=temp_dir,
            paths_only=True,
            poppler_path=r"C:\Users\AJIT ASHWATH R\Downloads\poppler-25.12.0\Library\bin"
        )
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