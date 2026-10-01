"""Reproducible FGJ acquisition-cohort diagnostic; no final crime KPI."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import geopandas as gpd
import pandas as pd
from spatial import assign_points

ROOT = Path(__file__).resolve().parents[1]


def prepare(frame, sha256):
    required = {"_id", "fecha_inicio", "fecha_hecho", "latitud", "longitud", "delito", "categoria_delito", "competencia"}
    if not required.issubset(frame.columns):
        raise ValueError(f"Missing fields: {required - set(frame.columns)}")
    if frame._id.eq("").any() or frame._id.duplicated().any():
        raise ValueError("Datastore row identifiers missing or duplicated")
    result = frame.copy()
    result["source_record_id"] = sha256 + ":" + result._id
    # Keep identical public rows: matching attributes do not prove duplicate investigations.
    result["duplicate_public_attributes"] = frame.drop(columns="_id").duplicated(keep=False)
    start = pd.to_datetime(frame.fecha_inicio, format="%Y-%m-%d", errors="coerce")
    event = pd.to_datetime(frame.fecha_hecho, format="%Y-%m-%d", errors="coerce")
    result["invalid_start_date"] = start.isna()
    result["invalid_event_date"] = event.isna()
    result["event_after_start"] = event.gt(start)
    result["event_in_2020"] = event.dt.year.eq(2020)
    result["flag_noncriminal"] = frame.categoria_delito.eq("HECHO NO DELICTIVO") | frame.competencia.eq("HECHO NO DELICTIVO")
    result["flag_incompetence"] = frame.competencia.eq("INCOMPETENCIA")
    result["flag_unknown_competence"] = frame.competencia.isin(["", "NA"])
    if start.isna().any() or not start.dt.year.eq(2020).all():
        raise ValueError("Source is not entirely a valid 2020 initiation cohort")
    return result


def run():
    config = json.loads((ROOT / "config/cdmx.json").read_text(encoding="utf-8"))
    source = ROOT / config["crime"]["path"]
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    frame = pd.read_csv(source, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    metadata = json.loads((ROOT / "data/raw/cdmx/fgj_count_metadata.json").read_text(encoding="utf-8"))
    expected = metadata["result"]["total"]
    if len(frame) != expected:
        raise ValueError(f"Incomplete export: {len(frame)} vs {expected}")
    out = ROOT / "outputs/cdmx/phase1"
    baseline = json.loads((out / "quality_report.json").read_text(encoding="utf-8"))
    if baseline["territory"] != config:
        raise ValueError("Configuration changed; rerun geographic assessment")
    for key, value in baseline["sha256"].items():
        if hashlib.sha256((ROOT / config["sources"][key]).read_bytes()).hexdigest() != value:
            raise ValueError(f"Source changed: {key}")
    areas_path = out / "areas.geojson"
    areas = gpd.read_file(areas_path)
    assigned = assign_points(prepare(frame, sha), areas, "longitud", "latitud")
    counts = assigned.loc[assigned.assignment_status.eq("assigned")].groupby("CVEGEO").size()
    by_area = areas[["CVEGEO"]].copy()
    by_area["fgj_source_records"] = by_area.CVEGEO.map(counts).fillna(0).astype(int)
    assert int(by_area.fgj_source_records.sum()) == int(assigned.assignment_status.eq("assigned").sum())
    flags = ["duplicate_public_attributes", "invalid_start_date", "invalid_event_date", "event_after_start", "event_in_2020", "flag_noncriminal", "flag_incompetence", "flag_unknown_competence"]
    report = {"generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": sha, "areas_sha256": hashlib.sha256(areas_path.read_bytes()).hexdigest(),
        "rows": len(frame), "expected_api_rows": expected,
        "record_unit": "Published FGJ row; _id is datastore identifier, not proven unique investigation identifier",
        "cohort": "Initiated in 2020; not a complete cohort of events occurring in 2020",
        "coordinate_assumption": config["crime"]["crs_basis"],
        "assignment_counts": {k: int(v) for k,v in assigned.assignment_status.value_counts().items()},
        "flags": {k: int(assigned[k].sum()) for k in flags},
        "start_years": frame.anio_inicio.value_counts().to_dict(),
        "event_years": frame.anio_hecho.value_counts().to_dict(),
        "categories": frame.categoria_delito.value_counts().to_dict(),
        "competence": frame.competencia.value_counts().to_dict(),
        "phase1_complete": False,
        "warning": "All records retained for spatial coverage only; no final crime eligibility filter. Unknown precision, rural coverage gaps, and two missing census polygons remain."}
    columns = ["source_record_id", "_id", "fecha_inicio", "fecha_hecho", "delito", "categoria_delito", "competencia", "CVEGEO", "assignment_status", "match_count"] + flags
    assigned[columns].to_csv(out / "crime_assignment.csv", index=False)
    by_area.to_csv(out / "crime_area_diagnostics.csv", index=False)
    pd.crosstab(assigned.categoria_delito, assigned.assignment_status).to_csv(out / "crime_category_coverage.csv")
    (out / "crime_quality_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["rows", "assignment_counts", "flags"]}, indent=2))


if __name__ == "__main__":
    run()
