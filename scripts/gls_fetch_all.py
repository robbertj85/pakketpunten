"""
GLS Parcel Shop Fetch - Nationwide grid-based approach.

Uses Playwright to capture GLS API responses, but searches using a grid of
coordinates covering the Netherlands instead of searching by municipality name.
This is much faster than searching 342 municipalities individually.

The GLS website loads data from apm.gls.nl/glspoints/nearby API.
By searching from strategic points, we can capture all locations efficiently.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Playwright not installed. Run:")
    print("   pip install playwright")
    print("   playwright install chromium")
    exit(1)


# Grid of coordinates covering the Netherlands
# Using ~50km spacing to ensure good coverage with overlap
NETHERLANDS_GRID = [
    # North
    (53.2, 5.8),   # Friesland
    (53.2, 6.6),   # Groningen
    (52.8, 5.0),   # Noord-Holland North
    (52.8, 5.8),   # Flevoland
    (52.8, 6.6),   # Drenthe
    # Central
    (52.4, 4.6),   # Amsterdam area
    (52.4, 5.4),   # Utrecht
    (52.4, 6.2),   # Overijssel
    (52.4, 7.0),   # East
    (52.0, 4.4),   # Den Haag/Rotterdam
    (52.0, 5.2),   # Central
    (52.0, 6.0),   # Gelderland
    (52.0, 6.8),   # East
    # South
    (51.6, 4.4),   # Zeeland/Brabant
    (51.6, 5.2),   # Brabant
    (51.6, 6.0),   # Brabant/Limburg
    (51.6, 6.8),   # Limburg
    (51.2, 5.0),   # South Brabant
    (51.2, 5.8),   # Limburg
    (50.9, 5.8),   # South Limburg
]


def extract_location_from_api(item: Dict) -> Optional[Dict]:
    """Extract standardized location data from a GLS API response item."""
    location_data = item.get('location', {})
    if not isinstance(location_data, dict):
        return None

    lat = location_data.get('latitude')
    lng = location_data.get('longitude')

    if lat is None or lng is None:
        return None

    try:
        lat = float(lat)
        lng = float(lng)
    except (ValueError, TypeError):
        return None

    if lat == 0 or lng == 0:
        return None

    # Extract name
    name1 = item.get('name1', '') or ''
    name2 = item.get('name2', '') or ''
    if name1 == 'Parcel Locker':
        name1 = 'Pakketautomaat'
    name = name1.strip()
    if name2 and name2.strip():
        name = f"{name} - {name2.strip()}" if name else name2.strip()

    # Address
    address_data = item.get('address', {}) or {}
    street = address_data.get('street', '') or ''
    house_no = str(address_data.get('houseNo', '') or '')
    house_addition = str(address_data.get('houseNoAddition', '') or '')
    street_nr = f"{house_no}{house_addition}".strip()
    postcode = address_data.get('zipCode', '') or ''
    city = address_data.get('city', '') or ''

    # Point type
    point_type = item.get('glsPointType', 0)
    punt_type = 'locker' if point_type == 4 else 'parcel_shop'

    loc_id = item.get('id', f"{lat}_{lng}")

    return {
        'id': str(loc_id),
        'locatieNaam': name,
        'straatNaam': street,
        'straatNr': street_nr,
        'postcode': postcode,
        'city': city,
        'latitude': lat,
        'longitude': lng,
        'vervoerder': 'GLS',
        'puntType': punt_type,
    }


def fetch_gls_grid(headless: bool = True) -> Dict[str, Dict]:
    """Fetch GLS locations using grid-based search."""
    print("=" * 80)
    print("GLS PARCEL SHOP LOCATION FETCH (Grid-based)")
    print("=" * 80)
    print()
    print(f"Searching {len(NETHERLANDS_GRID)} grid points covering the Netherlands")
    print()

    all_locations: Dict[str, Dict] = {}

    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            locale="nl-NL",
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = context.new_page()

        # Capture API responses
        captured_responses: List[Dict] = []

        def handle_response(response):
            url = response.url
            if 'gls' in url.lower() and 'points' in url.lower():
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        body = response.text()
                        captured_responses.append({'url': url, 'data': body})
                except:
                    pass

        page.on("response", handle_response)

        # Handle cookie consent once
        try:
            page.goto("https://www.gls-info.nl/parcel-shop", wait_until="networkidle", timeout=30000)
            time.sleep(2)

            cookie_selectors = [
                '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
                'button:has-text("Accepteren")',
            ]
            for selector in cookie_selectors:
                try:
                    btn = page.query_selector(selector)
                    if btn and btn.is_visible():
                        btn.click()
                        time.sleep(1)
                        break
                except:
                    continue
        except:
            pass

        for idx, (lat, lng) in enumerate(NETHERLANDS_GRID, 1):
            print(f"[{idx}/{len(NETHERLANDS_GRID)}] Searching around ({lat}, {lng})...")
            captured_responses.clear()

            try:
                # Search using coordinates - GLS website accepts lat/lng in URL
                # Format: ?zipcode=lat,lng or just navigate and let it use geolocation
                # Actually, GLS uses zipcode parameter - let's use a central postcode approach
                # Instead, we'll search for cities near these coordinates

                # Use a representative city/postcode for each grid point
                postcodes = {
                    (53.2, 5.8): "8911",   # Leeuwarden
                    (53.2, 6.6): "9711",   # Groningen
                    (52.8, 5.0): "1621",   # Hoorn
                    (52.8, 5.8): "8232",   # Lelystad
                    (52.8, 6.6): "9401",   # Assen
                    (52.4, 4.6): "1012",   # Amsterdam
                    (52.4, 5.4): "3811",   # Amersfoort
                    (52.4, 6.2): "8011",   # Zwolle
                    (52.4, 7.0): "7511",   # Enschede
                    (52.0, 4.4): "2511",   # Den Haag
                    (52.0, 5.2): "3511",   # Utrecht
                    (52.0, 6.0): "6811",   # Arnhem
                    (52.0, 6.8): "7001",   # Doetinchem
                    (51.6, 4.4): "4331",   # Middelburg
                    (51.6, 5.2): "5038",   # Tilburg
                    (51.6, 6.0): "5611",   # Eindhoven
                    (51.6, 6.8): "5911",   # Venlo
                    (51.2, 5.0): "4811",   # Breda
                    (51.2, 5.8): "6041",   # Roermond
                    (50.9, 5.8): "6211",   # Maastricht
                }

                postcode = postcodes.get((lat, lng), "1012")
                url = f"https://www.gls-info.nl/parcel-shop?zipcode={postcode}"

                page.goto(url, wait_until="networkidle", timeout=30000)
                time.sleep(3)

                # Extract locations from API responses
                for resp in captured_responses:
                    try:
                        data = json.loads(resp['data'])
                        if isinstance(data, list):
                            for item in data:
                                loc = extract_location_from_api(item)
                                if loc and loc['id'] not in all_locations:
                                    all_locations[loc['id']] = loc
                    except:
                        pass

                print(f"   Total unique locations so far: {len(all_locations)}")

            except PlaywrightTimeout:
                print(f"   Timeout, continuing...")
            except Exception as e:
                print(f"   Error: {e}")

            time.sleep(1)

        browser.close()

    return all_locations


def main():
    print()
    print(f"GLS Parcel Shop Location Fetch - Nationwide")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    all_locations = fetch_gls_grid(headless=True)

    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"Total unique locations: {len(all_locations)}")

    # Count by type
    lockers = sum(1 for loc in all_locations.values() if loc['puntType'] == 'locker')
    shops = sum(1 for loc in all_locations.values() if loc['puntType'] == 'parcel_shop')
    print(f"  Lockers: {lockers}")
    print(f"  Parcel shops: {shops}")

    # Save to cache file
    cache_path = Path(__file__).parent.parent / "data" / "gls_all_locations.json"
    locations_list = list(all_locations.values())

    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'fetched_at': datetime.now(timezone.utc).isoformat(),
                'method': 'grid-based-playwright',
                'grid_points': len(NETHERLANDS_GRID),
                'total_locations': len(locations_list),
            },
            'locations': locations_list
        }, f, indent=2, ensure_ascii=False)

    print(f"\nSaved to: {cache_path}")
    print()
    print("=" * 80)
    print("COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
