#!/usr/bin/env python3
"""Debug the Rotterdam polygon from Overpass"""

import requests
import time
from shapely.geometry import shape, Polygon, MultiPolygon, mapping

def get_rotterdam_raw():
    """Get Rotterdam boundary without any fixes"""
    time.sleep(1)

    overpass_url = "https://overpass-api.de/api/interpreter"
    query = """
    [out:json][timeout:30];
    area["name"="Rotterdam"]["admin_level"="8"]["boundary"="administrative"]->.searchArea;
    (
      relation(area.searchArea)["admin_level"="8"]["boundary"="administrative"]["name"="Rotterdam"];
    );
    out geom;
    """

    response = requests.post(
        overpass_url,
        data={'data': query},
        headers={'User-Agent': 'pakketpunten_debug/1.0'},
        timeout=60
    )
    data = response.json()

    if not data.get('elements'):
        print("No elements found!")
        return

    relation = data['elements'][0]
    print(f"Relation ID: {relation['id']}")
    print(f"Tags: {relation.get('tags', {})}")
    print(f"Number of members: {len(relation.get('members', []))}")

    # Count outer vs inner ways
    outer_count = sum(1 for m in relation['members'] if m.get('role') == 'outer')
    inner_count = sum(1 for m in relation['members'] if m.get('role') == 'inner')
    print(f"Outer ways: {outer_count}")
    print(f"Inner ways: {inner_count}")

    # Try to extract geometry
    outer_ways = []
    for member in relation['members']:
        if member['type'] != 'way' or member.get('role') != 'outer':
            continue

        geometry = member.get('geometry', [])
        if not geometry:
            continue

        coords = [(point['lon'], point['lat']) for point in geometry]
        outer_ways.append(coords)

    print(f"\nOuter way segments: {len(outer_ways)}")
    for i, way in enumerate(outer_ways[:5]):  # Show first 5
        print(f"  Way {i}: {len(way)} points")

    # Try creating MultiPolygon
    polygons = []
    for outer_coords in outer_ways:
        if outer_coords[0] != outer_coords[-1]:
            outer_coords.append(outer_coords[0])

        try:
            poly = Polygon(outer_coords)
            polygons.append(poly)
            print(f"  Created polygon: valid={poly.is_valid}, area={poly.area:.6f}")
        except Exception as e:
            print(f"  Failed to create polygon: {e}")

    # Create MultiPolygon
    if len(polygons) == 1:
        geom = polygons[0]
    elif len(polygons) > 1:
        geom = MultiPolygon(polygons)
    else:
        print("No polygons created!")
        return

    print(f"\nFinal geometry:")
    print(f"  Type: {geom.geom_type}")
    print(f"  Is valid: {geom.is_valid}")
    print(f"  Bounds: {geom.bounds}")
    print(f"  Area: {geom.area:.6f}")

    # Try buffer(0) fix
    if not geom.is_valid:
        print("\nApplying buffer(0) fix...")
        fixed = geom.buffer(0)
        print(f"  After fix:")
        print(f"    Type: {fixed.geom_type}")
        print(f"    Is valid: {fixed.is_valid}")
        print(f"    Bounds: {fixed.bounds}")
        print(f"    Area: {fixed.area:.6f}")
        print(f"    Area change: {(fixed.area - geom.area) / geom.area * 100:.1f}%")

if __name__ == "__main__":
    get_rotterdam_raw()
