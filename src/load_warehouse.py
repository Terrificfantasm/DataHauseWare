"""Load one immutable CDMX dataset from verified originals in one transaction."""
import argparse,hashlib,json,time
from pathlib import Path
import geopandas as gpd
import pandas as pd
from psycopg.types.json import Jsonb
from psycopg import ClientCursor
from database import ROOT,connect,migrate
from assess_geography import read_csv_zip,select_scope,normalize_business_keys

RULE='candidate-v1'

def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def inputs():
    cfg=json.loads((ROOT/'config/cdmx.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'docs/cdmx_acquisition.json').read_text(encoding='utf-8'))
    bypath={x['path'].replace('\\','/'):x for x in manifest}
    sources={}
    for role in ('census','boundaries','businesses','crime'):
        rel=cfg['crime']['path'] if role=='crime' else cfg['sources'][role]
        entry=bypath[rel]
        if digest(ROOT/rel)!=entry['sha256']:raise ValueError('Input hash mismatch: '+role)
        sources[role]=entry
    if cfg['id']!='cdmx' or cfg['business_release']!='2020-11' or cfg['census_year']!=2020 or cfg['boundary_year']!=2020:
        raise ValueError('Loader only supports validated CDMX 2020 snapshot')
    codefiles=[Path(__file__),ROOT/'src/assess_geography.py',ROOT/'src/validate_warehouse.py',ROOT/'sql/etl/load_cdmx.sql']+sorted((ROOT/'sql/migrations').glob('*.sql'))
    codehash=hashlib.sha256(''.join(str(p.relative_to(ROOT))+digest(p) for p in codefiles).encode()).hexdigest()
    descriptor={'config':cfg,'sources':{k:v['sha256'] for k,v in sources.items()},'rule':RULE,'pipeline_sha256':codehash}
    fingerprint=hashlib.sha256(json.dumps(descriptor,sort_keys=True).encode()).hexdigest()
    return cfg,sources,codehash,fingerprint

def source_frame(role,cfg):
    if role=='census':
        f=read_csv_zip(ROOT/cfg['sources'][role]);f=select_scope(f,cfg,'ENTIDAD','MUN','LOC')
        f=f.loc[f.MZA.eq('000') & f.AGEB.ne('0000')].copy()
        keys=f.ENTIDAD+f.MUN+f.LOC+f.AGEB
    elif role=='businesses':
        f=read_csv_zip(ROOT/cfg['sources'][role],cfg.get('business_encoding'))
        normalize_business_keys(f) # Validate declared keys; raw payload retains original spelling.
        keys=f.id
    else:
        f=pd.read_csv(ROOT/cfg['crime']['path'],dtype=str,keep_default_na=False,encoding='utf-8-sig');keys=f._id
    if keys.eq('').any() or keys.duplicated().any():raise ValueError('Missing or duplicated source key: '+role)
    return f,keys

def load(fail_after_stage=False):
    migrate();cfg,sources,codehash,fingerprint=inputs()
    with connect() as conn:
        run_id=conn.execute("INSERT INTO meta.etl_run(fingerprint,status) VALUES (%s,'running') RETURNING run_id",(fingerprint,)).fetchone()[0]
    started=time.monotonic()
    try:
        with connect() as conn:
            conn.execute('SELECT pg_advisory_xact_lock(20431004)')
            found=conn.execute('SELECT dataset_id FROM dw.dataset WHERE fingerprint=%s',(fingerprint,)).fetchone()
            from validate_warehouse import validate
            if found:
                report=validate(conn,found[0]);report['idempotent_skip']=True
            else:
                dataset=conn.execute('INSERT INTO dw.dataset(fingerprint,name,territory,cohort_year,rule_version,configuration,pipeline_sha256) VALUES (%s,%s,%s,2020,%s,%s,%s) RETURNING dataset_id',
                  (fingerprint,'CDMX urbano 2020','09',RULE,Jsonb(cfg),codehash)).fetchone()[0]
                ids={'dataset_id':dataset}
                labels={'census':'Censo 2020','boundaries':'Marco 2020','businesses':'DENUE 2020-11 / SCIAN 2018','crime':'FGJ inicio 2020, export 2026-09-30'}
                for role,e in sources.items():
                    conn.execute('INSERT INTO dw.dim_source_release(kind,sha256,url,local_path,release_label) VALUES (%s,%s,%s,%s,%s) ON CONFLICT(kind,sha256) DO NOTHING',
                      (role,e['sha256'],e['url'],e['path'].replace('\\','/'),labels[role]))
                    sid=conn.execute('SELECT source_id FROM dw.dim_source_release WHERE kind=%s AND sha256=%s',(role,e['sha256'])).fetchone()[0]
                    ids[role]=sid;conn.execute('INSERT INTO dw.dataset_source VALUES (%s,%s,%s)',(dataset,role,sid))
                path=(ROOT/cfg['sources']['boundaries']).as_posix()
                areas=gpd.read_file('/vsizip/'+path+'/'+cfg['sources']['boundary_member'])
                areas=select_scope(areas,cfg,'CVE_ENT','CVE_MUN','CVE_LOC').to_crs(4326)
                if len(areas)!=2431 or areas.CVEGEO.duplicated().any():raise ValueError('Unexpected geographic scope')
                conn.execute('CREATE TEMP TABLE incoming_geography(cvegeo text, wkb bytea) ON COMMIT DROP')
                with conn.cursor().copy('COPY incoming_geography FROM STDIN') as copy:
                    for key,geom in zip(areas.CVEGEO,areas.geometry):copy.write_row((key,geom.wkb))
                conn.execute("INSERT INTO dw.dim_geography(dataset_id,cvegeo,boundary_year,geom,area_km2) SELECT %s,cvegeo,2020,ST_Multi(ST_GeomFromWKB(wkb,4326)),ST_Area(ST_GeomFromWKB(wkb,4326)::geography)/1000000 FROM incoming_geography",(dataset,))
                conn.execute("INSERT INTO staging.source_record SELECT %s,%s,cvegeo,jsonb_build_object('CVEGEO',cvegeo,'boundary_year',2020) FROM incoming_geography",(dataset,ids['boundaries']))
                for role in ('census','businesses','crime'):
                    frame,keys=source_frame(role,cfg)
                    print('Staging',role,len(frame),flush=True)
                    with conn.cursor().copy('COPY staging.source_record(dataset_id,source_id,record_key,raw) FROM STDIN') as copy:
                        columns=list(frame.columns)
                        for key,row in zip(keys,frame.itertuples(index=False,name=None)):
                            copy.write_row((dataset,ids[role],key,Jsonb(dict(zip(columns,row)))))
                if fail_after_stage:raise RuntimeError('Injected failure after staging; transaction must roll back')
                print('Transforming in PostGIS...',flush=True)
                with ClientCursor(conn) as cursor:
                    cursor.execute((ROOT/'sql/etl/load_cdmx.sql').read_text(encoding='utf-8'),ids)
                report=validate(conn,dataset);report['idempotent_skip']=False
            report.update(run_id=run_id,fingerprint=fingerprint,elapsed_seconds=round(time.monotonic()-started,2))
            conn.execute("UPDATE meta.etl_run SET status=%s,finished_at=now(),report=%s WHERE run_id=%s",('skipped' if found else 'succeeded',Jsonb(report),run_id))
        output=ROOT/'outputs/cdmx/phase2';output.mkdir(parents=True,exist_ok=True)
        (output/'load_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report,indent=2));return report
    except Exception as exc:
        with connect() as conn:
            conn.execute("UPDATE meta.etl_run SET status='failed',finished_at=now(),error_type=%s WHERE run_id=%s",(type(exc).__name__,run_id))
        raise

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--fail-after-stage',action='store_true',help='Failure injection for isolated test database only')
    args=parser.parse_args()
    if args.fail_after_stage:
        from database import settings
        if not settings()['dbname'].endswith('_test'):raise ValueError('Failure injection requires database name ending _test')
    load(args.fail_after_stage)
