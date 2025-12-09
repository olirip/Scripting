import json
import re

# Read the original JSON file
print("Reading cloudinary_errors.json...")
with open('cloudinary_errors.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Initialize containers for the two splits
rolex_entries = {}
other_entries = {}

# Pattern to match rolex.com or rolex.cn URLs
rolex_pattern = re.compile(r'https://www\.rolex\.(com|cn)')

# Process the data
print("Processing and splitting entries...")
rolex_count = 0
other_count = 0

for top_key, top_value in data.items():
    # Check if the top-level key contains rolex.com or rolex.cn
    if rolex_pattern.search(top_key):
        rolex_entries[top_key] = top_value
        rolex_count += 1
    else:
        other_entries[top_key] = top_value
        other_count += 1

print(f"Found {rolex_count} Rolex URL entries")
print(f"Found {other_count} other entries")

# Write rolex entries to a new file
print(f"Writing {len(rolex_entries)} rolex entries to cloudinary_errors_rolex.json...")
with open('cloudinary_errors_rolex.json', 'w', encoding='utf-8') as f:
    json.dump(rolex_entries, f, indent=2, ensure_ascii=False)

# Write other entries to a new file
print(f"Writing other entries to cloudinary_errors_other.json...")
with open('cloudinary_errors_other.json', 'w', encoding='utf-8') as f:
    json.dump(other_entries, f, indent=2, ensure_ascii=False)

print("\nDone! Files created:")
print("- cloudinary_errors_rolex.json (entries with https://www.rolex.com or https://www.rolex.cn)")
print("- cloudinary_errors_other.json (all other entries)")
