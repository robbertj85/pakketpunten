"""
Fetch all InPost parcel locker and PUDO locations in the Netherlands.

InPost (owner of Mondial Relay) operates parcel lockers and pickup/drop-off
points across the Netherlands. The public EasyPack API provides paginated
access to all locations without authentication.

API: https://api-global-points.easypack24.net/v1/points?country=NL
     No authentication required. Paginated (max 100 per page).

Usage:
    python scripts/inpost_fetch_all.py
"""

import json
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import defaultdict


def fetch_all_inpost_locations() -> List[Dict]:
    """
    Fetch all InPost points in the Netherlands via paginated API.

    Returns
    -------
    list of dict
        InPost locations with standardized fields
    """
    print("=" * 80)
    print("INPOST COMPLETE LOCATION FETCH")
    print("=" * 80)
    print()

    print("📡 Fetching all InPost locations from EasyPack API...")
    print("   Endpoint: https://api-global-points.easypack24.net/v1/points")
    print("   Country: NL")
    print()

    all_items = []
    page = 1
    per_page = 100
    total_pages = None

    try:
        while True:
            response = requests.get(
                "https://api-global-points.easypack24.net/v1/points",
                params={
                    "country": "NL",
                    "per_page": per_page,
                    "page": page,
                },
                headers={"Accept": "application/json"},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            total_pages = data.get("total_pages", 1)
            total_count = data.get("count", 0)

            if page == 1:
                print(f"   Total locations reported: {total_count}")
                print(f"   Total pages: {total_pages}")

            all_items.extend(items)
            print(f"   Page {page}/{total_pages}: fetched {len(items)} items (total so far: {len(all_items)})")

            if page >= total_pages or not items:
                break

            page += 1
            time.sleep(1)  # Rate limiting

        print()
        print(f"✅ Fetched {len(all_items)} total InPost locations")

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error on page {page}: {e}")
        if all_items:
            print(f"   Continuing with {len(all_items)} items fetched so far")
        else:
            return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        if not all_items:
            return []

    # Filter to operating points only, exclude test items
    operating = []
    status_counts = defaultdict(int)

    for item in all_items:
        status = item.get("status", "")
        status_counts[status] += 1

        # Skip non-operating and test items
        if status != "Operating":
            continue
        if item.get("name", "").startswith("TESTNL"):
            continue

        loc = item.get("location", {})
        addr = item.get("address_details", {}) or {}
        addr_lines = item.get("address", {}) or {}

        # Determine point type
        item_type = item.get("type", [])
        if "parcel_locker" in item_type:
            punt_type = "automaat"
        else:
            punt_type = "servicepunt"

        operating.append({
            'inpost_id': item.get('name', ''),
            'locatieNaam': item.get('location_description_1', '') or item.get('location_description_2', ''),
            'straatNaam': addr.get('street', ''),
            'straatNr': addr.get('building_number', ''),
            'postcode': addr.get('post_code', ''),
            'city': addr.get('city', ''),
            'latitude': loc.get('latitude'),
            'longitude': loc.get('longitude'),
            'puntType': punt_type,
            'location_247': item.get('location_247', False),
            'functions': item.get('functions', []),
            'opening_hours': item.get('opening_hours', ''),
        })

    print()
    print(f"📊 Status breakdown:")
    for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
        print(f"   {status:15s}: {count:4d}")

    print()
    print(f"📦 Operating locations (excl. test): {len(operating)}")

    return operating


def analyze_locations(locations: List[Dict]):
    """Print statistics about fetched locations."""
    print()
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()

    # Count by type
    type_counts = defaultdict(int)
    for loc in locations:
        type_counts[loc.get('puntType', 'unknown')] += 1

    print("📦 By type:")
    for loc_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"   {loc_type:20s}: {count:4d}")

    # 24/7 locations
    h24_count = sum(1 for loc in locations if loc.get('location_247'))
    print(f"\n   24/7 accessible:    {h24_count:4d}")

    # Count by city (top 10)
    city_counts = defaultdict(int)
    for loc in locations:
        city = loc.get('city', 'Unknown')
        city_counts[city] += 1

    print()
    print("🏙️  Top 10 cities by location count:")
    for i, (city, count) in enumerate(sorted(city_counts.items(), key=lambda x: -x[1])[:10], 1):
        print(f"   {i:2d}. {city:25s}: {count:3d} locations")

    # Geographic coverage
    lats = [loc.get('latitude', 0) for loc in locations if loc.get('latitude')]
    lons = [loc.get('longitude', 0) for loc in locations if loc.get('longitude')]

    if lats and lons:
        print()
        print("🌍 Geographic coverage:")
        print(f"   Latitude:  {min(lats):.4f}° to {max(lats):.4f}°")
        print(f"   Longitude: {min(lons):.4f}° to {max(lons):.4f}°")


def save_results(locations: List[Dict]):
    """Save locations to JSON file."""
    print()
    print("=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)
    print()

    output_path = Path(__file__).parent.parent / "data" / "inpost_all_locations.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "metadata": {
            "total_locations": len(locations),
            "method": "api-easypack-paginated",
            "source": "https://api-global-points.easypack24.net/v1/points",
            "country": "Netherlands",
            "fetched_at": datetime.utcnow().isoformat() + "Z",
        },
        "locations": locations,
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    file_size_kb = output_path.stat().st_size / 1024
    print(f"💾 Saved to: {output_path}")
    print(f"   File size: {file_size_kb:.1f} KB")
    print(f"   Locations: {len(locations)}")

    # Log
    log_file = output_path.parent.parent / "scripts" / "inpost_update_log.txt"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} - Fetched {len(locations)} InPost locations\n")
    print(f"   Log updated: {log_file}")


def main():
    print()
    print(f"Starting InPost location fetch...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    locations = fetch_all_inpost_locations()

    if not locations:
        print()
        print("❌ Failed to fetch locations")
        return 1

    analyze_locations(locations)
    save_results(locations)

    print()
    print("=" * 80)
    print("✅ COMPLETE!")
    print("=" * 80)
    print()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
