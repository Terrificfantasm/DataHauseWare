"""Synthetic bounded jitter scenarios. Never estimates actual geocoding error."""
import json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from assess_geography import read_csv_zip
ROOT=Path(__file__).resolve().parents[1]
RADII=(10,25,50,100)
SEEDS=tuple(range(20260930,20260940))

def offsets(n,radius,seed):
    rng=np.random.default_rng(seed)
    angle=rng.uniform(0,2*np.pi,n)
    length=radius*np.sqrt(rng.uniform(0,1,n))
    return length*np.cos(angle),length*np.sin(angle)

def locate(tree,x,y):
    pairs=tree.query(shapely.points(x,y),predicate='intersects')
    count=np.bincount(pairs[0],minlength=len(x))
    answer=np.full(len(x),-1,dtype=int)
    single=count[pairs[0]]==1
    answer[pairs[0,single]]=pairs[1,single]
    answer[count>1]=-2
    return answer

def counts(labels,n):
    return np.bincount(labels[labels>=0],minlength=n)

def run():
    folder=ROOT/'outputs/cdmx/phase1';out=folder/'simulations';out.mkdir(exist_ok=True)
    cfg=json.loads((ROOT/'config/cdmx.json').read_text(encoding='utf-8'))
    base=json.loads((folder/'quality_report.json').read_text(encoding='utf-8'))
    crime=json.loads((folder/'crime_quality_report.json').read_text(encoding='utf-8'))
    if cfg!=base['territory']:raise ValueError('Changed config')
    for key,digest in base['sha256'].items():
        if hashlib.sha256((ROOT/cfg['sources'][key]).read_bytes()).hexdigest()!=digest:raise ValueError('Changed source')
    if hashlib.sha256((ROOT/cfg['crime']['path']).read_bytes()).hexdigest()!=crime['source_sha256']:raise ValueError('Changed crime source')
    if hashlib.sha256((folder/'areas.geojson').read_bytes()).hexdigest()!=crime['areas_sha256']:raise ValueError('Changed areas')
    areas=gpd.read_file(folder/'areas.geojson').sort_values('CVEGEO').reset_index(drop=True).to_crs(32614)
    tree=shapely.STRtree(areas.geometry.to_numpy()); n=len(areas)
    lookup=dict(zip(areas.CVEGEO,range(n)))
    municipality=pd.factorize(areas.CVEGEO.str[:5],sort=True)[0]
    summaries=[];all_runs=[];cohorts={}
    for name in ('crime','business'):
        if name=='crime':
            raw=pd.read_csv(ROOT/cfg['crime']['path'],dtype=str,keep_default_na=False);identifier='_id'
            a=pd.read_csv(folder/'crime_eligibility.csv',dtype=str,keep_default_na=False)
            a=a.loc[a.candidate.eq('True')]
        else:
            raw=read_csv_zip(ROOT/cfg['sources']['businesses'],cfg['business_encoding']);identifier='id'
            a=pd.read_csv(folder/'business_assignment.csv',dtype=str,keep_default_na=False)
        merged=a[[identifier,'CVEGEO','assignment_status']].merge(raw[[identifier,'longitud','latitud']],on=identifier,validate='one_to_one')
        x=pd.to_numeric(merged.longitud,errors='coerce');y=pd.to_numeric(merged.latitud,errors='coerce')
        valid=x.between(-180,180)&y.between(-90,90)&~(x.eq(0)&y.eq(0))
        f=merged.loc[valid].reset_index(drop=True)
        points=gpd.GeoSeries(gpd.points_from_xy(x[valid],y[valid]),crs=4326).to_crs(32614)
        px=points.x.to_numpy();py=points.y.to_numpy()
        initial=locate(tree,px,py)
        expected=f.CVEGEO.map(lookup).fillna(-1).astype(int).to_numpy(copy=True)
        expected[f.assignment_status.eq('ambiguous')]=-2
        if not np.array_equal(initial,expected):raise ValueError('Projected baseline differs from stored assignment')
        original=counts(initial,n); original_mun=np.bincount(municipality,weights=original)
        cohorts[name]={'source_rows':len(merged),'valid_points':len(f),'invalid_unperturbed':int((~valid).sum()),'initial_assigned':int((initial>=0).sum()),'initial_outside':int((initial==-1).sum())}
        for radius in RADII:
            simulations=[];metrics=[]
            for seed in SEEDS:
                dx,dy=offsets(len(f),radius,seed)
                labels=locate(tree,px+dx,py+dy);current=counts(labels,n)
                simulations.append(current)
                delta=np.abs(current-original)
                current_mun=np.bincount(municipality,weights=current)
                row={'source':name,'radius_m':radius,'seed':seed,
                     'changed_initially_assigned':int(((initial>=0)&(initial!=labels)).sum()),
                     'moved_to_other_ageb':int(((initial>=0)&(labels>=0)&(initial!=labels)).sum()),
                     'exits':int(((initial>=0)&(labels<0)).sum()),
                     'entries':int(((initial<0)&(labels>=0)).sum()),
                     'outside':int((labels==-1).sum()),'ambiguous':int((labels==-2).sum()),
                     'count_l1_percent':float(delta.sum()/original.sum()*100),
                     'municipal_urban_l1_percent':float(np.abs(current_mun-original_mun).sum()/original.sum()*100),
                     'ageb_rank_correlation':float(pd.Series(original).rank().corr(pd.Series(current).rank())),
                     'ageb_abs_change_ge_20pct_baseline_ge20':int(((original>=20)&(delta>=0.2*original)).sum())}
                if current.sum()!=np.sum(labels>=0):raise ValueError('Count mismatch')
                metrics.append(row);all_runs.append(row)
            matrix=np.asarray(simulations)
            per=areas[['CVEGEO']].copy();per['baseline']=original
            per['mean']=matrix.mean(axis=0);per['min']=matrix.min(axis=0);per['max']=matrix.max(axis=0)
            per['mean_absolute_change']=np.abs(matrix-original).mean(axis=0)
            per.to_csv(out/f'{name}_{radius}m_ageb.csv',index=False)
            m=pd.DataFrame(metrics)
            summary={'source':name,'radius_m':radius,'repetitions':len(SEEDS)}
            for col in m.columns[3:]:
                summary[col+'_mean']=float(m[col].mean());summary[col+'_min']=float(m[col].min());summary[col+'_max']=float(m[col].max())
            summary['changed_initially_assigned_percent_mean']=summary['changed_initially_assigned_mean']/cohorts[name]['initial_assigned']*100
            summaries.append(summary)
            pd.DataFrame(all_runs).to_csv(out/'runs.csv',index=False)
            print(name,radius,'changed %',round(summary['changed_initially_assigned_percent_mean'],2),'L1 %',round(summary['count_l1_percent_mean'],2),flush=True)
    report={'method':'Independent uniform disk jitter in EPSG:32614; paired seeds across radii; synthetic scenarios, not error estimates',
            'seeds':SEEDS,'radii_m':RADII,'source_sha256':base['sha256'],'crime_sha256':crime['source_sha256'],
            'derived_sha256':{name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in ['crime_eligibility.csv','business_assignment.csv','areas.geojson']},
            'cohorts':cohorts,'summaries':summaries,
            'limitations':['Ten repetitions are exploratory, not a convergence study','Independent isotropic displacements omit correlated/systematic errors','Invalid coordinates remain excluded; valid initially outside points can enter','Municipal aggregates cover only selected urban AGEB, not entire municipalities','L1 sums absolute count changes, so between-area transfers contribute twice; not percent of mislocated records','Rank correlation measures count ranking only, not rates, LISA or causality']}
    (out/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
if __name__=='__main__':run()
