"""Local configuration and checksum-verified transactional migrations."""
import hashlib, os
from pathlib import Path
import psycopg
ROOT=Path(__file__).resolve().parents[1]

def settings():
    values={}
    p=ROOT/'.env'
    if p.exists():
        for line in p.read_text(encoding='utf-8-sig').splitlines():
            if line.strip() and not line.lstrip().startswith('#') and '=' in line:
                key,value=line.split('=',1);values[key.strip()]=value.strip()
    def get(key,default=None):return os.environ.get(key,values.get(key,default))
    password=get('POSTGRES_PASSWORD')
    if not password or password=='replace_with_local_password':raise ValueError('Set a local POSTGRES_PASSWORD in .env')
    return dict(host=get('POSTGRES_HOST','127.0.0.1'),port=int(get('POSTGRES_PORT','5433')),
                dbname=get('POSTGRES_DB','urban_intelligence'),user=get('POSTGRES_USER','urban'),
                password=password,connect_timeout=10,application_name='datahouseware_etl')

def connect():return psycopg.connect(**settings())

def migrate():
    applied=[]
    with connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(20431003)')
        conn.execute('CREATE SCHEMA IF NOT EXISTS meta')
        conn.execute('CREATE TABLE IF NOT EXISTS meta.schema_migration (name text PRIMARY KEY, sha256 text NOT NULL, applied_at timestamptz NOT NULL DEFAULT now())')
        for path in sorted((ROOT/'sql/migrations').glob('*.sql')):
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            found=conn.execute('SELECT sha256 FROM meta.schema_migration WHERE name=%s',(path.name,)).fetchone()
            if found:
                if found[0]!=digest:raise ValueError('Applied migration changed: '+path.name)
                continue
            conn.execute(path.read_text(encoding='utf-8'))
            conn.execute('INSERT INTO meta.schema_migration(name,sha256) VALUES (%s,%s)',(path.name,digest))
            applied.append(path.name)
    return applied

if __name__=='__main__':print('Applied migrations:',migrate())
