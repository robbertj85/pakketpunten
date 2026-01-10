"""
GLS Parcel Shop Fetch POC - Playwright-based scraper for GLS parcel point locations.

Fetches GLS parcel shop locations in the Netherlands by searching for municipalities.
Uses Playwright to handle the Angular-based website and capture network requests.

The GLS website (gls-info.nl) uses Angular and loads parcel shop data via XHR requests
to apm.gls.nl API. This script captures those requests and extracts location data.

Prerequisites:
    pip install playwright
    playwright install chromium

Usage:
    python scripts/gls_fetch_poc.py
"""

import json
import time
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Playwright not installed. Run:")
    print("   pip install playwright")
    print("   playwright install chromium")
    exit(1)


def parse_location_from_text(text: str) -> Optional[Dict]:
    """
    Parse location data from text scraped from the page.
    Text format example:
    "Parcel Locker
    Keizersgracht 650
    1017ES AMSTERDAM
    Open tot 23:00"
    """
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]

    if len(lines) < 3:
        return None

    # Filter out UI elements
    lines = [l for l in lines if l not in ['navigate_before', 'keyboard_arrow_down', 'keyboard_arrow_up', 'update', 'NL', 'menu']]

    if len(lines) < 3:
        return None

    name = lines[0]

    # Find address line (contains street with number)
    address_line = None
    postcode_city_line = None

    for i, line in enumerate(lines[1:], 1):
        # Check for postcode pattern (4 digits + 2 letters + space + city)
        if re.match(r'^\d{4}[A-Z]{2}\s+', line.upper()) or re.match(r'^\d{4}\s*[A-Z]{2}\s+', line.upper()):
            postcode_city_line = line
            if i > 1:
                address_line = lines[i - 1]
            break

    if not postcode_city_line:
        return None

    # Parse postcode and city
    pc_match = re.match(r'^(\d{4}\s*[A-Z]{2})\s+(.+)$', postcode_city_line, re.IGNORECASE)
    if pc_match:
        postcode = pc_match.group(1).upper().replace(' ', '')
        city = pc_match.group(2).strip()
    else:
        return None

    # Parse street and number from address line
    street = ''
    street_nr = ''
    if address_line:
        # Try to extract house number at end
        addr_match = re.match(r'^(.+?)\s+(\d+[A-Za-z]?)$', address_line)
        if addr_match:
            street = addr_match.group(1)
            street_nr = addr_match.group(2)
        else:
            street = address_line

    return {
        'locatieNaam': name,
        'straatNaam': street,
        'straatNr': street_nr,
        'postcode': postcode,
        'city': city,
        'vervoerder': 'GLS',
        'puntType': 'locker' if 'locker' in name.lower() else 'parcel_shop',
    }


