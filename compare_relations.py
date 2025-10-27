#!/usr/bin/env python3
"""
Compare the two Rotterdam relations to see what the difference is
"""

import requests
import time

def lookup_osm_relation(osm_id):
    """Look up details for an OSM relation"""
    url = "https://nominatim.openstreetmap.org/lookup"
    params = {
        'osm_ids': f'R{osm_id}',
        'format': 'json',
        'polygon_geojson': 0,
        'extratags': 1,
        'addressdetails': 1
    }
    headers = {'User-Agent': 'pakketpunten_boundary_tester/1.0'}

    time.sleep(1)
    response = requests.get(url, params=params, headers=headers, timeout=30)
    data = response.json()

    return data[0] if data else None

def get_osm_tags(osm_id):
    """Get tags directly from OSM API"""
    url = f"https://www.openstreetmap.org/api/0.6/relation/{osm_id}.json"
    headers = {'User-Agent': 'pakketpunten_boundary_tester/1.0'}

    time.sleep(1)
    response = requests.get(url, headers=headers, timeout=30)
    data = response.json()

    if 'elements' in data and data['elements']:
        return data['elements'][0].get('tags', {})

    return {}

if __name__ == "__main__":
    print("Comparing Rotterdam relations...\n")

    relations = [1411101, 324431]

    for rel_id in relations:
        print("="*60)
        print(f"RELATION {rel_id}")
        print("="*60)

        # Get from Nominatim
        result = lookup_osm_relation(rel_id)
        if result:
            print(f"Display Name: {result.get('display_name')}")
            print(f"Type: {result.get('type')}")
            print(f"Bounding Box: {result.get('boundingbox')}")

        # Get tags from OSM API
        print("\nOSM Tags:")
        tags = get_osm_tags(rel_id)
        for key, value in sorted(tags.items()):
            if key in ['name', 'admin_level', 'boundary', 'type', 'ref:CBS', 'wikidata', 'wikipedia']:
                print(f"  {key}: {value}")

        print()

    print("="*60)
    print("🔍 ANALYSIS")
    print("="*60)
    print("\nLet's check the OSM pages directly:")
    print(f"  Relation 1411101: https://www.openstreetmap.org/relation/1411101")
    print(f"  Relation 324431: https://www.openstreetmap.org/relation/324431")
