"""List immutable datasets without assuming their surrogate IDs."""
import json
from database import connect
if __name__=='__main__':
    with connect() as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        rows=conn.execute('SELECT dataset_id,name,fingerprint,rule_version,created_at::text FROM dw.dataset ORDER BY dataset_id').fetchall()
    print(json.dumps([dict(zip(['dataset_id','name','fingerprint','rule_version','created_at'],row)) for row in rows],indent=2))