def fetch_gls_locations(search_terms: List[str], headless: bool = True) -> Tuple[Dict[str, List[Dict]], Dict[str, Dict]]:
    """
    Fetch GLS parcel shop locations for given search terms.

    Args:
        search_terms: List of municipality/city names to search
        headless: Run browser in headless mode

    Returns:
        Tuple of (results by search term, all unique locations)
    """
    print("=" * 80)
    print("GLS PARCEL SHOP LOCATION FETCH (Playwright POC)")
    print("=" * 80)
    print()

    all_results: Dict[str, List[Dict]] = {}
    all_locations: Dict[str, Dict] = {}  # Global dedup by unique key

    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            locale="nl-NL",
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Capture ALL network requests for debugging
        captured_api_responses: List[Dict] = []
        all_network_urls: List[str] = []

        def handle_response(response):
            """Capture all API responses."""
            url = response.url
            all_network_urls.append(url)

            # Capture any JSON response from gls.nl domains
            if 'gls' in url.lower():
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type or url.endswith('.json'):
                        body = response.text()
                        captured_api_responses.append({
                            'url': url,
                            'data': body,
                            'status': response.status
                        })
                except Exception:
                    pass

        page.on("response", handle_response)

        for search_term in search_terms:
            print(f"\n{'='*60}")
            print(f"Searching for: {search_term}")
            print("=" * 60)

            captured_api_responses.clear()
            all_network_urls.clear()
            search_results = []

            try:
                # Navigate to the parcel shop page with the search term
                url = f"https://www.gls-info.nl/parcel-shop?zipcode={search_term.lower()}"
                print(f"Loading: {url}")

                page.goto(url, wait_until="networkidle", timeout=30000)
                time.sleep(2)

                # Handle cookie consent banner if present
                try:
                    cookie_selectors = [
                        '#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll',
                        'button:has-text("Accepteren")',
                        'button:has-text("Accept")',
                        '#onetrust-accept-btn-handler',
                    ]

                    for selector in cookie_selectors:
                        try:
                            cookie_btn = page.query_selector(selector)
                            if cookie_btn and cookie_btn.is_visible():
                                print(f"Accepting cookies: {selector}")
                                cookie_btn.click()
                                time.sleep(1)
                                break
                        except:
                            continue
                except Exception as e:
                    print(f"Cookie handling: {e}")

                # Wait for Angular to render the content
                time.sleep(3)

                print(f"Page title: {page.title()}")

                # Debug: Print all captured GLS API calls
                print(f"\nCaptured {len(captured_api_responses)} GLS API responses:")
                for resp in captured_api_responses:
                    print(f"  - {resp['url']}")
                    try:
                        data = json.loads(resp['data'])
                        if isinstance(data, list):
                            print(f"    Array with {len(data)} items")
                            if data and isinstance(data[0], dict):
                                print(f"    Sample keys: {list(data[0].keys())[:8]}")
                        elif isinstance(data, dict):
                            print(f"    Dict with keys: {list(data.keys())[:8]}")
                    except:
                        print(f"    (not JSON)")

                # Look for parcel shop data API endpoint specifically
                parcel_shop_data = None
                for resp in captured_api_responses:
                    if 'parcel' in resp['url'].lower() or 'points' in resp['url'].lower():
                        try:
                            data = json.loads(resp['data'])
                            if isinstance(data, list) and len(data) > 0:
                                parcel_shop_data = data
                                print(f"\nFound parcel shop data in: {resp['url']}")
                                break
                        except:
                            pass

                # If we found API data, extract locations
                if parcel_shop_data:
                    for item in parcel_shop_data:
                        loc = extract_location_from_item(item)
                        if loc:
                            loc_id = loc.get('id')
                            if loc_id not in all_locations:
                                search_results.append(loc)
                                all_locations[loc_id] = loc

                # If no API data found, scrape from the visible DOM
                if not search_results:
                    print("\nNo API data found, scraping from DOM...")

                    # Scroll to load all items (Angular may lazy-load)
                    for _ in range(3):
                        page.evaluate('window.scrollBy(0, 500)')
                        time.sleep(0.5)

                    # Scrape location cards from the Angular app
                    scraped_data = page.evaluate('''() => {
                        const results = [];

                        // Find all mat-expansion-panel or similar Angular Material components
                        const panels = document.querySelectorAll('mat-expansion-panel, .mat-expansion-panel, mat-card, .mat-mdc-card');

                        panels.forEach((panel, idx) => {
                            const text = panel.innerText;
                            results.push({
                                index: idx,
                                text: text.substring(0, 600)
                            });
                        });

                        // Alternative: find by class patterns in GLS-specific structure
                        if (results.length === 0) {
                            const items = document.querySelectorAll('[class*="shop"], [class*="location"], [class*="result"]');
                            items.forEach((item, idx) => {
                                results.push({
                                    index: idx,
                                    text: item.innerText.substring(0, 600)
                                });
                            });
                        }

                        // Last resort: get all main content
                        if (results.length === 0) {
                            const main = document.querySelector('main, [role="main"], .main-content, app-root');
                            if (main) {
                                results.push({
                                    index: 0,
                                    text: main.innerText.substring(0, 5000)
                                });
                            }
                        }

                        return results;
                    }''')

                    print(f"Scraped {len(scraped_data)} DOM elements")

                    # Parse each scraped element
                    for item in scraped_data:
                        text = item.get('text', '')

                        # Split into individual location blocks
                        # Each location typically starts with a name and has postcode pattern
                        blocks = re.split(r'(?=\n(?:Parcel Locker|[A-Z][a-z]+\s+[A-Z][a-z]+|\w+\s+"\w+))', text)

                        for block in blocks:
                            if not block.strip():
                                continue

                            loc = parse_location_from_text(block)
                            if loc:
                                loc_key = f"{loc['postcode']}_{loc['straatNr']}"
                                if loc_key not in all_locations:
                                    search_results.append(loc)
                                    all_locations[loc_key] = loc

                    # Alternative: parse the whole page body
                    if not search_results:
                        body_text = page.evaluate('() => document.body.innerText')
                        print(f"\nParsing full page body ({len(body_text)} chars)...")

                        # Find all postcode patterns and extract surrounding context
                        postcode_pattern = r'(\d{4}[A-Z]{2})\s+([A-Z][A-Za-z\s\'-]+?)(?=\n|update|Open|Gesloten)'
                        matches = re.findall(postcode_pattern, body_text, re.IGNORECASE)

                        for postcode, city in matches:
                            # Find the location block around this postcode
                            idx = body_text.find(postcode)
                            if idx > 0:
                                # Get context around the postcode (name and address should be above)
                                start = max(0, idx - 200)
                                end = min(len(body_text), idx + 100)
                                context = body_text[start:end]

                                loc = parse_location_from_text(context)
                                if loc:
                                    loc_key = f"{loc['postcode']}_{loc['straatNr']}"
                                    if loc_key not in all_locations:
                                        search_results.append(loc)
                                        all_locations[loc_key] = loc

                # Store results for this search term
                all_results[search_term] = search_results
                print(f"\nFound {len(search_results)} locations for {search_term}")

                # Print sample locations
                for loc in search_results[:3]:
                    print(f"  - {loc['locatieNaam']}: {loc['straatNaam']} {loc['straatNr']}, {loc['postcode']} {loc['city']}")

            except PlaywrightTimeout as e:
                print(f"Timeout for {search_term}: {e}")
                all_results[search_term] = []
            except Exception as e:
                print(f"Error for {search_term}: {e}")
                import traceback
                traceback.print_exc()
                all_results[search_term] = []

            time.sleep(1)  # Delay between searches

        # Take a screenshot for debugging
        screenshot_path = Path(__file__).parent / "gls_debug_screenshot.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"\nSaved debug screenshot to: {screenshot_path}")

        browser.close()

    return all_results, all_locations


