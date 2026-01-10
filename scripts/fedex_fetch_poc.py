"""
Proof-of-concept: Fetch FedEx parcel point locations in the Netherlands.

Uses Playwright to interact with local.fedex.com and capture location data.
Searches by city name and extracts location information from the page.

Prerequisites:
    pip install playwright
    playwright install chromium

Usage:
    python scripts/fedex_fetch_poc.py
"""

import json
import time
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
from urllib.parse import unquote

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Playwright not installed. Run:")
    print("   pip install playwright")
    print("   playwright install chromium")
    exit(1)


def handle_cookie_banner(page) -> bool:
    """
    Handle FedEx cookie consent banner if present.
    Returns True if banner was handled, False otherwise.
    """
    try:
        # Look for common cookie consent buttons
        selectors = [
            'button[id*="accept"]',
            'button[id*="cookie"]',
            'button[class*="accept"]',
            'button[class*="consent"]',
            '#onetrust-accept-btn-handler',
            '.onetrust-close-btn-handler',
            'button:has-text("Accept")',
            'button:has-text("Accepteren")',
            'button:has-text("Alle cookies accepteren")',
            '[data-testid="cookie-accept"]',
        ]

        for selector in selectors:
            try:
                btn = page.query_selector(selector)
                if btn and btn.is_visible():
                    btn.click()
                    print("   Cookie banner accepted")
                    time.sleep(1)
                    return True
            except:
                continue

        return False
    except Exception as e:
        print(f"   Cookie handling error: {e}")
        return False


def extract_coordinates_from_maps_url(url: str) -> Optional[tuple]:
    """
    Extract latitude/longitude from Google Maps URL if present.
    Format: https://www.google.com/maps/search/?api=1&query=lat,lng
    """
    try:
        if 'query=' in url:
            query = url.split('query=')[1].split('&')[0]
            query = unquote(query)

            # Check if query contains coordinates (comma-separated numbers)
            coord_match = re.search(r'(-?\d+\.?\d*),\s*(-?\d+\.?\d*)', query)
            if coord_match:
                lat = float(coord_match.group(1))
                lng = float(coord_match.group(2))
                # Validate Netherlands coordinates
                if 50.0 < lat < 54.0 and 3.0 < lng < 8.0:
                    return (lat, lng)
        return None
    except:
        return None


