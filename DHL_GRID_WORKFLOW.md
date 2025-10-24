# DHL Grid-Based Complete Coverage Workflow

## Problem

The DHL API has a hard limit of 50 results per request, which means:
- Large municipalities (Amsterdam, Rotterdam, Utrecht) are incomplete
- Current data shows exactly 15 DHL locations per municipality (old default limit)
- Official DHL website shows ~6,200 locations, but we only capture ~4,500

## Solution: Grid-Based Fetching

Divide the Netherlands into a grid of overlapping search circles to capture all locations.

## How It Works

### 1. Grid Strategy

```
Grid Configuration:
- Search radius: 10km per circle
- Grid spacing: 15km between points (ensures overlap)
- Coverage: Full Netherlands (50.75°N to 53.55°N)
- Adaptive subdivision: Cells hitting 50-limit are split into 4 smaller cells
```

### 2. Deduplication

Locations appearing in multiple overlapping circles are deduplicated using:
- Latitude (rounded to 5 decimals ≈ 1m precision)
- Longitude (rounded to 5 decimals)
- Location name
- Location ID

### 3. Expected Results

Based on DHL's official count of ~6,200 locations:
- Initial grid: ~50-80 cells
- After subdivision: ~100-200 cells
- Total API calls: ~150-250
- Estimated runtime: 2-5 minutes (with 0.5s delay between requests)

## Workflow

### Step 1: Fetch Complete DHL Dataset

```bash
cd /Users/robbertjanssen/Documents/dev/pakketpunten
source venv/bin/activate
python dhl_grid_fetch.py
```

**Output**: `dhl_all_locations.json`

This file contains all DHL locations in the Netherlands with:
- Exact coordinates
- Location names
- Address information
- Type (parcelShop vs packStation)

**Expected metrics**:
```
✅ Total unique DHL locations: ~6,000-6,500
📡 Total API calls: ~150-250
⚠️  Cells that hit limit: ~20-40 (mostly in cities)
```

### Step 2: Integrate into Municipality Files

```bash
python integrate_dhl_grid_data.py
```

This script:
1. Loads the complete DHL dataset
2. For each municipality, filters locations within bounds
3. Replaces old DHL data with complete dataset
4. Updates metadata (counts, provider list)

**Expected output**:
```
📍 Total DHL locations:
   Before: ~4,500
   After:  ~6,000-6,500
   Change: +1,500-2,000 (+35-45% increase)

Top gainers:
   Amsterdam:     15 → 150+ locations
   Rotterdam:     15 → 100+ locations
   Den Haag:      15 → 80+ locations
   Utrecht:       15 → 70+ locations
```

### Step 3: Regenerate National Overview

```bash
python create_national_overview.py
```

This regenerates `webapp/public/data/nederland.geojson` with:
- Complete DHL data from all municipalities
- Deduplication of cross-boundary locations
- Updated statistics

### Step 4: Verify in Data Matrix

Navigate to: `http://localhost:3000/data-export/matrix`

Check that:
- DHL counts are no longer all 15
- Large cities show 50+ locations
- Total DHL count is ~6,000+

## Technical Details

### Grid Cell Calculation

```python
# Initial grid covers Netherlands with 15km spacing
Grid points: ~50-80 cells

# Cells hitting 50-limit are subdivided
Subdivision: 1 cell → 4 cells (radius halved)

# Example: Amsterdam area
Initial cell (10km): 50 locations → HIT LIMIT
Split into 4 cells (5km): 35 + 28 + 31 + 26 = 120 total
```

### API Request Example

```
GET https://api-gw.dhlparcel.nl/parcel-shop-locations/NL/by-geo
    ?latitude=52.3702
    &longitude=4.8952
    &radius=10000
    &limit=50
```

### Deduplication Key

```python
key = (
    round(latitude, 5),   # ~1m precision
    round(longitude, 5),
    location_name,
    location_id
)
```

## Performance Considerations

### Rate Limiting

- Delay: 0.5s between requests
- Total time: ~2-5 minutes for full fetch
- No parallel requests (to avoid rate limiting)

### Memory Usage

- ~6,500 locations × ~2KB each ≈ 13MB in memory
- Final JSON file: ~3-5MB

### API Call Optimization

**Without grid approach** (current):
- 326 municipalities × 1 call = 326 calls
- Result: ~4,500 locations (many municipalities capped at 15 or 50)

**With grid approach**:
- ~150-250 calls total
- Result: ~6,000-6,500 locations (complete dataset)

## Monitoring

### Check Grid Fetch Progress

The script shows real-time progress:
```
[15] Fetching (52.3702, 4.8952) r=10.0km... 50 results (32 new, 412 total unique)
  ⚠️  Hit 50-limit! Subdividing into 4 smaller cells...
[16] Fetching (52.3852, 4.9052) r=5.0km... 35 results (12 new, 424 total unique)
```

### Check Integration Results

The integration script shows per-municipality changes:
```
[1/326] Amsterdam... ✅ 15 → 152 DHL (+137)
[2/326] Rotterdam... ✅ 15 → 108 DHL (+93)
[3/326] Den Haag... ✅ 15 → 87 DHL (+72)
```

## Troubleshooting

### If grid fetch times out

Reduce rate limit delay in `dhl_grid_fetch.py`:
```python
RATE_LIMIT_DELAY = 0.3  # Faster but riskier
```

### If integration fails for a municipality

Check bounds calculation in `utils.py`:
- Municipality might be missing from CBS data
- Bounds might be incorrectly calculated

### If results seem low

1. Check grid spacing - might be too sparse
2. Check if adaptive subdivision is working
3. Verify deduplication isn't too aggressive

## Maintenance

### Regular Updates

Run grid fetch monthly to capture:
- New DHL locations
- Closed locations
- Changed addresses

### Incremental Updates

For specific municipalities only:
```python
# Modify integrate_dhl_grid_data.py
municipalities = [m for m in municipalities if m['name'] in ['Amsterdam', 'Rotterdam']]
```

## Benefits

1. **Completeness**: Capture all ~6,200 DHL locations
2. **Accuracy**: No longer limited by API caps
3. **Scalability**: Can fetch complete dataset in minutes
4. **Maintainability**: Single fetch for all municipalities
5. **Transparency**: Data matrix shows actual counts

## Next Steps

1. Run `python dhl_grid_fetch.py` to get complete dataset
2. Run `python integrate_dhl_grid_data.py` to update municipalities
3. Run `python create_national_overview.py` to regenerate overview
4. Verify results in Data Matrix view
5. Consider scheduling monthly updates
