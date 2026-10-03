"""Opt-in tests against a dedicated database; never run them in the working DW."""
import os,sys
from pathlib import Path
import pytest
import psycopg
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import database

@pytest.fixture(scope='module')
def test_database():
    name=os.environ.get('DW_TEST_DATABASE')
    if not name:pytest.skip('Set DW_TEST_DATABASE to a dedicated *_test database')
    if not name.endswith('_test'):raise ValueError('Integration database name must end _test')
    previous=os.environ.get('POSTGRES_DB')
    os.environ['POSTGRES_DB']=name
    database.migrate()
    from publish_analytics import publish
    publish()
    yield name
    if previous is None:os.environ.pop('POSTGRES_DB',None)
    else:os.environ['POSTGRES_DB']=previous

@pytest.fixture
def conn(test_database):
    with database.connect() as c:
        yield c
        c.rollback()

def test_migration_repeat_is_noop(test_database):
    assert database.migrate()==[]

def test_reserved_is_null_zero_is_zero_and_bad_token_fails(conn):
    assert conn.execute("SELECT staging.census_integer('*'),staging.census_integer(''),staging.census_integer('0'),staging.census_integer('12')").fetchone()==(None,None,0,12)
    with pytest.raises(psycopg.errors.RaiseException):
        with conn.transaction():conn.execute("SELECT staging.census_integer('not a number')")

def test_invalid_dates_and_coordinates_are_quarantined(conn):
    assert conn.execute("SELECT staging.iso_date('2020-02-30'),staging.iso_date('NA'),staging.iso_date('2020-02-29')::text").fetchone()==(None,None,'2020-02-29')
    for x,y in [('NaN','19'),('Infinity','19'),('NA','19'),('181','19'),('0','0')]:
        assert conn.execute('SELECT staging.wgs84_point(%s,%s) IS NULL',(x,y)).fetchone()[0]
    assert conn.execute("SELECT ST_SRID(staging.wgs84_point('-99','19'))").fetchone()[0]==4326

def dataset(conn,letter):
    return conn.execute("INSERT INTO dw.dataset(fingerprint,name,territory,cohort_year,rule_version,configuration,pipeline_sha256) VALUES (%s,'test','09',2020,'candidate-v1','{}',%s) RETURNING dataset_id",(letter*64,'a'*64)).fetchone()[0]

def test_cross_dataset_geography_cannot_link_to_population(conn):
    first=dataset(conn,'b');second=dataset(conn,'c')
    source=conn.execute("INSERT INTO dw.dim_source_release(kind,sha256,url,local_path,release_label) VALUES ('census',%s,'https://example.invalid','test','test') RETURNING source_id",('b'*64,)).fetchone()[0]
    conn.execute("INSERT INTO dw.dataset_source VALUES (%s,'census',%s)",(first,source))
    conn.execute("INSERT INTO staging.source_record VALUES (%s,%s,'row','{}')",(first,source))
    geo=conn.execute("INSERT INTO dw.dim_geography(dataset_id,cvegeo,boundary_year,geom,area_km2) VALUES (%s,'0900100010010',2020,ST_Multi(ST_MakeEnvelope(-100,19,-99,20,4326)),1) RETURNING geography_id",(second,)).fetchone()[0]
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        with conn.transaction():
            conn.execute("INSERT INTO dw.fact_population(dataset_id,geography_id,source_id,record_key,census_year,pobtot) VALUES (%s,%s,%s,'row',2020,10)",(first,geo,source))

def test_shared_boundary_remains_ambiguous(conn):
    # Same ST_Intersects predicate as the real ETL; no arbitrary first match.
    n=conn.execute("SELECT count(*) FROM (VALUES(ST_MakeEnvelope(0,0,1,1,4326)),(ST_MakeEnvelope(1,0,2,1,4326))) a(g) WHERE ST_Intersects(g,ST_SetSRID(ST_Point(1,.5),4326))").fetchone()[0]
    assert n==2

def test_transaction_failure_leaves_no_dataset(test_database):
    with pytest.raises(RuntimeError):
        with database.connect() as c:
            dataset(c,'d')
            raise RuntimeError('injected')
    with database.connect() as c:
        assert c.execute('SELECT count(*) FROM dw.dataset WHERE fingerprint=%s',('d'*64,)).fetchone()[0]==0

