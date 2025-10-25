"""
Complete DHL update workflow with before/after comparison.

This script:
1. Counts current DHL locations (deduplicated)
2. Runs grid-based fetch
3. Integrates new data
4. Shows comprehensive comparison
5. Regenerates national overview
"""

import json
import subprocess
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime


def count_current_dhl_locations():
    """Count DHL locations in current GeoJSON files."""
    print("=" * 80)
    print("STEP 1: COUNTING CURRENT DHL LOCATIONS")
    print("=" * 80)
    print()

    data_dir = Path("webapp/public/data")
    geojson_files = sorted(data_dir.glob("*.geojson"))

    # Track unique locations (for deduplication)
    unique_locations = set()  # (lat, lon, name) tuples
    municipality_counts = {}

    for geojson_file in geojson_files:
        if geojson_file.name == "nederland.geojson":
            continue  # Skip national overview

        try:
            with open(geojson_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            gemeente = data['metadata']['gemeente']

            # Count DHL pakketpunten
            dhl_points = [
                f for f in data['features']
                if f['properties'].get('type') == 'pakketpunt'
                and f['properties'].get('vervoerder') == 'DHL'
            ]

            municipality_counts[gemeente] = len(dhl_points)

            # Track for deduplication
            for point in dhl_points:
                coords = point['geometry']['coordinates']
                name = point['properties'].get('locatieNaam', '')
                key = (
                    round(coords[0], 5),  # lon
                    round(coords[1], 5),  # lat
                    name
                )
                unique_locations.add(key)

        except Exception as e:
            print(f"  ⚠️  Error reading {geojson_file.name}: {e}")

    total_raw = sum(municipality_counts.values())
    total_unique = len(unique_locations)
    duplicate_rate = ((total_raw - total_unique) / total_raw * 100) if total_raw > 0 else 0

    print(f"📍 Current DHL locations:")
    print(f"   Raw count: {total_raw:,}")
    print(f"   Unique (deduplicated): {total_unique:,}")
    print(f"   Duplicates: {total_raw - total_unique:,} ({duplicate_rate:.1f}%)")
    print(f"   Municipalities: {len(municipality_counts)}")
    print()

    # Show municipalities at 50-limit
    at_limit = {k: v for k, v in municipality_counts.items() if v >= 50}
    if at_limit:
        print(f"⚠️  Municipalities at 50-limit ({len(at_limit)}):")
        for gemeente, count in sorted(at_limit.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {gemeente}: {count}")
        print()

    return {
        'total_raw': total_raw,
        'total_unique': total_unique,
        'municipality_counts': municipality_counts,
        'duplicate_rate': duplicate_rate
    }


def run_grid_fetch():
    """Run the grid-based DHL fetch."""
    print("=" * 80)
    print("STEP 2: RUNNING GRID-BASED DHL FETCH")
    print("=" * 80)
    print()
    print("This will take 3-5 minutes...")
    print()

    # Run the grid fetch script
    result = subprocess.run(
        [sys.executable, "dhl_grid_fetch.py"],
        capture_output=False,
        text=True
    )

    if result.returncode != 0:
        print("\n❌ Grid fetch failed!")
        return False

    # Check if output file exists
    if not Path("../data/dhl_all_locations.json").exists():
        print("\n❌ Grid fetch completed but output file not found!")
        return False

    # Load and analyze
    with open("../data/dhl_all_locations.json", 'r', encoding='utf-8') as f:
        data = json.load(f)

    total = data['metadata']['total_locations']
    print()
    print(f"✅ Grid fetch complete: {total:,} locations fetched")
    print()

    return True


def run_integration():
    """Integrate grid data into municipality files."""
    print("=" * 80)
    print("STEP 3: INTEGRATING GRID DATA INTO MUNICIPALITY FILES")
    print("=" * 80)
    print()

    result = subprocess.run(
        [sys.executable, "integrate_dhl_grid_data.py"],
        capture_output=False,
        text=True
    )

    if result.returncode != 0:
        print("\n❌ Integration failed!")
        return False

    print()
    print("✅ Integration complete")
    print()
    return True


def count_new_dhl_locations():
    """Count DHL locations after update."""
    print("=" * 80)
    print("STEP 4: COUNTING NEW DHL LOCATIONS")
    print("=" * 80)
    print()

    data_dir = Path("webapp/public/data")
    geojson_files = sorted(data_dir.glob("*.geojson"))

    # Track unique locations
    unique_locations = set()
    municipality_counts = {}

    for geojson_file in geojson_files:
        if geojson_file.name == "nederland.geojson":
            continue

        try:
            with open(geojson_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            gemeente = data['metadata']['gemeente']

            dhl_points = [
                f for f in data['features']
                if f['properties'].get('type') == 'pakketpunt'
                and f['properties'].get('vervoerder') == 'DHL'
            ]

            municipality_counts[gemeente] = len(dhl_points)

            # Track for deduplication
            for point in dhl_points:
                coords = point['geometry']['coordinates']
                name = point['properties'].get('locatieNaam', '')
                key = (
                    round(coords[0], 5),
                    round(coords[1], 5),
                    name
                )
                unique_locations.add(key)

        except Exception as e:
            print(f"  ⚠️  Error reading {geojson_file.name}: {e}")

    total_raw = sum(municipality_counts.values())
    total_unique = len(unique_locations)
    duplicate_rate = ((total_raw - total_unique) / total_raw * 100) if total_raw > 0 else 0

    print(f"📍 New DHL locations:")
    print(f"   Raw count: {total_raw:,}")
    print(f"   Unique (deduplicated): {total_unique:,}")
    print(f"   Duplicates: {total_raw - total_unique:,} ({duplicate_rate:.1f}%)")
    print(f"   Municipalities: {len(municipality_counts)}")
    print()

    return {
        'total_raw': total_raw,
        'total_unique': total_unique,
        'municipality_counts': municipality_counts,
        'duplicate_rate': duplicate_rate
    }


def show_comparison(before, after):
    """Show detailed before/after comparison."""
    print("=" * 80)
    print("BEFORE/AFTER COMPARISON")
    print("=" * 80)
    print()

    # Overall stats
    print("📊 OVERALL STATISTICS")
    print("-" * 80)
    print(f"{'Metric':<30} {'Before':>15} {'After':>15} {'Change':>15}")
    print("-" * 80)

    raw_change = after['total_raw'] - before['total_raw']
    raw_pct = (raw_change / before['total_raw'] * 100) if before['total_raw'] > 0 else 0
    print(f"{'Raw count':<30} {before['total_raw']:>15,} {after['total_raw']:>15,} {raw_change:>+14,} ({raw_pct:+.1f}%)")

    unique_change = after['total_unique'] - before['total_unique']
    unique_pct = (unique_change / before['total_unique'] * 100) if before['total_unique'] > 0 else 0
    print(f"{'Unique (deduplicated)':<30} {before['total_unique']:>15,} {after['total_unique']:>15,} {unique_change:>+14,} ({unique_pct:+.1f}%)")

    print(f"{'Duplicate rate':<30} {before['duplicate_rate']:>14.1f}% {after['duplicate_rate']:>14.1f}% {after['duplicate_rate'] - before['duplicate_rate']:>+14.1f}%")
    print()

    # Top gainers
    print("📈 TOP 15 MUNICIPALITIES BY INCREASE")
    print("-" * 80)

    changes = []
    all_municipalities = set(before['municipality_counts'].keys()) | set(after['municipality_counts'].keys())

    for gemeente in all_municipalities:
        old_count = before['municipality_counts'].get(gemeente, 0)
        new_count = after['municipality_counts'].get(gemeente, 0)
        change = new_count - old_count

        if change != 0:
            changes.append((gemeente, old_count, new_count, change))

    changes.sort(key=lambda x: x[3], reverse=True)

    print(f"{'Municipality':<25} {'Before':>10} {'After':>10} {'Change':>12}")
    print("-" * 80)
    for gemeente, old, new, change in changes[:15]:
        pct = (change / old * 100) if old > 0 else 0
        print(f"{gemeente:<25} {old:>10} {new:>10} {change:>+11} ({pct:+.0f}%)")
    print()


def regenerate_national_overview():
    """Regenerate national overview with new data."""
    print("=" * 80)
    print("STEP 5: REGENERATING NATIONAL OVERVIEW")
    print("=" * 80)
    print()

    result = subprocess.run(
        [sys.executable, "create_national_overview.py"],
        capture_output=False,
        text=True
    )

    if result.returncode != 0:
        print("\n❌ National overview regeneration failed!")
        return False

    print()
    print("✅ National overview regenerated")
    print()
    return True


def main():
    """Run complete DHL update workflow."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " COMPLETE DHL UPDATE WORKFLOW ".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Step 1: Count current locations
    before = count_current_dhl_locations()

    # Step 2: Run grid fetch
    if not run_grid_fetch():
        print("\n❌ Workflow aborted: Grid fetch failed")
        return

    # Step 3: Integrate data
    if not run_integration():
        print("\n❌ Workflow aborted: Integration failed")
        return

    # Step 4: Count new locations
    after = count_new_dhl_locations()

    # Step 5: Show comparison
    show_comparison(before, after)

    # Step 6: Regenerate national overview
    if not regenerate_national_overview():
        print("\n⚠️  Warning: National overview regeneration failed")

    # Final summary
    print("=" * 80)
    print("✅ WORKFLOW COMPLETE")
    print("=" * 80)
    print()
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Next steps:")
    print("  1. Check Data Matrix: http://localhost:3000/data-export/matrix")
    print("  2. Verify counts look correct")
    print("  3. Test the map with a large city (Amsterdam, Rotterdam)")
    print()


if __name__ == "__main__":
    main()
