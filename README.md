# Pakketpunten Nederland

Een systeem voor het **verzamelen, analyseren en visualiseren van pakketpunten in Nederland**, bestaande uit een Python backend voor dataverzameling en een Next.js webapplicatie voor interactieve kaartvisualisatie.

Data wordt wekelijks automatisch bijgewerkt via GitHub Actions voor alle **343 Nederlandse gemeenten**.

**Disclaimer** — Dit project wordt geleverd "as is" zonder garantie. Data is verzameld van publieke bronnen en kan onnauwkeurigheden bevatten. Verifieer locatiegegevens bij de vervoerders. Dit project is niet gelieerd aan de databronbedrijven.

---

## Huidige Dekking

| Vervoerder | Methode | Locaties | Landelijk ophalen |
|------------|---------|----------|-------------------|
| PostNL | Publieke Widget API | ~4.560 | Per gemeente (bbox) |
| DHL | Publieke REST API | ~4.380 | Grid-based cache |
| DPD | Publieke REST API | ~2.100 | Cache (enkele API call) |
| VintedGo | Web scraping | ~2.090 | Per gemeente (bounds) |
| Amazon | OSM Overpass API | ~1.220 | Per gemeente |
| GLS | Publieke REST API | ~950 | Landelijk cache |
| De Buren | Web scraping | ~165 | Per gemeente |
| **Totaal** | | **~15.460** | |

Data wordt bijgehouden sinds november 2025 met wekelijkse snapshots.

---

## Webapplicatie

