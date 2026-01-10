"""
FedEx Location Fetch - Full Playwright approach.

Uses Playwright for both sitemap fetching and individual page scraping
to handle Cloudflare protection. Searches by municipality name.
"""

import json
import re
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


def load_municipalities() -> List[str]:
    """Load all municipality names from the data file."""
    municipalities_file = Path(__file__).parent.parent / "data" / "municipalities_all.json"
    with open(municipalities_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [m['name'] for m in data]


def extract_location_from_article(article, city: str) -> Optional[Dict]:
    """Extract location data from a teaser article element."""
    try:
        location = {'search_city': city}

        # Get all text content
        text_content = article.inner_text()
        lines = [l.strip() for l in text_content.split('\n') if l.strip()]

        # Filter navigation lines
        lines = [l for l in lines if l not in ['ROUTEBESCHRIJVING ZOEKEN', 'LINK OPENS IN NEW TAB']]

        if lines:
            location['locatieNaam'] = lines[0]

            # Find postal code and city
            for i, line in enumerate(lines):
                postal_city_match = re.match(r'^(\d{4}\s*[A-Z]{2})\s+(.+)$', line)
                if postal_city_match:
                    location['postcode'] = postal_city_match.group(1).replace(' ', '')
                    location['city'] = postal_city_match.group(2).strip()
                    if i > 0:
                        street_line = lines[i-1]
                        if 'Drop-offs' not in street_line:
                            location['street'] = street_line

        # Check drop-off capability
        location['accepts_dropoff'] = 'niet aanvaard' not in text_content.lower()

        # Get detail URL for coordinates
        location_link = article.query_selector('a[href*="/nl-nl/"]')
        if location_link:
            href = location_link.get_attribute('href')
            if href:
                id_match = re.search(r'/nl-nl/[^/]+/([a-z0-9]+)$', href)
                if id_match:
                    location['id'] = id_match.group(1)
                location['detail_url'] = href

        # Parse street number
        if location.get('street'):
            street = location['street']
            street_match = re.match(r'^(.+?)\s+(\d+[A-Za-z]?)$', street)
            if street_match:
                location['straatNaam'] = street_match.group(1)
                location['straatNr'] = street_match.group(2)
            else:
                location['straatNaam'] = street
                location['straatNr'] = ''
        else:
            location['straatNaam'] = ''
            location['straatNr'] = ''

        # Set vervoerder
        location['vervoerder'] = 'FedEx'
        location['puntType'] = 'dropoff' if location.get('accepts_dropoff', True) else 'pickup'

        return location if location.get('locatieNaam') else None

    except Exception as e:
        return None


def fetch_coordinates_from_detail(page, url: str) -> Optional[tuple]:
    """Fetch coordinates from a detail page."""
    try:
        if url.startswith('../'):
            url = 'https://local.fedex.com/' + url.replace('../', '')
        elif url.startswith('/'):
            url = 'https://local.fedex.com' + url

        response = page.goto(url, wait_until="domcontentloaded", timeout=15000)
        if not response or response.status != 200:
            return None

        time.sleep(0.5)

        # Extract JSON-LD
        scripts = page.query_selector_all('script[type="application/ld+json"]')
        for script in scripts:
            try:
                content = script.inner_text()
                data = json.loads(content)
                if isinstance(data, list):
                    data = data[0] if data else {}

                geo = data.get('geo', {})
                if geo:
                    lat = geo.get('latitude')
                    lng = geo.get('longitude')
                    if lat and lng:
                        lat, lng = float(lat), float(lng)
                        if 50.0 < lat < 54.0 and 3.0 < lng < 8.0:
                            return (lat, lng)
            except:
                continue

        # Try regex patterns
        content = page.content()
        patterns = [
            r'"latitude":\s*([0-9.]+),\s*"longitude":\s*([0-9.]+)',
            r'"lat":\s*([0-9.]+),\s*"lng":\s*([0-9.]+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                lat, lng = float(match.group(1)), float(match.group(2))
                if 50.0 < lat < 54.0 and 3.0 < lng < 8.0:
                    return (lat, lng)

    except:
        pass
    return None


def fetch_fedex_all(headless: bool = True) -> Dict[str, Dict]:
    """Fetch all FedEx locations using Playwright."""
    print("=" * 80)
    print("FEDEX LOCATION FETCH (All Municipalities)")
    print("=" * 80)

    municipalities = load_municipalities()
    print(f"Searching {len(municipalities)} municipalities")
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

        # Handle cookie consent
        try:
            page.goto("https://local.fedex.com/nl-nl", wait_until="networkidle", timeout=30000)
            time.sleep(3)

            cookie_selectors = [
                '#onetrust-accept-btn-handler',
                'button[id*="accept"]',
                'button:has-text("Accept")',
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

        for idx, municipality in enumerate(municipalities, 1):
            print(f"[{idx}/{len(municipalities)}] {municipality}...")

            city_slug = municipality.lower().replace(' ', '-').replace("'", "")
            url = f"https://local.fedex.com/nl-nl/{city_slug}"

            try:
                response = page.goto(url, wait_until="networkidle", timeout=30000)
                time.sleep(2)

                if response and response.status == 200:
                    articles = page.query_selector_all('article.Teaser, .Teaser')

                    locations_found = 0
                    for article in articles:
                        loc = extract_location_from_article(article, municipality)
                        if loc:
                            # Create unique ID
                            loc_id = loc.get('id') or f"{loc.get('locatieNaam', '')}_{loc.get('postcode', '')}".replace(' ', '_')

                            if loc_id not in all_locations:
                                # Try to get coordinates
                                if loc.get('detail_url'):
                                    coords = fetch_coordinates_from_detail(page, loc['detail_url'])
                                    if coords:
                                        loc['latitude'] = coords[0]
                                        loc['longitude'] = coords[1]
                                    time.sleep(0.2)

                                if loc.get('latitude'):
                                    all_locations[loc_id] = loc
                                    locations_found += 1

                    if locations_found > 0:
                        print(f"   Found {locations_found} new locations (total: {len(all_locations)})")

            except PlaywrightTimeout:
                print(f"   Timeout")
            except Exception as e:
                print(f"   Error: {e}")

            time.sleep(0.5)

        browser.close()

    return all_locations


def main():
    print()
    print(f"FedEx Location Fetch - All Netherlands")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    all_locations = fetch_fedex_all(headless=True)

    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"Total unique locations: {len(all_locations)}")

    dropoff = sum(1 for loc in all_locations.values() if loc.get('accepts_dropoff', True))
    pickup_only = len(all_locations) - dropoff
    print(f"  Accept drop-off: {dropoff}")
    print(f"  Pickup only: {pickup_only}")

    # Save to cache
    cache_path = Path(__file__).parent.parent / "data" / "fedex_all_locations.json"
    locations_list = list(all_locations.values())

    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'fetched_at': datetime.now(timezone.utc).isoformat(),
                'method': 'playwright-municipality-search',
                'municipalities_searched': 342,
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
