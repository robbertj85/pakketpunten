# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a dual-component system for collecting, analyzing, and visualizing parcel point (pakketpunten) locations across Dutch municipalities:
- **Python backend**: Data collection via APIs and web scraping (DHL, PostNL, DPD, Amazon, VintedGo, De Buren) with geospatial analysis using GeoPandas
- **Next.js webapp**: Interactive map visualization with Leaflet, featuring filters, statistics, and performance optimizations for large datasets

## Common Development Commands

### Python Backend

```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate data for a single municipality
python main.py --gemeente Amsterdam --filename test --format geojson

# Batch generate all municipalities (for webapp)
cd scripts
python batch_generate.py

# Fetch complete DHL grid data (nationwide) - Run once, then cached
python scripts/dhl_grid_fetch.py

# Fetch complete DPD data (nationwide) - Run once, then cached
python scripts/dpd_fetch_all.py

# Batch generate all municipalities (automatically uses cached DHL/DPD data if available)
cd scripts
python batch_generate.py

# Create national overview
python scripts/create_national_overview.py
```

### Next.js Webapp

```bash
cd webapp

# Install dependencies
npm install

# Development server (http://localhost:3000)
npm run dev

# Production build
npm run build
npm start

# Lint
npm run lint
```

## Architecture

### Python Backend Architecture

**Core Pipeline** (`main.py`):
1. `api_client.py` → Fetch raw data from multiple carrier APIs
2. `geo_analysis.py` → Generate buffer zones (300m/400m) in RD projection (EPSG:28992)
3. `visualize.py` → Legacy Folium map generation (static HTML)
4. `utils.py` → Coordinate transformation, geocoding, data normalization

**Key Patterns**:
- **CRS transformations**: Always WGS84 (EPSG:4326) for API/web → RD New (EPSG:28992) for metric calculations → back to WGS84 for output
- **API-specific search geometries**: DHL uses circle (lat/lon/radius), PostNL uses bbox, VintedGo uses bounds
- **Mock data**: `bezettingsgraad` (occupancy) is randomly generated for demonstration only
- **Grid-based fetching**: For nationwide coverage (DHL/DPD), use grid-based scripts instead of per-municipality calls to avoid API limits

**Data Flow**:
```
API calls (per municipality) → GeoDataFrame → CRS transform → Buffer analysis →
GeoJSON export → webapp/public/data/{slug}.geojson
```

### Next.js Webapp Architecture

**Component Hierarchy** (`app/page.tsx`):
```
Home (page.tsx)
├── MunicipalitySelector → Dropdown with autocomplete
├── FilterPanel → Provider filters, buffer toggles, occupancy slider
├── StatsPanel → Dynamic counts per provider
└── Map → Leaflet with adaptive rendering
```

**Map Component Performance Strategy** (`components/Map.tsx`):

The Map component implements **adaptive rendering** for handling 1,000-50,000+ markers:

1. **Canvas Rendering**: Uses Leaflet's `preferCanvas` when `useSimpleMarkers` is enabled (10x faster for large datasets)
2. **Simple vs Detailed Markers**:
   - Simple mode: Colored `CircleMarker` elements (4-6px radius based on zoom)
   - Detailed mode: Custom `divIcon` with carrier logos loaded from Clearbit API
3. **Automatic Spiderfy**: At zoom ≥15, markers with identical coordinates are spread in a circular pattern with blue connecting lines
4. **Provider Render Priority**: Randomized hourly using seeded RNG to ensure fair visibility (prevents one carrier from always being on top)
5. **Dynamic Icon Sizing**: Marker size scales with zoom level (34px → 42px → 48px) for better clickability

**State Management**: React hooks with `useMemo` for expensive computations (filtering, grouping, spreading overlapping markers)

**Data Loading**:
- `/municipalities.json` → List of available municipalities
- `/data/{slug}.geojson` → Complete municipality data (pakketpunten + buffer unions)

### TypeScript Types (`webapp/types/pakketpunten.ts`)

All GeoJSON features follow this structure:
- **Pakketpunt features**: `type: 'pakketpunt'` with properties: `locatieNaam`, `straatNaam`, `straatNr`, `vervoerder`, `puntType`, `bezettingsgraad`, `latitude`, `longitude`
- **Buffer features**: `type: 'buffer_union_300m' | 'buffer_union_400m'` with `buffer_m` property

## Coordinate Reference Systems (CRS)

**Critical**: This project uses two CRS throughout:
- **WGS84 (EPSG:4326)**: All API inputs/outputs, GeoJSON files, web maps (lat/lon in degrees)
- **RD New (EPSG:28992)**: Dutch grid system for metric calculations (buffer zones in meters)

Always transform to RD New before distance/buffer operations, then back to WGS84 for output.

## Cache-Based Data Loading

The system automatically uses cached data when available:

### DHL Grid Data (`data/dhl_all_locations.json`)
- Generated once using `scripts/dhl_grid_fetch.py` (grid-based approach, ~3,800+ locations)
- `api_client.get_data_dhl()` automatically loads from cache if file exists
- Falls back to 50-result API call if cache not found
- Cache filtered by municipality bounding box (fast pre-filter)
- Final polygon filtering in `get_data_pakketpunten()` ensures accurate boundaries

