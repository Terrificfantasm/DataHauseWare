"""Coverage audit and explicit candidate eligibility; no source records modified."""
import json
import hashlib
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely import STRtree
from assess_geography import read_csv_zip, normalize_business_keys
ROOT = Path(__file__).resolve().parents[1]


def eligibility(f):
    # Exact labels: references to minors as victims are not grounds for exclusion.
    reason = pd.Series("candidate_unknown_competence", index=f.index)
    reason.loc[f.competencia.eq("FUERO COMUN")] = "candidate_common_jurisdiction"
    reason.loc[~f.competencia.isin(["NA", "", "FUERO COMUN"])] = "review_other_competence"
    reason.loc[f.delito.isin(["DENUNCIA DE HECHOS", "DDH INCOMPETENCIA"])] = "excluded_report_of_facts"
    reason.loc[f.competencia.eq("INCOMPETENCIA")] = "excluded_incompetence"
    reason.loc[f.categoria_delito.eq("HECHO NO DELICTIVO") | f.competencia.eq("HECHO NO DELICTIVO")] = "excluded_noncriminal"
    return reason


def run():
    cfg = json.loads((ROOT / "config/cdmx.json").read_text(encoding="utf-8"))
    out = ROOT / "outputs/cdmx/phase1"
    baseline = json.loads((out / "quality_report.json").read_text(encoding="utf-8"))
    crime_report = json.loads((out / "crime_quality_report.json").read_text(encoding="utf-8"))
    for key, digest in baseline["sha256"].items():
        assert hashlib.sha256((ROOT/cfg["sources"][key]).read_bytes()).hexdigest() == digest
    crime_path = ROOT / cfg["crime"]["path"]
    assert hashlib.sha256(crime_path.read_bytes()).hexdigest() == crime_report["source_sha256"]
    assert hashlib.sha256((out/"areas.geojson").read_bytes()).hexdigest() == crime_report["areas_sha256"]
    archive = (ROOT / cfg["sources"]["boundaries"]).as_posix()
    def layer(name):
        return gpd.read_file(f"/vsizip/{archive}/conjunto_de_datos/{name}.shp")
    areas = layer("09a").to_crs(32614)
    entity = layer("09ent").to_crs(32614).geometry.union_all()
    localities = layer("09l")
    rural = layer("09ar")
    missing = []
    for key in cfg["acknowledged_census_without_polygon"]:
        loc = localities.loc[localities.CVEGEO.eq(key[:9])]
        rural_key = key[:5] + key[9:]
        missing.append({"census_key": key, "locality": loc.drop(columns="geometry").to_dict("records"),
                        "rural_key_match": rural_key if rural.CVEGEO.eq(rural_key).any() else None,
                        "interpretation": "Urban census vs rural cartographic classification; no geometric equivalence established"})
    tree = STRtree(areas.geometry.values)
    pairs = tree.query(areas.geometry.values, predicate="intersects")
    overlaps = []
    for i,j in zip(*pairs):
        if i < j:
            size = areas.geometry.iloc[i].intersection(areas.geometry.iloc[j]).area
            if size > 0:
                overlaps.append({"left": areas.CVEGEO.iloc[i], "right": areas.CVEGEO.iloc[j], "area_m2": size})
    pd.DataFrame(overlaps, columns=["left","right","area_m2"]).to_csv(out/"cdmx_polygon_overlaps.csv",index=False)
    urban = areas.geometry.union_all()
    def outside_audit(raw, assignment, identifier):
        joined = raw.merge(assignment[[identifier,"assignment_status"]],on=identifier,validate="one_to_one")
        f = joined.loc[joined.assignment_status.eq("outside_selected_areas")].copy()
        points = gpd.GeoSeries(gpd.points_from_xy(pd.to_numeric(f.longitud),pd.to_numeric(f.latitud)), index=f.index,crs=4326).to_crs(32614)
        f["inside_entity_polygon"] = points.intersects(entity)
        f["distance_urban_m"] = points.distance(urban)
        f[[identifier,"inside_entity_polygon","distance_urban_m"]].to_csv(out/("crime_outside_coverage.csv" if identifier == "_id" else "business_outside_coverage.csv"),index=False)
        return {"rows":len(f),"inside_entity":int(f.inside_entity_polygon.sum()),"outside_entity":int((~f.inside_entity_polygon).sum()),
                "within_100m_of_urban":int(f.distance_urban_m.le(100).sum()),"within_500m_of_urban":int(f.distance_urban_m.le(500).sum())}
    businesses = normalize_business_keys(read_csv_zip(ROOT/cfg["sources"]["businesses"],cfg["business_encoding"]))
    business_assignment = pd.read_csv(out/"business_assignment.csv",dtype=str,keep_default_na=False)
    business_coverage = outside_audit(businesses,business_assignment,"id")
    raw = pd.read_csv(crime_path,dtype=str,keep_default_na=False)
    assignment = pd.read_csv(out/"crime_assignment.csv",dtype=str,keep_default_na=False)
    crime_coverage = outside_audit(raw,assignment,"_id")
    raw["eligibility_reason"] = eligibility(raw)
    raw = raw.merge(assignment[["_id","assignment_status","CVEGEO"]],on="_id",validate="one_to_one")
    raw["candidate"] = raw.eligibility_reason.str.startswith("candidate_")
    raw["spatial_candidate"] = raw.candidate & raw.assignment_status.eq("assigned")
    raw[["_id","eligibility_reason","candidate","spatial_candidate","assignment_status","CVEGEO"]].to_csv(out/"crime_eligibility.csv",index=False)
    pd.crosstab(raw.eligibility_reason,raw.assignment_status).to_csv(out/"crime_eligibility_coverage.csv")
    monthly = raw.groupby(["mes_inicio","competencia"]).size().unstack(fill_value=0)
    monthly.to_csv(out/"crime_competence_month.csv")
    report = {"source_hashes":baseline["sha256"],"crime_sha256":crime_report["source_sha256"],
              "missing_polygon_evidence":missing,"overlap_pairs_positive_area":len(overlaps),
              "overlap_pairs_above_1m2":sum(x["area_m2"]>1 for x in overlaps),
              "business_outside":business_coverage,"crime_outside":crime_coverage,
              "eligibility_rule_version":"candidate-v1", "eligibility_counts":raw.eligibility_reason.value_counts().to_dict(),
              "candidate_rows":int(raw.candidate.sum()),"spatial_candidate_rows":int(raw.spatial_candidate.sum()),
              "strict_common_jurisdiction_spatial_rows":int((raw.eligibility_reason.eq("candidate_common_jurisdiction") & raw.assignment_status.eq("assigned")).sum()),
              "limitations":["WGS84 assumed; accuracy unknown", "Eligibility is a project candidate definition, not SESNSP harmonization", "No snapping or rural substitution"]}
    (out/"coverage_audit.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__ == "__main__":
    run()
