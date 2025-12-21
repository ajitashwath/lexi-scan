import spacy
from spacy.tokens import DocBin
from spacy.training import Example
from spacy.util import minibatch, compounding
import random
import json
import os

# [CONFIGURATION]
TRAIN_DATA_PATH = os.path.join("data", "processed", "train_data.jsonl")
MODEL_OUTPUT_DIR = os.path.join("models", "ner_model_v1")
ITERATIONS = 30

def load_doccano_data(file_path):
    """
    Reads the JSONL file exported from Doccano.
    """
    data = []
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at {file_path}")
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            text = item['text']
            # Doccano stores labels as [start, end, label]
            entities = [(start, end, label) for start, end, label in item['label']]
            data.append((text, {"entities": entities}))
    
    print(f"✅ Loaded {len(data)} raw documents.")
    return data

def train_model():
    # 1. Load Data
    TRAIN_DATA = load_doccano_data(TRAIN_DATA_PATH)
    if not TRAIN_DATA:
        return

    # 2. Setup SpaCy Model
    nlp = spacy.blank("en") 
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")

    # 3. Add Labels
    for _, annotations in TRAIN_DATA:
        for ent in annotations.get("entities"):
            ner.add_label(ent[2])

    # 4. Prepare Data (The "Forgiving" Logic)
    examples = []
    dropped_entities = 0
    
    print("Alignment check in progress...")
    
    for text, annots in TRAIN_DATA:
        doc = nlp.make_doc(text)
        valid_ents = []
        
        for start, end, label in annots["entities"]:
            # Try to snap to valid token boundaries
            # alignment_mode="contract" fixes spaces like " $500" -> "$500"
            span = doc.char_span(start, end, label=label, alignment_mode="contract")
            
            if span is None:
                # If that fails, try expanding to the whole word
                span = doc.char_span(start, end, label=label, alignment_mode="expand")
            
            if span:
                valid_ents.append(span)
            else:
                dropped_entities += 1
                # Use this print to debug specific bad labels if needed
                # print(f"⚠️ Dropped invalid label: '{text[start:end]}' ({label})")

        # Only add documents that have at least one valid entity
        if valid_ents:
            doc.ents = valid_ents
            example = Example(doc, doc)
            examples.append(example)

    print(f"ℹ️  Info: Dropped {dropped_entities} individual bad labels (whitespace issues).")
    print(f"🚀 Starting training with {len(examples)} valid documents...")

    if len(examples) == 0:
        print("❌ CRITICAL: No valid data found. Check your Doccano export format.")
        return

    # 5. Training Loop
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.begin_training()
        
        for itn in range(ITERATIONS):
            random.shuffle(examples)
            losses = {}
            batches = minibatch(examples, size=compounding(4.0, 32.0, 1.001))
            
            for batch in batches:
                nlp.update(batch, drop=0.35, losses=losses)
            
            # Print progress
            if (itn + 1) % 5 == 0:
                print(f"Epoch {itn + 1}/{ITERATIONS} - Loss: {losses.get('ner', 0.0):.2f}")

    # 6. Save Model
    if not os.path.exists(MODEL_OUTPUT_DIR):
        os.makedirs(MODEL_OUTPUT_DIR)
    nlp.to_disk(MODEL_OUTPUT_DIR)
    print(f"🎉 Model saved successfully to: {MODEL_OUTPUT_DIR}")

if __name__ == "__main__":
    train_model()