De Next.js webapp biedt een interactieve kaartvisualisatie op [pakketpunten.nl](https://pakketpunten.nl).

### Features

- **Interactieve kaart** met OpenStreetMap en Leaflet voor alle 343 gemeenten + nationaal overzicht
- **Adaptieve rendering** — canvas rendering en vereenvoudigde markers voor grote datasets (50.000+ punten)
- **Filters** — per vervoerder, bufferzone (300m/400m), bezettingsgraad, punttype
- **Statistieken** — per gemeente en vervoerder, met historische trends
- **Adres zoeken** — zoek naar een adres en vind nabijgelegen pakketpunten
- **Dichtstbijzijnde punten** — vind pakketpunten binnen 500m van een locatie
- **Gemeentegrenzen** — provinciale grenzen weergave in nationaal overzicht
- **Data export** — download data als GeoJSON of CSV via de API
- **Data matrix** — vergelijk dekking over alle gemeenten en vervoerders
- **Automatische spiderfy** — overlappende markers worden gespreid op hoog zoomniveau
- **Eerlijke zichtbaarheid** — vervoerder render-volgorde roteert elk uur

### Installatie

```bash
cd webapp
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in je browser.

---

## Python Backend

### Installatie

```bash
git clone https://github.com/robbertj85/pakketpunten.git
cd pakketpunten
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Gebruik

```bash
# Enkele gemeente verwerken
python main.py --gemeente Amsterdam --filename test --format geojson

# Complete DHL data ophalen (grid-based, ~3.800+ locaties) - eenmalig
python scripts/dhl_grid_fetch.py

# Complete DPD data ophalen - eenmalig
python scripts/dpd_fetch_all.py

# Complete GLS data ophalen - eenmalig
python scripts/gls_fetch_all.py

# Alle gemeenten batch verwerken (gebruikt caches automatisch)
python scripts/batch_generate.py

# Nationaal overzicht genereren
python scripts/create_national_overview.py

# Provinciale grenzen genereren (voor Nederland view)
python scripts/create_provincial_boundaries.py
```

### Statistische Analyse

Het project bevat een statistisch analyse-systeem dat gemeentedata correleert met pakketpuntdekking.

```bash
# CBS data ophalen (bevolking, oppervlakte)
python scripts/fetch_cbs_municipality_data.py

# Correlatie- en regressieanalyse uitvoeren
python scripts/municipality_statistics_analysis.py

# Professioneel PDF rapport genereren
python scripts/generate_pdf_report.py
```

De analyse omvat Pearson-correlatie, lineaire regressie (R² ~87%), en ranglijsten van over- en onderpresterende gemeenten.

---

## Projectstructuur

```
pakketpunten/
├── main.py                  # Hoofdscript: data ophalen en analyse
├── api_client.py            # API-aanroepen (DHL, DPD, PostNL, GLS, VintedGo, De Buren, Amazon)
├── geo_analysis.py          # Geografische analyses (buffers, unions)
├── utils.py                 # Hulpfuncties (CRS, geocoding, sessies)
├── visualize.py             # Kaartweergave met Folium (legacy)
├── requirements.txt         # Python dependencies
├── data/                    # Gecachte data en logs
│   ├── dhl_all_locations.json
│   ├── dpd_all_locations.json
│   └── gls_all_locations.json
├── scripts/                 # Automatisering en data processing
│   ├── batch_generate.py    # Batch verwerking alle gemeenten
│   ├── dhl_grid_fetch.py    # Landelijke DHL data (grid-based)
│   ├── dpd_fetch_all.py     # Landelijke DPD data
│   ├── gls_fetch_all.py     # Landelijke GLS data
│   ├── create_national_overview.py
│   ├── create_provincial_boundaries.py
│   ├── update_totals_history.py
│   ├── fetch_cbs_municipality_data.py
│   ├── municipality_statistics_analysis.py
│   └── generate_pdf_report.py
├── .github/workflows/       # GitHub Actions
│   ├── update-data.yml      # Wekelijkse data-update (alle vervoerders)
│   └── fetch-gls-data.yml   # Wekelijkse GLS data-update
├── docs/                    # Documentatie
└── webapp/                  # Next.js webapplicatie
    ├── app/                 # Next.js App Router (pagina's + API routes)
    │   ├── page.tsx         # Hoofdpagina met kaart
    │   ├── data-export/     # Data export pagina + matrix view
    │   └── api/             # REST API (download, geocode, v1)
    ├── components/          # React componenten
    │   ├── Map.tsx          # Leaflet kaart met adaptieve rendering
    │   ├── FilterPanel.tsx  # Vervoerder filters en opties
    │   ├── StatsPanel.tsx   # Statistieken dashboard
    │   ├── MunicipalitySelector.tsx
    │   ├── AddressSearchInput.tsx
    │   ├── NearestPointsFinder.tsx
    │   ├── AboutModal.tsx
    │   └── ...              # History modals, trends, clusters
    ├── utils/               # Hulpfuncties
    │   ├── boundaryLoader.ts
    │   └── distanceUtils.ts
    ├── types/               # TypeScript type definities
    └── public/
        ├── data/            # GeoJSON per gemeente + nationaal overzicht
        ├── logos/           # Vervoerder logo's (SVG/PNG)
        └── municipalities.json
```

---

## Automatisering

Data wordt wekelijks automatisch bijgewerkt via GitHub Actions:

- **`update-data.yml`** — Elke zondag: haalt data op voor alle 343 gemeenten, genereert nationaal overzicht, werkt historische snapshots bij
- **`fetch-gls-data.yml`** — Elke zondag: vernieuwt de GLS landelijke cache

Handmatig triggeren kan via `gh workflow run update-data.yml`.

---

## Technische Details

### Coordinatensystemen

- **WGS84 (EPSG:4326)** — API I/O, GeoJSON, webkaarten (graden)
- **RD New (EPSG:28992)** — Metrische berekeningen, buffers (meters)

Altijd transformeren naar RD New voor afstandsberekeningen, daarna terug naar WGS84 voor output.

### Stack

| Component | Technologie |
|-----------|------------|
| Backend | Python 3.10+, GeoPandas, Shapely, Requests |
| Frontend | Next.js 16, TypeScript, React, Leaflet, Tailwind CSS |
| CI/CD | GitHub Actions |
| Hosting | Vercel (webapp), GitHub (data) |

---

## Licentie

Dit project is vrijgegeven onder de **MIT-licentie**.
De licentie geldt voor de **broncode**, niet voor de **data**.

### Data Attributie

Bij gebruik van de gegenereerde data moet de volgende attributie worden opgenomen:

```
Data bronnen:
- DHL Parcel Netherlands (https://www.dhl.nl)
- PostNL (https://www.postnl.nl)
- DPD (https://www.dpd.nl)
- GLS Netherlands (https://gls-group.com/NL)
- Amazon (via OpenStreetMap)
- VintedGo / Mondial Relay (https://vintedgo.com)
- De Buren (https://deburen.nl)
- Gemeente grenzen (c) OpenStreetMap contributors
```
