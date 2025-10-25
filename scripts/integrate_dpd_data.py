"""
Integrate comprehensive DPD data into municipality GeoJSON files.

This script:
1. Loads the complete DPD dataset from dpd_fetch_all.py
2. For each municipality, filters DPD locations within bounds
3. Updates the GeoJSON files with complete DPD data
"""

import json
import geopandas as gpd
import pandas as pd
from pathlib import Path
from shapely.geometry import Point, box
from typing import Dict, List
from utils import get_gemeente_geometry


def load_dpd_data(data_file: str = "../data/dpd_all_locations.json") -> gpd.GeoDataFrame:
    """Load DPD locations from fetch results."""
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    locations = data['locations']

    # Convert to DataFrame
    rows = []
    for loc in locations:
        # Extract address components
        street = loc.get('street', '')
        house_number = loc.get('house_number', '')
        street_full = f"{street} {house_number}".strip() if house_number else street

        rows.append({
            'locatieNaam': loc.get('company', ''),
            'straatNaam': street,
            'straatNr': house_number,
            'latitude': loc.get('latitude'),
            'longitude': loc.get('longitude'),
            'puntType': loc.get('pickup_network_type', ''),  # pickup_point, parcel_locker, etc.
            'vervoerder': 'DPD',
            'postcode': loc.get('postcode', ''),
            'city': loc.get('city', ''),
            'dpd_id': loc.get('id', ''),
        })

    df = pd.DataFrame(rows)

    # Filter out locations without coordinates
    df = df.dropna(subset=['latitude', 'longitude'])

    # Create GeoDataFrame
    geometry = [Point(row['longitude'], row['latitude']) for _, row in df.iterrows()]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

    return gdf


def filter_locations_by_bounds(gdf: gpd.GeoDataFrame, bounds: List[float]) -> gpd.GeoDataFrame:
    """
    Filter locations within bounding box.
    bounds = [minx, miny, maxx, maxy]
    """
    minx, miny, maxx, maxy = bounds
    bbox = box(minx, miny, maxx, maxy)

    # Filter points within bbox
    mask = gdf.geometry.within(bbox)
    return gdf[mask].copy()


def get_municipality_bounds(gemeente: str) -> List[float]:
    """Get bounding box for municipality using existing geometry function."""
    try:
        # Get bbox coordinates
        bottom_left_lat, bottom_left_lon, top_right_lat, top_right_lon = get_gemeente_geometry(
            gemeente, mode="bbox"
        )

        # Convert to [minx, miny, maxx, maxy] format
        return [bottom_left_lon, bottom_left_lat, top_right_lon, top_right_lat]
    except Exception as e:
        print(f"  ⚠️  Error getting bounds for {gemeente}: {e}")
        return None


def update_municipality_geojson(
    gemeente: str,
    slug: str,
    dpd_gdf_full: gpd.GeoDataFrame,
    output_dir: Path
):
    """Update a municipality's GeoJSON file with complete DPD data."""

    geojson_file = output_dir / f"{slug}.geojson"

    if not geojson_file.exists():
        print(f"  ⚠️  File not found: {geojson_file.name}")
        return None

    # Load existing GeoJSON
    with open(geojson_file, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)

    # Get municipality bounds
    bounds = get_municipality_bounds(gemeente)
    if bounds is None:
        return None

    # Filter DPD locations within bounds
    dpd_in_bounds = filter_locations_by_bounds(dpd_gdf_full, bounds)

    # Remove existing DPD features
    features_non_dpd = [
        f for f in geojson_data['features']
        if f['properties'].get('vervoerder') != 'DPD'
    ]

    old_dpd_count = len(geojson_data['features']) - len(features_non_dpd)

    # Add new DPD features
    new_dpd_features = []
    for _, row in dpd_in_bounds.iterrows():
        new_dpd_features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row.geometry.x, row.geometry.y]
            },
            "properties": {
                "type": "pakketpunt",
                "locatieNaam": row['locatieNaam'],
                "straatNaam": row['straatNaam'],
                "straatNr": row['straatNr'],
                "latitude": row['latitude'],
                "longitude": row['longitude'],
                "vervoerder": "DPD",
                "puntType": row['puntType'],
                "bezettingsgraad": 0,  # Dummy data, kept consistent with other providers
            }
        })

    # Combine features
    geojson_data['features'] = features_non_dpd + new_dpd_features

    # Update metadata
    geojson_data['metadata']['total_points'] = len(
        [f for f in geojson_data['features'] if f['properties'].get('type') == 'pakketpunt']
    )

    # Update providers list
    providers = set()
    for feature in geojson_data['features']:
        if feature['properties'].get('type') == 'pakketpunt':
            provider = feature['properties'].get('vervoerder')
            if provider:
                providers.add(provider)
    geojson_data['metadata']['providers'] = sorted(list(providers))

    # Save updated GeoJSON
    with open(geojson_file, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, ensure_ascii=False)

    new_dpd_count = len(new_dpd_features)
    change = new_dpd_count - old_dpd_count
    change_str = f"+{change}" if change >= 0 else str(change)

    return {
        'gemeente': gemeente,
        'old_dpd_count': old_dpd_count,
        'new_dpd_count': new_dpd_count,
        'change': change,
        'total_points': geojson_data['metadata']['total_points']
    }


