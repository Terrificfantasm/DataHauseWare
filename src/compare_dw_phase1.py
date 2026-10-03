"""Read-only row-level parity check; diagnostics are reference evidence, not ETL inputs."""
import argparse,json
import pandas as pd
from database import ROOT,connect

def run(dataset):
    output=ROOT/'outputs/cdmx/phase1'
    result={'dataset_id':dataset,'checks':{}}
    with connect() as conn:
        for role,table,key in [('business','fact_business_snapshot','id'),('crime','fact_crime_record','_id')]:
            reference=pd.read_csv(output/(role+'_assignment.csv'),dtype=str,keep_default_na=False)
            from psycopg import sql
            records=conn.execute(sql.SQL("SELECT f.record_key,coalesce(g.cvegeo,''),f.assignment_status FROM dw.{} f LEFT JOIN dw.dim_geography g ON g.dataset_id=f.dataset_id AND g.geography_id=f.geography_id WHERE f.dataset_id=%s ORDER BY f.record_key").format(sql.Identifier(table)),(dataset,)).fetchall()
            actual=pd.DataFrame(records,columns=[key,'CVEGEO','assignment_status']).set_index(key).sort_index()
            expected=reference.set_index(key)[['CVEGEO','assignment_status']].sort_index()
            if not actual.equals(expected):
                if not actual.index.equals(expected.index):raise ValueError('Different row keys: '+role)
                raise ValueError('Different assignments: '+role+' '+str(int(actual.ne(expected).any(axis=1).sum())))
            result['checks'][role+'_assignments_equal']=len(actual)
        reference=pd.read_csv(output/'crime_eligibility.csv',dtype=str,keep_default_na=False).set_index('_id').sort_index()
        records=conn.execute('SELECT record_key,eligibility_reason,is_candidate FROM dw.fact_crime_record WHERE dataset_id=%s ORDER BY record_key',(dataset,)).fetchall()
        actual=pd.DataFrame(records,columns=['_id','eligibility_reason','candidate']).set_index('_id').sort_index()
        if not actual.eligibility_reason.equals(reference.eligibility_reason) or not actual.candidate.equals(reference.candidate.eq('True')):
            raise ValueError('Different eligibility')
        result['checks']['crime_eligibility_equal']=len(actual)
    out=ROOT/'outputs/cdmx/phase2';out.mkdir(parents=True,exist_ok=True)
    (out/'parity_report.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--dataset-id',type=int,required=True)
    run(parser.parse_args().dataset_id)
