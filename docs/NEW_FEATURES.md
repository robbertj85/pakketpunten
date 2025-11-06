# New Features - REST API & Address Search

This document describes the two new features added to the Pakketpunten project.

## Feature 1: REST API (OpenAPI 3.x Compatible)

A REST API for retrieving parcel point data by municipality.

### Endpoints

#### Get Municipality Data
```
GET /api/v1/municipality/{identifier}
```

Supports three identifier formats:
- **Municipality name**: `Amsterdam`, `Den Haag` (case-insensitive)
- **URL slug**: `amsterdam`, `den-haag`
- **CBS code**: `GM0363`, `GM0518`

### Examples

```bash
# By name
curl https://your-domain.com/api/v1/municipality/Amsterdam

# By slug
curl https://your-domain.com/api/v1/municipality/amsterdam

# By CBS code
curl https://your-domain.com/api/v1/municipality/GM0363
```

### Response Format

Returns GeoJSON FeatureCollection with:
- **Parcel points**: All parcel point locations with provider information
- **Buffer zones**: 300m and 400m coverage areas
- **Municipality boundaries**: Geographic boundaries

### Headers

Response includes custom headers:
- `X-Municipality-Name`: Official municipality name
- `X-Municipality-Slug`: URL-safe slug
- `X-Municipality-Code`: CBS municipality code
- `X-RateLimit-Limit`: Rate limit (100 req/15min)
- `Cache-Control`: Caching directives (1 hour)
- `Access-Control-Allow-Origin`: CORS enabled (*)

### Rate Limiting

- **Limit**: 100 requests per 15 minutes per IP address
- **Storage**: In-memory (resets on deployment)
- **Upgrade path**: Can be upgraded to Redis for persistent rate limiting

### API Documentation

Interactive API documentation available at:
- **Redocly UI**: `/api/v1/docs`
- **OpenAPI Spec**: `/openapi.yaml`

The documentation is powered by Redocly and follows OpenAPI 3.0.3 specification.

### Error Responses

| Status Code | Description |
|-------------|-------------|
| 200 | Success - Returns GeoJSON data |
| 400 | Bad request - Invalid identifier or restricted municipality |
| 404 | Not found - Municipality doesn't exist |
| 429 | Rate limit exceeded - Too many requests |
| 500 | Internal server error |

### Implementation Details

**Files created/modified**:
- `webapp/app/api/v1/municipality/[identifier]/route.ts` - Main API route
- `webapp/public/openapi.yaml` - OpenAPI specification
- `webapp/app/api/v1/docs/page.tsx` - Redocly documentation page
- `webapp/public/municipalities.json` - Enhanced with CBS codes
- `scripts/merge_cbs_codes.py` - Script to merge CBS codes

**CBS Codes Integration**:
- All 342 municipalities now have CBS codes
- Codes follow format: `GM` + 4 digits (e.g., `GM0363`)
- Source: CBS (Statistics Netherlands) `data/cbs_municipality_areas.json`
- Manual mappings for special cases (Den Haag, Utrecht, etc.)

---

## Feature 2: Address Search with Autocomplete

Search for addresses in the Netherlands and automatically zoom to them on the map.

### How It Works

1. **Type an address**: Start typing any address in the search field
2. **Autocomplete suggestions**: Get real-time suggestions from PDOK API
3. **Select address**: Click on a suggestion
4. **Auto-navigate**: Map automatically:
   - Switches to the correct municipality
   - Zooms to the address location (zoom level 17)
   - Shows nearby parcel points

### Features

- **Real-time autocomplete**: Suggestions appear as you type (300ms debounce)
- **Keyboard navigation**: Use arrow keys to navigate, Enter to select, Escape to close
- **Smart municipality matching**: Automatically finds the municipality in the database
- **Error handling**: Clear error messages when municipality isn't available
- **Loading indicators**: Visual feedback during search and lookup

### User Interface

Located in the header next to the municipality selector:
- Search input with placeholder: "Zoek adres in Nederland..."
- Dropdown with autocomplete results
- Clear button (X) to reset search
- Loading spinner during API calls

### Technical Implementation

**Components created**:
- `webapp/components/AddressSearchInput.tsx` - React component with autocomplete
- `webapp/app/api/geocode/route.ts` - Proxy API for PDOK Locatieserver

**Integration points**:
- `webapp/app/page.tsx` - Main page with address search integration
- `webapp/components/Map.tsx` - Enhanced FitBounds to support target coordinates

**API Service**: PDOK Locatieserver
- **Provider**: Dutch government (Publieke Dienstverlening Op de Kaart)
- **Endpoint**: `https://api.pdok.nl/bzk/locatieserver/search/v3_1/`
- **Features**: Suggest API (autocomplete) + Lookup API (full details)
- **No authentication required**
- **Rate limits**: Generous, suitable for public use

