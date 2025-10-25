# 📦 Pakketpunten Data

Een Python-project voor het **verzamelen, analyseren en visualiseren van pakketpunten in Nederland**.  
De data wordt opgehaald via verschillende API’s (zoals DHL en De Buren), geanalyseerd met **GeoPandas**,  
en weergegeven als interactieve kaarten met **Folium**.

Dit project is bedoeld als basis voor geodata-analyse, ruimtelijke visualisatie en verdere uitbreiding naar een webapplicatie.

---

## Functionaliteiten

- Ophalen van pakketpuntlocaties via API's en webscraping (voor DHL, DPD, PostNL, VintedGo en De Buren) voor een gegeven gemeente
- Het toevoegen van buffers rondom bestaande pakketpunten
- Het toevoegen van dummy data met de bezettingsgraad om een indicatie te geven van hoe de dekking van een gebied kan worden bepaald.
- Export van resultaten naar **GeoPackage (.gpkg)** en **GeoJSON (.geojson)**
- Interactieve kaartweergave in **Folium**, opgeslagen als HTML
- **Webapplicatie (Next.js)** voor interactieve visualisatie met filters en statistieken

---

## Data Bronnen

Dit project verzamelt pakketpuntlocaties van de volgende bronnen:

- **DHL Parcel** - Via publieke API (`api-gw.dhlparcel.nl`) - ~2000+ locaties
- **DPD** - Via publieke API (`pickup.dpd.cz`) - 1,933 locaties (parcel shops + lockers)
- **PostNL** - Via publieke locatie-widget API
- **VintedGo / Mondial Relay** - Via publieke website
- **De Buren** - Via publieke kaart interface

⚠️ **Belangrijk:** De bezettingsgraad (occupancy) data is **willekeurig gegenereerd** voor demonstratiedoeleinden en weerspiegelt geen echte capaciteitsgegevens.

📋 **Voor uitgebreide informatie** over data bronnen, gebruiksrechten en attributie-vereisten, zie [DATA_SOURCES.md](./docs/DATA_SOURCES.md) 

---

## Projectstructuur

```
pakketpunten/
├── main.py                 # Hoofdscript: haalt data op, voert analyse uit
├── api_client.py           # API-aanroepen (DHL, DPD, PostNL, VintedGo, De Buren)
├── utils.py                # Algemene hulpfuncties
├── geo_analysis.py         # Geografische analyses (buffers, unions, etc.)
├── visualize.py            # Kaartweergave met Folium (legacy)
├── requirements.txt        # Benodigde Python-pakketten
├── update.sh               # Automatische update script
├── README.md               # Projectdocumentatie
├── data/                   # Data bestanden en logs
│   ├── dhl_all_locations.json
│   ├── dpd_all_locations.json
│   ├── municipalities_all.json
│   ├── gemeenten-2025.xlsx
│   └── *_update_log.txt
├── docs/                   # Documentatie
│   ├── CLAUDE.md           # Technische documentatie voor ontwikkelaars
│   ├── AUTOMATION.md       # Automatisering documentatie
│   ├── DATA_SOURCES.md     # Uitgebreide documentatie over databronnen
│   ├── DHL_GRID_WORKFLOW.md
│   └── QUICKSTART_AUTOMATION.md
├── scripts/                # Automation en data processing scripts
│   ├── batch_generate.py   # Batch processing voor meerdere gemeentes
│   ├── dhl_grid_fetch.py   # Complete DHL data ophalen (grid-based approach)
│   ├── dpd_fetch_all.py    # Complete DPD data ophalen (single API call)
│   ├── integrate_dhl_grid_data.py  # DHL data integreren in gemeente files
│   ├── integrate_dpd_data.py       # DPD data integreren in gemeente files
│   ├── weekly_update.py            # Weekelijkse update van alle data
│   ├── create_national_overview.py # Genereer nationaal overzicht
│   └── run_complete_dhl_update.py  # Complete DHL update workflow
└── webapp/                 # Next.js webapplicatie
    ├── app/                # Next.js App Router
    ├── components/         # React componenten (Map, Filters, Stats)
    ├── types/              # TypeScript type definities
    ├── public/             # Statische bestanden
    │   ├── data/           # GeoJSON bestanden per gemeente
    │   └── municipalities.json
    └── package.json
```

---

## Gebruik

### Python Data Generatie

#### Installatie