def main():
    """Update all municipality files with comprehensive DPD data."""

    print("="*80)
    print("INTEGRATE DPD DATA INTO MUNICIPALITY FILES")
    print("="*80)
    print()

    # Check if data exists
    data_file = Path("../data/dpd_all_locations.json")
    if not data_file.exists():
        print("❌ ERROR: ../data/dpd_all_locations.json not found!")
        print("   Run 'python scripts/dpd_fetch_all.py' first to fetch complete DPD data.")
        return

    # Load complete DPD dataset
    print("📂 Loading DPD data...")
    dpd_gdf = load_dpd_data(data_file)
    print(f"   Loaded {len(dpd_gdf)} DPD locations")
    print()

    # Load municipalities
    with open("../data/municipalities_all.json", 'r', encoding='utf-8') as f:
        municipalities = json.load(f)

    # Filter out Nederland (we'll handle that separately)
    municipalities = [m for m in municipalities if m['slug'] != 'nederland']

    output_dir = Path("webapp/public/data")

    print(f"🔄 Updating {len(municipalities)} municipality files...")
    print()

    results = []

    for idx, muni in enumerate(municipalities, 1):
        gemeente = muni['name']
        slug = muni['slug']

        print(f"[{idx}/{len(municipalities)}] {gemeente}...", end=" ")

        result = update_municipality_geojson(gemeente, slug, dpd_gdf, output_dir)

        if result:
            results.append(result)
            change_str = f"+{result['change']}" if result['change'] >= 0 else str(result['change'])
            print(f"✅ {result['old_dpd_count']} → {result['new_dpd_count']} DPD ({change_str})")
        else:
            print("❌ Failed")

    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)

    if not results:
        print("❌ No municipalities were updated")
        return

    total_old = sum(r['old_dpd_count'] for r in results)
    total_new = sum(r['new_dpd_count'] for r in results)
    total_change = total_new - total_old

    print(f"✅ Updated: {len(results)} municipalities")
    print(f"📍 Total DPD locations:")
    print(f"   Before: {total_old}")
    print(f"   After:  {total_new}")

    if total_old > 0:
        change_pct = (total_change/total_old*100)
        print(f"   Change: {total_change:+d} ({change_pct:+.1f}%)")
    else:
        print(f"   Change: +{total_new} (new provider!)")

    print()

    # Show top municipalities by DPD location count
    results_sorted = sorted(results, key=lambda x: x['new_dpd_count'], reverse=True)
    print("Top 10 municipalities by DPD location count:")
    for i, r in enumerate(results_sorted[:10], 1):
        print(f"  {i:2d}. {r['gemeente']:20s} {r['new_dpd_count']:3d} locations")

    print()
    print("⚠️  Remember to regenerate the national overview:")
    print("   python create_national_overview.py")


if __name__ == "__main__":
    main()
