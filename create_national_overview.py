"""
Create a national overview by aggregating all municipality data
"""

import json
from pathlib import Path
import geopandas as gpd
from shapely.geometry import shape
import pandas as pd

def create_national_overview():
    """Combine all municipality GeoJSON files into a national overview"""

    print("🇳🇱 Creating National Overview...")

    data_dir = Path("webapp/public/data")
    geojson_files = list(data_dir.glob("*.geojson"))

    if not geojson_files:
        print("❌ No GeoJSON files found!")
        return

    print(f"Found {len(geojson_files)} municipality files")

    all_features = []
    all_points = []
    provider_stats = {}
    total_points = 0

    # Track unique locations to detect duplicates
    unique_locations = {}  # key: (lon, lat, provider, name) -> feature

    # Read all GeoJSON files
    for geojson_file in geojson_files:
        print(f"  Processing {geojson_file.name}...")

        with open(geojson_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extract just the pakketpunt features (not buffers)
        for feature in data['features']:
            if feature['properties'].get('type') == 'pakketpunt':
                # Create unique key for deduplication
                coords = feature['geometry']['coordinates']
                provider = feature['properties'].get('vervoerder', 'Unknown')
                name = feature['properties'].get('locatieNaam', 'Unknown')

                # Round coordinates to 6 decimal places (~10cm precision)
                key = (
                    round(coords[0], 6),
                    round(coords[1], 6),
                    provider,
                    name
                )

                # Only add if we haven't seen this exact location+provider+name before
                if key not in unique_locations:
                    unique_locations[key] = feature
                    all_features.append(feature)
                    all_points.append(feature)

                    # Count by provider
                    provider_stats[provider] = provider_stats.get(provider, 0) + 1
                    total_points += 1

    print(f"\n📊 National Statistics:")
    print(f"  Total points: {total_points}")
    print(f"  Providers:")
    for provider, count in sorted(provider_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"    {provider}: {count} points ({count/total_points*100:.1f}%)")

    # Create GeoDataFrame to calculate national bounds
    gdf = gpd.GeoDataFrame.from_features(all_features, crs="EPSG:4326")
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]

    # Create national GeoJSON
    national_data = {
        "type": "FeatureCollection",
        "metadata": {
            "gemeente": "Nederland",
            "slug": "nederland",
            "generated_at": pd.Timestamp.now().isoformat() + "Z",
            "total_points": total_points,
            "providers": sorted(provider_stats.keys()),
            "bounds": bounds.tolist(),
            "municipalities_included": len(geojson_files),
            "provider_stats": provider_stats
        },
        "features": all_features
    }

    # Save national overview
    output_file = data_dir / "nederland.geojson"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(national_data, f, ensure_ascii=False, indent=2)

    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"\n✅ National overview created:")
    print(f"   File: {output_file}")
    print(f"   Size: {file_size_mb:.1f} MB")
    print(f"   Points: {total_points}")
    print(f"   Municipalities: {len(geojson_files)}")

    return provider_stats

def update_municipalities_json():
    """Add Nederland entry to municipalities.json"""

    municipalities_file = Path("webapp/public/municipalities.json")

    with open(municipalities_file, 'r', encoding='utf-8') as f:
        municipalities = json.load(f)

    # Check if Nederland already exists
    if any(m['slug'] == 'nederland' for m in municipalities):
        print("\n'Nederland' already in municipalities.json")
        return

    # Add Nederland as first entry
    nederland = {
        "name": "🇳🇱 Nederland (Landelijk)",
        "slug": "nederland",
        "province": "Alle provincies",
        "population": sum(m['population'] for m in municipalities)
    }

    municipalities.insert(0, nederland)

    with open(municipalities_file, 'w', encoding='utf-8') as f:
        json.dump(municipalities, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Added 'Nederland' to municipalities.json")
    print(f"   Total population: {nederland['population']:,}")

if __name__ == "__main__":
    provider_stats = create_national_overview()
    update_municipalities_json()

    print("\n" + "="*60)
    print("✅ National Overview Complete!")
    print("="*60)
