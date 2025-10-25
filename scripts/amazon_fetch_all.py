"""
Fetch all Amazon Hub Locker and Counter locations in the Netherlands from OpenStreetMap.

Amazon does not provide a public API for querying pickup locations.
This script uses the Overpass API to fetch Amazon locations from OpenStreetMap,
which is community-maintained open data.

Data source: OpenStreetMap (Open Data Commons Open Database License - ODbL)
Attribution: © OpenStreetMap contributors
API: https://overpass-api.de/api/interpreter

Note: OSM data completeness depends on community contributions.
Not all Amazon locations may be mapped in OSM.
"""

import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import defaultdict


def fetch_all_amazon_locations() -> List[Dict]:
    """
    Fetch all Amazon Hub Locker and Counter locations in Netherlands from OpenStreetMap.

    Returns
    -------
    list of dict
        Complete list of Amazon locations with standardized format
    """
    print("="*80)
    print("AMAZON HUB COMPLETE LOCATION FETCH (via OpenStreetMap)")
    print("="*80)
    print()

    print("📡 Querying Overpass API (OpenStreetMap)...")
    print("   Endpoint: https://overpass-api.de/api/interpreter")
    print("   Region: Netherlands")
    print("   Data: amenity=parcel_locker with Amazon branding")
    print()

    # Overpass QL query to find all Amazon lockers in Netherlands
    # Searches for:
    # 1. Parcel lockers with operator=Amazon
    # 2. Parcel lockers with brand=Amazon
    # 3. Parcel lockers with "Amazon" in the name
    overpass_query = """
    [out:json][timeout:90];
    area["ISO3166-1"="NL"][admin_level=2]->.searchArea;
    (
      node["amenity"="parcel_locker"]["operator"~"Amazon",i](area.searchArea);
      node["amenity"="parcel_locker"]["brand"~"Amazon",i](area.searchArea);
      node["name"~"Amazon",i]["amenity"="parcel_locker"](area.searchArea);
    );
    out body;
    >;
    out skel qt;
    """

    try:
        response = requests.post(
            "https://overpass-api.de/api/interpreter",
            data={'data': overpass_query},
            timeout=120,  # Longer timeout for complete dataset
        )
        response.raise_for_status()
        data = response.json()

        # Extract nodes from Overpass response
        elements = data.get('elements', [])
        nodes = [elem for elem in elements if elem.get('type') == 'node']

        if not nodes:
            print("⚠️  No Amazon locations found in OpenStreetMap")
            print("   This could mean:")
            print("   - Amazon locations haven't been mapped in OSM yet")
            print("   - Amazon has limited presence in Netherlands")
            print("   - Different tagging scheme is used")
            print()
            print("   Consider:")
            print("   - Contributing to OpenStreetMap")
            print("   - Checking https://www.amazon.nl/ulp/view for actual locations")
            return []

        print(f"✅ Successfully fetched {len(nodes)} Amazon locations from OSM")

        # Convert OSM data to standardized format
        locations = []
        seen_ids = set()

        for node in nodes:
            node_id = node.get('id')
            if node_id in seen_ids:
                continue
            seen_ids.add(node_id)

            tags = node.get('tags', {})
            lat = node.get('lat')
            lon = node.get('lon')

            # Extract location information
            name = tags.get('name', tags.get('ref', 'Amazon Hub'))
            operator = tags.get('operator', tags.get('brand', 'Amazon'))
            street = tags.get('addr:street', '')
            housenumber = tags.get('addr:housenumber', '')
            postcode = tags.get('addr:postcode', '')
            city = tags.get('addr:city', '')

            # Determine type (locker vs counter)
            locker_type = tags.get('parcel_locker:type', '')
            if not locker_type:
                # Infer from name or other tags
                if 'counter' in name.lower():
                    locker_type = 'counter'
                elif 'locker' in name.lower():
                    locker_type = 'locker'
                else:
                    locker_type = 'locker'  # Default

            # Additional metadata
            opening_hours = tags.get('opening_hours', '')
            phone = tags.get('phone', '')
            website = tags.get('website', '')

            # Parcel services
            parcel_pickup = tags.get('parcel_pickup', 'yes')
            parcel_mail_in = tags.get('parcel_mail_in', '')

            location = {
                'osm_id': node_id,
                'osm_type': 'node',
                'locatieNaam': name,
                'operator': operator,
                'straatNaam': street,
                'straatNr': housenumber,
                'postcode': postcode,
                'city': city,
                'latitude': lat,
                'longitude': lon,
                'puntType': locker_type,
                'vervoerder': 'Amazon',
                'opening_hours': opening_hours,
                'phone': phone,
                'website': website,
                'parcel_pickup': parcel_pickup,
                'parcel_mail_in': parcel_mail_in,
                'osm_tags': tags,  # Keep original tags for reference
            }

            locations.append(location)

        return locations

    except requests.exceptions.Timeout:
        print("❌ Request timed out after 120 seconds")
        print("   Overpass API might be overloaded. Try again later.")
        return []
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return []
    except json.JSONDecodeError:
        print("❌ Invalid JSON response from Overpass API")
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return []


