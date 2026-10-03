"""Fixed-source reconciliation gate for the closed Phase 1 scope."""
import argparse,json
from database import connect

EXPECTED={'areas':2431,'population_rows':2431,'population':9138524,'business_rows':474328,
          'business_assigned':472608,'crime_rows':204121,'crime_assigned':194356,
          'crime_candidates':199650,'crime_candidates_assigned':191233,'census_without_polygon':2,
          'population_zero':17,'invalid_occurred_dates':43,'occurred_after_start':1,
          'noncriminal':3810,'incompetence':661,'repeated_public_rows':679}

def validate(conn,dataset):
    queries={
      'areas':"SELECT count(*) FROM dw.dim_geography WHERE dataset_id=%s",
      'population_rows':"SELECT count(*) FROM dw.fact_population WHERE dataset_id=%s",
      'population':"SELECT sum(pobtot) FROM dw.fact_population WHERE dataset_id=%s",
      'business_rows':"SELECT count(*) FROM dw.fact_business_snapshot WHERE dataset_id=%s",
      'business_assigned':"SELECT count(*) FROM dw.fact_business_snapshot WHERE dataset_id=%s AND assignment_status='assigned'",
      'crime_rows':"SELECT count(*) FROM dw.fact_crime_record WHERE dataset_id=%s",
      'crime_assigned':"SELECT count(*) FROM dw.fact_crime_record WHERE dataset_id=%s AND assignment_status='assigned'",
      'crime_candidates':"SELECT count(*) FROM dw.fact_crime_record WHERE dataset_id=%s AND is_candidate",
      'crime_candidates_assigned':"SELECT count(*) FROM dw.fact_crime_record WHERE dataset_id=%s AND is_candidate AND assignment_status='assigned'",
      'census_without_polygon':"SELECT count(*) FROM meta.quality_issue WHERE dataset_id=%s AND issue_code='census_without_polygon'",
      'population_zero':"SELECT count(*) FROM dw.fact_population WHERE dataset_id=%s AND pobtot=0",
      'invalid_occurred_dates':"SELECT count(*) FROM dw.fact_crime_record WHERE dataset_id=%s AND invalid_occurred_date",
      'occurred_after_start':"SELECT count(*) FROM dw.fact_crime_record WHERE dataset_id=%s AND occurred_after_start",
      'noncriminal':"SELECT count(*) FROM dw.fact_crime_record WHERE dataset_id=%s AND eligibility_reason='excluded_noncriminal'",
      'incompetence':"SELECT count(*) FROM dw.fact_crime_record WHERE dataset_id=%s AND eligibility_reason='excluded_incompetence'",
      'repeated_public_rows':"SELECT count(*) FROM meta.quality_issue WHERE dataset_id=%s AND issue_code='duplicate_public_attributes_not_deduplicated'"}
    actual={name:int(conn.execute(query,(dataset,)).fetchone()[0]) for name,query in queries.items()}
    wrong={k:{'expected':v,'actual':actual[k]} for k,v in EXPECTED.items() if actual[k]!=v}
    if wrong:raise ValueError('Warehouse reconciliation failed: '+json.dumps(wrong))
    years=conn.execute('SELECT DISTINCT extract(year FROM started_on)::int FROM dw.fact_crime_record WHERE dataset_id=%s',(dataset,)).fetchall()
    if years!=[(2020,)]:raise ValueError('Wrong initiation cohort')
    stages=dict(conn.execute('SELECT ds.role,count(*) FROM staging.source_record s JOIN dw.dataset_source ds USING(dataset_id,source_id) WHERE s.dataset_id=%s GROUP BY ds.role',(dataset,)).fetchall())
    if stages!={'census':2433,'boundaries':2431,'businesses':474328,'crime':204121}:raise ValueError('Staging counts differ')
    statuses={}
    for table in ('fact_business_snapshot','fact_crime_record'):
        from psycopg import sql
        statuses[table]=dict(conn.execute(sql.SQL('SELECT assignment_status,count(*) FROM dw.{} WHERE dataset_id=%s GROUP BY assignment_status').format(sql.Identifier(table)),(dataset,)).fetchall())
    return {'dataset_id':dataset,'checks_passed':len(EXPECTED)+2,'counts':actual,'staging':stages,'spatial_statuses':statuses}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dataset-id',required=True,type=int);a=p.parse_args()
    with connect() as c:print(json.dumps(validate(c,a.dataset_id),indent=2))
