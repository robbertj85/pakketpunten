# UPS API Integration Research Report

**Date:** 2025-10-29
**Status:** INTEGRATION NOT FEASIBLE - Authentication Required
**Recommendation:** DO NOT IMPLEMENT

---

## Executive Summary

After thorough research and testing, I determined that **UPS does not provide a publicly accessible API for parcel point location data** that meets the project's requirements. All UPS APIs require OAuth 2.0 authentication, which violates the core project constraint of authentication-free integrations.

**Verdict:** STOP - Do not implement UPS integration at this time.

---

## Research Findings

### 1. Official UPS Locator API

**API Documentation:** https://github.com/UPS-API/api-documentation/blob/main/Locator.yaml

**Endpoint Structure:**
- Base URL (Production): `https://onlinetools.ups.com/api`
- Endpoint: `/locations/{version}/search/availabilities/{reqOption}`
- Current Version: v3

**Authentication Requirements:**
- **OAuth 2.0 with Client Credentials flow** (REQUIRED)
- Client ID and Client Secret must be obtained from UPS Developer Portal
- Token endpoint: `https://wwwcie.ups.com/security/v1/oauth/token`
- No public/unauthenticated access available

**Rate Limiting:**
- Not publicly documented (requires developer account)

**Request Parameters:**
- Path: version, reqOption (location type indicator 1-64)
- Header: transId, transactionSrc
- Query: Locale (default: en_US)

**Response Structure:**
```json
{
  "Response": {
    "ResponseStatus": "...",
    "Alert": []
  },
  "Geocode": {
    "Latitude": "...",
    "Longitude": "..."
  },
  "SearchResults": {
    "LocationList": []
  }
}
```

**Coverage:** Netherlands supported (locale: en_NL)

**Rejection Reason:** Authentication required - violates project requirements.

---

### 2. OpenStreetMap Data

**Test Query Executed:**
```python
# Overpass API query for UPS locations in Netherlands
[out:json][timeout:30];
area["ISO3166-1"="NL"][admin_level=2]->.searchArea;
(
  node["amenity"="parcel_locker"]["operator"~"UPS",i](area.searchArea);
  node["amenity"="parcel_locker"]["brand"~"UPS",i](area.searchArea);
  node["name"~"UPS",i]["amenity"="parcel_locker"](area.searchArea);
);
out body;
```

**Results:** 0 locations found

**Analysis:**
- OpenStreetMap does not have UPS Access Point data coverage in the Netherlands
- UPS locations are not community-mapped like Amazon Hub locations
- OSM tagging structure supports parcel lockers (amenity=parcel_locker, operator=UPS) but data is missing
- Similar to Amazon integration, this could theoretically work IF the community mapped UPS locations

**Rejection Reason:** No data available in OpenStreetMap.

---

### 3. Web Scraping Investigation

**Official UPS Locator Website:**
- URL: https://www.ups.com/dropoff/?loc=en_NL
- URL: https://www.ups.com/mobile/locator?loc=en_nl

**Findings:**
- Connection attempts to UPS website timed out (ECONNRESET error)
- UPS implements strong anti-bot protections (Akamai)
- Website likely uses dynamic JavaScript rendering (React/Next.js based on search patterns)
- No publicly documented JSON endpoints found

**Selenium/Browser Automation:**
- Research indicates UPS uses Akamai security measures
- Scraping would require:
  - Headless browser (Selenium/Playwright)
  - User-Agent spoofing
  - Cookie/session management
  - Handling dynamic content loading
  - Potential CAPTCHA solving

**Rejection Reasons:**
1. High complexity and maintenance burden
2. Unreliable due to anti-scraping measures
3. Violates UPS Terms of Service
4. Would break frequently when UPS updates website
5. Slow performance (browser automation required)

---

### 4. Third-Party Aggregators

**Services Found:**
- Sendcloud UPS API (requires authentication with Sendcloud)
- Easyship Locations API (requires authentication with Easyship)
- RocketShipIt (commercial service, requires API key)

**Rejection Reason:** All require authentication with third-party services.

---

## Authentication Migration (2024)

**Important Update:**
- UPS deprecated access key authentication on **June 3, 2024**
- All APIs now **require OAuth 2.0** (as of August 5, 2024)
- No legacy authentication methods remain
- No public/free tier available

---

## Alternative Approaches Considered

### Option 1: Official UPS Developer Account
**Pros:**
- Official, reliable data source
- Complete coverage (15,000+ locations in Europe)
- Real-time accuracy
- Terms of Service compliant

**Cons:**
- Requires OAuth 2.0 authentication (violates project requirements)
- Requires developer account registration
- May have rate limits or usage costs
- Adds dependency on external credentials

**Verdict:** Not feasible for this project's authentication-free requirement.

---

