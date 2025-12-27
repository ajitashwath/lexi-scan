import json

def generate_final_labels():
    labels = [
        {"text": "PARTY_NAME", "background_color": "#00008B", "text_color": "#ffffff"},
        {"text": "EFFECTIVE_DATE", "background_color": "#B22222", "text_color": "#ffffff"},
        {"text": "EXPIRATION_DATE", "background_color": "#DC143C", "text_color": "#ffffff"},
        {"text": "JURISDICTION", "background_color": "#800080", "text_color": "#ffffff"},
        {"text": "TOTAL_AMOUNT", "background_color": "#006400", "text_color": "#ffffff"},
        {"text": "INTEREST_RATE", "background_color": "#32CD32", "text_color": "#000000"},
        {"text": "COLLATERAL", "background_color": "#2E8B57", "text_color": "#ffffff"},
        {"text": "CONFIDENTIALITY_PERIOD", "background_color": "#FF8C00", "text_color": "#000000"},
        {"text": "TERMINATION_NOTICE_PERIOD", "background_color": "#FF6347", "text_color": "#ffffff"},
        {"text": "GOVERNING_LAW", "background_color": "#BA55D3", "text_color": "#ffffff"}
    ]

    output_filename = "final_labels.json"

    with open(output_filename, "w") as f:
        json.dump(labels, f, indent=4)

    print(f"Success! Generated '{output_filename}' with {len(labels)} labels.")
    print(f"File location: {output_filename}")

if __name__ == "__main__":
    generate_final_labels()