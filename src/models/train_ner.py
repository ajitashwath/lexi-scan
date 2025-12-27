import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding
import random
import json
import os

TRAIN_DATA_PATH = os.path.join("data", "processed", "train_data.jsonl")
MODEL_OUTPUT_DIR = os.path.join("models", "ner_model_v1")
ITERATIONS = 30
DROPOUT = 0.35

def load_doccano_data(file_path):
    data = []
    if not os.path.exists(file_path):
        print(f"Error: Training data not found at {file_path}")
        print("Tip: Run scripts/auto_annotate.py first!")
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
                text = item['text']
                entities = [(start, end, label) for start, end, label in item['label']]
                data.append((text, {"entities": entities}))
            except Exception as e:
                print(f"Warning: Skipped malformed line: {e}")
                continue
    print(f"Loaded {len(data)} training documents")
    return data

def create_training_examples(nlp, train_data):
    examples = []
    dropped_entities = 0
    dropped_docs = 0
    print("Creating training examples...")
    for text, annots in train_data:
        doc = nlp.make_doc(text)
        valid_ents = []
        for start, end, label in annots["entities"]:
            span = doc.char_span(start, end, label=label, alignment_mode="contract")
            if span is None:
                span = doc.char_span(start, end, label=label, alignment_mode="expand")
            if span:
                valid_ents.append(span)
            else:
                dropped_entities += 1
        if valid_ents:
            doc.ents = valid_ents
            example = Example.from_dict(doc, {"entities": [(e.start_char, e.end_char, e.label_) for e in valid_ents]})
            examples.append(example)
        else:
            dropped_docs += 1
    if dropped_entities > 0:
        print(f"Dropped {dropped_entities} misaligned entities")
    if dropped_docs > 0:
        print(f"Dropped {dropped_docs} documents with no valid entities")
    return examples

def train_model():
    TRAIN_DATA = load_doccano_data(TRAIN_DATA_PATH)
    if len(TRAIN_DATA) == 0:
        print("No training data found. Exiting.")
        return
    if len(TRAIN_DATA) < 20:
        print("WARNING: Very small training set. Results may be poor.")
        print("Recommended: At least 50-100 annotated documents")
    nlp = spacy.blank("en")
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner", last=True)
    else:
        ner = nlp.get_pipe("ner")
    print("Adding entity labels...")
    labels_added = set()
    for _, annotations in TRAIN_DATA:
        for start, end, label in annotations.get("entities"):
            if label not in labels_added:
                ner.add_label(label)
                labels_added.add(label)
                print(f"   + {label}")
    examples = create_training_examples(nlp, TRAIN_DATA)
    if len(examples) == 0:
        print("CRITICAL: No valid training examples created!")
        print("This usually means entity positions don't align with text.")
        return
    print(f"Training on {len(examples)} valid examples...")
    print(f"   Iterations: {ITERATIONS}")
    print(f"   Dropout: {DROPOUT}")
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.initialize()
        print("Training Progress:")
        print("-" * 50)
        for iteration in range(ITERATIONS):
            random.shuffle(examples)
            losses = {}
            batches = minibatch(examples, size=compounding(4.0, 32.0, 1.001))
            for batch in batches:
                nlp.update(
                    batch,
                    drop=DROPOUT,
                    losses=losses
                )
            if (iteration + 1) % 5 == 0 or iteration == 0:
                loss_value = losses.get('ner', 0.0)
                print(f"Epoch {iteration + 1:02d}/{ITERATIONS} | Loss: {loss_value:.4f}")
        print("-" * 50)
    if not os.path.exists(MODEL_OUTPUT_DIR):
        os.makedirs(MODEL_OUTPUT_DIR)
    nlp.to_disk(MODEL_OUTPUT_DIR)
    print(f"Model saved successfully!")
    print(f"   Location: {MODEL_OUTPUT_DIR}")
    print(f"Next steps:")
    print(f"   1. Run: python src/models/test_model.py")
    print(f"   2. Run: python src/models/evaluate_model.py")

if __name__ == "__main__":
    train_model()