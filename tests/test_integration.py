import unittest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.postprocessing.rule_engine import apply_rules, deduplicate_entities


class TestEndToEndPipeline(unittest.TestCase):
    
    def test_complete_contract_extraction(self):
        raw_entities = [
            ("15/01/2024", "EFFECTIVE_DATE"),
            ("31st December 2025", "EXPIRATION_DATE"),
            ("Rs. 10 lakh", "TOTAL_AMOUNT"),
            ("ABC Corporation Private Limited", "PARTY_NAME"),
            ("XYZ Industries Ltd.", "PARTY_NAME"),
            ("Mumbai", "JURISDICTION"),
            ("12.5% per annum", "INTEREST_RATE"),
        ]
        
        cleaned = apply_rules(raw_entities)
        final = deduplicate_entities(cleaned)
        
        self.assertGreater(len(final), 0)
        
        dates = [e for e in final if e['label'] in ['EFFECTIVE_DATE', 'EXPIRATION_DATE']]
        for date_entity in dates:
            self.assertRegex(date_entity['text'], r'\d{4}-\d{2}-\d{2}')
        
        amounts = [e for e in final if e['label'] == 'TOTAL_AMOUNT']
        for amount_entity in amounts:
            self.assertRegex(amount_entity['text'], r'^[A-Z]{3} ')
    
    def test_noisy_ocr_extraction(self):
        raw_entities = [
            ("Date:  15 / 01 / 2024  ", "EFFECTIVE_DATE"),
            ("Rs.  1,50,000/-", "TOTAL_AMOUNT"),
            ("  ABC Corp  ", "PARTY_NAME"),
            ("", "JURISDICTION"),
            ("X", "PARTY_NAME"),
        ]
        
        cleaned = apply_rules(raw_entities)
        final = deduplicate_entities(cleaned)
        
        self.assertGreater(len(final), 0)
        
        for entity in final:
            self.assertGreater(len(entity['text']), 1)
    
    def test_duplicate_handling(self):
        raw_entities = [
            ("15/01/2024", "EFFECTIVE_DATE"),
            ("15-01-2024", "EFFECTIVE_DATE"),
            ("2024-01-15", "EFFECTIVE_DATE"),
            ("ABC Corp", "PARTY_NAME"),
            ("ABC Corp", "PARTY_NAME"),
        ]
        
        cleaned = apply_rules(raw_entities)
        final = deduplicate_entities(cleaned)
        
        dates = [e for e in final if e['label'] == 'EFFECTIVE_DATE']
        parties = [e for e in final if e['label'] == 'PARTY_NAME']
        
        self.assertEqual(len(dates), 1)
        self.assertEqual(len(parties), 1)


class TestQualityMetrics(unittest.TestCase):
    
    def test_precision_on_clean_data(self):
        entities = [
            ("2024-01-15", "EFFECTIVE_DATE"),
            ("INR 50000", "TOTAL_AMOUNT"),
            ("Valid Company Name", "PARTY_NAME"),
        ]
        
        cleaned = apply_rules(entities)
        
        self.assertEqual(len(cleaned), 3)
    
    def test_filtering_invalid_data(self):
        entities = [
            ("invalid", "EFFECTIVE_DATE"),
            ("not a number", "TOTAL_AMOUNT"),
            ("X", "PARTY_NAME"),
            ("", "JURISDICTION"),
        ]
        
        cleaned = apply_rules(entities)
        
        self.assertEqual(len(cleaned), 0)


if __name__ == '__main__':
    unittest.main()