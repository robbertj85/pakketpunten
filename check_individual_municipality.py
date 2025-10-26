#!/usr/bin/env python3
"""Check if individual municipality files contain duplicates"""

import json
from pathlib import Path
from collections import defaultdict

data_dir = Path('webapp/public/data')
geojson_files = [f for f in data_dir.glob("*.geojson") if f.name != "nederland.geojson"]

print(f"Checking {len(geojson_files)} municipality files for duplicates\n")

municipalities_with_duplicates = []
total_duplicate_entries = 0
total_points = 0

for geojson_file in sorted(geojson_files):  # Check all files
    with open(geojson_file, 'r') as f:
        data = json.load(f)

    pakketpunten = [f for f in data['features'] if f['properties'].get('type') == 'pakketpunt']
    total_points += len(pakketpunten)

    # Check for coordinate duplicates
    coord_map = defaultdict(list)
    for feature in pakketpunten:
        coords = tuple(feature['geometry']['coordinates'])
        coord_map[coords].append({
            'name': feature['properties'].get('locatieNaam'),
            'provider': feature['properties'].get('vervoerder')
        })

    exact_duplicates = {k: v for k, v in coord_map.items() if len(v) > 1}

    if exact_duplicates:
        duplicate_count = sum(len(v) - 1 for v in exact_duplicates.values())
        total_duplicate_entries += duplicate_count
        municipalities_with_duplicates.append(geojson_file.name)

print(f"\n{'='*60}")
print(f"SUMMARY:")
print(f"{'='*60}")
print(f"Total municipalities checked: {len(geojson_files)}")
print(f"Municipalities with duplicates: {len(municipalities_with_duplicates)}")
print(f"Total points across all municipalities: {total_points}")
print(f"Total duplicate entries: {total_duplicate_entries}")
print(f"Expected points after deduplication: {total_points - total_duplicate_entries}")
