#!/usr/bin/env python3
"""Check for duplicates in nederland.geojson"""

import json
from collections import defaultdict

# Load the file
with open('webapp/public/data/nederland.geojson', 'r') as f:
    data = json.load(f)

pakketpunten = [f for f in data['features'] if f['properties'].get('type') == 'pakketpunt']

print(f"Total pakketpunten: {len(pakketpunten)}")
print(f"Metadata claims: {data['metadata']['total_points']}")
print()

# Check for exact coordinate duplicates
coord_map = defaultdict(list)
for i, feature in enumerate(pakketpunten):
    coords = tuple(feature['geometry']['coordinates'])
    coord_map[coords].append({
        'index': i,
        'name': feature['properties'].get('locatieNaam'),
        'address': f"{feature['properties'].get('straatNaam')} {feature['properties'].get('straatNr')}",
        'provider': feature['properties'].get('vervoerder')
    })

# Find duplicates by exact coordinates
exact_duplicates = {k: v for k, v in coord_map.items() if len(v) > 1}
print(f"Locations with EXACT same coordinates: {len(exact_duplicates)}")
if exact_duplicates:
    print(f"Total duplicate entries from exact coords: {sum(len(v) - 1 for v in exact_duplicates.values())}")
    print("\nFirst 10 examples:")
    for i, (coords, locations) in enumerate(list(exact_duplicates.items())[:10]):
        print(f"\n  Coordinates: {coords}")
        for loc in locations:
            print(f"    - {loc['provider']}: {loc['name']} @ {loc['address']}")
        if i >= 9:
            break

print()

# Check for same location name + provider + address
location_map = defaultdict(list)
for i, feature in enumerate(pakketpunten):
    props = feature['properties']
    key = (
        props.get('locatieNaam', '').strip().lower(),
        props.get('straatNaam', '').strip().lower(),
        props.get('straatNr', '').strip(),
        props.get('vervoerder', '').strip()
    )
    location_map[key].append({
        'index': i,
        'coords': feature['geometry']['coordinates'],
        'name': props.get('locatieNaam'),
        'address': f"{props.get('straatNaam')} {props.get('straatNr')}",
        'provider': props.get('vervoerder')
    })

semantic_duplicates = {k: v for k, v in location_map.items() if len(v) > 1}
print(f"Locations with same name+address+provider: {len(semantic_duplicates)}")
if semantic_duplicates:
    print(f"Total duplicate entries from semantic matching: {sum(len(v) - 1 for v in semantic_duplicates.values())}")
    print("\nFirst 10 examples:")
    for i, (key, locations) in enumerate(list(semantic_duplicates.items())[:10]):
        print(f"\n  {key[3]}: {key[0]} @ {key[1]} {key[2]}")
        for loc in locations:
            print(f"    - Coords: {loc['coords']}")
        if i >= 9:
            break

print()

# Summary
unique_by_coords = len(coord_map)
unique_by_location = len(location_map)
print(f"Summary:")
print(f"  Total points in file: {len(pakketpunten)}")
print(f"  Unique by coordinates: {unique_by_coords}")
print(f"  Unique by name+address+provider: {unique_by_location}")
print(f"  Potential coordinate duplicates: {len(pakketpunten) - unique_by_coords}")
print(f"  Potential semantic duplicates: {len(pakketpunten) - unique_by_location}")
