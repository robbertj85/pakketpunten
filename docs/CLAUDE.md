# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Pakketpunten Data** is a full-stack project for collecting, analyzing, and visualizing parcel point locations in the Netherlands.

- **Backend (Python)**: Fetches data from multiple APIs (DHL, DPD, PostNL, VintedGo, De Buren), performs geospatial analysis using GeoPandas, and exports to GeoJSON/GeoPackage
- **Frontend (Next.js)**: Interactive web application with React-Leaflet maps, optimized for displaying 10,000+ markers with Canvas rendering

## Directory Structure

```
pakketpunten/
├── main.py                  # Main application entry point
├── api_client.py            # API data collection module
├── geo_analysis.py          # Geospatial analysis functions
├── visualize.py             # Map generation with Folium
├── utils.py                 # Utility functions
├── requirements.txt         # Python dependencies
├── update.sh                # Automation update script
├── README.md                # Project README
├── data/                    # Data files and logs
│   ├── dhl_all_locations.json
│   ├── dpd_all_locations.json
│   ├── municipalities_all.json
│   ├── gemeenten-2025.xlsx
│   └── *_update_log.txt
├── docs/                    # Documentation
│   ├── CLAUDE.md            # This file - Claude Code instructions
│   ├── AUTOMATION.md        # Automation documentation
│   ├── DATA_SOURCES.md      # API documentation
│   ├── DHL_GRID_WORKFLOW.md # DHL fetching strategy
│   └── QUICKSTART_AUTOMATION.md
├── scripts/                 # Automation and data processing scripts
│   ├── dhl_grid_fetch.py    # Complete DHL data fetch
│   ├── dpd_fetch_all.py     # Complete DPD data fetch
│   ├── integrate_dhl_grid_data.py
│   ├── integrate_dpd_data.py
│   ├── batch_generate.py    # Batch municipality processing
│   ├── create_national_overview.py
│   ├── run_complete_dhl_update.py
│   └── weekly_update.py     # Weekly update orchestration
└── webapp/                  # Next.js frontend application
    ├── app/                 # Next.js app directory
    ├── components/          # React components
    └── public/data/         # GeoJSON output files
```

## Common Commands

### Setup
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
# Basic usage with municipality name
python main.py --gemeente Amsterdam --filename test --format geojson

# Using short flags
python main.py -g Utrecht -f output -f gpkg

