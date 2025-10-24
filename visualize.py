import geopandas as gpd
import folium
from folium.plugins import MarkerCluster
from pathlib import Path
import webbrowser





# ---------- helper functions ----------


# visualize.py
import geopandas as gpd

def _to_gdf_4326(obj, crs_hint=None):
    """
    Converteer shapely/GeoSeries/GeoDataFrame naar GeoDataFrame met CRS=EPSG:4326.

    Parameters
    ----------
    obj : shapely.geometry | gpd.GeoSeries | gpd.GeoDataFrame
    crs_hint : int | str | None
        CRS-hint (bijv. 28992 of 'EPSG:28992') als obj geen CRS heeft.

    Returns
    -------
    gpd.GeoDataFrame
        GeoDataFrame met CRS EPSG:4326.
    """
    if isinstance(obj, gpd.GeoDataFrame):
        gdf = obj.copy()
    elif isinstance(obj, gpd.GeoSeries):
        gdf = gpd.GeoDataFrame(geometry=obj)
        if gdf.crs is None and crs_hint is not None:
            gdf = gdf.set_crs(crs_hint)
    else:
        # aannemen: shapely-geometry
        gdf = gpd.GeoDataFrame(geometry=[obj], crs=crs_hint)

    if gdf.crs is None:
        raise ValueError("CRS onbekend. Geef crs_hint mee (bv. EPSG:28992 of EPSG:4326).")

    return gdf.to_crs(4326)


def add_union_layer(m, union_geom, name, crs_hint=None, fill_opacity=0.15):
    """
    Voeg de (Multi)Polygon-union van het dekkingsgebied als één laag toe aan een Folium-kaart.

    Parameters
    ----------
    m : folium.Map
    union_geom : shapely.geometry | gpd.GeoSeries | gpd.GeoDataFrame
    name : str
        Laagnaam voor de LayerControl.
    crs_hint : int | str | None
        CRS-hint als union_geom geen CRS draagt (bv. 28992).
    fill_opacity : float
        Doorzichtigheid van vulling.
    """
    gdf4326 = _to_gdf_4326(union_geom, crs_hint=crs_hint)

    folium.GeoJson(
        data=gdf4326.__geo_interface__,
        name=name,
        style_function=lambda feat: {
            "color": "black",
            "weight": 2,
            "fill": True,
            "fillOpacity": fill_opacity,
        },
    ).add_to(m)

    return gdf4326


def create_map(filename, gdf_points, buffer_union300=None, buffer_union500=None,
               buffers_crs_hint=28992, zoom_start=12, tiles="OpenStreetMap"):
    """
    Maak een Folium-kaart met punten en optionele union-buffers.

    Parameters
    ----------
    gdf_points : gpd.GeoDataFrame
        Punten in willekeurige CRS; wordt naar EPSG:4326 geprojecteerd voor weergave.
        Verwachte (optionele) kolommen: 'locatieNaam', 'straatNaam', 'pakketdienst'.
    buffer_union300 : shapely|GeoSeries|GeoDataFrame | None
        Union-geometry voor 300m buffer (optioneel).
    buffer_union500 : shapely|GeoSeries|GeoDataFrame | None
        Union-geometry voor 500m buffer (optioneel).
    buffers_crs_hint : int | str
        CRS-hint voor de buffer geometrieën (bv. 28992 als ze uit RD komen).
    zoom_start : int
        Start zoomniveau.
    tiles : str
        Folium tiles, bv. 'OpenStreetMap', 'CartoDB positron', etc.

    Returns
    -------
    folium.Map
    """
    # 1) Kaart centreren op centroid van alle punten (in 4326)
    pts4326 = gdf_points.to_crs(4326)
    center = pts4326.geometry.unary_union.centroid  # robuust en compatibel
    m = folium.Map(location=[center.y, center.x], zoom_start=zoom_start, tiles=tiles)

    # 2) Pakketpunten tekenen met clustering
    cluster = MarkerCluster(name="Pakketpunten").add_to(m)
    for _, row in pts4326.iterrows():
        lat, lon = row.geometry.y, row.geometry.x
        title = str(row.get("locatieNaam", "Punt"))
        subtitle = " | ".join(
            s for s in [row.get("straatNaam", ""), row.get("pakketdienst", "")] if s
        )
        label = f"{title}" + (f" | {subtitle}" if subtitle else "")

        folium.CircleMarker(
            [lat, lon],
            radius=4,
            fill=True,
            fill_opacity=1,
            tooltip=label,
            popup=f"<b>{label}</b><br/>({lat:.6f}, {lon:.6f})",
        ).add_to(cluster)

    # 3) Union-buffers toevoegen als ze zijn meegegeven
    bounds_list = [pts4326.total_bounds]  # voor auto-zoom
    if buffer_union300 is not None:
        g300 = add_union_layer(
            m, buffer_union300, "Buffer 300 m (union)",
            crs_hint=buffers_crs_hint, fill_opacity=0.15
        )
        bounds_list.append(g300.total_bounds)

    if buffer_union500 is not None:
        g500 = add_union_layer(
            m, buffer_union500, "Buffer 500 m (union)",
            crs_hint=buffers_crs_hint, fill_opacity=0.10
        )
        bounds_list.append(g500.total_bounds)

    # 4) Auto-zoomen op punten + (eventuele) buffers
    try:
        west = min(b[0] for b in bounds_list)
        south = min(b[1] for b in bounds_list)
        east = max(b[2] for b in bounds_list)
        north = max(b[3] for b in bounds_list)
        m.fit_bounds([[south, west], [north, east]])
    except Exception:
        pass

    folium.LayerControl().add_to(m)

    # Sla kaart op als html
    output_dir = Path(__file__).resolve().parent / "output"
    output_dir.mkdir(exist_ok=True)
    path = output_dir / f"{filename}_kaart.html"
    m.save(path)

    # Open de kaart in de browser
    webbrowser.open(path.resolve().as_uri())

    return m





