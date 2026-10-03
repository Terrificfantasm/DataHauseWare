"""Version analytics separately: changing views must not reload source facts."""
import hashlib
from database import ROOT,connect,migrate

def publish():
    migrate();applied=[]
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(20431003)')
        for path in sorted((ROOT/'sql/analytics').glob('*.sql')):
            name='analytics/'+path.name;digest=hashlib.sha256(path.read_bytes()).hexdigest()
            previous=conn.execute('SELECT sha256 FROM meta.schema_migration WHERE name=%s',(name,)).fetchone()
            if previous:
                if previous[0]!=digest:raise ValueError('Applied analytics migration changed: '+name)
                continue
            conn.execute(path.read_text(encoding='utf-8'))
            conn.execute('INSERT INTO meta.schema_migration(name,sha256) VALUES (%s,%s)',(name,digest));applied.append(name)
    return applied

if __name__=='__main__':print('Published analytics:',publish())
