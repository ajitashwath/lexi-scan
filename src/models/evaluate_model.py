import spacy
from spacy.scorer import Scorer
from spacy.training import Example
import json
import os
import random

MODEL_PATH = os.path.join("models", "ner_model_v1")
TEST_DATA_PATH = os.path.join("data", "processed", "train_data.jsonl")
TEST_SPLIT = 0.2

def load_test_data(file_path, split_ratio=0.2):
    all_data = []
    if not os.path.exists(file_path):
        print(f"Error: Data not found at {file_path}")
        return []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
                text = item['text']
                entities = [(start, end, label) for start, end, label in item['label']]
                all_data.append((text, {"entities": entities}))
            except:
                continue
    random.shuffle(all_data)
    split_idx = int(len(all_data) * split_ratio)
    test_data = all_data[:split_idx] if split_idx > 0 else all_data[:10]
    print(f"Loaded {len(test_data)} test documents")
    return test_data

def create_examples(nlp, test_data):
    examples = []
    for text, annots in test_data:
        pred_doc = nlp(text)
        gold_doc = nlp.make_doc(text)
        valid_ents = []
        for start, end, label in annots["entities"]:
            span = gold_doc.char_span(start, end, label=label, alignment_mode="contract")
            if span:
                valid_ents.append(span)
        if valid_ents:
            gold_doc.ents = valid_ents
            example = Example(pred_doc, gold_doc)
            examples.append(example)
    return examples

def calculate_entity_f1(examples):
    scores_per_label = {}
    for label in ["PARTY_NAME", "EFFECTIVE_DATE", "TOTAL_AMOUNT", "JURISDICTION"]:
        tp = 0
        fp = 0
        fn = 0
        for example in examples:
            pred_ents = [e for e in example.predicted.ents if e.label_ == label]
            gold_ents = [e for e in example.reference.ents if e.label_ == label]
            pred_set = {(e.start_char, e.end_char, e.label_) for e in pred_ents}
            gold_set = {(e.start_char, e.end_char, e.label_) for e in gold_ents}
            tp += len(pred_set & gold_set)
            fp += len(pred_set - gold_set)
            fn += len(gold_set - pred_set)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        scores_per_label[label] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': tp + fn
        }
    return scores_per_label

def evaluate_model():
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model not found at {MODEL_PATH}")
        print("Tip: Train the model first using src/models/train_ner.py")
        return
    print(f"Loading model from {MODEL_PATH}...")
    nlp = spacy.load(MODEL_PATH)
    test_data = load_test_data(TEST_DATA_PATH, TEST_SPLIT)
    if len(test_data) == 0:
        print("No test data available")
        return
    print("Preparing evaluation examples...")
    examples = create_examples(nlp, test_data)
    if len(examples) == 0:
        print("No valid test examples created")
        return
    print("\n" + "="*60)
    print("OVERALL MODEL PERFORMANCE")
    print("="*60)
    scorer = Scorer()
    scores = scorer.score(examples)
    print(f"\nOverall NER Metrics:")
    print(f"   Precision: {scores['ents_p']:.2%}")
    print(f"   Recall:    {scores['ents_r']:.2%}")
    print(f"   F1-Score:  {scores['ents_f']:.2%}")
    print("\n" + "="*60)
    print("PER-ENTITY PERFORMANCE")
    print("="*60)
    per_label_scores = calculate_entity_f1(examples)
    critical_labels = ["EFFECTIVE_DATE", "TOTAL_AMOUNT"]
    print("\nCRITICAL ENTITIES:\n")
    for label in critical_labels:
        if label in per_label_scores:
            score = per_label_scores[label]
            print(f"{label}:")
            print(f"   Precision: {score['precision']:.2%}")
            print(f"   Recall:    {score['recall']:.2%}")
            print(f"   F1-Score:  {score['f1']:.2%}")
            print(f"   Support:   {score['support']} entities")
            print()
    print("OTHER ENTITIES:\n")
    for label in ["PARTY_NAME", "JURISDICTION"]:
        if label in per_label_scores:
            score = per_label_scores[label]
            print(f"{label}:")
            print(f"   F1-Score: {score['f1']:.2%} (Support: {score['support']})")
            print()
    print("="*60)
    print("RECOMMENDATIONS")
    print("="*60)
    avg_critical_f1 = sum(per_label_scores[l]['f1'] for l in critical_labels if l in per_label_scores) / len(critical_labels)
    if avg_critical_f1 >= 0.75:
        print("EXCELLENT: Model meets production standards!")
    elif avg_critical_f1 >= 0.60:
        print("GOOD: Model is functional but could be improved")
        print("   - Add more training examples (target: 100+ documents)")
        print("   - Review and fix annotation errors")
    else:
        print("NEEDS IMPROVEMENT:")
        print("   - Increase training data significantly")
        print("   - Check if entities are properly annotated")
        print("   - Review entity patterns in auto_annotate.py")
        print("   - Consider training for more epochs (try 50)")
    print("\n" + "="*60)

if __name__ == "__main__":
    evaluate_model()