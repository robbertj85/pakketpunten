# Pakketpunten Data Flow Architecture

## Overview: How Data Moves Through The System

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          STEP 1: CACHE GENERATION                        │
│                     (Run once, then data is cached)                      │
└─────────────────────────────────────────────────────────────────────────┘

    DHL API                          DPD API
    (api-gw.dhlparcel.nl)           (pickup.dpd.cz)
           │                                │
           │ Grid-based fetch               │ Nationwide fetch
           │ 590 grid points                │ Single call
           │ 10km radius each               │
           ▼                                ▼

    scripts/dhl_grid_fetch.py       scripts/dpd_fetch_all.py
           │                                │
           │ Deduplicates                   │ Extracts all locations
           │ Handles 50-limit               │
           │ Subdivides dense areas         │
           ▼                                ▼

    data/dhl_all_locations.json     data/dpd_all_locations.json
    (~4,078 locations)               (~1,900 locations)
    17 MB                            3.8 MB


┌─────────────────────────────────────────────────────────────────────────┐
│                   STEP 2: MUNICIPALITY GENERATION                        │
│              (Runs weekly via GitHub Actions)                            │
└─────────────────────────────────────────────────────────────────────────┘

    scripts/batch_generate.py
           │
           │ For each municipality:
           │   1. Calls api_client.get_data_pakketpunten()
           │   2. Fetches from 5 carriers
           │
           ├──────────────────────────────────────────────────┐
           │                                                  │
           ▼                                                  ▼

    api_client.py                              Carrier-specific functions
           │                                          │
           │                                          ├─→ get_data_deburen()
           │                                          │   └─→ Live web scraping
           │                                          │
           │                                          ├─→ get_data_dhl()
           │                                          │   ├─→ Tries cache first
           │                                          │   │   (data/dhl_all_locations.json)
           │                                          │   └─→ Falls back to API (50-limit)
           │                                          │
           │                                          ├─→ get_data_dpd()
           │                                          │   ├─→ Tries cache first
           │                                          │   │   (data/dpd_all_locations.json)
           │                                          │   └─→ Falls back to API (100-limit)
           │                                          │
           │                                          ├─→ get_data_postnl()
           │                                          │   └─→ Live API call (bbox search)
           │                                          │
           │                                          └─→ get_data_vintedgo()
           │                                              └─→ Live web scraping
           │
           ▼
    Combined GeoDataFrame (all carriers)
           │
           │ CRITICAL FILTERING STEP:
           │
           ├─→ get_gemeente_polygon(gemeente_name)
           │   └─→ Overpass API
           │       └─→ Returns exact municipality boundary
           │
           ├─→ gdf.geometry.within(gemeente_polygon)
           │   └─→ Filters points INSIDE boundary only
           │   └─→ Removes points OUTSIDE boundary
           │
           ▼

    Filtered pakketpunten for municipality
           │
           ├─→ Add mock bezettingsgraad (random 0-100)
           ├─→ Generate 300m buffer zones
           ├─→ Generate 400m buffer zones
           ├─→ Add municipality boundary
           │
           ▼

    webapp/public/data/{slug}.geojson
    (Example: rotterdam.geojson)


┌─────────────────────────────────────────────────────────────────────────┐
│                   STEP 3: NATIONAL OVERVIEW                              │
│              (Aggregates all municipality files)                         │
└─────────────────────────────────────────────────────────────────────────┘

    scripts/create_national_overview.py
           │
           │ For each *.geojson in webapp/public/data/:
           │   - Extract all pakketpunt features
           │   - Extract boundary features
           │   - Aggregate statistics
           │
           ▼

    webapp/public/data/nederland.geojson
    (All pakketpunten from all municipalities combined)


┌─────────────────────────────────────────────────────────────────────────┐
│                          KEY DATA FLOWS                                  │
└─────────────────────────────────────────────────────────────────────────┘

SCENARIO A: Municipality generation WITH cache
─────────────────────────────────────────────

    DHL cache (4,078 points)
         │
         ▼
    Load ALL 4,078 points into memory
         │
         ▼
    Filter by municipality bounding box (fast pre-filter)
         │
         ▼
    Filter by municipality POLYGON (exact boundary)
         │
         ▼
    Rotterdam: ~86 points (only those within exact boundary)


SCENARIO B: Municipality generation WITHOUT cache
──────────────────────────────────────────────────

    DHL API (center of municipality, 10km radius)
         │
         ▼
    Returns 50 points maximum (API LIMIT!)
         │
         ▼
    Filter by municipality POLYGON
         │
         ▼
    Rotterdam: ~50 points (INCOMPLETE - hit API limit!)


┌─────────────────────────────────────────────────────────────────────────┐
│                     CRITICAL FILTERING LOGIC                             │
└─────────────────────────────────────────────────────────────────────────┘

In api_client.py (lines 558-577):

    1. Fetch data from all carriers
    2. Combine into single GeoDataFrame (6,000+ points for Rotterdam area)
    3. Get exact municipality polygon from Overpass API
    4. Filter: gdf[gdf.geometry.within(gemeente_geom)]
       └─→ Only keeps points INSIDE the polygon
       └─→ Removes 6,000+ points OUTSIDE Rotterdam boundary
    5. Result: ~369 points within Rotterdam


┌─────────────────────────────────────────────────────────────────────────┐
│                        POTENTIAL ISSUES                                  │
└─────────────────────────────────────────────────────────────────────────┘

ISSUE 1: DHL Grid Fetch Coverage Gaps
──────────────────────────────────────
- 12km grid spacing with 10km radius
- Should have overlap, but might miss dense urban areas
- Rotterdam centrum at (51.92, 4.47)
- Grid points: (51.9392, 4.3622) and (51.9392, 4.5375)
- Both within 10km, so SHOULD capture centrum

ISSUE 2: API Limit (50 results) in Subdivision
───────────────────────────────────────────────
- When grid cell hits 50-limit, it subdivides
- Subdivided cells might ALSO hit 50-limit
- Could miss points in very dense areas

ISSUE 3: Municipality Boundary Filtering Too Strict
────────────────────────────────────────────────────
- Points just outside boundary get removed
- Rotterdam centrum might be at boundary edge
- Overpass polygon might not match DHL's location data

ISSUE 4: Temporal Data Issue
─────────────────────────────
- DHL cache from Oct 24 (15km grid)
- Nederland file from Oct 26 (has centrum points)
- Rotterdam file from Oct 27 (no centrum points)
- DHL might have temporarily closed/moved locations


┌─────────────────────────────────────────────────────────────────────────┐
│                      DEBUGGING QUESTIONS                                 │
└─────────────────────────────────────────────────────────────────────────┘

Q1: Are the centrum points in the NEW DHL cache?
    Check: data/dhl_all_locations.json
    Search for: Markthal, Rotterdam CS, Kruisplein

Q2: Does the DHL API currently return centrum points?
    Test: Direct API call to (51.92, 4.47) with 5km radius

Q3: Are centrum points filtered out by boundary check?
    Test: Check if centrum coordinates are within Rotterdam polygon

Q4: Are centrum points in neighboring municipality files?
    Check: Schiedam, Capelle aan den IJssel files
