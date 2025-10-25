"""
Grid-based DHL location fetching to overcome 50-result API limit.

Strategy:
1. Create a grid of search circles covering the Netherlands
2. Fetch data for each grid cell
3. Deduplicate results across overlapping cells
4. Adaptively subdivide cells that hit the 50-limit
"""

import json
import time
import requests
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple, Set, Dict
import math

# Netherlands bounding box (approximate)
NL_BOUNDS = {
    'min_lat': 50.75,   # Southern tip (Limburg)
    'max_lat': 53.55,   # Northern tip (Groningen)
    'min_lon': 3.31,    # Western tip (Zeeland)
    'max_lon': 7.23,    # Eastern tip (Groningen)
}

# Grid configuration
SEARCH_RADIUS = 10000  # 10km radius per search circle
GRID_SPACING_KM = 15   # 15km between grid points (ensures overlap)

# API configuration
DHL_API_URL = "https://api-gw.dhlparcel.nl/parcel-shop-locations/NL/by-geo"
API_LIMIT = 50
RATE_LIMIT_DELAY = 0.5  # seconds between requests


def lat_lon_to_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two lat/lon points in km."""
    # Haversine formula
    R = 6371  # Earth radius in km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat/2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon/2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def km_to_lat_lon_offset(km: float, lat: float) -> Tuple[float, float]:
    """Convert km to approximate lat/lon offset at given latitude."""
    # 1 degree latitude ≈ 111 km everywhere
    lat_offset = km / 111.0

    # 1 degree longitude varies by latitude
    # At equator: ~111 km, at poles: 0 km
    lon_offset = km / (111.0 * math.cos(math.radians(lat)))

    return lat_offset, lon_offset


def generate_grid_points() -> List[Tuple[float, float]]:
    """Generate grid of lat/lon points covering the Netherlands."""
    grid_points = []

    # Start from southwest corner
    current_lat = NL_BOUNDS['min_lat']

    while current_lat <= NL_BOUNDS['max_lat']:
        current_lon = NL_BOUNDS['min_lon']

        while current_lon <= NL_BOUNDS['max_lon']:
            grid_points.append((current_lat, current_lon))

            # Move east
            _, lon_offset = km_to_lat_lon_offset(GRID_SPACING_KM, current_lat)
            current_lon += lon_offset

        # Move north
        lat_offset, _ = km_to_lat_lon_offset(GRID_SPACING_KM, current_lat)
        current_lat += lat_offset

    return grid_points


def fetch_dhl_locations(lat: float, lon: float, radius: int, limit: int = API_LIMIT) -> List[Dict]:
    """Fetch DHL locations from API for given circle."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "radius": radius,
        "limit": limit,
    }

    try:
        response = requests.get(DHL_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])
    except Exception as e:
        print(f"  ⚠️  API error at ({lat:.4f}, {lon:.4f}): {e}")
        return []


def location_to_key(location: Dict) -> Tuple:
    """Create unique key for a location based on coordinates and name."""
    geo = location.get('geoLocation', {})
    lat = geo.get('latitude')
    lon = geo.get('longitude')
    name = location.get('name', '')
    loc_id = location.get('id', '')

    # Round to ~1 meter precision
    return (round(lat, 5), round(lon, 5), name, loc_id)


def subdivide_grid_cell(lat: float, lon: float, radius: int) -> List[Tuple[float, float, int]]:
    """
    Subdivide a grid cell into 4 smaller cells when it hits the limit.
    Returns list of (lat, lon, new_radius) tuples.
    """
    # New radius is half the original
    new_radius = radius // 2

    # Calculate offsets (about 1/2 of original radius in each direction)
    offset_km = new_radius * 0.7  # 0.7 ensures overlap
    lat_offset, lon_offset = km_to_lat_lon_offset(offset_km, lat)

    # Create 4 subcells
    subcells = [
        (lat + lat_offset, lon + lon_offset, new_radius),  # NE
        (lat + lat_offset, lon - lon_offset, new_radius),  # NW
        (lat - lat_offset, lon + lon_offset, new_radius),  # SE
        (lat - lat_offset, lon - lon_offset, new_radius),  # SW
    ]

    return subcells


