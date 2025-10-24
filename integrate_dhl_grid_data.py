"""
Integrate comprehensive DHL grid data into municipality GeoJSON files.

This script:
1. Loads the complete DHL dataset from grid fetch
2. For each municipality, filters DHL locations within bounds
3. Updates the GeoJSON files with complete DHL data
"""

import json
import geopandas as gpd
import pandas as pd
from pathlib import Path
from shapely.geometry import Point, box
from typing import Dict, List
from utils import get_gemeente_geometry


def load_dhl_grid_data(grid_file: str = "dhl_all_locations.json") -> gpd.GeoDataFrame:
    """Load DHL locations from grid fetch results."""
    with open(grid_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    locations = data['locations']

    # Convert to DataFrame
    rows = []
    for loc in locations:
        geo = loc.get('geoLocation', {})
        addr = loc.get('address', {})

        rows.append({
            'locatieNaam': loc.get('name', ''),
            'straatNaam': addr.get('street', ''),
            'straatNr': str(addr.get('number', '')) + (addr.get('addition', '') or ''),
            'latitude': geo.get('latitude'),
            'longitude': geo.get('longitude'),
            'puntType': loc.get('shopType', ''),  # parcelShop or packStation
            'vervoerder': 'DHL',
        })

    df = pd.DataFrame(rows)

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
    dhl_gdf_full: gpd.GeoDataFrame,
    output_dir: Path
):
    """Update a municipality's GeoJSON file with complete DHL data."""

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

    # Filter DHL locations within bounds
    dhl_in_bounds = filter_locations_by_bounds(dhl_gdf_full, bounds)

    # Remove existing DHL features
    features_non_dhl = [
        f for f in geojson_data['features']
        if f['properties'].get('vervoerder') != 'DHL'
    ]

    old_dhl_count = len(geojson_data['features']) - len(features_non_dhl)

    # Add new DHL features
    new_dhl_features = []
    for _, row in dhl_in_bounds.iterrows():
        new_dhl_features.append({
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
                "vervoerder": "DHL",
                "puntType": row['puntType'],
                "bezettingsgraad": 0,  # Keep existing or set to 0
            }
        })

    # Combine features
    geojson_data['features'] = features_non_dhl + new_dhl_features

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

    new_dhl_count = len(new_dhl_features)
    change = new_dhl_count - old_dhl_count
    change_str = f"+{change}" if change >= 0 else str(change)

    return {
        'gemeente': gemeente,
        'old_dhl_count': old_dhl_count,
        'new_dhl_count': new_dhl_count,
        'change': change,
        'total_points': geojson_data['metadata']['total_points']
    }


def main():
    """Update all municipality files with comprehensive DHL data."""

    print("="*80)
    print("INTEGRATE DHL GRID DATA INTO MUNICIPALITY FILES")
    print("="*80)
    print()

    # Check if grid data exists
    grid_file = Path("dhl_all_locations.json")
    if not grid_file.exists():
        print("❌ ERROR: dhl_all_locations.json not found!")
        print("   Run 'python dhl_grid_fetch.py' first to fetch complete DHL data.")
        return

    # Load complete DHL dataset
    print("📂 Loading DHL grid data...")
    dhl_gdf = load_dhl_grid_data(grid_file)
    print(f"   Loaded {len(dhl_gdf)} DHL locations")
    print()

    # Load municipalities
    with open("municipalities_all.json", 'r', encoding='utf-8') as f:
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

        result = update_municipality_geojson(gemeente, slug, dhl_gdf, output_dir)

        if result:
            results.append(result)
            change_str = f"+{result['change']}" if result['change'] >= 0 else str(result['change'])
            print(f"✅ {result['old_dhl_count']} → {result['new_dhl_count']} DHL ({change_str})")
        else:
            print("❌ Failed")

    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)

    total_old = sum(r['old_dhl_count'] for r in results)
    total_new = sum(r['new_dhl_count'] for r in results)
    total_change = total_new - total_old

    print(f"✅ Updated: {len(results)} municipalities")
    print(f"📍 Total DHL locations:")
    print(f"   Before: {total_old}")
    print(f"   After:  {total_new}")
    print(f"   Change: +{total_change} ({(total_change/total_old*100):.1f}% increase)")
    print()

    # Show top gainers
    results_sorted = sorted(results, key=lambda x: x['change'], reverse=True)
    print("Top 10 municipalities by increase:")
    for i, r in enumerate(results_sorted[:10], 1):
        print(f"  {i:2d}. {r['gemeente']:20s} +{r['change']:3d} ({r['old_dhl_count']} → {r['new_dhl_count']})")

    print()
    print("⚠️  Remember to regenerate the national overview:")
    print("   python create_national_overview.py")


if __name__ == "__main__":
    main()