def analyze_locations(locations: List[Dict]):
    """Analyze fetched locations and print statistics."""
    print()
    print("="*80)
    print("ANALYSIS")
    print("="*80)
    print()

    if not locations:
        print("⚠️  No locations to analyze")
        return

    # Count by type
    type_counts = defaultdict(int)
    for loc in locations:
        loc_type = loc.get('puntType', 'unknown')
        type_counts[loc_type] += 1

    print("📦 By type:")
    for loc_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"   {loc_type:20s}: {count:4d}")

    # Count by city (top 10)
    city_counts = defaultdict(int)
    for loc in locations:
        city = loc.get('city', 'Unknown')
        if city:
            city_counts[city] += 1

    if city_counts:
        print()
        print("🏙️  Top 10 cities by location count:")
        for i, (city, count) in enumerate(sorted(city_counts.items(), key=lambda x: -x[1])[:10], 1):
            print(f"   {i:2d}. {city:25s}: {count:3d} locations")

    # Data completeness
    print()
    print("📊 Data completeness:")
    with_address = sum(1 for loc in locations if loc.get('straatNaam'))
    with_postcode = sum(1 for loc in locations if loc.get('postcode'))
    with_city = sum(1 for loc in locations if loc.get('city'))
    with_hours = sum(1 for loc in locations if loc.get('opening_hours'))
    with_phone = sum(1 for loc in locations if loc.get('phone'))

    total = len(locations)
    print(f"   With street address: {with_address:4d} ({with_address/total*100:.1f}%)")
    print(f"   With postcode:       {with_postcode:4d} ({with_postcode/total*100:.1f}%)")
    print(f"   With city:           {with_city:4d} ({with_city/total*100:.1f}%)")
    print(f"   With opening hours:  {with_hours:4d} ({with_hours/total*100:.1f}%)")
    print(f"   With phone:          {with_phone:4d} ({with_phone/total*100:.1f}%)")

    # Geographic distribution
    lats = [loc.get('latitude', 0) for loc in locations if loc.get('latitude')]
    lons = [loc.get('longitude', 0) for loc in locations if loc.get('longitude')]

    if lats and lons:
        print()
        print("🌍 Geographic coverage:")
        print(f"   Latitude:  {min(lats):.4f}° to {max(lats):.4f}°")
        print(f"   Longitude: {min(lons):.4f}° to {max(lons):.4f}°")

    # OSM data quality note
    print()
    print("ℹ️  Data Quality Note:")
    print("   This data comes from OpenStreetMap, maintained by volunteers.")
    print("   Coverage may be incomplete. Consider contributing to OSM:")
    print("   https://www.openstreetmap.org/")


def save_results(locations: List[Dict], output_file: str = "../data/amazon_all_locations.json"):
    """
    Save locations to JSON file.

    Parameters
    ----------
    locations : list of dict
        Amazon locations data
    output_file : str
        Output filename (default: ../data/amazon_all_locations.json)
    """
    print()
    print("="*80)
    print("SAVING RESULTS")
    print("="*80)
    print()

    # Create output structure
    output = {
        "metadata": {
            "total_locations": len(locations),
            "method": "openstreetmap-overpass-api",
            "source": "https://www.openstreetmap.org",
            "api": "https://overpass-api.de/api/interpreter",
            "license": "ODbL (Open Database License)",
            "attribution": "© OpenStreetMap contributors",
            "country": "Netherlands",
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "note": "Data completeness depends on OSM community contributions"
        },
        "locations": locations
    }

    # Save to file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    file_size_kb = output_path.stat().st_size / 1024
    print(f"💾 Saved to: {output_file}")
    print(f"   File size: {file_size_kb:.1f} KB")
    print(f"   Locations: {len(locations)}")

    # Log to update file
    log_file = Path("amazon_update_log.txt")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} - Fetched {len(locations)} Amazon locations from OSM\n")
    print(f"   Log updated: {log_file}")


def main():
    """Main execution function."""
    print()
    print("Starting Amazon Hub location fetch from OpenStreetMap...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Fetch all locations
    locations = fetch_all_amazon_locations()

    if not locations:
        print()
        print("❌ No locations fetched")
        print()
        print("⚠️  This is expected if Amazon locations aren't mapped in OSM yet.")
        print("   The script will still create an empty cache file.")
        print()

    # Analyze (even if empty)
    if locations:
        analyze_locations(locations)

    # Save (even if empty - creates cache file)
    save_results(locations)

    print()
    print("="*80)
    print("✅ COMPLETE!")
    print("="*80)
    print()

    if locations:
        print("Next steps:")
        print("  1. Run: python integrate_amazon_data.py")
        print("     (Integrate Amazon data into municipality files)")
        print()
        print("  2. Or regenerate everything:")
        print("     python weekly_update.py")
    else:
        print("⚠️  No Amazon locations found in OpenStreetMap.")
        print("   The integration will work but return no Amazon data.")
        print("   Consider contributing Amazon Hub locations to OSM!")
    print()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
