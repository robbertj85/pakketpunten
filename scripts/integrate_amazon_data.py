"""
Integrate Amazon Hub data from OpenStreetMap into municipality GeoJSON files.

This script:
1. Loads the Amazon dataset fetched from OSM (via amazon_fetch_all.py)
2. For each municipality, filters Amazon locations within bounds
3. Updates the GeoJSON files with Amazon data

Note: Amazon data comes from OpenStreetMap and may be incomplete.
Coverage depends on community contributions to OSM.
"""

import json
import geopandas as gpd
import pandas as pd
from pathlib import Path
from shapely.geometry import Point, box
from typing import Dict, List
from utils import get_gemeente_geometry


def load_amazon_data(data_file: str = "../data/amazon_all_locations.json") -> gpd.GeoDataFrame:
    """Load Amazon Hub locations from fetch results."""
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    locations = data['locations']

    if not locations:
        # Return empty GeoDataFrame with correct schema
        df = pd.DataFrame(columns=['locatieNaam', 'straatNaam', 'straatNr', 'latitude', 'longitude', 'puntType', 'vervoerder'])
        geometry = []
        return gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

    # Convert to DataFrame
    rows = []
    for loc in locations:
        rows.append({
            'locatieNaam': loc.get('locatieNaam', 'Amazon Hub'),
            'straatNaam': loc.get('straatNaam', ''),
            'straatNr': loc.get('straatNr', ''),
            'latitude': loc.get('latitude'),
            'longitude': loc.get('longitude'),
            'puntType': loc.get('puntType', 'locker'),
            'vervoerder': 'Amazon',
            'postcode': loc.get('postcode', ''),
            'city': loc.get('city', ''),
            'osm_id': loc.get('osm_id', ''),
        })

    df = pd.DataFrame(rows)

    # Filter out locations without coordinates
    df = df.dropna(subset=['latitude', 'longitude'])

    if df.empty:
        # Return empty GeoDataFrame with correct schema
        geometry = []
        return gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

    # Create GeoDataFrame
    geometry = [Point(row['longitude'], row['latitude']) for _, row in df.iterrows()]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')

    return gdf


def filter_locations_by_bounds(gdf: gpd.GeoDataFrame, bounds: List[float]) -> gpd.GeoDataFrame:
    """
    Filter locations within bounding box.
    bounds = [minx, miny, maxx, maxy]
    """
    if gdf.empty:
        return gdf

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
    amazon_gdf_full: gpd.GeoDataFrame,
    output_dir: Path
):
    """Update a municipality's GeoJSON file with Amazon Hub data."""

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

    # Filter Amazon locations within bounds
    amazon_in_bounds = filter_locations_by_bounds(amazon_gdf_full, bounds)

    # Remove existing Amazon features
    features_non_amazon = [
        f for f in geojson_data['features']
        if f['properties'].get('vervoerder') != 'Amazon'
    ]

    old_amazon_count = len(geojson_data['features']) - len(features_non_amazon)

    # Add new Amazon features
    new_amazon_features = []
    for _, row in amazon_in_bounds.iterrows():
        new_amazon_features.append({
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
                "vervoerder": "Amazon",
                "puntType": row['puntType'],
                "bezettingsgraad": 0,  # Dummy data, kept consistent with other providers
            }
        })

    # Combine features
    geojson_data['features'] = features_non_amazon + new_amazon_features

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

    new_amazon_count = len(new_amazon_features)
    change = new_amazon_count - old_amazon_count
    change_str = f"+{change}" if change >= 0 else str(change)

    return {
        'gemeente': gemeente,
        'old_amazon_count': old_amazon_count,
        'new_amazon_count': new_amazon_count,
        'change': change,
        'total_points': geojson_data['metadata']['total_points']
    }


def main():
    """Update all municipality files with Amazon Hub data from OpenStreetMap."""

    print("="*80)
    print("INTEGRATE AMAZON HUB DATA (from OpenStreetMap) INTO MUNICIPALITY FILES")
    print("="*80)
    print()

    # Check if data exists
    data_file = Path("../data/amazon_all_locations.json")
    if not data_file.exists():
        print("❌ ERROR: ../data/amazon_all_locations.json not found!")
        print("   Run 'python scripts/amazon_fetch_all.py' first to fetch Amazon data from OSM.")
        print()
        print("⚠️  Note: Amazon data comes from OpenStreetMap and may be incomplete.")
        print("   If OSM doesn't have Amazon locations mapped, the fetch will create an empty file.")
        return

    # Load Amazon dataset
    print("📂 Loading Amazon Hub data from OpenStreetMap...")
    amazon_gdf = load_amazon_data(data_file)

    if amazon_gdf.empty:
        print("   ⚠️  No Amazon locations in dataset (OSM may not have coverage)")
        print("   Integration will continue but add no Amazon locations.")
        print()
    else:
        print(f"   Loaded {len(amazon_gdf)} Amazon Hub locations")
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

        result = update_municipality_geojson(gemeente, slug, amazon_gdf, output_dir)

        if result:
            results.append(result)
            change_str = f"+{result['change']}" if result['change'] >= 0 else str(result['change'])

            if result['new_amazon_count'] == 0:
                print(f"✅ No Amazon locations")
            else:
                print(f"✅ {result['old_amazon_count']} → {result['new_amazon_count']} Amazon ({change_str})")
        else:
            print("❌ Failed")

    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)

    if not results:
        print("❌ No municipalities were updated")
        return

    total_old = sum(r['old_amazon_count'] for r in results)
    total_new = sum(r['new_amazon_count'] for r in results)
    total_change = total_new - total_old

    print(f"✅ Updated: {len(results)} municipalities")
    print(f"📍 Total Amazon Hub locations:")
    print(f"   Before: {total_old}")
    print(f"   After:  {total_new}")

    if total_old > 0:
        change_pct = (total_change/total_old*100)
        print(f"   Change: {total_change:+d} ({change_pct:+.1f}%)")
    elif total_new > 0:
        print(f"   Change: +{total_new} (new provider!)")
    else:
        print(f"   Change: No locations (OSM data not available)")

    print()

    if total_new > 0:
        # Show municipalities with Amazon locations
        with_amazon = [r for r in results if r['new_amazon_count'] > 0]
        results_sorted = sorted(with_amazon, key=lambda x: x['new_amazon_count'], reverse=True)

        print(f"Municipalities with Amazon Hub locations ({len(with_amazon)}):")
        for i, r in enumerate(results_sorted[:10], 1):
            print(f"  {i:2d}. {r['gemeente']:20s} {r['new_amazon_count']:3d} locations")

        if len(with_amazon) > 10:
            print(f"  ... and {len(with_amazon) - 10} more")
    else:
        print("ℹ️  No Amazon Hub locations found in OpenStreetMap data.")
        print("   This is expected if Amazon locations haven't been mapped in OSM yet.")
        print("   Consider contributing to OpenStreetMap to improve coverage!")

    print()
    print("⚠️  Remember to regenerate the national overview:")
    print("   python create_national_overview.py")


if __name__ == "__main__":
    main()