### Option 2: Community OSM Mapping Campaign
**Pros:**
- Would be authentication-free once data exists
- Follows existing Amazon integration pattern
- Community-driven, open data

**Cons:**
- No UPS data currently exists in OSM
- Would require massive community effort to map 15,000+ locations
- Data freshness/accuracy concerns
- Not practical for immediate implementation

**Verdict:** Not viable in short-term; could revisit if OSM community maps UPS locations.

---

### Option 3: Selenium Web Scraping
**Pros:**
- No API authentication required
- Technically possible to extract data from website

**Cons:**
- Violates UPS Terms of Service
- Extremely fragile (breaks when website changes)
- High complexity (Akamai protection, JavaScript rendering)
- Slow performance (requires browser automation)
- Maintenance nightmare
- Potential legal issues

**Verdict:** Not recommended - violates project quality standards and ToS.

---

## Comparison with Existing Integrations

| Provider | Method | Auth Required | Coverage (NL) | Implementation |
|----------|--------|---------------|---------------|----------------|
| DHL | Public REST API | No | ~2,000+ | Implemented |
| PostNL | Public Widget API | No | High | Implemented |
| DPD | Public REST API | No | ~1,900 | Implemented |
| Amazon | OSM Overpass API | No | Low (community) | Implemented |
| VintedGo | Web Scraping | No | Medium | Implemented |
| De Buren | Web Scraping | No | Low | Implemented |
| **UPS** | **OAuth 2.0 API** | **Yes** | **15,000+ (EU)** | **NOT FEASIBLE** |

**Key Difference:** UPS is the only major carrier with mandatory authentication and no public alternative.

---

## Netherlands Market Context

**UPS Presence:**
- 40% increase in Access Point locations in Netherlands over past 2 years (as of 2021)
- Significant market share in Netherlands
- Would be valuable addition to dataset

**Competitive Landscape:**
- DHL, PostNL, DPD all have public APIs
- UPS is outlier in requiring authentication
- Users would benefit from UPS coverage, but technical constraints prevent implementation

---

## Recommendations

### Short-Term (Current Project)
**DO NOT IMPLEMENT UPS INTEGRATION**

Reasons:
1. No authentication-free API available
2. No OpenStreetMap data coverage
3. Web scraping violates ToS and quality standards
4. Does not meet project's core technical requirements

### Long-Term (Future Possibilities)

**Option A: OAuth Integration (Requires Project Scope Change)**
- If project requirements change to allow authenticated APIs
- Implement OAuth 2.0 client credentials flow
- Secure credential storage (environment variables, secrets manager)
- Handle token refresh logic
- Document authentication setup process for users

**Option B: OSM Community Mapping**
- Monitor OpenStreetMap for UPS location mapping efforts
- Consider organizing community mapping campaign
- Would align with existing Amazon integration pattern
- Could revisit integration if data becomes available

**Option C: User-Provided API Keys**
- Allow users to optionally provide their own UPS OAuth credentials
- Document registration process for UPS Developer account
- Implement credential management in config file
- Skip UPS if credentials not provided

**Recommended:** Option C (user-provided credentials) if demand exists

---

## Technical Implementation Notes

If project requirements change to support authentication, here's the implementation outline:

