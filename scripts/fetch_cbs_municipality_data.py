"""
Fetch municipality area data from CBS (Statistics Netherlands) Open Data API.
This script downloads area (km²) data for all Dutch municipalities and caches it locally.
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path to import from project modules
sys.path.append(str(Path(__file__).parent.parent))

try:
    import cbsodata
except ImportError:
    print("ERROR: cbsodata package not installed")
    print("Please run: pip install cbsodata")
    sys.exit(1)

import pandas as pd


def fetch_municipality_area_data():
    """
    Fetch municipality area data from CBS StatLine.

    Returns:
        dict: Municipality data with area in km²
    """
    print("Fetching municipality area data from CBS...")

    # CBS table 70072NED contains regional key figures including area
    # "Regionale kerncijfers Nederland"
    table_id = "70072ned"

    try:
        # Get table info
        info = cbsodata.get_info(table_id)
        print(f"Table: {info['Title']}")

        # Get data
        data = pd.DataFrame(cbsodata.get_data(table_id))
        print(f"Total rows: {len(data)}")

        # Filter for municipalities only (exclude provinces, corop regions, etc.)
        # Municipality codes start with 'GM'
        if 'KoppelvariabeleRegioCode_316' in data.columns:
            municipalities = data[data['KoppelvariabeleRegioCode_316'].str.startswith('GM', na=False)]
            print(f"Found {len(municipalities)} municipalities")
        else:
            print("Warning: Could not filter by municipality code")
            municipalities = data

        # Extract relevant data
        # TotaleOppervlakte_243 is total area in km²
        result = {}

        for _, row in municipalities.iterrows():
            gemeente = row.get('RegioS', '').strip()
            area_km2 = row.get('TotaleOppervlakte_243', None)

            if gemeente and area_km2 is not None:
                try:
                    area_km2 = float(area_km2)
                    if area_km2 > 0:  # Only include valid areas
                        result[gemeente] = {
                            'name': gemeente,
                            'area_km2': round(area_km2, 2),
                            'code': row.get('KoppelvariabeleRegioCode_316', '')
                        }
                except (ValueError, TypeError):
                    pass

        print(f"Successfully fetched area data for {len(result)} municipalities")
        return result

    except Exception as e:
        print(f"Error fetching CBS data: {e}")
        import traceback
        traceback.print_exc()
        return {}


def main():
    """Main function to fetch and cache CBS data."""

    # Output directory
    output_dir = Path(__file__).parent.parent / "data"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "cbs_municipality_areas.json"

    # Fetch data
    area_data = fetch_municipality_area_data()

    if not area_data:
        print("ERROR: No data fetched. Exiting.")
        sys.exit(1)

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(area_data, f, indent=2, ensure_ascii=False)

    print(f"\nData saved to: {output_file}")
    print(f"Total municipalities: {len(area_data)}")

    # Show sample
    print("\nSample data:")
    for i, (name, data) in enumerate(area_data.items()):
        if i >= 5:
            break
        print(f"  {name}: {data['area_km2']} km² (code: {data['code']})")


if __name__ == "__main__":
    main()
