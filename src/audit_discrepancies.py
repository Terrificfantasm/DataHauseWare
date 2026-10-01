"""Audit boundary discrepancies without changing source coordinates or assignments."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import geopandas as gpd
import pandas as pd
from assess_geography import ROOT, read_csv_zip, select_scope


def run(config_path):
    config = json.loads(config_path.read_text(encoding='utf-8'))
    if not config.get('enabled'):
        raise ValueError('Disabled configuration')
    out = ROOT / 'outputs' / config['id'] / 'phase1'
    baseline = json.loads((out / 'quality_report.json').read_text(encoding='utf-8'))
    if baseline['territory'] != config:
        raise ValueError('Configuration differs from baseline; regenerate assessment first')
    hashes = {}
    for kind in ('census', 'boundaries', 'businesses'):
        path = ROOT / config['sources'][kind]
        hashes[kind] = hashlib.sha256(path.read_bytes()).hexdigest()
        if hashes[kind] != baseline['sha256'][kind]:
            raise ValueError('Source differs from baseline: ' + kind)
    source = read_csv_zip(ROOT / config['sources']['businesses'])
    assignment = pd.read_csv(out / 'business_assignment.csv', dtype=str, keep_default_na=False)
    if source.id.duplicated().any() or assignment.id.duplicated().any():
        raise ValueError('Duplicate IDs require resolution')
    data = assignment.merge(source[['id','cve_ent','municipio','localidad','ageb','manzana','longitud','latitud']],
                            on='id', how='left', validate='one_to_one', indicator=True)
    if not data['_merge'].eq('both').all():
        raise ValueError('Assignment references missing source IDs')
    declared = data.index.isin(select_scope(data, config, 'cve_ent','cve_mun','cve_loc').index)
    assigned = data.assignment_status.eq('assigned')
    discrepancy = data.loc[(declared & ~assigned) | (~declared & assigned)].copy()
    discrepancy['case'] = ['declared_inside_spatially_outside' if inside else 'declared_outside_spatially_inside'
                           for inside in declared[discrepancy.index]]
    archive = (ROOT / config['sources']['boundaries']).as_posix()
    areas = gpd.read_file(f"/vsizip/{archive}/{config['sources']['boundary_member']}")
    selected = select_scope(areas, config, 'CVE_ENT','CVE_MUN','CVE_LOC').reset_index(drop=True)
    metric_crs = selected.estimate_utm_crs()
    projected = selected.to_crs(metric_crs)
    points = gpd.GeoDataFrame(discrepancy, geometry=gpd.points_from_xy(
        pd.to_numeric(discrepancy.longitud, errors='raise'),
        pd.to_numeric(discrepancy.latitud, errors='raise')), crs=4326).to_crs(metric_crs)
    union = projected.geometry.union_all()
    points['distance_to_study_area_m'] = points.geometry.distance(union)
    points['distance_to_study_boundary_m'] = points.geometry.distance(union.boundary)
    # Nearest is diagnostic only, never an assignment rule. Retain ties as lists.
    nearest = gpd.sjoin_nearest(points[['geometry']], projected[['CVEGEO','geometry']], how='left')
    nearest_codes = nearest.groupby(level=0).CVEGEO.agg(lambda s: '|'.join(sorted(set(s.dropna()))))
    points['nearest_selected_ageb'] = nearest_codes
    statewide = gpd.sjoin(points[['geometry']], areas[['CVEGEO','geometry']].to_crs(metric_crs),
                          how='left', predicate='intersects')
    statewide_codes = statewide.groupby(level=0).CVEGEO.agg(lambda s: '|'.join(sorted(set(s.dropna()))))
    points['containing_state_ageb_2020'] = statewide_codes
    points['declared_ageb_key'] = points.cve_ent + points.cve_mun + points.cve_loc + points.ageb
    points['declared_ageb_exists_2020'] = points.declared_ageb_key.isin(areas.CVEGEO)
    overlap_rows = []
    for i, geometry in enumerate(projected.geometry):
        for j in projected.sindex.query(geometry, predicate='intersects'):
            if int(j) <= i:
                continue
            intersection_area = geometry.intersection(projected.geometry.iloc[j]).area
            if intersection_area > 0:
                overlap_rows.append({'left': projected.CVEGEO.iloc[i], 'right': projected.CVEGEO.iloc[j],
                                     'overlap_m2': float(intersection_area)})
    outside = points.loc[points.case.eq('declared_inside_spatially_outside')]
    buckets = pd.cut(outside.distance_to_study_area_m, [-1,1,10,50,100,500,1000,float('inf')],
                     labels=['0-1m','>1-10m','>10-50m','>50-100m','>100-500m','>500-1000m','>1000m'])
    report = {
        'generated_utc': datetime.now(timezone.utc).isoformat(), 'source_sha256': hashes,
        'config': config, 'distance_crs': str(metric_crs),
        'discrepancies': len(points), 'outside': len(outside), 'inside_other_codes': len(points)-len(outside),
        'outside_distance_buckets': {str(k): int(v) for k,v in buckets.value_counts(sort=False).items()},
        'outside_distance_m': {str(k): float(v) for k,v in outside.distance_to_study_area_m.describe().items()},
        'outside_in_other_state_ageb_2020': int(outside.containing_state_ageb_2020.ne('').sum()),
        'outside_declared_ageb_not_in_2020': int((~outside.declared_ageb_exists_2020).sum()),
        'inside_other_codes_localities': points.loc[points.case.eq('declared_outside_spatially_inside')].groupby(
             ['cve_mun','cve_loc','localidad']).size().reset_index(name='count').to_dict(orient='records'),
        'positive_area_overlap_pairs': len(overlap_rows),
        'overlap_pairs_over_1m2': sum(x['overlap_m2'] > 1 for x in overlap_rows),
        'overlap_total_pairwise_m2': sum(x['overlap_m2'] for x in overlap_rows),
        'limitations': ['Distances are projected approximations, not evidence of source accuracy.',
                       'No source coordinates or prior assignments were changed.',
                       'Overlap audit does not prove absence of gaps or complete territorial coverage.',
                       'No cause is established without another vintage or positional evidence.']}
    assert len(points) == len(discrepancy)
    assert sum(report['outside_distance_buckets'].values()) == len(outside)
    fields = ['id','case','cve_mun','cve_loc','localidad','ageb','declared_ageb_key',
              'declared_ageb_exists_2020','CVEGEO','containing_state_ageb_2020','nearest_selected_ageb',
              'distance_to_study_area_m','distance_to_study_boundary_m']
    points[fields].to_csv(out / 'discrepancy_audit.csv', index=False)
    pd.DataFrame(overlap_rows, columns=['left','right','overlap_m2']).to_csv(out / 'polygon_overlaps.csv', index=False)
    (out / 'discrepancy_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, default=ROOT / 'config/merida.json')
    run(parser.parse_args().config.resolve())
