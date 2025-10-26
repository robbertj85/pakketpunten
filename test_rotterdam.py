#!/usr/bin/env python3
"""
Test script to generate Rotterdam data with new boundaries
This script is for testing the GitHub Actions workflow
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from api_client import get_data_pakketpunten
from geo_analysis import get_bufferzones
from utils import get_gemeente_polygon
import numpy as np
import geopandas as gpd

def process_rotterdam():
    """Process Rotterdam with the new admin_level=8 boundary"""

    gemeente_name = "Rotterdam"
    slug = "rotterdam"

    print(f"\n{'='*60}")
    print(f"🧪 Testing Rotterdam with new admin_level=8 boundary")
    print(f"{'='*60}\n")

    try:
        # Fetch pakketpunten data
        print("📡 Fetching pakketpunten data...")
        gdf_pakketpunten = get_data_pakketpunten(gemeente_name)

        if gdf_pakketpunten.empty:
            print(f"❌ No data found for {gemeente_name}")
            return False

        print(f"✅ Found {len(gdf_pakketpunten)} pakketpunten")

        # Check providers
        providers = sorted(gdf_pakketpunten['vervoerder'].unique())
        print(f"📦 Providers: {', '.join(providers)}")

        # Add dummy occupancy data
        gdf_pakketpunten["bezettingsgraad"] = np.random.randint(0, 101, size=len(gdf_pakketpunten))

        # Replace NaN values
        gdf_pakketpunten = gdf_pakketpunten.fillna("")

        # Generate buffers
        print("🔵 Generating buffer zones...")
        gdf_buffers300, gdf_bufferunion300 = get_bufferzones(gdf_pakketpunten, radius=300)
        gdf_buffers400, gdf_bufferunion400 = get_bufferzones(gdf_pakketpunten, radius=400)

        # Convert back to WGS84
        gdf_buffers300_wgs = gdf_buffers300.to_crs(epsg=4326)
        gdf_buffers400_wgs = gdf_buffers400.to_crs(epsg=4326)

        # Get boundary
        print("🗺️  Fetching municipality boundary (admin_level=8)...")
        gdf_boundary = get_gemeente_polygon(gemeente_name)
        bounds = gdf_boundary.total_bounds

        print(f"   Boundary: [{bounds[0]:.4f}, {bounds[1]:.4f}, {bounds[2]:.4f}, {bounds[3]:.4f}]")
        print(f"   West boundary: {bounds[0]:.4f} (should be ~3.94 for full municipality)")

        # Prepare output
        output_dir = Path(__file__).parent / "webapp" / "public" / "data"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{slug}.geojson"

        # Create comprehensive GeoJSON
        all_features = []

        # Add pakketpunten
        for _, row in gdf_pakketpunten.iterrows():
            feature = {
                "type": "Feature",
                "properties": {
                    "type": "pakketpunt",
                    "locatieNaam": row.get("locatieNaam", ""),
                    "straatNaam": row.get("straatNaam", ""),
                    "straatNr": row.get("straatNr", ""),
                    "vervoerder": row["vervoerder"],
                    "puntType": row.get("puntType", ""),
                    "bezettingsgraad": int(row["bezettingsgraad"]),
                    "latitude": row["latitude"],
                    "longitude": row["longitude"]
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [row["longitude"], row["latitude"]]
                }
            }
            all_features.append(feature)

        # Add buffer unions
        for buffer_m, gdf_buffer in [(300, gdf_buffers300_wgs), (400, gdf_buffers400_wgs)]:
            buffer_union = gdf_buffer.geometry.unary_union
            feature = {
                "type": "Feature",
                "properties": {
                    "type": f"buffer_union_{buffer_m}m",
                    "buffer_m": buffer_m
                },
                "geometry": gpd.GeoSeries([buffer_union], crs="EPSG:4326").to_json(to_wgs84=True)
            }
            # Parse the geometry from the JSON string
            import json as json_lib
            geom_data = json_lib.loads(feature["geometry"])
            feature["geometry"] = geom_data["features"][0]["geometry"]
            all_features.append(feature)

        # Add boundary
        for _, row in gdf_boundary.iterrows():
            feature = {
                "type": "Feature",
                "properties": {
                    "type": "boundary",
                    "gemeente": gemeente_name
                },
                "geometry": gpd.GeoSeries([row.geometry], crs="EPSG:4326").to_json(to_wgs84=True)
            }
            import json as json_lib
            geom_data = json_lib.loads(feature["geometry"])
            feature["geometry"] = geom_data["features"][0]["geometry"]
            all_features.append(feature)

        # Create final GeoJSON
        geojson_data = {
            "type": "FeatureCollection",
            "metadata": {
                "gemeente": gemeente_name,
                "slug": slug,
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "total_points": len(gdf_pakketpunten),
                "providers": providers,
                "bounds": bounds.tolist(),
                "test_run": True,
                "admin_level": 8
            },
            "features": all_features
        }

        # Save
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, ensure_ascii=False, indent=2)

        file_size_mb = output_file.stat().st_size / (1024 * 1024)

        print(f"\n✅ Success!")
        print(f"   Points: {len(gdf_pakketpunten)}")
        print(f"   File: {output_file}")
        print(f"   Size: {file_size_mb:.1f} MB")

        # Compare with expected
        print(f"\n📊 Comparison:")
        print(f"   Old Rotterdam: 311 points (admin_level=10, city center)")
        print(f"   New Rotterdam: {len(gdf_pakketpunten)} points (admin_level=8, full municipality)")

        if len(gdf_pakketpunten) > 311:
            improvement = ((len(gdf_pakketpunten) - 311) / 311 * 100)
            print(f"   Improvement: +{len(gdf_pakketpunten) - 311} points (+{improvement:.1f}%) ✅")
        elif len(gdf_pakketpunten) < 311:
            print(f"   ⚠️  Warning: Fewer points than before!")

        return True

    except Exception as e:
        print(f"\n❌ Error processing {gemeente_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = process_rotterdam()
    sys.exit(0 if success else 1)
