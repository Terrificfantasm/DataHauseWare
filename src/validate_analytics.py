"""Validate analytical contracts and independent aggregations from the DW."""
import argparse,json
from database import ROOT,connect

def validate(conn,dataset):
    queries={
      'ageb_rows':('SELECT count(*) FROM analytics.kpi_ageb WHERE dataset_id=%s',2431),
      'population_sum':('SELECT sum(population) FROM analytics.kpi_ageb WHERE dataset_id=%s',9138524),
      'business_sum':('SELECT sum(business_count) FROM analytics.kpi_ageb WHERE dataset_id=%s',472608),
      'crime_sum':('SELECT sum(crime_record_count) FROM analytics.kpi_ageb WHERE dataset_id=%s',191233),
      'population_null_ratios':("SELECT count(*) FROM analytics.kpi_ageb WHERE dataset_id=%s AND population=0 AND businesses_per_1000 IS NULL AND crime_records_per_1000 IS NULL",17),
      'business_null_ratios':("SELECT count(*) FROM analytics.kpi_ageb WHERE dataset_id=%s AND business_count=0 AND crime_records_per_100_businesses IS NULL AND dominant_sectors IS NULL",12),
      'dominant_ties':('SELECT count(*) FROM analytics.kpi_ageb WHERE dataset_id=%s AND cardinality(dominant_sectors)>1',77),
      'age_groups':('SELECT count(*) FROM analytics.age_distribution WHERE dataset_id=%s',2431*8),
      'derived_age_missing':("SELECT count(*) FROM analytics.age_distribution WHERE dataset_id=%s AND age_group='25-59' AND population IS NULL",20),
      'monthly_type_sum':('SELECT sum(crime_record_count) FROM analytics.crime_by_type_month WHERE dataset_id=%s',191233),
      'retail_sum':('SELECT sum(retail_count) FROM analytics.business_by_ageb WHERE dataset_id=%s',202829)}
    actual={name:int(conn.execute(q,(dataset,)).fetchone()[0]) for name,(q,_) in queries.items()}
    wrong={name:{'actual':actual[name],'expected':expected} for name,(_,expected) in queries.items() if actual[name]!=expected}
    if wrong:raise ValueError('Analytics mismatch: '+json.dumps(wrong))
    return {'dataset_id':dataset,'checks_passed':len(queries),'counts':actual}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dataset-id',required=True,type=int);a=p.parse_args()
    with connect() as c:r=validate(c,a.dataset_id)
    out=ROOT/'outputs/cdmx/phase2';out.mkdir(parents=True,exist_ok=True)
    (out/'analytics_report.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r,indent=2))
