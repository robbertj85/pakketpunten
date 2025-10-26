"""
Batch processing script to generate pakketpunten data for multiple municipalities.
This script is designed to be run daily via GitHub Actions.
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api_client import get_data_pakketpunten
from geo_analysis import get_bufferzones
from utils import get_gemeente_polygon
import numpy as np
import geopandas as gpd

def load_municipalities():
    """Load the list of municipalities to process."""
    # Use path relative to script location, not current working directory
    script_dir = Path(__file__).parent
    municipalities_file = script_dir.parent / "data" / "municipalities_all.json"
    with open(municipalities_file, "r", encoding="utf-8") as f:
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
        # Fetch pakketpunten data with carrier status
        gdf_pakketpunten, carrier_status = get_data_pakketpunten(gemeente_name, return_carrier_status=True)

        if gdf_pakketpunten.empty:
            print(f"⚠️  No data found for {gemeente_name}")
            return {"success": False, "error": "No data found", "count": 0, "carrier_status": carrier_status}

        # Add dummy occupancy data
        gdf_pakketpunten["bezettingsgraad"] = np.random.randint(0, 101, size=len(gdf_pakketpunten))

        # Replace NaN values with None for valid JSON
        gdf_pakketpunten = gdf_pakketpunten.fillna("")

        # Generate buffers
        gdf_buffers300, gdf_bufferunion300 = get_bufferzones(gdf_pakketpunten, radius=300)
        gdf_buffers400, gdf_bufferunion400 = get_bufferzones(gdf_pakketpunten, radius=400)

        # Convert back to WGS84 for web display
        gdf_buffers300_wgs = gdf_buffers300.to_crs(epsg=4326)
        gdf_buffers400_wgs = gdf_buffers400.to_crs(epsg=4326)

        # Prepare output directory (relative to project root, not scripts dir)
        output_dir = Path(__file__).parent.parent / "webapp" / "public" / "data"
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

        # Add buffer union 400m
        for _, row in gdf_bufferunion400.iterrows():
            geom = row.geometry
            features.append({
                "type": "Feature",
                "geometry": json.loads(gpd.GeoSeries([geom]).to_json())["features"][0]["geometry"],
                "properties": {
                    "type": "buffer_union_400m",
                    "buffer_m": 400
                }
            })

        # Add municipality boundary
        try:
            gdf_boundary = get_gemeente_polygon(gemeente_name)
            for _, row in gdf_boundary.iterrows():
                geom = row.geometry
                features.append({
                    "type": "Feature",
                    "geometry": json.loads(gpd.GeoSeries([geom]).to_json())["features"][0]["geometry"],
                    "properties": {
                        "type": "boundary",
                        "gemeente": gemeente_name
                    }
                })
            print(f"  🗺️  Municipality boundary added")
        except Exception as e:
            print(f"  ⚠️  Could not add boundary: {e}")

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

        # Display carrier-level status
        failed_carriers = [name for name, status in carrier_status.items() if not status['success']]
        if failed_carriers:
            print(f"   ⚠️  Failed carriers: {', '.join(failed_carriers)}")

        return {
            "success": True,
            "count": len(gdf_pakketpunten),
            "file_size_kb": file_size_kb,
            "carrier_status": carrier_status,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        print(f"❌ Error processing {gemeente_name}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "count": 0,
            "carrier_status": {},
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }

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

    # Aggregate carrier-level statistics
    carrier_stats = {}
    carriers = ['DHL', 'PostNL', 'DPD', 'VintedGo', 'DeBuren']

    for carrier in carriers:
        successful_fetches = 0
        failed_fetches = 0
        total_points = 0
        latest_update = None

        for r in successful:
            carrier_status = r.get('carrier_status', {}).get(carrier, {})
            if carrier_status.get('success'):
                successful_fetches += 1
                total_points += carrier_status.get('count', 0)
                # Track latest update time
                update_time = r.get('generated_at')
                if update_time and (not latest_update or update_time > latest_update):
                    latest_update = update_time
            else:
                failed_fetches += 1

        carrier_stats[carrier] = {
            'successful_municipalities': successful_fetches,
            'failed_municipalities': failed_fetches,
            'total_points': total_points,
            'latest_update': latest_update,
            'overall_success_rate': round(successful_fetches / len(results) * 100, 1) if results else 0
        }

    # Print carrier summary
    print("\n📊 CARRIER STATUS SUMMARY:")
    for carrier, stats in carrier_stats.items():
        status_icon = "✅" if stats['failed_municipalities'] == 0 else "⚠️"
        print(f"  {status_icon} {carrier}: {stats['successful_municipalities']}/{len(results)} municipalities ({stats['overall_success_rate']}%)")
        if stats['failed_municipalities'] > 0:
            print(f"     Failed in {stats['failed_municipalities']} municipalities")

    # Save summary (use absolute path relative to script location)
    summary_file = Path(__file__).parent.parent / "webapp" / "public" / "data" / "summary.json"
    summary_file.parent.mkdir(parents=True, exist_ok=True)

    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump({
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "total_municipalities": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "carrier_stats": carrier_stats,
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
