"""
Fetch all Amazon Hub Locker and Counter locations in the Netherlands.

Uses Playwright to interact with amazon.nl/ulp and capture the fetch_locations API.
Searches by municipality name and clicks on autocomplete suggestions to trigger searches.

Prerequisites:
    pip install playwright
    playwright install chromium

Usage:
    python scripts/amazon_fetch_all.py
"""

import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Playwright not installed. Run:")
    print("   pip install playwright")
    print("   playwright install chromium")
    exit(1)


def load_municipalities() -> List[str]:
    """
    Load municipality names from municipalities.json.
    Returns a list of 342 municipality names (excluding "Nederland (totaal)").
    """
    municipalities_file = Path(__file__).parent.parent / "webapp" / "public" / "municipalities.json"

    with open(municipalities_file, 'r', encoding='utf-8') as f:
        municipalities = json.load(f)

    # Filter out "Nederland (totaal)" and extract just the names
    names = [
        m['name'] for m in municipalities
        if m.get('code') is not None
    ]

    print(f"Loaded {len(names)} municipality names")
    return names


def fetch_all_amazon_locations() -> List[Dict]:
    """
    Fetch all Amazon Hub locations in the Netherlands using municipality-based search.
    Uses autocomplete selection to properly trigger location searches.
    """
    print("=" * 80)
    print("AMAZON HUB COMPLETE LOCATION FETCH (via Playwright)")
    print("Search method: Municipality names with autocomplete")
    print("=" * 80)
    print()

    municipalities = load_municipalities()
    print()

    all_locations: Dict[str, Dict] = {}  # Keyed by location ID for deduplication

    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="nl-NL",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        # Response handler to capture location data
        captured_responses = []

        def handle_response(response):
            if 'fetch_locations' in response.url:
                try:
                    if 'json' in response.headers.get('content-type', ''):
                        body = response.text()
                        captured_responses.append(body)
                except:
                    pass

        page.on("response", handle_response)

        # Navigate to ULP page
        print("Loading amazon.nl/ulp...")
        try:
            page.goto("https://www.amazon.nl/ulp", wait_until="networkidle", timeout=60000)
        except PlaywrightTimeout:
            print("Page load timeout, continuing anyway...")

        time.sleep(5)

        # Accept cookies if present
        accept_btn = page.query_selector('#sp-cc-accept')
        if accept_btn:
            accept_btn.click()
            time.sleep(2)

        print()

        # Search each municipality
        total = len(municipalities)
        start_time = time.time()
        failed_searches = []

        for idx, municipality in enumerate(municipalities):
            # Progress update every 10 municipalities
            if idx % 10 == 0:
                elapsed = time.time() - start_time
                rate = idx / elapsed if elapsed > 0 else 0
                eta = (total - idx) / rate if rate > 0 else 0
                print(f"Progress: {idx}/{total} ({idx*100//total}%) - {len(all_locations)} unique locations - ETA: {eta/60:.1f} min", flush=True)

            # Clear previous responses
            captured_responses.clear()

            # Find search input (might need to re-find after interactions)
            search_input = page.query_selector('#lsView input[type="text"]')
            if not search_input:
                search_input = page.query_selector('input[placeholder*="Voer"]')

            if not search_input:
                failed_searches.append(municipality)
                continue

            try:
                # Clear and type the municipality name
                search_input.click()
                time.sleep(0.2)
                search_input.fill('')
                time.sleep(0.2)
                search_input.type(municipality, delay=50)
                time.sleep(1.2)  # Wait for autocomplete

                # Look for autocomplete suggestions
                suggestions = page.query_selector_all('#lsView li')

                # Click on the first matching suggestion
                clicked = False
                for suggestion in suggestions:
                    try:
                        text = suggestion.inner_text().lower()
                        if text.startswith(municipality.lower()):
                            suggestion.click()
                            clicked = True
                            time.sleep(2.5)  # Wait for API response
                            break
                    except:
                        continue

                # If no exact match, click first suggestion
                if not clicked and suggestions:
                    try:
                        suggestions[0].click()
                        time.sleep(2.5)
                    except:
                        pass

            except Exception as e:
                failed_searches.append(municipality)
                # Try to recover by refreshing
                try:
                    page.goto("https://www.amazon.nl/ulp", wait_until="networkidle", timeout=30000)
                    time.sleep(3)
                    # Re-accept cookies if needed
                    accept_btn = page.query_selector('#sp-cc-accept')
                    if accept_btn:
                        accept_btn.click()
                        time.sleep(2)
                except:
                    pass
                continue

            # Process captured responses
            for resp_body in captured_responses:
                try:
                    data = json.loads(resp_body)
                    locations = data.get('locationList') or []

                    for loc in locations:
                        loc_id = loc.get('id')
                        if not loc_id or loc_id in all_locations:
                            continue

                        # Extract coordinates
                        coords = loc.get('location', {})
                        latitude = coords.get('latitude', 0)
                        longitude = coords.get('longitude', 0)

                        # Skip if no valid coordinates
                        if not latitude or latitude == 0:
                            continue

                        # Store location with standardized format
                        address = loc.get('addressLine1', '') or loc.get('addressLine2', '') or ''
                        all_locations[loc_id] = {
                            'id': loc_id,
                            'locatieNaam': loc.get('name', ''),
                            'straatNaam': address.strip(),
                            'straatNr': '',
                            'postcode': loc.get('postalCode', ''),
                            'city': loc.get('city', ''),
                            'latitude': latitude,
                            'longitude': longitude,
                            'puntType': loc.get('accessPointType', '').lower(),
                            'apisType': loc.get('apisAccessPointType', ''),
                            'vervoerder': 'Amazon',
                        }

                except json.JSONDecodeError:
                    continue

            # Small delay between searches
            time.sleep(0.3)

        browser.close()

    locations_list = list(all_locations.values())
    print()
    print(f"Fetched {len(locations_list)} unique Amazon locations")

    if failed_searches:
        print(f"Failed searches ({len(failed_searches)}): {', '.join(failed_searches[:10])}...")

    return locations_list


