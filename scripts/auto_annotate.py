import spacy
import re
import os
import json

# [CONFIGURATION]
INPUT_DIR = os.path.join("data", "interim")
OUTPUT_FILE = os.path.join("data", "processed", "train_data.jsonl")

nlp = spacy.load("en_core_web_sm")

# --- IMPROVED BLACKLIST ---
# We added "auditor", "auditee", "government", etc.
BLACKLIST = {
    "company", "party", "annexes", "agreement", "contract", "hereinafter", 
    "schedule", "page", "section", "clause", "eur", "usd", "inr", "jpy", 
    "rupees", "rs", "rss", "rupoos", "date", "place", "signed", "signature",
    "business", "exclusivity", "ui", "iso", "global negotiator",
    "auditor", "auditee", "government", "guidelines", "confidential information",
    "terms", "digital locker", "service provider", "information security",
    "client", "board of directors", "act", "rule", "regulations", "courts",
    "forums", "ministry", "department", "state", "central"
}

def find_entities(text):
    labels = []
    
    # 1. FIND DATES
    date_pattern = r'(\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})|(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})'
    for match in re.finditer(date_pattern, text, re.IGNORECASE):
        labels.append([match.start(), match.end(), "EFFECTIVE_DATE"])

    # 2. FIND MONEY (FIXED)
    # The regex [0-9] ensures there is at least one DIGIT. 
    # It prevents matching just "," or "." as money.
    money_pattern = r'(Rs\.?|INR|USD|\$|€|£|EUR|JPY)\s*[0-9][0-9,]*(\.\d{2})?'
    for match in re.finditer(money_pattern, text, re.IGNORECASE):
        labels.append([match.start(), match.end(), "TOTAL_AMOUNT"])

    # 3. FIND PARTIES (Stricter)
    doc = nlp(text)
    for ent in doc.ents:
        clean_text = ent.text.lower().strip().replace(".", "")
        
        # SKIP if in Blacklist
        if clean_text in BLACKLIST:
            continue
        # SKIP if it looks like a generic title (e.g. "The Auditor")
        if "auditor" in clean_text or "auditee" in clean_text:
            continue
            
        if len(clean_text) < 3:
            continue

        if ent.label_ in ["ORG", "PERSON"]:
            labels.append([ent.start_char, ent.end_char, "PARTY_NAME"])
        elif ent.label_ == "GPE":
            labels.append([ent.start_char, ent.end_char, "JURISDICTION"])

    # 4. CLEANUP (Remove Overlaps)
    labels = sorted(labels, key=lambda x: x[0])
    final_labels = []
    for label in labels:
        is_overlap = False
        start, end, _ = label
        for existing in final_labels:
            e_start, e_end, _ = existing
            if (start < e_end and end > e_start):
                is_overlap = True
                break
        if not is_overlap:
            final_labels.append(label)
            
    return final_labels

def main():
    if not os.path.exists(INPUT_DIR):
        print(f"❌ Error: {INPUT_DIR} does not exist.")
        return

    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]
    print(f"🤖 Auto-annotating {len(files)} documents (Final Polish)...")
    
    processed_count = 0
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f_out:
        for filename in files:
            file_path = os.path.join(INPUT_DIR, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f_in:
                    text = f_in.read()
                    # Garbage Filter
                    if len(text.split()) > 0:
                        if (sum(len(w) for w in text.split()) / len(text.split())) < 3: 
                            continue 

                    labels = find_entities(text)
                    if labels:
                        data = {"text": text, "label": labels}
                        f_out.write(json.dumps(data) + "\n")
                        processed_count += 1
            except Exception:
                pass

    print(f"✅ Training Data Updated! ({processed_count} docs)")

if __name__ == "__main__":
    main()