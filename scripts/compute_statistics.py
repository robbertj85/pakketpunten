"""
Compute per-municipality statistics for the /data-export/statistieken page.

For every municipality this records:
  - point counts per carrier and per category (pakketautomaat vs pakketpunt)
  - density per 10.000 inhabitants and per km²
  - the share of the municipality's land area within 300/400/500 m of a point

Coverage is the expensive part: it buffers every point and intersects the union
with the municipal outline, in RD New so the metres are real metres. Buffering
in degrees is wrong across the country, not merely imprecise.

Input is the generated GeoJSON in webapp/public/data rather than the fetch
pipeline: those files already carry both the points and the municipal boundary,
so this can run any time without re-fetching from ten carriers.

    python scripts/compute_statistics.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import geopandas as gpd  # noqa: E402
from shapely.geometry import shape  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

PROJECT_ROOT = Path(__file__).parent.parent
WEBAPP_DATA_DIR = PROJECT_ROOT / "webapp" / "public" / "data"
MUNICIPALITIES_FILE = PROJECT_ROOT / "webapp" / "public" / "municipalities.json"
OUTPUT_PATH = WEBAPP_DATA_DIR / "statistics.json"

BUFFER_RADII = (300, 400, 500)

# Must mirror CARRIER_ORDER in webapp/lib/carriers.ts. A carrier present here
# but missing there (or the reverse) silently drops out of the charts.
CARRIERS = (
    "PostNL",
    "DHL",
    "DPD",
    "VintedGo",
    "Amazon",
    "GLS",
    "InPost",
    "Budbee",
    "ViaTim",
    "DeBuren",
)

# Must mirror LOCKER_TYPES in webapp/types/pakketpunten.ts.
LOCKER_TYPES = {
    "packStation",  # DHL
    "automaat",  # PostNL, InPost, Budbee
    "dpd_box",  # DPD
    "locker",  # Amazon, VintedGo
    "Buitenkluis",  # DeBuren
}

CATEGORIES = ("locker", "shop")


def point_category(punt_type: str) -> str:
    return "locker" if punt_type in LOCKER_TYPES else "shop"


def coverage_ratio(points_rd, boundary_geom, radius: int) -> float:
    """Fraction of the municipality within `radius` metres of any point.

    Clamped to 1.0: buffers spill across the municipal border, and that
    overspill should not read as more than full coverage.
    """
    if not len(points_rd) or boundary_geom.is_empty:
        return 0.0

    boundary_area = boundary_geom.area
    if boundary_area <= 0:
        return 0.0

    buffered = unary_union(points_rd.buffer(radius))
    return min(buffered.intersection(boundary_geom).area / boundary_area, 1.0)


def municipality_stats(slug: str, meta: dict, payload: dict) -> dict | None:
    """Build the statistics record for one municipality."""
    features = payload.get("features", [])

    points = [f for f in features if (f.get("properties") or {}).get("type") == "pakketpunt"]
    boundaries = [f for f in features if (f.get("properties") or {}).get("type") == "boundary"]

    if not boundaries:
        return None

    boundary_geom_wgs = unary_union([shape(f["geometry"]) for f in boundaries])
    boundary_rd = (
        gpd.GeoSeries([boundary_geom_wgs], crs="EPSG:4326").to_crs(28992).iloc[0]
    )

    area_km2 = round(boundary_rd.area / 1_000_000, 2)
    population = int(meta.get("population") or 0)
    total = len(points)

    per_carrier = {carrier: 0 for carrier in CARRIERS}
    per_category = {category: 0 for category in CATEGORIES}

    for feature in points:
        properties = feature["properties"]
        carrier = properties.get("vervoerder")
        if carrier in per_carrier:
            per_carrier[carrier] += 1
        per_category[point_category(properties.get("puntType") or "")] += 1

    coverage = {str(radius): 0.0 for radius in BUFFER_RADII}
    if total:
        points_rd = gpd.GeoSeries(
            [shape(f["geometry"]) for f in points], crs="EPSG:4326"
        ).to_crs(28992)
        for radius in BUFFER_RADII:
            coverage[str(radius)] = round(
                coverage_ratio(points_rd, boundary_rd, radius), 4
            )

    return {
        "slug": slug,
        "gemeente": meta.get("name") or payload.get("metadata", {}).get("gemeente") or slug,
        "provincie": meta.get("province"),
        "code": meta.get("code"),
        "population": population,
        "area_km2": area_km2,
        "total": total,
        "per_10k_inwoners": round(total / population * 10_000, 2) if population else 0.0,
        "per_km2": round(total / area_km2, 2) if area_km2 else 0.0,
        "vervoerders": per_carrier,
        "categorieen": per_category,
        "dekking": coverage,
    }


def main() -> int:
    print("📊 Computing municipality statistics...")

    if not MUNICIPALITIES_FILE.exists():
        print(f"❌ {MUNICIPALITIES_FILE} not found")
        return 1

    with open(MUNICIPALITIES_FILE, "r", encoding="utf-8") as handle:
        municipalities = json.load(handle)

    by_slug = {m["slug"]: m for m in municipalities if m["slug"] != "nederland"}

    records = []
    skipped = []

    for index, (slug, meta) in enumerate(sorted(by_slug.items()), 1):
        path = WEBAPP_DATA_DIR / f"{slug}.geojson"
        if not path.exists():
            skipped.append(slug)
            continue

        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (json.JSONDecodeError, OSError) as error:
            print(f"  ⚠️  {slug}: {error}")
            skipped.append(slug)
            continue

        record = municipality_stats(slug, meta, payload)
        if record is None:
            skipped.append(slug)
            continue

        records.append(record)

        if index % 50 == 0:
            print(f"  [{index}/{len(by_slug)}] municipalities processed...")

    if not records:
        print("❌ No statistics computed — aborting")
        return 1

    records.sort(key=lambda record: record["gemeente"])

    # National roll-up. Coverage is an area-weighted mean: averaging the ratios
    # directly would give Vlieland the same weight as Amsterdam.
    total_area = sum(record["area_km2"] for record in records) or 1
    national = {
        "total": sum(record["total"] for record in records),
        "population": sum(record["population"] for record in records),
        "area_km2": round(total_area, 2),
        "vervoerders": {
            carrier: sum(record["vervoerders"][carrier] for record in records)
            for carrier in CARRIERS
        },
        "categorieen": {
            category: sum(record["categorieen"][category] for record in records)
            for category in CATEGORIES
        },
        "dekking": {
            str(radius): round(
                sum(
                    record["dekking"][str(radius)] * record["area_km2"]
                    for record in records
                )
                / total_area,
                4,
            )
            for radius in BUFFER_RADII
        },
    }

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "national": national,
        "municipalities": records,
    }

    WEBAPP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False)

    size_kb = OUTPUT_PATH.stat().st_size / 1024
    print(f"\n  ✅ {len(records)} municipalities")
    if skipped:
        print(f"  ⚠️  {len(skipped)} skipped (no file or no boundary)")
    if national["population"]:
        print(
            f"  📍 {national['total']:,} points, "
            f"{national['total'] / national['population'] * 10_000:.1f} per 10.000 inhabitants"
        )
    for radius in BUFFER_RADII:
        print(
            f"  🎯 Coverage within {radius} m: "
            f"{national['dekking'][str(radius)] * 100:.1f}% of land area"
        )
    print(f"  💾 {OUTPUT_PATH.name}: {size_kb:.0f} KB")

    return 0


if __name__ == "__main__":
    sys.exit(main())
