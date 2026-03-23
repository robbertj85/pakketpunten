"""
Fetch all ViaTim service point locations in the Netherlands.

ViaTim operates a network of neighbourhood service points ("buurtpunten")
that handle parcels for multiple carriers (DHL, UPS, GLS, DPD).

API: https://production.viapunt-api.viatim.nl/public/servicepoints
     No authentication required. Single GET returns all locations.

Usage:
    python scripts/viatim_fetch_all.py
"""

import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import defaultdict


def fetch_all_viatim_locations() -> List[Dict]:
    """
    Fetch all ViaTim service points and filter to NL parcel locations.

    Returns
    -------
    list of dict
        ViaTim locations in the Netherlands with standardized fields
    """
    print("=" * 80)
    print("VIATIM COMPLETE LOCATION FETCH")
    print("=" * 80)
    print()

    print("📡 Fetching all ViaTim service points from public API...")
    print("   Endpoint: https://production.viapunt-api.viatim.nl/public/servicepoints")
    print()

    try:
        response = requests.get(
            "https://production.viapunt-api.viatim.nl/public/servicepoints",
            params={"limit": 1000},  # 554 total as of 2026, 1000 is enough
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        # Response is a dict with 'pagination' and 'servicepoints' keys
        if isinstance(data, dict):
            all_servicepoints = data.get('servicepoints', [])
            total = data.get('pagination', {}).get('total', len(all_servicepoints))
            print(f"   API reports {total} total service points")
        elif isinstance(data, list):
            all_servicepoints = data
        else:
            print(f"❌ Unexpected response format: {type(data)}")
            return []

        print(f"✅ Fetched {len(all_servicepoints)} service points (NL + BE)")

        # Filter to NL only
        nl_locations = [sp for sp in all_servicepoints if sp.get('location', {}).get('country') == 'NL']
        print(f"   🇳🇱 Netherlands: {len(nl_locations)}")

        # Convert to standardized format
        locations = []
        for sp in nl_locations:
            loc = sp.get('location', {})
            transporters = sp.get('transporters', [])

            locations.append({
                'viacode': sp.get('viacode', ''),
                'locatieNaam': sp.get('name', ''),
                'straatNaam': loc.get('streetname', ''),
                'straatNr': str(loc.get('housenr', '')) + (loc.get('housenr_extra', '') or ''),
                'postcode': loc.get('postcode', ''),
                'city': loc.get('city', ''),
                'latitude': loc.get('latitude'),
                'longitude': loc.get('longitude'),
                'email': loc.get('email', ''),
                'phone': loc.get('phone', ''),
                'transporters': transporters,
                'hours': sp.get('hours', {}),
            })

        print(f"   📦 Converted {len(locations)} NL locations")
        return locations

    except requests.exceptions.Timeout:
        print("❌ Request timed out after 60 seconds")
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return []
    except json.JSONDecodeError:
        print("❌ Invalid JSON response")
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return []


def analyze_locations(locations: List[Dict]):
    """Analyze fetched locations and print statistics."""
    print()
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()

    # Count by transporters
    transporter_counts = defaultdict(int)
    for loc in locations:
        for t in loc.get('transporters', []):
            transporter_counts[t] += 1

    print("📦 Carriers served:")
    for carrier, count in sorted(transporter_counts.items(), key=lambda x: -x[1]):
        print(f"   {carrier:20s}: {count:4d}")

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

    output_path = Path(__file__).parent.parent / "data" / "viatim_all_locations.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "metadata": {
            "total_locations": len(locations),
            "method": "api-public-servicepoints",
            "source": "https://production.viapunt-api.viatim.nl/public/servicepoints",
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
    log_file = output_path.parent.parent / "scripts" / "viatim_update_log.txt"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} - Fetched {len(locations)} ViaTim locations\n")
    print(f"   Log updated: {log_file}")


def main():
    print()
    print(f"Starting ViaTim location fetch...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    locations = fetch_all_viatim_locations()

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