### DPD Complete Data (`data/dpd_all_locations.json`)
- Generated once using `scripts/dpd_fetch_all.py` (~1,900 locations)
- `api_client.get_data_dpd()` automatically loads from cache if file exists
- Falls back to 100-result API call if cache not found
- Same bbox + polygon filtering approach as DHL

### Workflow
1. **First time**: Run `dhl_grid_fetch.py` and `dpd_fetch_all.py` to create caches
2. **Regular updates**: Run `batch_generate.py` - automatically uses cached data
3. **Regenerate caches**: Re-run grid fetch scripts when you want updated data

## API Integration Notes

### Rate Limiting
- **Nominatim (geocoding)**: 1 request/second enforced in `utils.py`
- **Batch processing**: `batch_generate.py` uses 2-second delays between municipalities
- **DHL API**: Limit 50 results per call (use grid approach for nationwide coverage)
- **PostNL API**: Requires bounding box (not center/radius)

### Data Sources
- **DHL**: `api-gw.dhlparcel.nl` - Circle search (lat/lon/radius)
- **PostNL**: `productprijslokatie.postnl.nl` - Bounding box search
- **DPD**: `pickup.dpd.cz` - Address-based search (cached nationwide, ~1900 locations)
- **Amazon**: OpenStreetMap Overpass API - Community-maintained data
- **VintedGo**: `vintedgo.com` - Web scraping with bounds parameter
- **De Buren**: `mijnburen.deburen.nl` - Web scraping with JS array extraction

All API calls use `requests.Session()` with proxy bypass for specific domains (handled in `utils.make_session()`).

## Output Formats

### GeoJSON Structure
```json
{
  "type": "FeatureCollection",
  "metadata": {
    "gemeente": "Amsterdam",
    "slug": "amsterdam",
    "generated_at": "2025-01-15T10:30:00Z",
    "total_points": 156,
    "providers": ["DHL", "PostNL", "VintedGo", "DeBuren"],
    "bounds": [4.72, 52.28, 5.07, 52.43]
  },
  "features": [
    // Pakketpunt features (type: "pakketpunt")
    // Buffer union features (type: "buffer_union_300m", "buffer_union_400m")
  ]
}
```

### File Organization
- **Python outputs**: `output/` directory (legacy)
- **Webapp data**: `webapp/public/data/` directory
  - `{slug}.geojson` → Per-municipality data
  - `municipalities.json` → Municipality index
  - `summary.json` → Batch processing results

## Performance Considerations

### Python
- **Geocoding cache**: `utils.py` caches Nominatim results to disk
- **Grid-based fetching**: For DHL/DPD, fetch once nationwide instead of per-municipality
- **Batch processing**: Rate-limited to respect API usage policies

### Next.js
- **Dynamic imports**: Map component uses `next/dynamic` with `ssr: false` to avoid Leaflet SSR issues
- **Memoization**: Expensive operations (filtering, spreading markers) are memoized
- **Canvas rendering**: Enabled for 3000+ markers (50ms vs 2000ms render time)
- **Simple markers**: Automatically enabled for "Nederland" national view
- **GeoJSON size**: Amsterdam ≈100 KB, national overview ≈5 MB

## Data Attribution Requirements

When using generated data, include:
```
Data bronnen:
- DHL Parcel Netherlands (https://www.dhl.nl)
- PostNL (https://www.postnl.nl)
- VintedGo / Mondial Relay (https://vintedgo.com)
- De Buren (https://deburen.nl)
- Gemeente grenzen © OpenStreetMap contributors
- Bedrijfslogo's © respectieve merkhouders

Bezettingsgraad data is willekeurig gegenereerd voor demonstratie (niet echt)
```

## Known Limitations

- **Bezettingsgraad (occupancy)**: Mock data only - not real capacity information
- **DPD via `api_client.get_data_dpd()`**: Limited to 100 results (use `dpd_fetch_all.py` + integration script for complete coverage)
- **Amazon via OSM**: OpenStreetMap data is community-maintained and may have gaps
- **De Buren**: Web scraping - may break if website structure changes
- **Logo loading**: Relies on Clearbit API availability (falls back to initials)
- **Nederland view**: Very large dataset (50,000+ markers) - simple markers recommended

## Provider Coverage Summary

| Provider | Method | Auth Required | Coverage | Cache-Based | Grid Fetch |
|----------|--------|---------------|----------|-------------|------------|
| DHL | Public REST API | No | ~2000+ | Optional | Yes |
| PostNL | Public Widget API | No | High | No | No |
| DPD | Public REST API | No | ~1900 | Yes (recommended) | No |
| Amazon | OSM Overpass API | No | Low (community data) | Optional | No |
| VintedGo | Web Scraping | No | Medium | No | No |
| De Buren | Web Scraping | No | Low | No | No |

**Notes**:
- **Grid Fetch**: Providers using grid-based approach for complete nationwide coverage
- **Cache-Based**: Recommended to run fetch once and cache results for faster municipality generation