def extract_location_from_item(item: Dict) -> Optional[Dict]:
    """
    Extract standardized location data from a GLS API response item.

    GLS API response format (from apm.gls.nl/glspoints/nearby):
    {
        "glsPointType": 4,  // 4 = LOCKER, other values = PARCELSHOP
        "id": "M3FA7OcYYjYXKz",
        "name1": "Pakketautomaat",
        "name2": "",
        "location": {
            "latitude": 51.9197712,
            "longitude": 4.48626423
        },
        "address": {
            "street": "Ds. Jan Scharpstraat",
            "houseNo": "298",
            "houseNoAddition": "",
            "zipCode": "3011GZ",
            "city": "ROTTERDAM",
            "country": "NL",
            "locCode": "NL2500"
        },
        "website": "",
        "info1": "",
        "isViaTim": false,
        ...
    }
    """
    # GLS stores coordinates in 'location' object
    location_data = item.get('location', {})

    if not isinstance(location_data, dict):
        return None

    # Extract coordinates from location object
    lat = location_data.get('latitude')
    lng = location_data.get('longitude')

    if lat is None or lng is None:
        return None

    # Try to get float values
    try:
        lat = float(lat)
        lng = float(lng)
    except (ValueError, TypeError):
        return None

    # Skip if coordinates are 0 (invalid)
    if lat == 0 or lng == 0:
        return None

    # Extract name (GLS uses name1 and name2)
    name1 = item.get('name1', '') or ''
    name2 = item.get('name2', '') or ''

    # Dutch translation for locker
    if name1 == 'Parcel Locker':
        name1 = 'Pakketautomaat'

    name = name1.strip()
    if name2 and name2.strip():
        name = f"{name} - {name2.strip()}" if name else name2.strip()

    # Address fields from separate 'address' object (NOT location!)
    address_data = item.get('address', {}) or {}

    street = address_data.get('street', '') or ''
    house_no = str(address_data.get('houseNo', '') or '')
    house_addition = str(address_data.get('houseNoAddition', '') or '')
    street_nr = f"{house_no}{house_addition}".strip()

    postcode = address_data.get('zipCode', '') or ''
    city = address_data.get('city', '') or ''

    # Point type based on glsPointType (4 = LOCKER, typically)
    point_type = item.get('glsPointType', 0)
    punt_type = 'locker' if point_type == 4 else 'parcel_shop'

    # ID
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


def analyze_results(results: Dict[str, List[Dict]], all_locations: Dict[str, Dict]):
    """Analyze and print results summary."""
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    for search_term, locations in results.items():
        print(f"\n{search_term}:")
        print(f"  Found {len(locations)} locations")

        for i, loc in enumerate(locations[:5], 1):
            name = loc.get('locatieNaam', 'Unknown')
            city = loc.get('city', '')
            lat = loc.get('latitude')
            lng = loc.get('longitude')
            address = f"{loc.get('straatNaam', '')} {loc.get('straatNr', '')}".strip()
            postcode = loc.get('postcode', '')

            print(f"    {i}. {name}")
            if address:
                print(f"       Address: {address}")
            if postcode:
                print(f"       Postcode: {postcode}")
            if city:
                print(f"       City: {city}")
            if lat and lng:
                print(f"       Coordinates: ({lat}, {lng})")
            else:
                print(f"       Coordinates: (not available - text scraping)")

        if len(locations) > 5:
            print(f"    ... and {len(locations) - 5} more")

    print(f"\nTotal unique locations across all searches: {len(all_locations)}")


def main():
    print()
    print(f"GLS Parcel Shop Location Fetch POC")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Search terms to test
    search_terms = ["Rotterdam", "Elburg", "Amsterdam"]

    results, all_locations = fetch_gls_locations(search_terms, headless=True)

    analyze_results(results, all_locations)

    # Save raw data for analysis
    output_path = Path(__file__).parent / "gls_poc_results.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'fetched_at': datetime.now(timezone.utc).isoformat(),
                'search_terms': search_terms,
            },
            'results': {k: [loc for loc in v] for k, v in results.items()},
            'all_locations': list(all_locations.values())
        }, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nSaved results to: {output_path}")

    print("\n" + "=" * 80)
    print("COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