```bash
git clone https://github.com/Ida-BirdsEye/pakketpunten.git
cd pakketpunten

# Maak virtual environment
python3 -m venv venv
source venv/bin/activate  # Op Windows: venv\Scripts\activate

# Installeer dependencies
pip install -r requirements.txt
```

#### Enkele gemeente verwerken

```bash
python main.py --gemeente Amsterdam --filename test --format geojson
```

#### Meerdere gemeentes in batch verwerken

```bash
python scripts/batch_generate.py
```

Dit genereert GeoJSON bestanden voor alle gemeentes in `data/municipalities_all.json` en plaatst ze in `webapp/public/data/`.

#### Resultaten bekijken
- **Kaart:** `output/kaart.html` → open in je browser
- **GeoPackage / GeoJSON:** open in QGIS, GeoPandas of een andere GIS-tool

---

### Webapplicatie (Next.js)

#### Installatie

```bash
cd webapp
npm install
```

#### Development server starten

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in je browser.

#### Features

- **Interactieve kaart** met OpenStreetMap en Leaflet
- **Gemeente selectie** via dropdown (5 POC gemeentes beschikbaar)
- **Filters:**
  - Vervoerders (DHL, PostNL, VintedGo, De Buren)
  - Bezettingsgraad (mock data, optioneel)
  - Buffer zones (300m en 500m)
- **Statistieken** per gemeente en vervoerder
- **Real-time logos** van vervoerders via Clearbit API
- **Popup details** met locatie-informatie en ruwe JSON data

#### Productie build

```bash
npm run build
npm start
```

---

## Technische details

### Python Backend

- **Taal:** Python 3.10+
- **Belangrijkste libraries:**
  - `geopandas` - Geospatial data processing
  - `shapely` - Geometric operations
  - `folium` - Interactive maps (legacy)
  - `requests` - API calls
  - `fiona` - Geospatial file I/O
  - `pandas` - Data manipulation
  - `geopy` - Geocoding

### Next.js Frontend

- **Framework:** Next.js 16 (App Router)
- **Taal:** TypeScript
- **Belangrijkste libraries:**
  - `react-leaflet` - Interactive maps
  - `leaflet` - Mapping library
  - `tailwindcss` - Styling

### Bestandsformaten

- `.gpkg` → GeoPackage (voor GIS-software)
- `.geojson` → Webvriendelijk formaat
- `.html` → Interactieve kaartweergave (legacy)
- `.json` → Metadata en configuratie

### Coordinate Systems

- **WGS84 (EPSG:4326)** - Web maps, API output
- **RD New (EPSG:28992)** - Dutch grid, metric calculations  

---

## Toekomstige uitbreidingen

### Korte termijn
- ✅ ~~Webapplicatie met Next.js~~ (Voltooid - POC klaar)
- ✅ ~~Interactieve filters en statistieken~~ (Voltooid)
- ✅ ~~Mock data toggle voor bezettingsgraad~~ (Voltooid)
- 🔄 Uitbreiding naar alle 345 Nederlandse gemeentes
- 🔄 GitHub Actions voor wekelijkse data updates
- 🔄 Deployment naar Vercel

### Middellange termijn
- 📋 Object storage integratie (Cloudflare R2 of AWS S3)
- 📋 Performance optimalisatie (caching, lazy loading)
- 📋 Search functionaliteit voor gemeentes
- 📋 Export functionaliteit (download gefilterde data)
- 📋 Dark mode voor webinterface

### Lange termijn
- 📋 Echte bezettingsgraad data via carrier API's (indien beschikbaar)
- 📋 Historische data tracking en trending
- 📋 Routeplanning integratie
- 📋 Coverage gap analysis (ondergeserveerde gebieden)
- 📋 Mobiele app (React Native)
- 📋 API voor externe integraties

**Legenda:**
- ✅ Voltooid
- 🔄 In ontwikkeling
- 📋 Gepland

---

## Licentie

Dit project is vrijgegeven onder de **MIT-licentie**.
Je mag de code gebruiken, aanpassen en verspreiden zolang de originele auteursvermelding behouden blijft.

### Data Attributie

⚠️ **Let op:** De MIT-licentie geldt voor de **broncode**, niet voor de **data**.

Bij gebruik van de gegenereerde data moet de volgende attributie worden opgenomen:

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

Zie [DATA_SOURCES.md](./docs/DATA_SOURCES.md) voor volledige details over gebruiksrechten.



