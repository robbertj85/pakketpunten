"""
Create a national overview GeoJSON file by combining all municipality data.
This ensures Nederland totals match the sum of all municipalities with boundary filtering applied.
"""

import json
import glob
from pathlib import Path
from collections import defaultdict

def create_national_overview():
    # Path to municipality data files
    webapp_data_dir = Path(__file__).parent.parent / "webapp" / "public" / "data"

    print("📊 Creating national overview from municipality data...")

    # Get all municipality GeoJSON files (excluding nederland.geojson)
    geojson_files = [f for f in webapp_data_dir.glob("*.geojson") if f.name != "nederland.geojson"]

    print(f"  📁 Found {len(geojson_files)} municipality files")

    # Collect all pakketpunt features
    all_pakketpunten = []
    all_providers = set()
    provider_counts = defaultdict(int)

    # Track bounds
    min_lon, min_lat = float('inf'), float('inf')
    max_lon, max_lat = float('-inf'), float('-inf')

    for geojson_file in geojson_files:
        try:
            with open(geojson_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

                # Extract only pakketpunt features
                pakketpunten = [
                    feature for feature in data['features']
                    if feature['properties'].get('type') == 'pakketpunt'
                ]

                all_pakketpunten.extend(pakketpunten)

                # Track providers and update bounds
                for pp in pakketpunten:
                    provider = pp['properties'].get('vervoerder')
                    if provider:
                        all_providers.add(provider)
                        provider_counts[provider] += 1

                    # Update bounds from coordinates
                    coords = pp['geometry']['coordinates']
                    lon, lat = coords[0], coords[1]
                    min_lon = min(min_lon, lon)
                    max_lon = max(max_lon, lon)
                    min_lat = min(min_lat, lat)
                    max_lat = max(max_lat, lat)

        except Exception as e:
            print(f"  ⚠️  Error processing {geojson_file.name}: {e}")

    print(f"  ✅ Collected {len(all_pakketpunten)} total pakketpunten")
    print(f"  📍 Providers: {', '.join(sorted(all_providers))}")
    for provider in sorted(provider_counts.keys()):
        print(f"     - {provider}: {provider_counts[provider]}")

    # Create GeoJSON structure
    nederland_geojson = {
        "type": "FeatureCollection",
        "metadata": {
            "gemeente": "Nederland",
            "slug": "nederland",
            "generated_at": "2025-10-26T00:00:00Z",  # Will be updated by next batch run
            "total_points": len(all_pakketpunten),
            "providers": sorted(list(all_providers)),
            "bounds": [min_lon, min_lat, max_lon, max_lat]
        },
        "features": all_pakketpunten
    }

    # Save to file
    output_file = webapp_data_dir / "nederland.geojson"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(nederland_geojson, f, ensure_ascii=False, separators=(',', ':'))

    file_size = output_file.stat().st_size / 1024  # KB
    print(f"  💾 Saved: {output_file}")
    print(f"  📦 File size: {file_size:.1f} KB")
    print(f"✅ National overview created successfully!")

    return len(all_pakketpunten)

if __name__ == "__main__":
    total = create_national_overview()
    print(f"\n🎉 Done! Nederland.geojson now contains {total} pakketpunten")
