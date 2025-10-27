#!/usr/bin/env python3
"""
Backfill script for municipalities that failed during batch generation.

This script reprocesses specific municipalities that failed due to:
- Overpass API timeouts (504)
- Municipality name matching issues
- Rate limiting (429)

The script uses the improved utils.py with:
- Retry logic with exponential backoff
- Municipality name mappings for special cases
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.batch_generate import process_municipality

# List of failed municipalities from the GitHub Actions log
FAILED_MUNICIPALITIES = [
    "Bergen (L.)",
    "Bergen (NH.)",
    "Heumen",
    "Houten",
    "Land van Cuijk",
    "Lelystad",
    "Leusden",
    "Loon op Zand",
    "Maasgouw",
    "Maashorst",
    "Midden-Delfland",
    "Midden-Groningen",
    "Molenlanden",
    "Neder-Betuwe",
    "Nieuwegein",
    "Nuenen",
    "Opmeer",
    "Pekela",
    "Pijnacker-Nootdorp",
    "Rijssen-Holten",
    "Roosendaal",
    "Schiedam",
    "Smallingerland",
    "Stede Broec",
    "Steenwijkerland",
    "Wijdemeren",
    "Zutphen",
    "'s-Hertogenbosch",
]

def load_municipalities():
    """Load the full municipality list to get slugs."""
    script_dir = Path(__file__).parent
    municipalities_file = script_dir.parent / "data" / "municipalities_all.json"

    with open(municipalities_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def main():
    """Backfill failed municipalities."""
    print("=" * 80)
    print("MUNICIPALITY BACKFILL")
    print("=" * 80)
    print()
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 Processing {len(FAILED_MUNICIPALITIES)} failed municipalities")
    print()

    # Load all municipalities to get slugs
    all_municipalities = load_municipalities()
    municipality_lookup = {m["name"]: m for m in all_municipalities}

    successes = []
    failures = []

    for i, gemeente_name in enumerate(FAILED_MUNICIPALITIES, 1):
        print(f"[{i}/{len(FAILED_MUNICIPALITIES)}] Processing {gemeente_name}...")
        print()

        # Try to find municipality data
        # First try exact match
        gemeente_data = municipality_lookup.get(gemeente_name)

        # If not found, try alternate names (e.g., 's-Hertogenbosch vs s-Hertogenbosch)
        if not gemeente_data:
            # Try without apostrophe
            alt_name = gemeente_name.replace("'", "")
            gemeente_data = municipality_lookup.get(alt_name)

        if not gemeente_data:
            print(f"⚠️  Municipality '{gemeente_name}' not found in municipalities list")
            failures.append((gemeente_name, "Not found in municipalities list"))
            print()
            continue

        try:
            result = process_municipality(gemeente_data)
            if result.get("success"):
                successes.append(gemeente_name)
                print(f"✅ {gemeente_name} completed successfully")
            else:
                error_msg = result.get("error", "Unknown error")
                failures.append((gemeente_name, error_msg))
                print(f"❌ {gemeente_name} failed: {error_msg}")
        except Exception as e:
            failures.append((gemeente_name, str(e)))
            print(f"❌ {gemeente_name} failed: {e}")

        print()

        # Rate limiting between municipalities
        if i < len(FAILED_MUNICIPALITIES):
            print("⏳ Waiting 5 seconds before next municipality...")
            print()
            time.sleep(5)

    # Summary
    print("=" * 80)
    print("BACKFILL SUMMARY")
    print("=" * 80)
    print()
    print(f"✅ Successful: {len(successes)}/{len(FAILED_MUNICIPALITIES)}")
    print(f"❌ Failed: {len(failures)}/{len(FAILED_MUNICIPALITIES)}")
    print()

    if successes:
        print("✅ Successfully backfilled:")
        for name in successes:
            print(f"   - {name}")
        print()

    if failures:
        print("❌ Still failing:")
        for name, error in failures:
            print(f"   - {name}: {error}")
        print()

    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Exit with error code if any failures remain
    if failures:
        print(f"⚠️  {len(failures)} municipalities still failing")
        return 1
    else:
        print("🎉 All municipalities backfilled successfully!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