def fetch_all_dhl_locations_grid() -> Dict[Tuple, Dict]:
    """
    Fetch all DHL locations in Netherlands using grid approach.
    Returns dict mapping location keys to location data.
    """
    all_locations = {}  # key -> location data
    cells_to_process = []  # (lat, lon, radius)
    cells_at_limit = []  # cells that hit the 50-limit

    # Generate initial grid
    print("="*80)
    print("DHL GRID-BASED LOCATION FETCHING")
    print("="*80)
    print()

    grid_points = generate_grid_points()
    for lat, lon in grid_points:
        cells_to_process.append((lat, lon, SEARCH_RADIUS))

    print(f"📍 Generated {len(cells_to_process)} initial grid cells")
    print(f"   Grid spacing: {GRID_SPACING_KM} km")
    print(f"   Search radius: {SEARCH_RADIUS/1000} km")
    print(f"   Coverage area: {NL_BOUNDS['min_lat']:.2f}°N to {NL_BOUNDS['max_lat']:.2f}°N")
    print(f"                  {NL_BOUNDS['min_lon']:.2f}°E to {NL_BOUNDS['max_lon']:.2f}°E")
    print()

    total_api_calls = 0
    processed_cells = 0

    while cells_to_process:
        lat, lon, radius = cells_to_process.pop(0)
        processed_cells += 1

        print(f"[{processed_cells}] Fetching ({lat:.4f}, {lon:.4f}) r={radius/1000:.1f}km...", end=" ")

        # Fetch locations
        locations = fetch_dhl_locations(lat, lon, radius)
        total_api_calls += 1

        # Track unique locations
        new_count = 0
        for location in locations:
            key = location_to_key(location)
            if key not in all_locations:
                all_locations[key] = location
                new_count += 1

        print(f"{len(locations)} results ({new_count} new, {len(all_locations)} total unique)")

        # If we hit the limit and radius is still divisible, subdivide
        if len(locations) >= API_LIMIT and radius > 2000:  # Don't subdivide below 2km
            print(f"  ⚠️  Hit 50-limit! Subdividing into 4 smaller cells...")
            subcells = subdivide_grid_cell(lat, lon, radius)
            cells_to_process.extend(subcells)
            cells_at_limit.append((lat, lon, radius))

        # Rate limiting
        if cells_to_process:  # Don't sleep after last request
            time.sleep(RATE_LIMIT_DELAY)

    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ Total unique DHL locations: {len(all_locations)}")
    print(f"📡 Total API calls: {total_api_calls}")
    print(f"📍 Grid cells processed: {processed_cells}")
    print(f"⚠️  Cells that hit limit: {len(cells_at_limit)}")
    print()

    return all_locations


def save_results(locations: Dict[Tuple, Dict], output_file: str = "../data/dhl_all_locations.json"):
    """Save locations to JSON file."""
    # Convert to list of location dicts
    location_list = list(locations.values())

    # Create output structure
    output = {
        "metadata": {
            "total_locations": len(location_list),
            "method": "grid-based-fetch",
            "grid_spacing_km": GRID_SPACING_KM,
            "search_radius_m": SEARCH_RADIUS,
            "coverage_area": NL_BOUNDS,
        },
        "locations": location_list
    }

    # Save to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    file_size_kb = Path(output_file).stat().st_size / 1024
    print(f"💾 Saved to: {output_file} ({file_size_kb:.1f} KB)")


def analyze_results(locations: Dict[Tuple, Dict]):
    """Analyze the fetched locations."""
    print("\nANALYSIS")
    print("-"*80)

    # Count by type
    type_counts = defaultdict(int)
    for location in locations.values():
        shop_type = location.get('shopType', 'unknown')
        type_counts[shop_type] += 1

    print("By type:")
    for shop_type, count in sorted(type_counts.items()):
        print(f"  {shop_type}: {count}")

    # Geographic distribution
    lats = [loc.get('geoLocation', {}).get('latitude', 0) for loc in locations.values()]
    lons = [loc.get('geoLocation', {}).get('longitude', 0) for loc in locations.values()]

    print(f"\nGeographic spread:")
    print(f"  Latitude: {min(lats):.4f}° to {max(lats):.4f}°")
    print(f"  Longitude: {min(lons):.4f}° to {max(lons):.4f}°")


if __name__ == "__main__":
    print("Starting grid-based DHL location fetch...")
    print("This will take several minutes due to API rate limiting.")
    print()

    # Fetch all locations
    locations = fetch_all_dhl_locations_grid()

    # Analyze
    analyze_results(locations)

    # Save results
    save_results(locations)

    print()
    print("✅ Complete! Use this data to update your municipality GeoJSON files.")
