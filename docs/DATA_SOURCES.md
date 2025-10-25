# 📊 Data Sources & Usage Rights

This document outlines the origins of all data used in the Pakketpunten Nederland project and the terms under which this data may be used.

---

## Table of Contents

- [Overview](#overview)
- [Primary Data Sources](#primary-data-sources)
- [Supplementary Data Sources](#supplementary-data-sources)
- [Mock/Generated Data](#mockgenerated-data)
- [Usage Rights & Legal Considerations](#usage-rights--legal-considerations)
- [Attribution Requirements](#attribution-requirements)
- [Data Update Frequency](#data-update-frequency)

---

## Overview

This project aggregates publicly accessible parcel point location data from multiple carriers operating in the Netherlands. All data is retrieved from public-facing APIs and websites that are accessible without authentication.

**Data Collection Date:** Weekly automated updates (planned)
**Geographic Scope:** Netherlands (all 345 municipalities)
**Coordinate System:** WGS84 (EPSG:4326)

---

## Primary Data Sources

### 1. DHL Parcel Netherlands

**Source:** DHL Parcel Shop Locations API
**Endpoint:** `https://api-gw.dhlparcel.nl/parcel-shop-locations/NL/by-geo`
**Access Method:** Public REST API (no authentication required)
**Data Retrieved:**
- Location name
- Street address and number
- Coordinates (latitude/longitude)
- Location type (e.g., ServicePoint, Parcel Locker)

**Implementation:** `api_client.py:get_data_dhl()`

**Terms of Use:**
- Data is publicly accessible through DHL's customer-facing website
- Used for informational and visualization purposes only
- Not for commercial redistribution
- See: https://www.dhl.nl/en/home.html

**Attribution:** Data source: DHL Parcel Netherlands

---

### 2. PostNL

**Source:** PostNL Location Widget API
**Endpoint:** `https://productprijslokatie.postnl.nl/location-widget/api/locations`
**Access Method:** Public REST API (no authentication required)
**Data Retrieved:**
- Location name
- Street address and number
- Coordinates (latitude/longitude)
- Location type

**Implementation:** `api_client.py:get_data_postnl()`

**Terms of Use:**
- Data is publicly accessible through PostNL's location finder
- Used for informational and visualization purposes only
- Not for commercial redistribution
- See: https://www.postnl.nl/

**Attribution:** Data source: PostNL

---

### 3. VintedGo (Mondial Relay)

**Source:** VintedGo Carrier Locations
**Endpoint:** `https://vintedgo.com/nl/carrier-locations`
**Access Method:** Public web page (HTML parsing)
**Data Retrieved:**
- Location name
- Street address
- Coordinates (latitude/longitude)

**Implementation:** `api_client.py:get_data_vintedgo()`

**Terms of Use:**
- Data extracted from publicly accessible web pages
- Used for informational purposes only
- VintedGo is operated by Mondial Relay
- See: https://vintedgo.com/

**Attribution:** Data source: VintedGo / Mondial Relay

---

### 4. De Buren

**Source:** De Buren Maps Interface
**Endpoint:** `https://mijnburen.deburen.nl/maps`
**Access Method:** Public web page (JavaScript array extraction)
**Data Retrieved:**
- Location name (neighbor's name)
- Street address and number
- Postal code
- City
- Coordinates (latitude/longitude)

**Implementation:** `api_client.py:get_data_deburen()`

**Terms of Use:**
- Data extracted from publicly accessible neighborhood network
- Used for informational purposes only
- Privacy note: Only aggregated location data is stored, not personal information
- See: https://deburen.nl/

**Attribution:** Data source: De Buren

---

### 5. Amazon Hub (Lockers & Counters)

**Source:** OpenStreetMap (via Overpass API)
**Endpoint:** `https://overpass-api.de/api/interpreter`
**Access Method:** Overpass API query for `amenity=parcel_locker` with Amazon branding
**Data Retrieved:**
- Location name (Amazon Hub name/code)
- Street address and number
- Postal code
- City
- Coordinates (latitude/longitude)
- Location type (locker vs counter)
- Opening hours (if available in OSM)

**Implementation:** `api_client.py:get_data_amazon()`

**Data Source Notes:**
- Amazon does **not provide a public API** for querying pickup locations
- Data is sourced from **OpenStreetMap**, a community-maintained open database
- Coverage depends on OSM community contributions and may be incomplete
- Amazon locations are tagged in OSM as `amenity=parcel_locker` with `operator=Amazon` or `brand=Amazon`

**Complete Coverage Strategy:**
- **Script:** `scripts/amazon_fetch_all.py` - Fetches all Amazon locations in Netherlands from OSM
- **Integration:** `scripts/integrate_amazon_data.py` - Filters by municipality and updates GeoJSON files
- **Cache:** Stored in `data/amazon_all_locations.json`
- **Update frequency:** Weekly (OSM data changes as community contributes)

**Terms of Use:**
- OpenStreetMap data is available under the **Open Database License (ODbL)**
- Attribution required: **© OpenStreetMap contributors**
- Data can be used for any purpose with proper attribution
- See: https://www.openstreetmap.org/copyright

**Attribution:** Data source: OpenStreetMap contributors (ODbL license)

**Data Quality Considerations:**
- OSM completeness varies by region and depends on volunteer mappers
- Some Amazon locations may not be mapped in OSM yet
- Data accuracy depends on community updates
- Consider contributing to OSM if you know of unmapped Amazon Hubs: https://www.openstreetmap.org/

**Alternative Data Sources Explored:**
- **Amazon Hub Counter API** (`github.com/amzn/amazon-hub-counter-api-docs`): Partner-only API for stores registering as pickup locations, not for querying locations
- **Amazon.nl location selector** (`/location_selector` endpoint): Returns HTML, not suitable for automated data extraction
- **LockerMap.com**: Third-party aggregator using client-side rendering, no public API available

---

## Supplementary Data Sources

### Municipality Boundaries

**Source:** Dutch Cadastre (Kadaster) - BAG (Basisregistratie Adressen en Gebouwen)
**Access Method:** Via `geopy.geocoders.Nominatim` (OpenStreetMap)
**Data Retrieved:**
- Municipality names
- Geographic boundaries (for bounding box calculations)
- Centroid coordinates

**Implementation:** `utils.py:get_gemeente_geometry()`

**Terms of Use:**
- OpenStreetMap data is available under the Open Database License (ODbL)
- See: https://www.openstreetmap.org/copyright

**Attribution:** Municipality data © OpenStreetMap contributors

---

### Company Logos

**Source:** Clearbit Logo API
**Endpoint:** `https://logo.clearbit.com/{domain}`
**Access Method:** Public CDN (client-side fetching)
**Data Retrieved:**
- Company logos for map markers

**Implementation:** `webapp/components/Map.tsx:PROVIDER_INFO`

**Terms of Use:**
- Clearbit Logo API is free for non-commercial use
- Logos remain property of respective companies
- See: https://clearbit.com/logo

**Attribution:** Company logos © respective trademark owners

---

## Mock/Generated Data

### Occupancy Rates (Bezettingsgraad)

**Source:** Randomly generated
**Purpose:** Demonstration of potential feature
**Implementation:** `main.py` and `batch_generate.py`

```python
# Mock occupancy data generation
gdf_pakketpunten["bezettingsgraad"] = np.random.randint(0, 101, size=len(gdf_pakketpunten))
```

**Important Notes:**
- ⚠️ **NOT REAL DATA** - Occupancy rates are randomly generated for demonstration purposes
- Cannot be used for actual capacity planning or business decisions
- Clearly marked as "(mock)" in the web interface
- Users can toggle visibility via "Show Mock Data" checkbox
- Real occupancy data would require direct API access from carriers (not publicly available)

**Future Work:**
- Replace with real-time API data if/when carriers provide public access
- Potential integration with carrier partner programs

---

### Buffer Zones

**Source:** Calculated using GeoPandas
**Method:** Geometric buffer calculations around parcel points
**Implementation:** `geo_analysis.py:add_buffers_to_gdf()`

**Buffer Types:**
- **300m radius:** Walking distance (~3-4 minutes)
- **500m radius:** Extended walking distance (~6-7 minutes)

**Purpose:**
- Visualize service coverage areas
- Identify underserved regions
- Analyze spatial distribution

---

## Usage Rights & Legal Considerations

### Permitted Uses

✅ **Allowed:**
- Personal research and analysis
- Educational purposes
- Non-commercial visualization
- Open-source development
- Academic research
- Urban planning studies

### Restricted Uses

❌ **Not Allowed:**
- Commercial redistribution of raw data
- Selling or licensing the aggregated dataset
- Using data to compete with source carriers
- Automated high-frequency API requests (rate limiting applies)
- Violating individual carriers' terms of service

### Web Scraping Ethics

This project follows ethical web scraping practices:
- **Rate Limiting:** Requests are throttled to avoid server overload
- **Robots.txt:** Respected where applicable
- **Public Data Only:** No authentication bypass or private data access
- **Caching:** Results are cached to minimize repeated requests
- **User-Agent:** Proper identification in HTTP headers

---

## Attribution Requirements

When using or redistributing this project's outputs, include the following attribution:

```
Data sources:
- Amazon Hub locations © OpenStreetMap contributors (ODbL)
- DHL Parcel Netherlands (https://www.dhl.nl)
- PostNL (https://www.postnl.nl)
- VintedGo / Mondial Relay (https://vintedgo.com)
- De Buren (https://deburen.nl)
- Municipality boundaries © OpenStreetMap contributors
- Company logos © respective trademark owners

Project: Pakketpunten Nederland
Repository: https://github.com/Ida-BirdsEye/pakketpunten
License: MIT
```

### In Web Applications

Add to footer or about section:
```html
<footer>
  <p>Data sources: DHL, PostNL, VintedGo, De Buren</p>
  <p>Municipality data © OpenStreetMap contributors</p>
  <p>Bezettingsgraad data is randomly generated for demonstration (not real)</p>
</footer>
```

**Current Implementation:** `webapp/app/page.tsx:149-160`

---

## Data Update Frequency

### Current Status (POC)
- **Manual updates:** On-demand via `batch_generate.py`
- **Municipalities covered:** 5 (Amsterdam, Rotterdam, Utrecht, Eindhoven, Groningen)

### Planned Production Schedule
- **Automated updates:** Weekly (every Sunday at 02:00 UTC)
- **Municipalities covered:** All 345 Dutch municipalities
- **Update mechanism:** GitHub Actions workflow
- **Change detection:** Git-based versioning

**Expected data freshness:**
- Parcel point locations: Updated weekly
- New locations appear within 1 week of being added by carriers
- Closed locations may take up to 1 week to be removed

---

## Privacy & GDPR Compliance

### Personal Data

This project **does not collect or store personal data**:
- ✅ Location addresses (public business locations)
- ✅ Business names (public information)
- ✅ Geographic coordinates (public)
- ❌ Customer data (not collected)
- ❌ Transaction data (not collected)
- ❌ User tracking (not implemented)

### De Buren Special Note

De Buren data represents neighborhood pickup points at private residences:
- **Data stored:** Street addresses and coordinates only
- **Not stored:** Personal names, contact information
- **Public data:** Only information publicly visible on De Buren maps
- **Aggregated use:** Location data is anonymized in visualizations

---

## Disclaimer

```
This project is provided "as is" without warranty of any kind. The data is
aggregated from public sources and may contain inaccuracies. Location data
should be verified with carriers before making business decisions.

Occupancy data (bezettingsgraad) is randomly generated for demonstration
purposes only and does not reflect actual parcel point capacity or usage.

This project is not affiliated with, endorsed by, or sponsored by any of
the data source companies (DHL, PostNL, VintedGo, De Buren).
```

---

## Contact & Questions

For questions about data usage rights:
1. **Source Data:** Contact the respective carrier directly
2. **Project Code:** Open an issue on GitHub
3. **Legal Concerns:** Contact repository maintainer

**Last Updated:** 2025-01-22
