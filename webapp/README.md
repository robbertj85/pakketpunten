# Pakketpunten Web App

Interactive web application for visualizing parcel point locations across Dutch municipalities.

## Features

- 📍 **Interactive Map**: View parcel points on an OpenStreetMap-based interactive map
- 🏘️ **Municipality Selection**: Search and select from 5+ Dutch municipalities
- 🎨 **Provider Filtering**: Filter by DHL, PostNL, VintedGo, and De Buren
- 📊 **Occupancy Filter**: Filter by occupancy rate (bezettingsgraad)
- 🎯 **Coverage Zones**: Toggle 300m and 500m buffer zones
- 📈 **Real-time Statistics**: See totals, averages, and provider breakdowns

## Tech Stack

- **Framework**: Next.js 16 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Maps**: React-Leaflet + OpenStreetMap
- **Data**: Static GeoJSON files (pre-generated via GitHub Actions)

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

The app will be available at [http://localhost:3000](http://localhost:3000)

## Data Updates

Data is automatically updated daily at 02:00 UTC via GitHub Actions. The workflow:

1. Runs Python scripts to fetch fresh data from all provider APIs
2. Generates GeoJSON files for each municipality
3. Commits updated files to the repository
4. Vercel automatically redeploys with fresh data

## Project Structure

```
webapp/
├── app/
│   ├── page.tsx              # Main application page
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Global styles + Leaflet CSS
├── components/
│   ├── Map.tsx               # Interactive map component
│   ├── MunicipalitySelector.tsx  # Municipality dropdown
│   ├── FilterPanel.tsx       # Filter controls
│   └── StatsPanel.tsx        # Statistics display
├── types/
│   └── pakketpunten.ts       # TypeScript type definitions
└── public/
    ├── data/                 # GeoJSON files per municipality
    │   ├── amsterdam.geojson
    │   ├── rotterdam.geojson
    │   └── ...
    └── municipalities.json   # List of available municipalities
```

## Deployment

### Vercel (Recommended)

1. Push to GitHub
2. Import project in Vercel
3. Vercel will auto-detect Next.js and deploy
4. Data updates via GitHub Actions will trigger automatic redeployments

### Environment Variables

No environment variables are required. All data is static and committed to the repository.

## Development Notes

- Map component uses `dynamic` import with `ssr: false` to avoid Leaflet SSR issues
- Data is loaded on-demand per municipality to optimize performance
- Filters are applied client-side for instant feedback
- Leaflet CSS must be imported in `globals.css`

## Future Enhancements

- Add search by address/postcode
- Add route planning to nearest parcel point
- Add heatmap visualization
- Export filtered data as CSV/JSON
- Add municipality comparison view
- Expand to all 345 Dutch municipalities

## License

MIT License - See parent project for details
