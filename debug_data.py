import json
import os

file_path = os.path.join("data", "processed", "train_data.jsonl")

if not os.path.exists(file_path):
    print(f"❌ Error: File not found at {file_path}")
else:
    print(f"✅ Found file at: {file_path}")
    print("--- CONTENT OF FIRST DOCUMENT ---")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            first_line = f.readline()
            data = json.loads(first_line)
            # Print the keys (e.g. 'text', 'label', 'meta')
            print(f"KEYS FOUND: {list(data.keys())}")
            
            # Print the label data specifically
            if 'label' in data:
                print(f"LABEL CONTENT: {data['label']}")
            elif 'entities' in data:
                print(f"ENTITIES CONTENT: {data['entities']}")
            else:
                print("⚠️ No 'label' or 'entities' key found!")
                
            print("\n--- RAW LINE ---")
            print(first_line[:200] + "...") # Print first 200 chars
            
        except Exception as e:
            print(f"❌ Error reading JSON: {e}")