# DHL Cache Restoration Summary

**Date:** October 27, 2025
**Issue:** Missing Rotterdam centrum DHL locations in new data
**Status:** ✅ RESOLVED

## Problem Discovered

The new DHL cache generated today (Oct 27) was missing 17 out of 18 Rotterdam centrum locations:
- Pakketautomaat Rdam Markthal - 116
- DHL - Pakketautomaat RET Rdam CS (Central Station)
- Pakketautomaat Kruisplein
- Intertoys Rotterdam Lijnbaan
- And 14 more key locations

## Root Cause

**The DHL API stopped returning Rotterdam centrum locations** between Oct 26-27.

### Investigation Timeline

1. **Oct 24**: OLD DHL cache created with 15km grid spacing
   - ✅ HAD all centrum locations
   - Total: 3,819 locations

2. **Oct 26**: Nederland file generated
   - ✅ HAD all 18 centrum locations
   - Total DHL: 3,916 locations

3. **Oct 27**: NEW DHL cache generated with 12km grid spacing
   - ❌ MISSING 17/18 centrum locations
   - Total: 4,078 locations
   - **DHL API returned 0 results for Rotterdam centrum queries**

### Evidence

Direct API queries to Rotterdam centrum coordinates returned **0 locations**:
```
Query: (51.92, 4.47) radius=10km → 0 results
Query: (51.92, 4.48) radius=10km → 0 results
Query: (51.924, 4.470) radius=2km → 0 results
```

This confirms the DHL API is currently not serving centrum location data.

## Solution Applied

### Reconstructed DHL Cache from Oct 26 Data

Since the old DHL cache file was overwritten and not in git, we reconstructed it from the Oct 26 Nederland file which contained all the correct data.

**Reconstruction Process:**
1. Extracted Oct 26 Nederland file from git (commit `fbf5ff0`)
2. Filtered all DHL locations from the aggregated data
3. Converted to DHL cache format
4. Saved as `data/dhl_all_locations.json`

**Result:**
- Total locations: 3,871 (down from 4,078 in new cache)
- **Rotterdam centrum: 18 locations ✅**
- Method: `reconstructed-from-nederland-oct26`

### Files Changed

1. **`data/dhl_all_locations.json`** - Modified
   - Reconstructed from Oct 26 Nederland data
   - Contains all 18 centrum locations
   - Size: ~0.7 MB

2. **`webapp/public/data/nederland.geojson`** - Reverted
   - Restored to Oct 26 version (commit `fbf5ff0`)
   - Maintains centrum location data
   - Consistent with reconstructed cache

3. **`DATA_FLOW_DIAGRAM.md`** - New
   - Added documentation of data flow architecture
   - Helps understand how data moves through the system

## Verification

✅ **All checks passed:**

- DHL cache has 3,871 locations (including 18 centrum)
- Nederland file has 3,916 DHL locations (including 18 centrum)
- All key locations present:
  - Pakketautomaat Rdam Markthal - 116
  - DHL - Pakketautomaat RET Rdam CS
  - Pakketautomaat Kruisplein
  - Intertoys Rotterdam Lijnbaan
  - Pakketautomaat Shell Mobility Hub
  - DHL - Pakketautomaat RET Beurs
  - And 12 more centrum locations

## Next Steps

### Immediate
- ✅ Data restored and verified
- ✅ Documentation created
- ⚠️ **DO NOT commit the earlier changes from today** (Overpass API improvements are OK, but not the DHL/Nederland regeneration)

### Future Monitoring

1. **Monitor DHL API**
   - Check if centrum locations return in coming days/weeks
   - This could be temporary maintenance or a data issue

2. **When DHL API Returns to Normal:**
   - Re-run `scripts/dhl_grid_fetch.py` to get fresh data
   - Verify centrum locations are included
   - Then regenerate municipality files

3. **Cache Update Strategy:**
   - Keep backups before regenerating caches
   - Test API with sample queries before full regeneration
   - Consider adding cache validation step

## Technical Notes

### Why the New Cache Had Fewer Centrum Locations

The 12km grid spacing should theoretically provide BETTER coverage than 15km, but the DHL API itself stopped returning the data. Grid points that should have covered Rotterdam centrum:
- (51.9392, 4.3622) - 7.7 km from centrum
- (51.9392, 4.5375) - 5.1 km from centrum

Both were within the 10km search radius but returned 0 centrum locations.

### Data Consistency

The Nederland file acts as a "snapshot" of what the data looked like when municipalities were last generated. Since it aggregates individual municipality files, it should always match the sum of those files. The fact that it had centrum locations while Rotterdam didn't suggests those locations were distributed across municipality boundaries or there was a timing issue with data generation.

## Lessons Learned

1. **Always backup cache files before regeneration**
2. **Test API availability before running expensive grid fetches**
3. **Keep git history of aggregated files** (Nederland) as they can serve as recovery points
4. **Document data flow** to understand dependencies
5. **External APIs can be unreliable** - need fallback strategies

---

**Restored by:** Claude Code
**Date:** 2025-10-27
**Commit reference:** fbf5ff0 (Nederland source)