def analyze_locations(locations: List[Dict]):
    """Print statistics about fetched locations."""
    print()
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()

    if not locations:
        print("No locations to analyze")
        return

    # Count by type
    type_counts = {}
    for loc in locations:
        loc_type = loc.get('puntType', 'unknown')
        type_counts[loc_type] = type_counts.get(loc_type, 0) + 1

    print("By type:")
    for loc_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"   {loc_type:20s}: {count:4d}")

    # Count by city (top 15)
    city_counts = {}
    for loc in locations:
        city = loc.get('city', 'Unknown')
        if city:
            # Normalize city names (some are uppercase)
            city_normalized = city.title()
            city_counts[city_normalized] = city_counts.get(city_normalized, 0) + 1

    if city_counts:
        print()
        print("Top 15 cities:")
        for i, (city, count) in enumerate(sorted(city_counts.items(), key=lambda x: -x[1])[:15], 1):
            print(f"   {i:2d}. {city:25s}: {count:3d}")

    # Geographic bounds
    lats = [loc['latitude'] for loc in locations if loc.get('latitude')]
    lons = [loc['longitude'] for loc in locations if loc.get('longitude')]

    if lats and lons:
        print()
        print("Geographic coverage:")
        print(f"   Latitude:  {min(lats):.4f} to {max(lats):.4f}")
        print(f"   Longitude: {min(lons):.4f} to {max(lons):.4f}")


def save_results(locations: List[Dict]):
    """Save locations to JSON file."""
    print()
    print("=" * 80)
    print("SAVING RESULTS")
    print("=" * 80)
    print()

    output = {
        "metadata": {
            "total_locations": len(locations),
            "method": "playwright-scraping-municipality-autocomplete",
            "source": "https://www.amazon.nl/ulp",
            "country": "Netherlands",
            "fetched_at": datetime.utcnow().isoformat() + "Z",
        },
        "locations": locations
    }

    # Save to data directory (same format as other carriers)
    output_path = Path(__file__).parent.parent / "data" / "amazon_all_locations.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    file_size_kb = output_path.stat().st_size / 1024
    print(f"Saved to: {output_path}")
    print(f"   File size: {file_size_kb:.1f} KB")
    print(f"   Locations: {len(locations)}")

    # Update log
    log_path = Path(__file__).parent / "amazon_update_log.txt"
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().isoformat()} - Fetched {len(locations)} Amazon locations via Playwright (municipality autocomplete)\n")


def main():
    print()
    print(f"Starting Amazon Hub location fetch...")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    locations = fetch_all_amazon_locations()

    if locations:
        analyze_locations(locations)
        save_results(locations)
    else:
        print("No locations fetched")

    print()
    print("=" * 80)
    print("COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
