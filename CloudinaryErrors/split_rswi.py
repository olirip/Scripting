import json
import re

# Read the rolex JSON file
print("Reading cloudinary_errors_rolex.json...")
with open('cloudinary_errors_rolex.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Initialize containers for the two splits
rswi_entries = {}
non_rswi_entries = {}

# Pattern to match rswi in URLs (case insensitive)
rswi_pattern = re.compile(r'rswi', re.IGNORECASE)

# Process the data
print("Processing and splitting entries...")
rswi_count = 0
non_rswi_count = 0

for url_key, url_value in data.items():
    # Check if the URL contains "rswi"
    if rswi_pattern.search(url_key):
        rswi_entries[url_key] = url_value
        rswi_count += 1
    else:
        non_rswi_entries[url_key] = url_value
        non_rswi_count += 1

print(f"Found {rswi_count} entries with 'rswi' in URL")
print(f"Found {non_rswi_count} entries without 'rswi' in URL")

# Write rswi entries to a new file
print(f"Writing {len(rswi_entries)} entries to cloudinary_errors_rolex_rswi.json...")
with open('cloudinary_errors_rolex_rswi.json', 'w', encoding='utf-8') as f:
    json.dump(rswi_entries, f, indent=2, ensure_ascii=False)

# Write non-rswi entries to a new file
print(f"Writing {len(non_rswi_entries)} entries to cloudinary_errors_rolex_no_rswi.json...")
with open('cloudinary_errors_rolex_no_rswi.json', 'w', encoding='utf-8') as f:
    json.dump(non_rswi_entries, f, indent=2, ensure_ascii=False)

print("\nDone! Files created:")
print("- cloudinary_errors_rolex_rswi.json (Rolex URLs containing 'rswi')")
print("- cloudinary_errors_rolex_no_rswi.json (Rolex URLs without 'rswi')")
