import json
from pathlib import Path

input_file = Path(__file__).parent / "tesco_parsed_turbo.json"

with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    if item['price'] == 0:
        item['price'] = item['price_per_unit']

with open(input_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Updated {input_file}")
