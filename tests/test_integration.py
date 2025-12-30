import unittest
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.postprocessing.rule_engine import apply_rules, deduplicate_entities


class TestEndToEndPipeline(unittest.TestCase):
    """Test complete extraction pipeline"""
    
    def test_complete_contract_extraction(self):
        """Simulate extraction from a complete contract"""
        # Simulated NER output (what model would extract)
        raw_entities = [
            ("15/01/2024", "EFFECTIVE_DATE"),
            ("31st December 2025", "EXPIRATION_DATE"),
            ("Rs. 10 lakh", "TOTAL_AMOUNT"),
            ("ABC Corporation Private Limited", "PARTY_NAME"),
            ("XYZ Industries Ltd.", "PARTY_NAME"),
            ("Mumbai", "JURISDICTION"),
            ("12.5% per annum", "INTEREST_RATE"),
        ]
        
        # Apply post-processing rules
        cleaned = apply_rules(raw_entities)
        final = deduplicate_entities(cleaned)
        
        # Verify all entities were processed
        self.assertGreater(len(final), 0)
        
        # Verify dates are standardized
        dates = [e for e in final if e['label'] in ['EFFECTIVE_DATE', 'EXPIRATION_DATE']]
        for date_entity in dates:
            # Should be in YYYY-MM-DD format
            self.assertRegex(date_entity['text'], r'\d{4}-\d{2}-\d{2}')
        
        # Verify amounts are standardized
        amounts = [e for e in final if e['label'] == 'TOTAL_AMOUNT']
        for amount_entity in amounts:
            # Should start with currency code
            self.assertRegex(amount_entity['text'], r'^[A-Z]{3} ')
    
    def test_noisy_ocr_extraction(self):
        """Test handling of noisy OCR output"""
        raw_entities = [
            ("Date:  15 / 01 / 2024  ", "EFFECTIVE_DATE"),  # Extra spaces
            ("Rs.  1,50,000/-", "TOTAL_AMOUNT"),  # Irregular formatting
            ("  ABC Corp  ", "PARTY_NAME"),  # Leading/trailing spaces
            ("", "JURISDICTION"),  # Empty extraction
            ("X", "PARTY_NAME"),  # Too short
        ]
        
        cleaned = apply_rules(raw_entities)
        final = deduplicate_entities(cleaned)
        
        # Should filter out invalid entities
        self.assertGreater(len(final), 0)
        
        # Verify no empty or too-short entities
        for entity in final:
            self.assertGreater(len(entity['text']), 1)
    
    def test_duplicate_handling(self):
        """Test that duplicates are properly removed"""
        raw_entities = [
            ("15/01/2024", "EFFECTIVE_DATE"),
            ("15-01-2024", "EFFECTIVE_DATE"),  # Same date, different format
            ("2024-01-15", "EFFECTIVE_DATE"),  # Same date, ISO format
            ("ABC Corp", "PARTY_NAME"),
            ("ABC Corp", "PARTY_NAME"),  # Exact duplicate
        ]
        
        cleaned = apply_rules(raw_entities)
        final = deduplicate_entities(cleaned)
        
        # Should have only 1 date and 1 party name
        dates = [e for e in final if e['label'] == 'EFFECTIVE_DATE']
        parties = [e for e in final if e['label'] == 'PARTY_NAME']
        
        self.assertEqual(len(dates), 1)
        self.assertEqual(len(parties), 1)


class TestQualityMetrics(unittest.TestCase):
    """Test quality and precision metrics"""
    
    def test_precision_on_clean_data(self):
        """All valid entities should pass through"""
        entities = [
            ("2024-01-15", "EFFECTIVE_DATE"),
            ("INR 50000", "TOTAL_AMOUNT"),
            ("Valid Company Name", "PARTY_NAME"),
        ]
        
        cleaned = apply_rules(entities)
        
        # All should pass
        self.assertEqual(len(cleaned), 3)
    
    def test_filtering_invalid_data(self):
        """Invalid entities should be filtered"""
        entities = [
            ("invalid", "EFFECTIVE_DATE"),
            ("not a number", "TOTAL_AMOUNT"),
            ("X", "PARTY_NAME"),
            ("", "JURISDICTION"),
        ]
        
        cleaned = apply_rules(entities)
        
        # All should be filtered
        self.assertEqual(len(cleaned), 0)


if __name__ == '__main__':
    unittest.main()