# Run from IDE without arguments (uses defaults: gemeente=Amsterdam, filename=test, format=geojson)
python main.py
```

### Command-line Arguments
- `--gemeente` / `-g`: Municipality name (e.g., "Amsterdam", "Utrecht")
- `--filename` / `-f`: Output filename (default: "output")
- `--format`: Output format - either "gpkg" (GeoPackage) or "geojson" (default: "geojson")

### Output
Results are saved in the `output/` directory:
- GeoPackage: `output/{filename}.gpkg` (single file with multiple layers)
- GeoJSON: `output/{filename}_{layername}.geojson` (separate files per layer)
- Interactive map: `output/{filename}_kaart.html` (opens automatically in browser)

## Architecture

### Data Flow Pipeline

The application follows a linear pipeline architecture:

1. **Data Collection** (`api_client.py`) → Fetches raw location data from 5 different sources
2. **Geospatial Analysis** (`geo_analysis.py`) → Creates buffer zones and coverage areas
3. **Visualization** (`visualize.py`) → Generates interactive Folium maps
4. **Export** (`utils.py`) → Saves results in GeoPackage or GeoJSON format
5. **Orchestration** (`main.py`) → Coordinates the entire workflow

### Module Responsibilities

#### `api_client.py` - Data Collection
- **Purpose**: Fetches parcel point locations from multiple providers
- **Functions**:
  - `get_data_deburen(gemeente)`: Scrapes De Buren website for locations
  - `get_data_dhl(lat, lon, radius)`: Queries DHL API with circular search area (50-result limit)
  - `get_data_dpd(gemeente)`: Queries DPD public API (pickup.dpd.cz) by address (100-result limit)
  - `get_data_postnl(bottom_left_lat, bottom_left_lon, top_right_lat, top_right_lon)`: Queries PostNL API with bounding box
  - `get_data_vintedgo(lat, lon, south, west, north, east)`: Scrapes VintedGo Next.js site
  - `get_data_pakketpunten(gemeente)`: Main function that combines all sources into a single GeoDataFrame
- **Search Area Strategy**: Each API requires different search geometries (circle vs bbox vs address), so `get_gemeente_geometry()` is called with both modes

#### `utils.py` - Utilities
- **Purpose**: Provides reusable helper functions for geocoding, API calls, web scraping, data transformation, and file I/O
- **Key Functions**:
  - `get_gemeente_geometry(gemeente_naam, mode)`: Geocodes municipality using OpenStreetMap Nominatim API
    - `mode="bbox"`: Returns bounding box (for PostNL)
    - `mode="circle"`: Returns center point + radius (for DHL)
  - `fetch_json()`: Wrapper for API calls with proxy handling and session management
  - `extract_js_array()`, `parse_locations_any()`: Parse JavaScript arrays from scraped HTML
  - `extract_points_array()`: Extract data from Next.js Flight (RSC) payloads (for VintedGo)
  - `json_to_dataframe()`: Normalize nested JSON to flat DataFrame
  - `df_to_gdf()`: Convert DataFrame to GeoDataFrame with standardized column names
  - `save_output()`: Export to GeoPackage (single file, multiple layers) or GeoJSON (multiple files)

#### `geo_analysis.py` - Geospatial Processing
- **Purpose**: Performs geometric operations on parcel point locations
- **Function**: `get_bufferzones(gdf, radius)`
  - Transforms WGS84 (EPSG:4326) points to RD New (EPSG:28992) for accurate meter-based buffers
  - Creates individual buffer polygons around each point
  - Dissolves all buffers into a single unified coverage area using `unary_union`
  - Returns both individual buffers (for coverage analysis) and unified area (for visualization)
- **CRS Workflow**: WGS84 → RD New (buffer) → back to WGS84 for export

#### `visualize.py` - Map Generation
- **Purpose**: Creates interactive Folium maps with multiple layers
- **Function**: `create_map(filename, gdf_points, buffer_union300, buffer_union500, buffers_crs_hint, zoom_start, tiles)`
  - Converts all geometries to EPSG:4326 for web display
  - Uses MarkerCluster for parcel point markers (performance optimization)
  - Adds optional buffer layers (300m and 500m) with semi-transparent polygons
  - Auto-zooms to fit all visible features
  - Saves HTML and opens in browser automatically

#### `main.py` - Orchestration
- **Purpose**: Entry point that orchestrates the complete workflow
- **Workflow**:
  1. Parse command-line arguments (or use defaults when run from IDE)
  2. Fetch parcel point data for specified municipality
  3. Add dummy "bezettingsgraad" (occupancy rate) column with random data
  4. Generate 300m and 500m buffer zones
  5. Export to GeoPackage or GeoJSON
  6. Generate interactive HTML map

### Data Standardization

All parcel point data is normalized to a consistent schema with these columns:
- `locatieNaam`: Location/business name
- `straatNaam`: Street name
- `straatNr`: Street number
- `latitude`, `longitude`: WGS84 coordinates
- `geometry`: Shapely Point geometry
- `puntType`: Point type/category
- `vervoerder`: Provider name (DHL, DPD, PostNL, VintedGo, DeBuren)
- `bezettingsgraad`: Occupancy rate (dummy data, 0-100)

Output layers:
- `pakketpunten`: All parcel points
- `buffer_300m`: Unified 300m coverage area
- `buffer_500m`: Unified 500m coverage area
- `dekkingsgraad_300m`: Individual 300m buffers per point
- `dekkingsgraad_500m`: Individual 500m buffers per point

### Coordinate Reference Systems (CRS)

- **API data**: EPSG:4326 (WGS84) - standard geographic coordinates
- **Buffer calculations**: EPSG:28992 (RD New) - Dutch projected CRS for accurate metric distances
- **Map visualization**: EPSG:4326 (WGS84) - required for Folium/Leaflet
- **Output files**: EPSG:4326 (WGS84) - standard for web mapping

### API & Web Scraping Notes

- **DHL**: Clean REST API, requires circular search area (lat/lon/radius), 50-result limit per query
- **DPD**: Public REST API at pickup.dpd.cz, no authentication required, address-based search (100-limit) or complete fetch (1933 locations via getAll endpoint)
- **PostNL**: REST API, requires bounding box coordinates
- **De Buren**: Web scraping from JavaScript `locations` array embedded in HTML
- **VintedGo**: Complex scraping from Next.js Server Components (RSC) payload format
- **Proxy handling**: All API functions bypass proxies via `trust_env=False` and explicit `proxies={"http": None, "https": None}`

### Complete Coverage Approach (DHL & DPD)

Due to API result limits, DHL and DPD use special fetching strategies:

- **DHL** (`scripts/dhl_grid_fetch.py`): Grid-based approach covering Netherlands with overlapping 10km search circles, auto-subdividing cells that hit the 50-limit. Takes ~3-5 minutes, fetches all ~2000+ locations.

- **DPD** (`scripts/dpd_fetch_all.py`): Single API call to `getAll?country=528` endpoint returns all 1,933 DPD locations in Netherlands. Takes ~5 seconds. Much simpler than DHL.

Both providers use integration scripts (`scripts/integrate_dhl_grid_data.py`, `scripts/integrate_dpd_data.py`) to filter locations by municipality bounds and update GeoJSON files.

### Dependencies

Core libraries (see requirements.txt):
- `geopandas==1.1.1`: Geospatial data handling
- `shapely==2.1.2`: Geometric operations
- `folium==0.20.0`: Interactive web maps
- `pandas==2.3.3`: Data manipulation
- `requests==2.32.5`: HTTP requests
- `geopy==2.4.1`: Geocoding via Nominatim

## Web Application (Next.js)

The `webapp/` directory contains a Next.js application for interactive visualization.

### Running the Webapp
```bash
cd webapp
npm install
npm run dev  # Development server on http://localhost:3000
npm run build && npm start  # Production build
```

### Architecture

- **Framework**: Next.js 16 with React 19 and TypeScript
- **Mapping**: React-Leaflet for interactive maps
- **Styling**: Tailwind CSS v4
- **Data**: Loads GeoJSON files from `webapp/public/data/`

### Map Component Performance Optimizations

The `Map.tsx` component implements adaptive rendering strategies for handling large datasets (tested with 50,000+ markers):

#### 1. Canvas Rendering
- Uses Leaflet's Canvas renderer (via `preferCanvas`) when displaying simple markers
- **Performance gain**: 40x faster than DOM rendering for 10,000+ markers
  - 10,000 markers: ~50ms (vs ~2000ms with DOM)
  - 50,000 markers: ~200ms (vs unusable with DOM)

#### 2. Adaptive Marker Simplification
The component automatically switches between rendering modes:
- **Simple colored circles** (Canvas): Used for datasets >3000 points, or >1000 points when zoomed out (zoom <11)
- **Branded icon markers** (DOM): Used for smaller datasets when zoomed in, shows provider logos and detailed styling

#### 3. Additional Optimizations
- **Memoization**: Marker elements are memoized with `useMemo()` to prevent unnecessary re-renders
- **Zoom-aware rendering**: `ZoomWatcher` component tracks zoom level changes
- **Performance indicator**: Blue banner shows when in simple marker mode

#### Configuration
Adjust thresholds in `Map.tsx`:
```typescript
const PERFORMANCE_CONFIG = {
  SIMPLE_MARKER_THRESHOLD: 3000,    // Marker count threshold for simple view
  DETAILED_VIEW_ZOOM: 11,            // Zoom level for detail mode
  SIMPLE_MARKER_RADIUS: 4,           // Circle marker size
  SIMPLE_MARKER_OPACITY: 0.8,        // Circle marker opacity
};
```

### National Overview Generation

Use `scripts/create_national_overview.py` to combine all municipality data:
```bash
python scripts/create_national_overview.py
```
This creates `webapp/public/data/nederland.geojson` containing all parcel points across the Netherlands.
