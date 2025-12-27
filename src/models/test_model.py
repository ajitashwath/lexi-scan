import spacy
import os
import random

MODEL_PATH = os.path.join("models", "ner_model_v1")
TEST_DATA_DIR = os.path.join("data", "interim")

def test_model():
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model not found at {MODEL_PATH}")
        return
    print(f"Loading model from: {MODEL_PATH}...")
    nlp = spacy.load(MODEL_PATH)
    print("Model loaded successfully")
    files = [f for f in os.listdir(TEST_DATA_DIR) if f.endswith(".txt")]
    if not files:
        print("No test files found to test")
        return
    random_file = random.choice(files)
    file_path = os.path.join(TEST_DATA_DIR, random_file)
    print(f"\n --- Testing on file: {random_file} ---")
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    doc = nlp(text)
    if not doc.ents:
        print("The model found NO entities")
    else:
        print(f"\nFound {len(doc.ents)} entities:\n")
        for ent in doc.ents:
            clean_text = ent.text.replace("\n", " ").strip()
            print(f"{clean_text:<30} | {ent.label_}")

if __name__ == "__main__":
    test_model()