def fetch_location_coordinates(page, detail_url: str) -> Optional[tuple]:
    """
    Fetch coordinates from an individual location detail page.
    Look for JSON-LD schema markup or embedded coordinates in JavaScript.
    """
    try:
        # Make the URL absolute if needed
        if detail_url.startswith('../'):
            detail_url = 'https://local.fedex.com/' + detail_url.replace('../', '')
        elif detail_url.startswith('/'):
            detail_url = 'https://local.fedex.com' + detail_url

        response = page.goto(detail_url, wait_until="domcontentloaded", timeout=10000)

        if response and response.status == 200:
            time.sleep(0.5)

            # Method 1: Look for JSON-LD schema with geo coordinates
            scripts = page.query_selector_all('script[type="application/ld+json"]')
            for script in scripts:
                try:
                    content = script.inner_text()
                    data = json.loads(content)

                    # Handle array of schemas
                    if isinstance(data, list):
                        data = data[0] if data else {}

                    # Look for geo coordinates
                    geo = data.get('geo', {})
                    if geo:
                        lat = geo.get('latitude')
                        lng = geo.get('longitude')
                        if lat and lng:
                            return (float(lat), float(lng))

                    # Check in address
                    address = data.get('address', {})
                    if isinstance(address, dict):
                        geo = address.get('geo', {})
                        if geo:
                            lat = geo.get('latitude')
                            lng = geo.get('longitude')
                            if lat and lng:
                                return (float(lat), float(lng))

                except json.JSONDecodeError:
                    continue

            # Method 2: Look for coordinates in page JavaScript
            page_content = page.content()

            # Look for common coordinate patterns
            patterns = [
                r'"latitude":\s*([0-9.]+),\s*"longitude":\s*([0-9.]+)',
                r'"lat":\s*([0-9.]+),\s*"lng":\s*([0-9.]+)',
                r'"lat":\s*([0-9.]+),\s*"lon":\s*([0-9.]+)',
                r'displayCoordinate.*?"latitude":\s*([0-9.]+).*?"longitude":\s*([0-9.]+)',
                r'yextDisplayCoordinate.*?"latitude":\s*([0-9.]+).*?"longitude":\s*([0-9.]+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, page_content, re.DOTALL)
                if match:
                    lat = float(match.group(1))
                    lng = float(match.group(2))
                    # Validate Netherlands coordinates
                    if 50.0 < lat < 54.0 and 3.0 < lng < 8.0:
                        return (lat, lng)

    except Exception as e:
        pass

    return None


def scrape_directory_page(page) -> List[Dict]:
    """
    Scrape all locations from the current directory page by parsing HTML structure.
    Uses article/.Teaser elements which contain location information.
    """
    locations = []

    try:
        # Find all location articles/teasers
        articles = page.query_selector_all('article.Teaser, .Teaser')

        for article in articles:
            try:
                location = {}

                # Get all text content from the article
                text_content = article.inner_text()
                lines = [l.strip() for l in text_content.split('\n') if l.strip()]

                # Filter out navigation-type lines
                lines = [l for l in lines if l not in ['ROUTEBESCHRIJVING ZOEKEN', 'LINK OPENS IN NEW TAB']]

                if lines:
                    # First non-empty line is the name
                    location['name'] = lines[0]

                    # Look for Dutch postal code pattern and extract address
                    for i, line in enumerate(lines):
                        # Dutch postal code: 4 digits + space + 2 letters (e.g., "3027 HM Rotterdam")
                        postal_city_match = re.match(r'^(\d{4}\s*[A-Z]{2})\s+(.+)$', line)
                        if postal_city_match:
                            location['postcode'] = postal_city_match.group(1).replace(' ', '')
                            location['city'] = postal_city_match.group(2).strip()
                            # Previous line should be the street address
                            if i > 0:
                                street_line = lines[i-1]
                                # Skip if previous line is status message
                                if 'Drop-offs' not in street_line:
                                    location['street'] = street_line

                    # Check for status message (drop-off acceptance)
                    if 'niet aanvaard' in text_content.lower():
                        location['accepts_dropoff'] = False
                        location['status'] = 'Drop-offs worden niet aanvaard'
                    else:
                        location['accepts_dropoff'] = True

                # Look for Google Maps link within this article
                maps_link = article.query_selector('a[href*="google.com/maps"]')
                if maps_link:
                    href = maps_link.get_attribute('href')
                    if href:
                        coords = extract_coordinates_from_maps_url(href)
                        if coords:
                            location['latitude'] = coords[0]
                            location['longitude'] = coords[1]
                        else:
                            # Store the URL for potential geocoding later
                            location['maps_url'] = href

                # Look for link to individual location page (may contain ID)
                location_link = article.query_selector('a[href*="/nl-nl/"]')
                if location_link:
                    href = location_link.get_attribute('href')
                    if href:
                        # Extract location ID from URL (e.g., /nl-nl/rotterdam/rtmwm -> rtmwm)
                        id_match = re.search(r'/nl-nl/[^/]+/([a-z0-9]+)$', href)
                        if id_match:
                            location['location_id'] = id_match.group(1)
                        location['detail_url'] = href

                # Only add if we have at least a name
                if location.get('name') and location.get('name') != 'NL':
                    location['vervoerder'] = 'FedEx'
                    locations.append(location)

            except Exception as e:
                print(f"   Error parsing article: {e}")
                continue

    except Exception as e:
        print(f"   Error in directory scraping: {e}")

    return locations


def fetch_fedex_locations_poc(cities: List[str]) -> Dict[str, List[Dict]]:
    """
    Proof-of-concept: Fetch FedEx locations for specified cities.
    """
    print("=" * 80)
    print("FEDEX LOCATION FETCH POC (via Playwright)")
    print("=" * 80)
    print()

    results = {}
    all_locations = []

    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="nl-NL",
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Initial navigation to handle cookies once
        print("Loading FedEx location finder...")
        try:
            page.goto("https://local.fedex.com/nl-nl", wait_until="networkidle", timeout=30000)
            time.sleep(3)
            handle_cookie_banner(page)
        except PlaywrightTimeout:
            print("Initial page load timeout, continuing...")

        print()

        for city in cities:
            print(f"Searching: {city}")
            city_locations = []

            # Method 1: Try direct directory URL
            city_slug = city.lower().replace(' ', '-').replace("'", "")
            url = f"https://local.fedex.com/nl-nl/{city_slug}"

            # Try up to 2 attempts for each city
            for attempt in range(2):
                try:
                    response = page.goto(url, wait_until="networkidle", timeout=60000)
                    time.sleep(2)

                    if response and response.status == 200:
                        # Scrape the page
                        city_locations = scrape_directory_page(page)

                        if city_locations:
                            print(f"   Found {len(city_locations)} locations via directory page")

                            # Fetch coordinates from detail pages for locations without coords
                            coords_fetched = 0
                            for loc in city_locations:
                                if not loc.get('latitude') and loc.get('detail_url'):
                                    coords = fetch_location_coordinates(page, loc['detail_url'])
                                    if coords:
                                        loc['latitude'] = coords[0]
                                        loc['longitude'] = coords[1]
                                        coords_fetched += 1
                                    # Small delay between detail page requests
                                    time.sleep(0.2)

                            if coords_fetched > 0:
                                print(f"   Fetched coordinates for {coords_fetched} locations from detail pages")
                            break  # Success, exit retry loop
                        else:
                            print(f"   Directory page loaded but no locations extracted")
                            break  # No retry needed, page just has no data
                    else:
                        print(f"   No direct city page (status: {response.status if response else 'N/A'})")
                        break

                except PlaywrightTimeout:
                    if attempt == 0:
                        print(f"   Timeout, retrying...")
                        time.sleep(2)
                    else:
                        print(f"   Timeout on directory page (after retry)")
                except Exception as e:
                    print(f"   Error: {e}")
                    break

            # Store results for this city
            for loc in city_locations:
                loc['search_city'] = city

            results[city] = city_locations
            all_locations.extend(city_locations)

            time.sleep(0.5)  # Small delay between cities

        browser.close()

    print()
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()

    total = 0
    for city, locs in results.items():
        print(f"{city}: {len(locs)} locations")
        total += len(locs)

        # Show first 5 locations with details
        for i, loc in enumerate(locs[:5]):
            name = loc.get('name', 'Unknown')
            street = loc.get('street', '')
            postcode = loc.get('postcode', '')
            lat = loc.get('latitude', 'N/A')
            lng = loc.get('longitude', 'N/A')
            dropoff = 'Yes' if loc.get('accepts_dropoff', True) else 'No'

            coord_str = f"({lat}, {lng})" if lat != 'N/A' else "(no coords)"
            print(f"   {i+1}. {name}")
            print(f"      Address: {street}, {postcode}")
            print(f"      Coords: {coord_str}")
            print(f"      Drop-off: {dropoff}")

        if len(locs) > 5:
            print(f"   ... and {len(locs) - 5} more")
        print()

    print(f"Total locations found: {total}")

    # Count those with coordinates
    with_coords = sum(1 for loc in all_locations if loc.get('latitude'))
    print(f"Locations with coordinates: {with_coords}")

    return results


def save_poc_results(results: Dict[str, List[Dict]]):
    """Save POC results to JSON file."""
    output = {
        "metadata": {
            "type": "proof_of_concept",
            "method": "playwright-scraping",
            "source": "https://local.fedex.com/nl-nl",
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
        "results_by_city": results,
        "all_locations": [loc for locs in results.values() for loc in locs]
    }

    output_path = Path(__file__).parent.parent / "data" / "fedex_poc_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print()
    print(f"Results saved to: {output_path}")


def main():
    print()
    print(f"FedEx Location Fetch - Proof of Concept")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test cities as specified
    test_cities = ["Rotterdam", "Elburg", "Amsterdam"]

    results = fetch_fedex_locations_poc(test_cities)

    if any(results.values()):
        save_poc_results(results)
    else:
        print("\nNo locations found - may need to adjust scraping approach")

    print()
    print("=" * 80)
    print("POC COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
