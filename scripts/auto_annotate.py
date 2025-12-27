import spacy
import re
import os
import json

INPUT_DIR = os.path.join("data", "interim")
OUTPUT_FILE = os.path.join("data", "processed", "train_data.jsonl")

nlp = spacy.load("en_core_web_sm")

BLACKLIST = {
    "company", "party", "annexes", "agreement", "contract", "hereinafter",
    "schedule", "page", "section", "clause", "eur", "usd", "inr", "jpy",
    "rupees", "rs", "date", "place", "signed", "signature",
    "business", "exclusivity", "auditor", "auditee", "government",
    "guidelines", "confidential information", "terms", "service provider",
    "client", "board of directors", "act", "rule", "regulations", "courts",
    "ministry", "department", "state", "central", "herein", "thereof",
    "whereas", "witnesseth", "parties", "undersigned", "executed"
}

def is_valid_entity(text, label):
    clean = text.lower().strip().replace(".", "").replace(",", "")
    if clean in BLACKLIST:
        return False
    if len(clean) < 3 and label != "TOTAL_AMOUNT":
        return False
    special_ratio = sum(1 for c in clean if not c.isalnum()) / max(len(clean), 1)
    if special_ratio > 0.5:
        return False
    return True

def find_entities(text):
    labels = []
    date_patterns = [
        r'\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{4}\b',
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b\d{4}-\d{2}-\d{2}\b'
    ]
    for pattern in date_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            labels.append([match.start(), match.end(), "EFFECTIVE_DATE"])
    money_patterns = [
        r'(?:Rs\.?|INR|USD|\$|€|£|EUR)\s*\d[\d,]*(?:\.\d{2})?(?:\s*(?:crore|lakh|thousand|million|billion))?',
        r'\d[\d,]*(?:\.\d{2})?\s*(?:crore|lakh|thousand|million|billion)\s*(?:rupees|dollars|euros)',
        r'(?:rupees|dollars)\s+\d[\d,]*(?:\.\d{2})?'
    ]
    for pattern in money_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            if any(c.isdigit() for c in match.group()):
                labels.append([match.start(), match.end(), "TOTAL_AMOUNT"])
    doc = nlp(text)
    for ent in doc.ents:
        if not is_valid_entity(ent.text, ent.label_):
            continue
        if ent.label_ in ["ORG", "PERSON"]:
            labels.append([ent.start_char, ent.end_char, "PARTY_NAME"])
        elif ent.label_ == "GPE":
            labels.append([ent.start_char, ent.end_char, "JURISDICTION"])
    labels = sorted(labels, key=lambda x: (x[0], -(x[1] - x[0])))
    final_labels = []
    for label in labels:
        start, end, label_type = label
        is_overlap = False
        for existing in final_labels:
            e_start, e_end, _ = existing
            if start < e_end and end > e_start:
                is_overlap = True
                break
        if not is_overlap:
            final_labels.append(label)
    return final_labels

def is_valid_document(text):
    if len(text.strip()) < 100:
        return False
    words = text.split()
    if len(words) == 0:
        return False
    avg_word_len = sum(len(w) for w in words) / len(words)
    if avg_word_len < 3:
        return False
    alpha_ratio = sum(c.isalpha() or c.isspace() for c in text) / len(text)
    if alpha_ratio < 0.6:
        return False
    return True

def main():
    if not os.path.exists(INPUT_DIR):
        print(f"Error: {INPUT_DIR} does not exist.")
        return
    
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]
    print(f"Auto-annotating {len(files)} documents...")
    
    processed_count = 0
    skipped_count = 0
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
        for filename in files:
            file_path = os.path.join(INPUT_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f_in:
                    text = f_in.read()
                
                # Quality check
                if not is_valid_document(text):
                    skipped_count += 1
                    continue
                
                labels = find_entities(text)
                
                # Only save documents with entities
                if labels:
                    data = {"text": text, "label": labels}
                    f_out.write(json.dumps(data) + "\n")
                    processed_count += 1
                    
            except Exception as e:
                print(f"Error processing {filename}: {e}")
                skipped_count += 1
    
    print(f"Annotation Complete!")
    print(f"   Processed: {processed_count} documents")
    print(f"   Skipped: {skipped_count} documents (low quality)")

if __name__ == "__main__":
    main()