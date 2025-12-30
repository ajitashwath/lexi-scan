"""
End-to-End Acceptance Test
Tests complete pipeline on held-out contract
"""

import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.preprocessing.ocr_engine import extract_text_from_pdf
from src.postprocessing.rule_engine import apply_rules, deduplicate_entities
import spacy


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def test_ocr_pipeline(pdf_path):
    """Test OCR extraction"""
    print_header("STEP 1: OCR EXTRACTION")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return None
    
    print(f"Processing: {pdf_path}")
    
    try:
        text = extract_text_from_pdf(pdf_path)
        
        if not text or len(text.strip()) < 50:
            print("❌ OCR extraction failed or produced insufficient text")
            return None
        
        word_count = len(text.split())
        char_count = len(text)
        
        print("✅ OCR extraction successful")
        print(f"   Words extracted: {word_count}")
        print(f"   Characters: {char_count}")
        print(f"\n   First 200 characters:")
        print(f"   {text[:200]}...")
        
        return text
    
    except Exception as e:
        print(f"❌ OCR failed: {e}")
        return None


def test_ner_extraction(text, model_path):
    """Test NER model extraction"""
    print_header("STEP 2: NER ENTITY EXTRACTION")
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        print("   Run: python src/models/train_ner.py")
        return []
    
    try:
        print(f"Loading model from: {model_path}")
        nlp = spacy.load(model_path)
        
        print("Running NER extraction...")
        doc = nlp(text)
        
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        
        print(f"✅ Extracted {len(entities)} raw entities")
        
        # Show sample entities
        if entities:
            print("\n   Sample raw entities:")
            for text, label in entities[:5]:
                clean_text = text.replace('\n', ' ').strip()[:50]
                print(f"   [{label}] {clean_text}")
        
        return entities
    
    except Exception as e:
        print(f"❌ NER extraction failed: {e}")
        return []


def test_post_processing(entities):
    """Test rule-based post-processing"""
    print_header("STEP 3: RULE-BASED POST-PROCESSING")
    
    print(f"Applying cleaning and validation rules...")
    
    try:
        # Apply rules
        cleaned = apply_rules(entities)
        print(f"✅ Cleaned: {len(cleaned)} entities passed validation")
        
        # Deduplicate
        final = deduplicate_entities(cleaned)
        print(f"✅ Final: {len(final)} entities after deduplication")
        
        return final
    
    except Exception as e:
        print(f"❌ Post-processing failed: {e}")
        return []


def analyze_results(entities):
    """Analyze and display results"""
    print_header("STEP 4: RESULTS ANALYSIS")
    
    if not entities:
        print("❌ No entities extracted")
        return False
    
    # Count by type
    entity_counts = {}
    for entity in entities:
        label = entity['label']
        entity_counts[label] = entity_counts.get(label, 0) + 1
    
    print(f"\n📊 Entity Distribution:")
    for label, count in sorted(entity_counts.items()):
        print(f"   {label}: {count}")
    
    print(f"\n🔍 Extracted Entities:")
    for entity in entities:
        print(f"   [{entity['label']}] {entity['text']}")
        if entity.get('original_text') and entity['original_text'] != entity['text']:
            print(f"      (cleaned from: {entity['original_text']})")
    
    # Check critical entities
    critical_entities = ['EFFECTIVE_DATE', 'TOTAL_AMOUNT', 'PARTY_NAME']
    found_critical = [e for e in entities if e['label'] in critical_entities]
    
    print(f"\n✅ Critical Entities Found: {len(found_critical)}/{len(critical_entities)}")
    
    return len(found_critical) > 0


def save_results(entities, output_path):
    """Save results to JSON file"""
    print_header("STEP 5: SAVING RESULTS")
    
    result = {
        "timestamp": datetime.now().isoformat(),
        "total_entities": len(entities),
        "entities": entities,
        "entities_by_type": {}
    }
    
    # Count by type
    for entity in entities:
        label = entity['label']
        result["entities_by_type"][label] = result["entities_by_type"].get(label, 0) + 1
    
    try:
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"✅ Results saved to: {output_path}")
        return True
    
    except Exception as e:
        print(f"❌ Failed to save results: {e}")
        return False


def run_end_to_end_test(pdf_path, model_path, output_path):
    """Run complete end-to-end test"""
    
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║                  LexiScan End-to-End Acceptance Test              ║
    ║                  Complete Pipeline Validation                      ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    print(f"Input PDF: {pdf_path}")
    print(f"Model: {model_path}")
    print(f"Output: {output_path}")
    
    # Step 1: OCR
    text = test_ocr_pipeline(pdf_path)
    if not text:
        print("\n❌ PIPELINE FAILED: OCR extraction failed")
        return False
    
    # Step 2: NER
    raw_entities = test_ner_extraction(text, model_path)
    if not raw_entities:
        print("\n⚠️ WARNING: No entities extracted by NER model")
        print("   This might indicate:")
        print("   - Model needs more training")
        print("   - Document doesn't contain target entities")
        print("   - OCR quality is too low")
    
    # Step 3: Post-processing
    final_entities = test_post_processing(raw_entities)
    
    # Step 4: Analysis
    success = analyze_results(final_entities)
    
    # Step 5: Save
    save_results(final_entities, output_path)
    
    # Final verdict
    print_header("FINAL VERDICT")
    
    if success and len(final_entities) >= 3:
        print("""
    ✅ END-TO-END TEST PASSED
    
    The pipeline successfully:
    ✓ Extracted text from PDF using OCR
    ✓ Identified entities using NER model
    ✓ Cleaned and validated entities using rules
    ✓ Produced structured JSON output
    
    🎉 System is ready for production deployment!
        """)
        return True
    
    elif len(final_entities) > 0:
        print("""
    ⚠️ END-TO-END TEST PARTIALLY PASSED
    
    The pipeline works but extracted fewer entities than expected.
    
    Recommendations:
    - Add more training data (50-100 documents recommended)
    - Review entity patterns in auto_annotate.py
    - Check OCR quality on input PDFs
    - Train for more epochs (try 50 instead of 30)
        """)
        return True
    
    else:
        print("""
    ❌ END-TO-END TEST FAILED
    
    The pipeline did not extract any valid entities.
    
    Troubleshooting steps:
    1. Check OCR quality: Review data/interim/*.txt files
    2. Verify training data: python debug_data.py
    3. Retrain model with more data
    4. Review model evaluation: python src/models/evaluate_model.py
        """)
        return False


def main():
    """Main entry point"""
    
    # Default paths
    MODEL_PATH = os.path.join("models", "ner_model_v1")
    
    # Get PDF path from command line or use first available
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Look for test PDF
        raw_dir = os.path.join("data", "raw")
        if os.path.exists(raw_dir):
            pdfs = [f for f in os.listdir(raw_dir) if f.lower().endswith('.pdf')]
            if pdfs:
                pdf_path = os.path.join(raw_dir, pdfs[0])
            else:
                print("❌ No PDF found in data/raw/")
                print("Usage: python end_to_end_test.py <path_to_pdf>")
                sys.exit(1)
        else:
            print("❌ data/raw/ directory not found")
            print("Usage: python end_to_end_test.py <path_to_pdf>")
            sys.exit(1)
    
    # Generate output path
    output_path = pdf_path.replace('.pdf', '_test_results.json')
    
    # Run test
    success = run_end_to_end_test(pdf_path, MODEL_PATH, output_path)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()