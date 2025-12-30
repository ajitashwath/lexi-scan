import re
from datetime import datetime
from typing import List, Dict, Tuple

class RuleBasedProcessor:
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
        date_str = date_str.strip()
        
        for pattern, fmt in self.date_patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    if any(month in date_str.lower() for month in self.month_map):
                        day = match.group(1)
                        month = self.month_map[match.group(2).lower()[:3]]
                        year = match.group(3)
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    
                    if '/' in date_str or '-' in date_str:
                        parts = re.split('[/-]', date_str)
                        if len(parts) == 3:
                            if len(parts[0]) == 4:
                                return f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                            else:
                                return f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                except:
                    pass
        
        return date_str
    
    def normalize_amount(self, amount_str: str) -> Dict[str, str]:
        amount_str = amount_str.strip()
        
        currency = 'INR'
        if any(x in amount_str.upper() for x in ['USD', '$']):
            currency = 'USD'
        elif any(x in amount_str.upper() for x in ['EUR', '€']):
            currency = 'EUR'
        elif any(x in amount_str.upper() for x in ['GBP', '£']):
            currency = 'GBP'
        
        numeric = re.sub(r'[^\d,.]', '', amount_str)
        numeric = numeric.replace(',', '')
        
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
        noise_words = [
            'hereinafter', 'referred to as', 'the party', 'party of',
            'witnesseth', 'whereas', 'represented by'
        ]
        
        cleaned = party_str.strip()
        for noise in noise_words:
            cleaned = re.sub(noise, '', cleaned, flags=re.IGNORECASE)
        
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        cleaned = cleaned.rstrip(',.;:')
        
        return cleaned
    
    def validate_entity(self, text: str, label: str) -> bool:
        text = text.strip()
        
        if len(text) < 2:
            return False
        
        if label == 'EFFECTIVE_DATE' or label == 'EXPIRATION_DATE':
            if not any(c.isdigit() for c in text):
                return False
            if len(text) < 6:
                return False
        
        elif label == 'TOTAL_AMOUNT':
            if not any(c.isdigit() for c in text):
                return False
        
        elif label == 'PARTY_NAME':
            if not any(c.isalpha() for c in text):
                return False
            if len(text) < 3:
                return False
        
        elif label == 'JURISDICTION':
            alpha_ratio = sum(c.isalpha() or c.isspace() for c in text) / len(text)
            if alpha_ratio < 0.5:
                return False
        
        return True
    
    def process_entities(self, entities: List[Tuple[str, str]]) -> List[Dict]:
        processed = []
        
        for text, label in entities:
            if not self.validate_entity(text, label):
                continue
            
            normalized_text = text
            original_text = None
            
            if label in ['EFFECTIVE_DATE', 'EXPIRATION_DATE']:
                normalized_text = self.normalize_date(text)
                original_text = text
            
            elif label == 'TOTAL_AMOUNT':
                amount_data = self.normalize_amount(text)
                normalized_text = f"{amount_data['currency']} {amount_data['normalized']}"
                original_text = amount_data['raw']
            
            elif label == 'PARTY_NAME':
                normalized_text = self.clean_party_name(text)
                if normalized_text != text:
                    original_text = text
            
            entity_dict = {
                'text': normalized_text,
                'label': label
            }
            if original_text:
                entity_dict['original_text'] = original_text
            
            processed.append(entity_dict)
        
        return processed
    
    def deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        seen = set()
        unique = []
        
        for entity in entities:
            key = (entity['text'].lower(), entity['label'])
            if key not in seen:
                seen.add(key)
                unique.append(entity)
        
        return unique


def apply_rules(entities: List[Tuple[str, str]]) -> List[Dict]:
    processor = RuleBasedProcessor()
    return processor.process_entities(entities)


def deduplicate_entities(entities: List[Dict]) -> List[Dict]:
    processor = RuleBasedProcessor()
    return processor.deduplicate_entities(entities)


if __name__ == "__main__":
    processor = RuleBasedProcessor()
    
    test_dates = [
        "15th March 2024",
        "15/03/2024",
        "2024-03-15",
        "15-3-2024"
    ]
    
    print("Date Normalization Tests:")
    for date in test_dates:
        print(f"  {date} -> {processor.normalize_date(date)}")
    
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