def test_applied_migration_change_rejected(test_database,tmp_path,monkeypatch):
    folder=tmp_path/'sql/migrations';folder.mkdir(parents=True)
    (folder/'001_warehouse.sql').write_text('-- changed migration',encoding='utf-8')
    monkeypatch.setattr(database,'ROOT',tmp_path)
    # Keep credentials in the existing connection settings rather than a fake .env.
    monkeypatch.setattr(database,'connect',lambda: psycopg.connect(**test_applied_migration_change_rejected.credentials))
    with pytest.raises(ValueError,match='Applied migration changed'):database.migrate()

# Fixture snapshots credentials only in process memory; never logs or serializes them.
@pytest.fixture(autouse=True)
def remember_connection(test_database):
    test_applied_migration_change_rejected.credentials=database.settings()


def test_analytics_repeat_is_noop(test_database):
    from publish_analytics import publish
    assert publish()==[]

def test_analytics_aggregates_facts_before_joining(conn):
    ds=dataset(conn,'f')
    geo=conn.execute("INSERT INTO dw.dim_geography(dataset_id,cvegeo,boundary_year,geom,area_km2) VALUES (%s,'0900100010010',2020,ST_Multi(ST_MakeEnvelope(-100,19,-99,20,4326)),1) RETURNING geography_id",(ds,)).fetchone()[0]
    sources={}
    for kind,letter in [('census','1'),('businesses','2'),('crime','3')]:
        sid=conn.execute("INSERT INTO dw.dim_source_release(kind,sha256,url,local_path,release_label) VALUES (%s,%s,'https://example.invalid','test','test') RETURNING source_id",(kind,letter*64)).fetchone()[0]
        conn.execute('INSERT INTO dw.dataset_source VALUES (%s,%s,%s)',(ds,kind,sid));sources[kind]=sid
    conn.execute("INSERT INTO staging.source_record VALUES (%s,%s,'pop','{}')",(ds,sources['census']))
    conn.execute("INSERT INTO dw.fact_population(dataset_id,geography_id,source_id,record_key,census_year,pobtot,p_12ymas,pea) VALUES (%s,%s,%s,'pop',2020,0,0,NULL)",(ds,geo,sources['census']))
    activity=conn.execute("INSERT INTO dw.dim_economic_activity(scian_version,code,sector) VALUES (2018,'461110','46') RETURNING activity_id").fetchone()[0]
    for key in ['b1','b2']:
        conn.execute("INSERT INTO staging.source_record VALUES (%s,%s,%s,'{}')",(ds,sources['businesses'],key))
        conn.execute("INSERT INTO dw.fact_business_snapshot VALUES (%s,%s,%s,%s,%s,'original','0 a 5','declared',ST_SetSRID(ST_Point(-99.5,19.5),4326),'assigned',1)",(ds,sources['businesses'],key,geo,activity))
    typ=conn.execute("INSERT INTO dw.dim_crime_type(origin,type_original,category_original) VALUES ('FGJ','test','test') RETURNING crime_type_id").fetchone()[0]
    conn.execute("INSERT INTO dw.dim_date VALUES ('2020-01-01',2020,1,1,1) ON CONFLICT DO NOTHING")
    for key in ['c1','c2','c3']:
        conn.execute("INSERT INTO staging.source_record VALUES (%s,%s,%s,'{}')",(ds,sources['crime'],key))
        conn.execute("INSERT INTO dw.fact_crime_record VALUES (%s,%s,%s,%s,%s,'2020-01-01',NULL,true,false,'NA','candidate_unknown_competence',true,ST_SetSRID(ST_Point(-99.5,19.5),4326),'assigned',1)",(ds,sources['crime'],key,geo,typ))
    row=conn.execute('SELECT business_count,crime_record_count,businesses_per_1000,crime_records_per_1000,pea_percent,dominant_sectors,crime_records_per_100_businesses FROM analytics.kpi_ageb WHERE dataset_id=%s',(ds,)).fetchone()
    assert row==(2,3,None,None,None,['46'],150)
