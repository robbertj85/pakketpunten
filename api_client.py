
import requests
import pandas as pd, geopandas as gpd
from utils import extract_js_array, parse_locations_any
from utils import make_session, get_gemeente_geometry, fetch_json, json_to_dataframe, df_to_gdf, extract_points_array

# ---------- data ophalen voor "De Buren" ----------

def get_data_deburen(gemeente):
    """
    Parameters
    ----------
    gemeente : str
        Naam van de gemeente waarvoor de pakketpunten moeten worden opgehaald.

    Returns
    -------
    geopandas.GeoDataFrame
        Een GeoDataFrame met de pakketpuntlocaties binnen de opgegeven gemeente.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    url = "https://mijnburen.deburen.nl/maps"

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()  

    js_text = extract_js_array(response.text)
    rows = parse_locations_any(js_text)[0]

    cols = ["naam","lat","lon","id","straat","nummer","postcode","city","flag_a","type","flag_b","flag_c"]
    df = pd.DataFrame(rows, columns=cols)
    df["city"] = df["city"].str.lower()

    df_ = df[df["city"] == gemeente.lower()]
    gdf = df_to_gdf(df_, "DeBuren")
    return gdf


# ---------- data ophalen voor "DHL" ----------


def get_data_dhl(lat, lon, radius):
    """
    Parameters
    ----------
    gemeente : str
        Naam van de gemeente waarvoor de pakketpunten moeten worden opgehaald.

    Returns
    -------
    geopandas.GeoDataFrame
        Een GeoDataFrame met de pakketpuntlocaties binnen de opgegeven gemeente.
    """
    # Input voor zoekgebied DHL api is een cirkel
    session = make_session()
    data = fetch_json(
        "https://api-gw.dhlparcel.nl/parcel-shop-locations/NL/by-geo",
        params={
            "latitude": lat,
            "longitude": lon,
            "radius": radius,
            "limit": 50,  # API default is 15, max is 50
        },
        no_proxy_domains=["api-gw.dhlparcel.nl"],
        session=session,
    )

    df = json_to_dataframe(data)
    gdf = df_to_gdf(df, "DHL")
    return gdf


# ---------- data ophalen voor "PostNL" ----------


def get_data_postnl(bottom_left_lat, bottom_left_lon, top_right_lat, top_right_lon):
    """
    Parameters
    ----------
    gemeente : str
        Naam van de gemeente waarvoor de pakketpunten moeten worden opgehaald.

    Returns
    -------
    geopandas.GeoDataFrame
        Een GeoDataFrame met de pakketpuntlocaties binnen de opgegeven gemeente.
    """
    session = make_session()
                      
    data= fetch_json(
        url= "https://productprijslokatie.postnl.nl/location-widget/api/locations",
        params={
            "country": "nld", # alleen nederlandse locaties ophalen 
            "business": "false", # alleen particuliere afhaalpunten, geen zakelijke
            "filters": "[]", # geen extra filters
            "productFilters": '[{"productId":"23"}]',
            "defaultFilters": "[]", # geen extra filters
            "bottomLeftLat": bottom_left_lat,#"52.44490000000000", # boundingbox zoekgebied
            "bottomLeftLon": bottom_left_lon,#"5.878000000000000", # boundingbox zoekgebied
            "topRightLat": top_right_lat,#"52.59230000000000", # boundingbox zoekgebied
            "topRightLon": top_right_lon,#"6.358900000000000", # boundingbox zoekgebied
            "lang": "NL", # taal in het nederlands
        },
        no_proxy_domains=["productprijslokatie.postnl.nl"],
        session=session,
    )
    df = json_to_dataframe(data)
    gdf = df_to_gdf(df, "PostNL")
    return gdf


# ---------- data ophalen voor "DPD" ----------

def get_data_dpd(gemeente):
    """
    Fetch DPD parcel points for a specific municipality.

    Note: This function uses address-based search which is limited to 100 results.
    For complete DPD coverage, use dpd_fetch_all.py + integrate_dpd_data.py.

    Parameters
    ----------
    gemeente : str
        Naam van de gemeente waarvoor de pakketpunten moeten worden opgehaald.

    Returns
    -------
    geopandas.GeoDataFrame
        Een GeoDataFrame met de pakketpuntlocaties binnen de opgegeven gemeente.
    """
    session = make_session()

    # Use the public DPD API (Czech endpoint that works for all countries)
    data = fetch_json(
        url="https://pickup.dpd.cz/api/GetParcelShopsByAddress",
        params={
            "address": gemeente,
            "limit": 100,  # API maximum (enough for most municipalities)
        },
        no_proxy_domains=["pickup.dpd.cz"],
        session=session,
    )

    # Extract items from response structure
    # Response format: {"status": "ok", "count": X, "data": {"items": [...]}}
    items = []
    if isinstance(data, dict):
        if 'data' in data and isinstance(data['data'], dict):
            items = data['data'].get('items', [])
        elif 'items' in data:
            items = data['items']
    elif isinstance(data, list):
        items = data

    # Convert to dataframe with standardized columns
    rows = []
    for loc in items:
        street = loc.get('street', '')
        house_number = loc.get('house_number', '')

        rows.append({
            'locatieNaam': loc.get('company', ''),
            'straatNaam': street,
            'straatNr': house_number,
            'latitude': loc.get('latitude'),
            'longitude': loc.get('longitude'),
            'puntType': loc.get('pickup_network_type', ''),
            'vervoerder': 'DPD',
        })

    if not rows:
        # Return empty GeoDataFrame with correct structure
        df = pd.DataFrame(columns=['locatieNaam', 'straatNaam', 'straatNr', 'latitude', 'longitude', 'puntType', 'vervoerder'])
        return df_to_gdf(df, "DPD")

    df = pd.DataFrame(rows)
    gdf = df_to_gdf(df, "DPD")
    return gdf


# ---------- data ophalen voor "Amazon" ----------

def get_data_amazon(lat=None, lon=None, radius=None):
    """
    Fetch Amazon Hub Locker and Counter locations from OpenStreetMap via Overpass API.

    Amazon does not provide a public API for querying pickup locations.
    This function uses OpenStreetMap data which is community-maintained and
    may not be 100% complete or up-to-date.

    For complete Amazon coverage, use amazon_fetch_all.py + integrate_amazon_data.py
    which fetches all Amazon locations in the Netherlands once and caches them.

    Data source: OpenStreetMap (Open Data Commons Open Database License - ODbL)
    Attribution: © OpenStreetMap contributors

    Parameters
    ----------
    lat : float, optional
        Center latitude for bounding box search (default: None = all Netherlands)
    lon : float, optional
        Center longitude for bounding box search (default: None = all Netherlands)
    radius : float, optional
        Search radius in km (default: None = all Netherlands)

    Returns
    -------
    geopandas.GeoDataFrame
        GeoDataFrame with Amazon Hub location data
    """
    import json
    from pathlib import Path

    # Try to load from cache file first (faster and more reliable)
    cache_file = Path("data/amazon_all_locations.json")

    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                all_locations = json.load(f)

            # If lat/lon/radius provided, filter cached data
            if lat is not None and lon is not None and radius is not None:
                from math import radians, sin, cos, sqrt, atan2

                def haversine_distance(lat1, lon1, lat2, lon2):
                    """Calculate distance in km between two points"""
                    R = 6371  # Earth radius in km
                    dlat = radians(lat2 - lat1)
                    dlon = radians(lon2 - lon1)
                    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
                    c = 2 * atan2(sqrt(a), sqrt(1-a))
                    return R * c

                filtered_locations = [
                    loc for loc in all_locations
                    if haversine_distance(lat, lon, loc['latitude'], loc['longitude']) <= radius
                ]
            else:
                filtered_locations = all_locations

            if filtered_locations:
                df = pd.DataFrame(filtered_locations)
                return df_to_gdf(df, "Amazon")

        except Exception as e:
            print(f"  ⚠️  Error loading Amazon cache: {e}, falling back to Overpass API")

    # Fallback to Overpass API if no cache
    session = make_session()

    # Overpass API endpoint
    overpass_url = "https://overpass-api.de/api/interpreter"

    # Build Overpass QL query
    # Query for parcel lockers with Amazon as operator or brand in Netherlands
    if lat is not None and lon is not None and radius is not None:
        # Bounding box search around point
        radius_deg = radius / 111  # Rough conversion km to degrees
        bbox = f"{lat-radius_deg},{lon-radius_deg},{lat+radius_deg},{lon+radius_deg}"
        overpass_query = f"""
        [out:json][timeout:30];
        (
          node["amenity"="parcel_locker"]["operator"~"Amazon",i]({bbox});
          node["amenity"="parcel_locker"]["brand"~"Amazon",i]({bbox});
          node["name"~"Amazon",i]["amenity"="parcel_locker"]({bbox});
        );
        out body;
        """
    else:
        # Query all of Netherlands
        overpass_query = """
        [out:json][timeout:60];
        area["ISO3166-1"="NL"][admin_level=2]->.searchArea;
        (
          node["amenity"="parcel_locker"]["operator"~"Amazon",i](area.searchArea);
          node["amenity"="parcel_locker"]["brand"~"Amazon",i](area.searchArea);
          node["name"~"Amazon",i]["amenity"="parcel_locker"](area.searchArea);
        );
        out body;
        """

    try:
        response = session.post(
            overpass_url,
            data={'data': overpass_query},
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()

        elements = data.get('elements', [])

        if not elements:
            print("  ℹ️  No Amazon locations found in OpenStreetMap")
            print("     Consider contributing to OSM or running: python scripts/amazon_fetch_all.py")
            df = pd.DataFrame(columns=['locatieNaam', 'straatNaam', 'straatNr', 'latitude', 'longitude', 'puntType', 'vervoerder'])
            return df_to_gdf(df, "Amazon")

        # Convert OSM data to standardized format
        rows = []
        seen = set()  # Deduplicate by ID

        for elem in elements:
            if elem['type'] != 'node':
                continue

            elem_id = elem.get('id')
            if elem_id in seen:
                continue
            seen.add(elem_id)

            tags = elem.get('tags', {})
            lat_val = elem.get('lat')
            lon_val = elem.get('lon')

            # Extract name (Amazon locker code/name)
            name = tags.get('name', tags.get('ref', 'Amazon Hub'))

            # Extract address
            street = tags.get('addr:street', '')
            house_number = tags.get('addr:housenumber', '')

            # Determine type (Locker vs Counter)
            locker_type = tags.get('parcel_locker:type', '')
            if not locker_type:
                # Infer from name
                if 'counter' in name.lower():
                    locker_type = 'counter'
                else:
                    locker_type = 'locker'

            rows.append({
                'locatieNaam': name,
                'straatNaam': street,
                'straatNr': house_number,
                'latitude': lat_val,
                'longitude': lon_val,
                'puntType': locker_type,
                'vervoerder': 'Amazon',
            })

        if not rows:
            df = pd.DataFrame(columns=['locatieNaam', 'straatNaam', 'straatNr', 'latitude', 'longitude', 'puntType', 'vervoerder'])
            return df_to_gdf(df, "Amazon")

        df = pd.DataFrame(rows)
        gdf = df_to_gdf(df, "Amazon")
        return gdf

    except Exception as e:
        print(f"  ⚠️  Amazon Overpass API error: {e}")
        df = pd.DataFrame(columns=['locatieNaam', 'straatNaam', 'straatNr', 'latitude', 'longitude', 'puntType', 'vervoerder'])
        return df_to_gdf(df, "Amazon")


# ---------- data ophalen voor "VintedGo" ----------

def get_data_vintedgo(lat, lon, south, west, north, east):
    """
    Parameters
    ----------
    gemeente : str
        Naam van de gemeente waarvoor de pakketpunten moeten worden opgehaald.

    Returns
    -------
    geopandas.GeoDataFrame
        Een GeoDataFrame met de pakketpuntlocaties binnen de opgegeven gemeente.
    """
    url = ("https://vintedgo.com/nl/carrier-locations"
        f"?lat={lat}"
        f"&lng={lon}"
        f"&bounds=%7B%22south%22%3A{south}%2C%22west%22%3A{west}%2C%22north%22%3A{north}%2C%22east%22%3A{east}%7D"
        "&region=europe")

    headers = {"User-Agent": "Mozilla/5.0"}  
    txt = requests.get(url, headers=headers, timeout=30).text
    points = extract_points_array(txt)

    # pak de puntenlijst uit
    points_list = points[3]['points']

    # return als dataframe
    df = pd.json_normalize(points_list)
    gdf = df_to_gdf(df, "VintedGo")
    return gdf


# ---------- maak 1 dataset van alle gevonden pakketpunten ----------

def get_data_pakketpunten(gemeente):

    # haal coordinaten op voor het zoekgebied o.b.v. de gemeente
    lat, lon, radius = get_gemeente_geometry(gemeente, mode="circle")
    bottom_left_lat, bottom_left_lon, top_right_lat, top_right_lon = get_gemeente_geometry(gemeente, mode="bbox")
    south, west, north, east = bottom_left_lat, bottom_left_lon, top_right_lat, top_right_lon

    # gdf_amazon = get_data_amazon(lat, lon, radius)  # Disabled: No OSM data available yet
    gdf_deburen = get_data_deburen(gemeente)
    gdf_dhl = get_data_dhl(lat, lon, radius)
    gdf_dpd = get_data_dpd(gemeente)
    gdf_postnl = get_data_postnl(bottom_left_lat, bottom_left_lon, top_right_lat, top_right_lon)
    gdf_vintedgo = get_data_vintedgo(lat, lon, south, west, north, east)

    gdf = gpd.GeoDataFrame(
    pd.concat([gdf_dhl, gdf_dpd, gdf_postnl, gdf_vintedgo, gdf_deburen], ignore_index=True),
    crs=gdf_dhl.crs  # beide hebben CRS EPSG:4326 als het goed is
    )

    desired_order = [
    "locatieNaam",
    "straatNaam",
    "straatNr",
    "latitude",
    "longitude",
    "geometry",
    "puntType", 
    "vervoerder"    
    ]

    gdf = gdf[desired_order]
    return gdf