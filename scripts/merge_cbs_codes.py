#!/usr/bin/env python3
"""
Merge CBS municipality codes into webapp/public/municipalities.json

This script reads CBS municipality data (which includes official municipality codes)
and merges the codes into the webapp's municipalities.json file.
"""

import json
import sys
from pathlib import Path

def normalize_name(name: str) -> str:
    """Normalize municipality name for comparison"""
    return name.lower().strip()

# Manual mapping for municipalities with different names in CBS data
# webapp name -> CBS name
MANUAL_MAPPING = {
    "den haag": "'s-gravenhage (gemeente)",
    "groningen": "groningen (gemeente)",
    "utrecht": "utrecht (gemeente)",
    "hengelo": "hengelo (o.)",
    "laren": "laren (nh.)",
    "middelburg": "middelburg (z.)",
    "nuenen": "nuenen, gerwen en nederwetten",
    "rijswijk": "rijswijk (zh.)",
    "stein": "stein (l.)",
    "beek": "beek (l.)",
}

def main():
    # Define paths
    project_root = Path(__file__).parent.parent
    cbs_data_path = project_root / "data" / "cbs_municipality_areas.json"
    municipalities_path = project_root / "webapp" / "public" / "municipalities.json"

    # Check if files exist
    if not cbs_data_path.exists():
        print(f"❌ CBS data file not found: {cbs_data_path}", file=sys.stderr)
        sys.exit(1)

    if not municipalities_path.exists():
        print(f"❌ Municipalities file not found: {municipalities_path}", file=sys.stderr)
        sys.exit(1)

    # Load CBS data
    print(f"📖 Reading CBS data from {cbs_data_path}")
    with open(cbs_data_path, 'r', encoding='utf-8') as f:
        cbs_data = json.load(f)

    # Load municipalities data
    print(f"📖 Reading municipalities from {municipalities_path}")
    with open(municipalities_path, 'r', encoding='utf-8') as f:
        municipalities = json.load(f)

    # Create lookup dictionary from CBS data (normalized name -> code)
    cbs_lookup = {}
    for muni_name, muni_data in cbs_data.items():
        normalized = normalize_name(muni_name)
        code = muni_data.get('code', '').strip()
        if code:
            cbs_lookup[normalized] = code

    print(f"✅ Loaded {len(cbs_lookup)} CBS municipality codes")

    # Merge codes into municipalities
    matched = 0
    not_matched = []

    for municipality in municipalities:
        name = municipality['name']
        normalized = normalize_name(name)

        # Skip "Nederland (totaal)" - it's not a real municipality
        if municipality['slug'] == 'nederland':
            municipality['code'] = None
            continue

        # Try manual mapping first
        if normalized in MANUAL_MAPPING:
            cbs_name = MANUAL_MAPPING[normalized]
            if cbs_name in cbs_lookup:
                municipality['code'] = cbs_lookup[cbs_name]
                matched += 1
                continue

        # Try direct match
        if normalized in cbs_lookup:
            municipality['code'] = cbs_lookup[normalized]
            matched += 1
        else:
            # Try without special characters for edge cases
            # e.g., "s-Hertogenbosch" vs "'s-Hertogenbosch"
            normalized_alt = normalized.replace("'", "").replace("-", "").replace(" ", "")

            found = False
            for cbs_name, code in cbs_lookup.items():
                cbs_normalized_alt = cbs_name.replace("'", "").replace("-", "").replace(" ", "")
                if normalized_alt == cbs_normalized_alt:
                    municipality['code'] = code
                    matched += 1
                    found = True
                    break

            if not found:
                municipality['code'] = None
                not_matched.append(name)

    # Save updated municipalities
    print(f"💾 Writing updated municipalities to {municipalities_path}")
    with open(municipalities_path, 'w', encoding='utf-8') as f:
        json.dump(municipalities, f, ensure_ascii=False, indent=2)

    # Print summary
    print(f"\n✅ Merge complete!")
    print(f"   Matched: {matched}/{len(municipalities) - 1} municipalities")  # -1 for Nederland

    if not_matched:
        print(f"\n⚠️  Not matched ({len(not_matched)}):")
        for name in sorted(not_matched):
            print(f"   - {name}")
        print("\nThese municipalities may need manual matching or may not exist in CBS data.")

    return 0 if len(not_matched) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
