"""Distance-to-assigned-boundary scenarios, not measured positional error."""
import json, hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from assess_geography import read_csv_zip
ROOT=Path(__file__).resolve().parents[1]

def summarize(distances):
    return {str(r): {'rows':int(np.sum(distances<=r)), 'percent':float(np.mean(distances<=r)*100)} for r in (10,25,50,100)}

def run():
    out=ROOT/'outputs/cdmx/phase1'
    cfg=json.loads((ROOT/'config/cdmx.json').read_text(encoding='utf-8'))
    baseline=json.loads((out/'quality_report.json').read_text(encoding='utf-8'))
    for key,digest in baseline['sha256'].items():
        assert hashlib.sha256((ROOT/cfg['sources'][key]).read_bytes()).hexdigest()==digest
    crime_report=json.loads((out/'crime_quality_report.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((ROOT/cfg['crime']['path']).read_bytes()).hexdigest()==crime_report['source_sha256']
    assert hashlib.sha256((out/'areas.geojson').read_bytes()).hexdigest()==crime_report['areas_sha256']
    areas=gpd.read_file(out/'areas.geojson').to_crs(32614).set_index('CVEGEO')
    report={'source_sha256':baseline['sha256'],'crime_sha256':crime_report['source_sha256'],
            'method':'Distance to boundary of assigned polygon in EPSG:32614; illustrative radii, not known errors; no relocation or reassignment', 'samples':{}}
    for name in ('business','crime'):
        if name=='business':
            raw=read_csv_zip(ROOT/cfg['sources']['businesses'],cfg['business_encoding']); identifier='id'
            chosen=pd.read_csv(out/'business_assignment.csv',dtype=str,keep_default_na=False)
            chosen=chosen.loc[chosen.assignment_status.eq('assigned')]
        else:
            raw=pd.read_csv(ROOT/cfg['crime']['path'],dtype=str,keep_default_na=False);identifier='_id'
            chosen=pd.read_csv(out/'crime_eligibility.csv',dtype=str,keep_default_na=False)
            chosen=chosen.loc[chosen.spatial_candidate.eq('True')]
        f=chosen[[identifier,'CVEGEO']].merge(raw[[identifier,'longitud','latitud']],on=identifier,validate='one_to_one')
        points=gpd.GeoSeries(gpd.points_from_xy(pd.to_numeric(f.longitud),pd.to_numeric(f.latitud)),crs=4326).to_crs(32614)
        boundaries=areas.geometry.boundary.reindex(f.CVEGEO).to_numpy()
        distance=shapely.distance(points.to_numpy(),boundaries)
        if not np.isfinite(distance).all():raise ValueError('Invalid distance')
        f['boundary_distance_m']=distance
        f[[identifier,'CVEGEO','boundary_distance_m']].to_csv(out/(name+'_boundary_sensitivity.csv'),index=False)
        report['samples'][name]={'rows':len(f),'near_boundary':summarize(distance)}
        table=f.groupby('CVEGEO').agg(rows=(identifier,'size'),median_distance_m=('boundary_distance_m','median'))
        table.to_csv(out/(name+'_boundary_by_ageb.csv'))
    (out/'spatial_sensitivity.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report['samples'],indent=2))
if __name__=='__main__':run()
