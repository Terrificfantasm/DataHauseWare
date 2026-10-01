"""Phase 1 diagnostics. Outputs are not final warehouse analytical datasets."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile
from datetime import datetime, timezone

import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from spatial import assign_points

ROOT = Path(__file__).resolve().parents[1]


def read_csv_zip(path, encoding=None):
    with zipfile.ZipFile(path) as archive:
        members = [m for m in archive.namelist()
                   if "conjunto_de_datos/" in m and m.lower().endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"Expected one data CSV: {members}")
        data = archive.read(members[0])
    if encoding:
        text = data.decode(encoding)
    else:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("cp1252")
    return pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)


def select_scope(frame, config, state, municipality, locality):
    mask = frame[state].eq(config["state"])
    if config["municipalities"]:
        mask &= frame[municipality].isin(config["municipalities"])
    if config["localities"]:
        mask &= frame[locality].isin(config["localities"])
    return frame.loc[mask].copy()


def normalize_business_keys(frame):
    frame = frame.copy()
    for column, width in (("cve_ent", 2), ("cve_mun", 3), ("cve_loc", 4)):
        if not frame[column].str.fullmatch(r"[0-9]{1," + str(width) + "}").all():
            raise ValueError(f"Invalid geographic codes: {column}")
        frame[column] = frame[column].str.zfill(width)
    return frame


def locality_totals(scope):
    """Exclude entity and municipality totals when selecting all localities."""
    return scope.loc[scope.AGEB.eq("0000") & scope.MZA.eq("000")
                     & scope.MUN.ne("000") & scope.LOC.ne("0000"), "POBTOT"]


def run(config_path):
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not config.get("enabled"):
        raise ValueError("Configuration disabled: verify sources and scope first")
    if config["census_year"] != config["boundary_year"]:
        raise ValueError("Census/boundary vintages require an explicit crosswalk")
    paths = {key: ROOT / config["sources"][key]
             for key in ("census", "boundaries", "businesses")}
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    output = ROOT / "outputs" / config["id"] / "phase1"
    output.mkdir(parents=True, exist_ok=True)
    report = {"territory": config, "generated_utc": datetime.now(timezone.utc).isoformat(),
              "phase1_complete": False, "crime_status": config["crime"]["status"],
              "sha256": {k: hashlib.sha256(p.read_bytes()).hexdigest() for k, p in paths.items()},
              "warnings": ["Census and business releases differ; no contemporary population estimate.",
                           "Crime integration pending. These outputs are Phase 1 diagnostics."]}
    census = read_csv_zip(paths["census"])
    scope = select_scope(census, config, "ENTIDAD", "MUN", "LOC")
    ageb = scope.loc[scope.MZA.eq("000") & ~scope.AGEB.eq("0000")].copy()
    ageb["CVEGEO"] = ageb.ENTIDAD + ageb.MUN + ageb.LOC + ageb.AGEB
    if ageb.empty or ageb.CVEGEO.duplicated().any():
        raise ValueError("Missing or duplicate census AGEB totals")
    population = pd.to_numeric(ageb.POBTOT, errors="coerce")
    local_totals = locality_totals(scope)
    report["census"] = {"ageb_rows": len(ageb), "missing_population": int(population.isna().sum()),
                        "ageb_population_sum": int(population.sum()),
                        "locality_population_sum": int(pd.to_numeric(local_totals, errors="raise").sum())}
    print("Loading official polygons...", flush=True)
    member = config["sources"]["boundary_member"]
    areas = gpd.read_file(f"/vsizip/{paths['boundaries'].as_posix()}/{member}")
    areas = select_scope(areas, config, "CVE_ENT", "CVE_MUN", "CVE_LOC")
    missing = sorted(set(ageb.CVEGEO) - set(areas.CVEGEO))
    extra = sorted(set(areas.CVEGEO) - set(ageb.CVEGEO))
    report["geography"] = {"polygons": len(areas), "crs": str(areas.crs),
        "invalid": int((~areas.is_valid).sum()), "empty": int(areas.geometry.is_empty.sum()),
        "null": int(areas.geometry.isna().sum()), "duplicate_keys": int(areas.CVEGEO.duplicated().sum()),
        "census_keys_without_polygon": missing, "polygon_keys_without_census": extra}
    if (areas.empty or areas.crs is None or report["geography"]["invalid"]
            or report["geography"]["empty"] or report["geography"]["null"]
            or report["geography"]["duplicate_keys"]
            or missing != sorted(config.get("acknowledged_census_without_polygon", [])) or extra):
        (output / "quality_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        raise ValueError("Geography validation failed; inspect quality_report.json")
    report["census"]["population_without_polygon"] = int(pd.to_numeric(ageb.loc[ageb.CVEGEO.isin(missing), "POBTOT"]).sum())
    report["census"]["mapped_population"] = int(population.sum()) - report["census"]["population_without_polygon"]
    areas = areas.merge(ageb[["CVEGEO", "POBTOT"]], on="CVEGEO", validate="one_to_one")
    # Geodesic surface avoids treating degrees squared or a non-equal-area CRS as km2.
    wgs84 = areas.to_crs(4326)
    from pyproj import Geod
    from shapely.geometry.polygon import orient
    geod = Geod(ellps="WGS84")
    def surface(geometry):
        parts = geometry.geoms if geometry.geom_type == "MultiPolygon" else [geometry]
        return sum(abs(geod.geometry_area_perimeter(orient(p, sign=1.0))[0]) for p in parts) / 1e6
    areas["area_km2"] = [surface(g) for g in wgs84.geometry]
    businesses = normalize_business_keys(read_csv_zip(paths["businesses"], config.get("business_encoding")))
    # Use state-wide candidates so stale locality codes cannot discard points physically inside the study area.
    candidates = businesses.loc[businesses.cve_ent.eq(config["state"])].copy()
    if candidates.empty:
        raise ValueError("No businesses in selected state; inspect source geographic codes")
    print(f"Assigning {len(candidates):,} business points...", flush=True)
    assigned = assign_points(candidates, areas, "longitud", "latitud")
    declared_mask = assigned["cve_ent"].eq(config["state"])
    if config["municipalities"]:
        declared_mask &= assigned.cve_mun.isin(config["municipalities"])
    if config["localities"]:
        declared_mask &= assigned.cve_loc.isin(config["localities"])
    statuses = assigned.assignment_status.value_counts().to_dict()
    report["businesses"] = {"state_candidates": len(candidates),
        "duplicate_id_rows": int(candidates.id.duplicated(keep=False).sum()),
        "declared_scope_rows": int(declared_mask.sum()),
        "assignment_counts_state": {k: int(v) for k, v in statuses.items()},
        "assignment_counts_declared_scope": {k: int(v) for k, v in assigned.loc[declared_mask, "assignment_status"].value_counts().items()},
        "assigned_with_other_locality_codes": int((~declared_mask & assigned.assignment_status.eq("assigned")).sum())}
    counts = assigned.loc[assigned.assignment_status.eq("assigned")].groupby("CVEGEO").size()
    areas["business_records"] = areas.CVEGEO.map(counts).fillna(0).astype(int)
    if int(areas.business_records.sum()) != statuses.get("assigned", 0):
        raise ValueError("Spatial count reconciliation failed")
    # Minimal diagnostic export; omit contact/address fields.
    assigned[["id", "codigo_act", "cve_mun", "cve_loc", "CVEGEO", "assignment_status", "match_count"]].to_csv(output / "business_assignment.csv", index=False)
    areas[["CVEGEO", "POBTOT", "area_km2", "business_records"]].to_csv(output / "area_diagnostics.csv", index=False)
    areas.to_crs(4326).to_file(output / "areas.geojson", driver="GeoJSON")
    fig, ax = plt.subplots(figsize=(10, 9))
    areas.plot(column="business_records", cmap="YlGnBu", linewidth=0.15,
               edgecolor="#8b9ba6", legend=True, ax=ax,
               legend_kwds={"label": "Registros DENUE asignados"})
    ax.set_title(f"{config['name']}\nPrueba espacial: DENUE {config['business_release']} / AGEB {config['boundary_year']}")
    ax.set_axis_off()
    fig.text(0.5, 0.025, "DiagnÃƒÆ’Ã‚Â³stico de Fase 1 Ãƒâ€šÃ‚Â· INEGI Ãƒâ€šÃ‚Â· Seguridad pendiente Ãƒâ€šÃ‚Â· No es un KPI final del DW", ha="center", fontsize=9)
    fig.savefig(output / "spatial_check.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    (output / "quality_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(output), "census": report["census"], "businesses": report["businesses"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "merida.json")
    args = parser.parse_args()
    run(args.config.resolve())
