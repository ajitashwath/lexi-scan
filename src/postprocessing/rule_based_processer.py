import re
from datetime import datetime
from typing import List, Dict, Tuple

class RuleBasedProcessor:
    """Post-processes NER outputs to improve precision"""
    
    def __init__(self):
        self.date_patterns = [
            (r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{4})\b', '%d %B %Y'),
            (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', '%d/%m/%Y'),
            (r'\b(\d{4})-(\d{2})-(\d{2})\b', '%Y-%m-%d'),
        ]
        
        self.month_map = {
            'jan': '01', 'january': '01',
            'feb': '02', 'february': '02',
            'mar': '03', 'march': '03',
            'apr': '04', 'april': '04',
            'may': '05',
            'jun': '06', 'june': '06',
            'jul': '07', 'july': '07',
            'aug': '08', 'august': '08',
            'sep': '09', 'september': '09',
            'oct': '10', 'october': '10',
            'nov': '11', 'november': '11',
            'dec': '12', 'december': '12',
        }
    
    def normalize_date(self, date_str: str) -> str:
        """Convert any date format to ISO 8601 (YYYY-MM-DD)"""
        date_str = date_str.strip()
        
        # Try standard formats first
        for pattern, fmt in self.date_patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    # Handle month name format
                    if any(month in date_str.lower() for month in self.month_map):
                        day = match.group(1)
                        month = self.month_map[match.group(2).lower()[:3]]
                        year = match.group(3)
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    
                    # Handle numeric formats
                    if '/' in date_str or '-' in date_str:
                        parts = re.split('[/-]', date_str)
                        if len(parts) == 3:
                            if len(parts[0]) == 4:  # YYYY-MM-DD
                                return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                            else:  # DD/MM/YYYY
                                return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                except:
                    pass
        
        return date_str  # Return original if parsing fails
    
    def normalize_amount(self, amount_str: str) -> Dict[str, str]:
        """Standardize monetary amounts"""
        amount_str = amount_str.strip()
        
        # Extract currency
        currency = 'INR'  # Default
        if any(x in amount_str.upper() for x in ['USD', '$']):
            currency = 'USD'
        elif any(x in amount_str.upper() for x in ['EUR', '€']):
            currency = 'EUR'
        elif any(x in amount_str.upper() for x in ['GBP', '£']):
            currency = 'GBP'
        
        # Extract numeric value
        numeric = re.sub(r'[^\d,.]', '', amount_str)
        numeric = numeric.replace(',', '')
        
        # Handle Indian notation (crore, lakh)
        multiplier = 1
        lower = amount_str.lower()
        if 'crore' in lower:
            multiplier = 10000000
        elif 'lakh' in lower:
            multiplier = 100000
        elif 'thousand' in lower:
            multiplier = 1000
        elif 'million' in lower:
            multiplier = 1000000
        elif 'billion' in lower:
            multiplier = 1000000000
        
        try:
            value = float(numeric) * multiplier
            return {
                'raw': amount_str,
                'normalized': f"{value:.2f}",
                'currency': currency
            }
        except:
            return {
                'raw': amount_str,
                'normalized': amount_str,
                'currency': currency
            }
    
    def clean_party_name(self, party_str: str) -> str:
        """Clean up party names"""
        # Remove common noise
        noise_words = [
            'hereinafter', 'referred to as', 'the party', 'party of',
            'witnesseth', 'whereas', 'represented by'
        ]
        
        cleaned = party_str.strip()
        for noise in noise_words:
            cleaned = re.sub(noise, '', cleaned, flags=re.IGNORECASE)
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Remove trailing punctuation
        cleaned = cleaned.rstrip(',.;:')
        
        return cleaned
    
    def validate_entity(self, text: str, label: str) -> bool:
        """Validate if entity makes sense for its label"""
        text = text.strip()
        
        # Minimum length check
        if len(text) < 2:
            return False
        
        # Label-specific validation
        if label == 'EFFECTIVE_DATE' or label == 'EXPIRATION_DATE':
            # Must contain numbers
            if not any(c.isdigit() for c in text):
                return False
            # Too short for a date
            if len(text) < 6:
                return False
        
        elif label == 'TOTAL_AMOUNT':
            # Must contain numbers
            if not any(c.isdigit() for c in text):
                return False
        
        elif label == 'PARTY_NAME':
            # Should have some letters
            if not any(c.isalpha() for c in text):
                return False
            # Too short
            if len(text) < 3:
                return False
        
        elif label == 'JURISDICTION':
            # Should be mostly letters
            alpha_ratio = sum(c.isalpha() or c.isspace() for c in text) / len(text)
            if alpha_ratio < 0.5:
                return False
        
        return True
    
    def process_entities(self, entities: List[Tuple[str, str]]) -> List[Dict]:
        """Process and standardize all entities"""
        processed = []
        
        for text, label in entities:
            # Validate
            if not self.validate_entity(text, label):
                continue
            
            # Normalize based on type
            normalized_text = text
            metadata = {}
            
            if label in ['EFFECTIVE_DATE', 'EXPIRATION_DATE']:
                normalized_text = self.normalize_date(text)
                metadata['original'] = text
            
            elif label == 'TOTAL_AMOUNT':
                amount_data = self.normalize_amount(text)
                normalized_text = amount_data['normalized']
                metadata = {
                    'original': amount_data['raw'],
                    'currency': amount_data['currency']
                }
            
            elif label == 'PARTY_NAME':
                normalized_text = self.clean_party_name(text)
            
            processed.append({
                'text': normalized_text,
                'label': label,
                'metadata': metadata
            })
        
        return processed
    
    def deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """Remove duplicate entities"""
        seen = set()
        unique = []
        
        for entity in entities:
            key = (entity['text'].lower(), entity['label'])
            if key not in seen:
                seen.add(key)
                unique.append(entity)
        
        return unique


if __name__ == "__main__":
    # Test the processor
    processor = RuleBasedProcessor()
    
    # Test date normalization
    test_dates = [
        "15th March 2024",
        "15/03/2024",
        "2024-03-15",
        "15-3-2024"
    ]
    
    print("Date Normalization Tests:")
    for date in test_dates:
        print(f"  {date} -> {processor.normalize_date(date)}")
    
    # Test amount normalization
    test_amounts = [
        "Rs. 50,00,000",
        "INR 5 crore",
        "$1,000,000",
        "USD 1 million"
    ]
    
    print("\nAmount Normalization Tests:")
    for amount in test_amounts:
        result = processor.normalize_amount(amount)
        print(f"  {amount} -> {result['normalized']} {result['currency']}")
    
    # Test entity processing
    test_entities = [
        ("15th March 2024", "EFFECTIVE_DATE"),
        ("Rs. 50 lakh", "TOTAL_AMOUNT"),
        ("ABC Corporation Pvt. Ltd.", "PARTY_NAME"),
        ("Delhi", "JURISDICTION")
    ]
    
    print("\nEntity Processing Tests:")
    processed = processor.process_entities(test_entities)
    for entity in processed:
        print(f"  {entity['label']}: {entity['text']}")
        if entity['metadata']:
            print(f"    Metadata: {entity['metadata']}")