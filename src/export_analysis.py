"""Example consumer: export analytical views and geometry ONLY from the DW."""
import argparse,json,hashlib
from datetime import datetime,timezone
from psycopg import sql
from database import ROOT,connect

def export(dataset):
    output=ROOT/'outputs/cdmx/phase3_inputs'/str(dataset);output.mkdir(parents=True,exist_ok=True)
    with connect() as conn:
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        info=conn.execute('SELECT name,fingerprint,rule_version FROM dw.dataset WHERE dataset_id=%s',(dataset,)).fetchone()
        if not info:raise ValueError('Unknown dataset_id')
        for name in ['kpi_ageb','age_distribution','crime_by_type_month']:
            query=sql.SQL('COPY (SELECT * FROM analytics.{} WHERE dataset_id=%s ORDER BY geography_id) TO STDOUT WITH (FORMAT CSV, HEADER TRUE)').format(sql.Identifier(name))
            with conn.cursor().copy(query,(dataset,)) as copy,(output/(name+'.csv')).open('wb') as f:
                for chunk in copy:f.write(chunk)
        geo=conn.execute("SELECT jsonb_build_object('type','FeatureCollection','features',jsonb_agg(jsonb_build_object('type','Feature','geometry',ST_AsGeoJSON(geom)::jsonb,'properties',jsonb_build_object('dataset_id',dataset_id,'geography_id',geography_id,'CVEGEO',cvegeo)) ORDER BY geography_id)) FROM dw.dim_geography WHERE dataset_id=%s",(dataset,)).fetchone()[0]
        (output/'areas.geojson').write_text(json.dumps(geo),encoding='utf-8')
    paths=[output/(n+'.csv') for n in ['kpi_ageb','age_distribution','crime_by_type_month']]+[output/'areas.geojson']
    manifest={'dataset_id':dataset,'name':info[0],'fingerprint':info[1],'rule_version':info[2],
              'exported_utc':datetime.now(timezone.utc).isoformat(),'origin':'PostgreSQL dw and analytics; no raw or phase1 outputs read',
              'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dataset-id',required=True,type=int);args=p.parse_args();export(args.dataset_id)