**Why use a proxy?**
- Bypasses Content Security Policy (CSP) restrictions
- Hides API implementation details from client
- Allows server-side rate limiting if needed
- Enables server-side caching (future enhancement)

### Rate Limiting

Address search API:
- **Limit**: 30 requests per minute per IP
- **Applied to**: `/api/geocode` endpoint
- **Storage**: In-memory

### Error Messages

| Error | Message |
|-------|---------|
| No coordinates | "Geen coördinaten beschikbaar voor dit adres" |
| No municipality | "Geen gemeente beschikbaar voor dit adres" |
| Municipality not in database | "Gemeente \"{name}\" niet beschikbaar in de database" |
| Geocoding failed | "Adres zoeken mislukt. Probeer het opnieuw." |
| Lookup failed | "Adres ophalen mislukt. Probeer het opnieuw." |

---

## Testing

### REST API Testing

```bash
# Test with different identifier types
curl http://localhost:3000/api/v1/municipality/Amsterdam | jq '.metadata'
curl http://localhost:3000/api/v1/municipality/amsterdam | jq '.metadata'
curl http://localhost:3000/api/v1/municipality/GM0363 | jq '.metadata'

# Test error handling
curl http://localhost:3000/api/v1/municipality/InvalidCity

# Check response headers
curl -I http://localhost:3000/api/v1/municipality/amsterdam
```

### Address Search Testing

1. Start dev server: `cd webapp && npm run dev`
2. Open browser: `http://localhost:3000`
3. In address search field, type: "Kalverstraat Amsterdam"
4. Select a suggestion from dropdown
5. Verify:
   - Municipality changes to Amsterdam
   - Map zooms to Kalverstraat area
   - Nearby parcel points are visible

### API Documentation Testing

Visit `http://localhost:3000/api/v1/docs` to see the interactive Redocly documentation.

---

## Deployment Notes

### Vercel Deployment

Both features work out-of-the-box on Vercel:
- ✅ API routes deploy as serverless functions
- ✅ Rate limiting works (in-memory, resets on deploy)
- ✅ File system access works (reads from `public/` directory)
- ✅ CORS headers configured
- ✅ No environment variables required

### CSP Configuration

Content Security Policy updated in `next.config.ts`:
- Added `https://cdn.redoc.ly` to `script-src` for Redocly documentation
- Existing CSP allows PDOK API calls (via server-side proxy)

### Future Enhancements

**For REST API**:
- [ ] Upgrade to Redis-based rate limiting (persistent across deployments)
- [ ] Add API authentication for premium features
- [ ] Add response caching with Redis
- [ ] Add API usage analytics
- [ ] Create client SDKs (Python, JavaScript, Go)

**For Address Search**:
- [ ] Add recent searches history (localStorage)
- [ ] Add geolocation support ("Use my location")
- [ ] Add direct coordinate input (lat/lon)
- [ ] Add postal code search
- [ ] Cache frequently searched addresses
- [ ] Add map marker for searched address

---

## Files Modified/Created

### REST API
- ✅ `scripts/merge_cbs_codes.py` - Merge CBS codes into municipalities.json
- ✅ `webapp/public/municipalities.json` - Enhanced with CBS codes
- ✅ `webapp/app/api/v1/municipality/[identifier]/route.ts` - API endpoint
- ✅ `webapp/public/openapi.yaml` - OpenAPI 3.0.3 specification
- ✅ `webapp/app/api/v1/docs/page.tsx` - Redocly documentation page
- ✅ `webapp/next.config.ts` - Updated CSP for Redocly CDN

### Address Search
- ✅ `webapp/app/api/geocode/route.ts` - PDOK proxy API
- ✅ `webapp/components/AddressSearchInput.tsx` - Search component
- ✅ `webapp/app/page.tsx` - Integrated address search
- ✅ `webapp/components/Map.tsx` - Enhanced with target coordinates

---

## Browser Compatibility

- **Modern browsers**: Chrome, Firefox, Safari, Edge (last 2 versions)
- **Mobile**: iOS Safari, Chrome Mobile, Samsung Internet
- **Required**: JavaScript enabled
- **Recommended**: Screen width ≥768px for optimal layout

---

## Performance Considerations

**REST API**:
- Response time: ~20-50ms for cached data
- File size: ~100KB (Amsterdam) to ~5MB (Nederland)
- Rate limit: Prevents abuse, allows reasonable usage
- Caching: 1 hour browser cache + stale-while-revalidate

**Address Search**:
- Debounced input: 300ms delay reduces API calls
- Autocomplete: <500ms response time (PDOK)
- Lookup: <200ms for full address details
- Client-side caching: Previous results stored during session

---

## Support & Feedback

- **GitHub**: https://github.com/robbertj85/pakketpunten
- **Issues**: https://github.com/robbertj85/pakketpunten/issues
- **Documentation**: `/docs/CLAUDE.md`
- **API Docs**: `/api/v1/docs`