### get_data_ups() Function Structure
```python
def get_data_ups(lat, lon, radius, gemeente=None):
    """
    Fetch UPS Access Point locations (REQUIRES AUTHENTICATION).

    Parameters
    ----------
    lat : float
        Latitude for search center
    lon : float
        Longitude for search center
    radius : int
        Search radius in meters (convert to km for API)
    gemeente : str, optional
        Municipality name for filtering

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame with UPS Access Point locations

    Notes
    -----
    Requires UPS OAuth 2.0 credentials (CLIENT_ID, CLIENT_SECRET).
    Set environment variables:
        UPS_CLIENT_ID
        UPS_CLIENT_SECRET
    """
    import os
    from datetime import datetime, timedelta

    # Check for credentials
    client_id = os.getenv('UPS_CLIENT_ID')
    client_secret = os.getenv('UPS_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("  ⚠️  UPS: OAuth credentials not configured, skipping")
        return gpd.GeoDataFrame(
            columns=['locatieNaam', 'straatNaam', 'straatNr',
                     'latitude', 'longitude', 'puntType', 'vervoerder'],
            crs='EPSG:4326'
        )

    # OAuth token management (with caching)
    token = _get_ups_oauth_token(client_id, client_secret)

    # API call
    session = make_session()
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    # Convert radius to km (API uses km)
    radius_km = radius / 1000

    # API endpoint
    url = "https://onlinetools.ups.com/api/locations/v3/search/availabilities/64"

    # Request body (UPS uses POST with JSON body)
    payload = {
        "OriginAddress": {
            "Latitude": str(lat),
            "Longitude": str(lon)
        },
        "MaximumListSize": "50",
        "SearchRadius": str(int(radius_km)),
        "SearchOption": "01",  # Access Point locations
        "Locale": "en_NL"
    }

    response = session.post(
        url,
        headers=headers,
        json=payload,
        timeout=30
    )
    response.raise_for_status()

    data = response.json()

    # Parse response
    locations = []
    for loc in data.get('SearchResults', {}).get('LocationList', []):
        address = loc.get('Address', {})
        geocode = loc.get('Geocode', {})

        locations.append({
            'locatieNaam': loc.get('LocationName', ''),
            'straatNaam': address.get('AddressLine', [''])[0],
            'straatNr': '',  # UPS doesn't separate number
            'latitude': float(geocode.get('Latitude', 0)),
            'longitude': float(geocode.get('Longitude', 0)),
            'puntType': 'Access Point',
            'vervoerder': 'UPS',
        })

    df = pd.DataFrame(locations)
    gdf = df_to_gdf(df, "UPS")
    return gdf


def _get_ups_oauth_token(client_id, client_secret):
    """Get OAuth token from UPS (with 1-hour caching)."""
    import base64
    from pathlib import Path
    import json

    # Check cache
    cache_file = Path("data/ups_token_cache.json")
    if cache_file.exists():
        with open(cache_file) as f:
            cache = json.load(f)

        expiry = datetime.fromisoformat(cache['expires_at'])
        if datetime.now() < expiry:
            return cache['access_token']

    # Request new token
    token_url = "https://onlinetools.ups.com/security/v1/oauth/token"

    # Basic auth header
    auth_str = f"{client_id}:{client_secret}"
    auth_bytes = base64.b64encode(auth_str.encode()).decode()

    headers = {
        'Authorization': f'Basic {auth_bytes}',
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    data = {'grant_type': 'client_credentials'}

    session = make_session()
    response = session.post(token_url, headers=headers, data=data)
    response.raise_for_status()

    token_data = response.json()
    access_token = token_data['access_token']
    expires_in = token_data.get('expires_in', 3600)  # default 1 hour

    # Cache token
    cache = {
        'access_token': access_token,
        'expires_at': (datetime.now() + timedelta(seconds=expires_in - 60)).isoformat()
    }

    cache_file.parent.mkdir(exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(cache, f)

    return access_token
```

### Integration into get_data_pakketpunten()
```python
# Add to api_client.py after line 546
# UPS (requires authentication - skip if credentials not provided)
try:
    gdf_ups = get_data_ups(lat, lon, radius, gemeente=gemeente)
    if len(gdf_ups) > 0:  # Only add if not empty
        gdfs_to_concat.append(gdf_ups)
        carrier_status['UPS'] = {'success': True, 'count': len(gdf_ups), 'error': None}
except Exception as e:
    print(f"  ⚠️  UPS fetch failed: {e}")
    carrier_status['UPS'] = {'success': False, 'count': 0, 'error': str(e)}
```

### Environment Setup Documentation
Add to README.md:
```markdown
### Optional: UPS Integration (Requires Authentication)

UPS requires OAuth 2.0 authentication. To enable UPS support:

1. Register for UPS Developer account: https://developer.ups.com/
2. Create an application and enable "Locator" API
3. Copy your Client ID and Client Secret
4. Set environment variables:
   ```bash
   export UPS_CLIENT_ID="your_client_id"
   export UPS_CLIENT_SECRET="your_client_secret"
   ```
5. Run data collection normally - UPS will be included automatically

If credentials are not provided, UPS will be skipped (no error).
```

---

## Testing Performed

1. **Overpass API Query:** Tested OSM for UPS locations - 0 results
2. **UPS Website Access:** Connection attempts failed (ECONNRESET)
3. **API Documentation Review:** Confirmed OAuth 2.0 requirement from official GitHub repo
4. **Third-Party Services:** All require separate authentication

---

## Conclusion

**UPS integration is NOT FEASIBLE under current project requirements** due to mandatory OAuth 2.0 authentication. The project's core principle of authentication-free data collection cannot be met with UPS APIs.

**Recommended Action:** Document UPS as a known limitation and revisit if:
1. Project scope expands to support authenticated APIs (with user-provided credentials)
2. OpenStreetMap community maps UPS locations
3. UPS releases a public, authentication-free endpoint (unlikely)

**Current Integration Status:** NOT IMPLEMENTED - Authentication barrier

---

## Additional Resources

- UPS Developer Portal: https://developer.ups.com/
- UPS API Documentation: https://github.com/UPS-API/api-documentation
- UPS Netherlands Locator: https://www.ups.com/dropoff/?loc=en_NL
- OAuth 2.0 Migration Announcement: August 5, 2024

---

**Report Status:** COMPLETE
**Next Steps:** None - integration blocked by technical constraints
