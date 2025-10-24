"""
Batch processing script to generate pakketpunten data for multiple municipalities.
This script is designed to be run daily via GitHub Actions.
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime
from api_client import get_data_pakketpunten
from geo_analysis import get_bufferzones
import numpy as np

def load_municipalities():
    """Load the list of municipalities to process."""
    with open("municipalities_all.json", "r", encoding="utf-8") as f:
        return json.load(f)

def process_municipality(gemeente_data):
    """
    Process a single municipality and generate GeoJSON output.

    Parameters
    ----------
    gemeente_data : dict
        Municipality data with 'name' and 'slug' keys

    Returns
    -------
    dict
        Result with success status and optional error message
    """
    gemeente_name = gemeente_data["name"]
    slug = gemeente_data["slug"]

    print(f"\n{'='*60}")
    print(f"Processing: {gemeente_name}")
    print(f"{'='*60}")

    try:
        # Fetch pakketpunten data
        gdf_pakketpunten = get_data_pakketpunten(gemeente_name)

        if gdf_pakketpunten.empty:
            print(f"⚠️  No data found for {gemeente_name}")
            return {"success": False, "error": "No data found", "count": 0}

        # Add dummy occupancy data
        gdf_pakketpunten["bezettingsgraad"] = np.random.randint(0, 101, size=len(gdf_pakketpunten))

        # Replace NaN values with None for valid JSON
        gdf_pakketpunten = gdf_pakketpunten.fillna("")

        # Generate buffers
        gdf_buffers300, gdf_bufferunion300 = get_bufferzones(gdf_pakketpunten, radius=300)
        gdf_buffers500, gdf_bufferunion500 = get_bufferzones(gdf_pakketpunten, radius=500)

        # Convert back to WGS84 for web display
        gdf_buffers300_wgs = gdf_buffers300.to_crs(epsg=4326)
        gdf_buffers500_wgs = gdf_buffers500.to_crs(epsg=4326)

        # Prepare output directory
        output_dir = Path("public/data")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save as single comprehensive GeoJSON with all layers
        output_file = output_dir / f"{slug}.geojson"

        # Create a feature collection with multiple feature types
        features = []

        # Add pakketpunten as features
        for _, row in gdf_pakketpunten.iterrows():
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [row["longitude"], row["latitude"]]
                },
                "properties": {
                    "type": "pakketpunt",
                    "locatieNaam": row["locatieNaam"],
                    "straatNaam": row.get("straatNaam", ""),
                    "straatNr": str(row.get("straatNr", "")) if row.get("straatNr") else "",
                    "vervoerder": row["vervoerder"],
                    "puntType": row.get("puntType", ""),
                    "bezettingsgraad": int(row["bezettingsgraad"]),
                    "latitude": row["latitude"],
                    "longitude": row["longitude"]
                }
            })

        # Add buffer union 300m
        for _, row in gdf_bufferunion300.iterrows():
            geom = row.geometry
            features.append({
                "type": "Feature",
                "geometry": json.loads(gpd.GeoSeries([geom]).to_json())["features"][0]["geometry"],
                "properties": {
                    "type": "buffer_union_300m",
                    "buffer_m": 300
                }
            })

        # Add buffer union 500m
        for _, row in gdf_bufferunion500.iterrows():
            geom = row.geometry
            features.append({
                "type": "Feature",
                "geometry": json.loads(gpd.GeoSeries([geom]).to_json())["features"][0]["geometry"],
                "properties": {
                    "type": "buffer_union_500m",
                    "buffer_m": 500
                }
            })

        # Create GeoJSON structure with metadata
        geojson_data = {
            "type": "FeatureCollection",
            "metadata": {
                "gemeente": gemeente_name,
                "slug": slug,
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "total_points": len(gdf_pakketpunten),
                "providers": gdf_pakketpunten["vervoerder"].unique().tolist(),
                "bounds": gdf_pakketpunten.total_bounds.tolist()  # [minx, miny, maxx, maxy]
            },
            "features": features
        }

        # Write to file
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(geojson_data, f, ensure_ascii=False, indent=2)

        # Calculate file size
        file_size_kb = output_file.stat().st_size / 1024

        print(f"✅ Success!")
        print(f"   Points found: {len(gdf_pakketpunten)}")
        print(f"   Providers: {', '.join(gdf_pakketpunten['vervoerder'].unique())}")
        print(f"   File size: {file_size_kb:.1f} KB")
        print(f"   Output: {output_file}")

        return {
            "success": True,
            "count": len(gdf_pakketpunten),
            "file_size_kb": file_size_kb
        }

    except Exception as e:
        print(f"❌ Error processing {gemeente_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e), "count": 0}

def main():
    """Main batch processing function."""
    print("🚀 Starting batch data generation")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load municipalities
    municipalities = load_municipalities()
    total = len(municipalities)
    print(f"\n📋 Found {total} municipalities to process")

    # Process each municipality
    results = []
    for idx, gemeente_data in enumerate(municipalities, 1):
        print(f"\n[{idx}/{total}] Processing {gemeente_data['name']}...")

        result = process_municipality(gemeente_data)
        results.append({
            "gemeente": gemeente_data["name"],
            "slug": gemeente_data["slug"],
            **result
        })

        # Rate limiting: Wait 2 seconds between requests to respect Nominatim usage policy
        # (1 request per second, but we're being extra cautious)
        if idx < total:
            print(f"⏳ Rate limiting: waiting 2 seconds before next municipality...")
            time.sleep(2)

    # Summary
    print("\n" + "="*60)
    print("📊 BATCH PROCESSING SUMMARY")
    print("="*60)

    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")

    if successful:
        total_points = sum(r["count"] for r in successful)
        total_size = sum(r.get("file_size_kb", 0) for r in successful)
        print(f"📍 Total points: {total_points}")
        print(f"💾 Total size: {total_size:.1f} KB")

    if failed:
        print("\n❌ Failed municipalities:")
        for r in failed:
            print(f"   - {r['gemeente']}: {r.get('error', 'Unknown error')}")

    # Save summary
    summary_file = Path("public/data/summary.json")
    summary_file.parent.mkdir(parents=True, exist_ok=True)

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_municipalities": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "results": results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Summary saved to: {summary_file}")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Exit with error code if any failed
    if failed:
        sys.exit(1)

if __name__ == "__main__":
    import geopandas as gpd  # Import here to avoid issues with module-level imports
    main()
