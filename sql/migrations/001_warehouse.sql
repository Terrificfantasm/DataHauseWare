CREATE EXTENSION IF NOT EXISTS postgis;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS dw;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE meta.etl_run (
 run_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 fingerprint text NOT NULL, started_at timestamptz NOT NULL DEFAULT now(), finished_at timestamptz,
 status text NOT NULL CHECK (status IN ('running','succeeded','failed','skipped')),
 report jsonb NOT NULL DEFAULT '{}', error_type text
);
CREATE TABLE dw.dataset (
 dataset_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 fingerprint text NOT NULL UNIQUE CHECK(length(fingerprint)=64),
 name text NOT NULL, territory text NOT NULL, cohort_year integer NOT NULL,
 rule_version text NOT NULL, configuration jsonb NOT NULL, pipeline_sha256 text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE dw.dim_source_release (
 source_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 kind text NOT NULL CHECK(kind IN ('census','boundaries','businesses','crime')),
 sha256 text NOT NULL CHECK(length(sha256)=64), url text NOT NULL, local_path text NOT NULL,
 release_label text NOT NULL, UNIQUE(kind,sha256)
);
CREATE TABLE dw.dataset_source (
 dataset_id bigint NOT NULL REFERENCES dw.dataset, role text NOT NULL,
 source_id bigint NOT NULL REFERENCES dw.dim_source_release,
 PRIMARY KEY(dataset_id,role), UNIQUE(dataset_id,source_id)
);
CREATE TABLE staging.source_record (
 dataset_id bigint NOT NULL, source_id bigint NOT NULL, record_key text NOT NULL,
 raw jsonb NOT NULL, PRIMARY KEY(dataset_id,source_id,record_key),
 FOREIGN KEY(dataset_id,source_id) REFERENCES dw.dataset_source(dataset_id,source_id)
);
CREATE TABLE dw.dim_geography (
 geography_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 dataset_id bigint NOT NULL REFERENCES dw.dataset,
 cvegeo text NOT NULL CHECK(cvegeo ~ '^[0-9A-Z]{13}$'),
 boundary_year integer NOT NULL, geom geometry(MultiPolygon,4326) NOT NULL,
 area_km2 double precision NOT NULL CHECK(area_km2>0),
 CHECK(ST_IsValid(geom) AND NOT ST_IsEmpty(geom)),
 UNIQUE(dataset_id,cvegeo), UNIQUE(dataset_id,geography_id)
);
CREATE INDEX dim_geography_geom ON dw.dim_geography USING gist(geom);
CREATE TABLE dw.dim_date (
 calendar_date date PRIMARY KEY,
 calendar_year integer NOT NULL, calendar_month integer NOT NULL CHECK(calendar_month BETWEEN 1 AND 12),
 calendar_day integer NOT NULL CHECK(calendar_day BETWEEN 1 AND 31), quarter integer NOT NULL CHECK(quarter BETWEEN 1 AND 4),
 CHECK(calendar_year=extract(year FROM calendar_date) AND calendar_month=extract(month FROM calendar_date)
   AND calendar_day=extract(day FROM calendar_date) AND quarter=extract(quarter FROM calendar_date))
);
CREATE TABLE dw.dim_economic_activity (
 activity_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 scian_version integer NOT NULL, code text NOT NULL CHECK(code ~ '^[0-9]{6}$'), sector text NOT NULL,
 UNIQUE(scian_version,code)
);
CREATE TABLE dw.dim_crime_type (
 crime_type_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 origin text NOT NULL, type_original text NOT NULL, category_original text NOT NULL,
 UNIQUE(origin,type_original,category_original)
);
CREATE TABLE dw.fact_population (
 dataset_id bigint NOT NULL, geography_id bigint NOT NULL, source_id bigint NOT NULL, record_key text NOT NULL,
 census_year integer NOT NULL,
 pobtot integer CHECK(pobtot>=0), p_0a2 integer CHECK(p_0a2>=0), p_3a5 integer CHECK(p_3a5>=0),
 p_6a11 integer CHECK(p_6a11>=0), p_12a14 integer CHECK(p_12a14>=0), p_15a17 integer CHECK(p_15a17>=0),
 p_18a24 integer CHECK(p_18a24>=0), p_18ymas integer CHECK(p_18ymas>=0), p_60ymas integer CHECK(p_60ymas>=0),
 p_12ymas integer CHECK(p_12ymas>=0), pea integer CHECK(pea>=0), pe_inac integer CHECK(pe_inac>=0),
 vivtot integer CHECK(vivtot>=0), tvivhab integer CHECK(tvivhab>=0), vivpar_hab integer CHECK(vivpar_hab>=0),
 vivparh_cv integer CHECK(vivparh_cv>=0), vph_inter integer CHECK(vph_inter>=0),
 PRIMARY KEY(dataset_id,geography_id),
 FOREIGN KEY(dataset_id,geography_id) REFERENCES dw.dim_geography(dataset_id,geography_id),
 FOREIGN KEY(dataset_id,source_id,record_key) REFERENCES staging.source_record
);
CREATE TABLE dw.fact_business_snapshot (
 dataset_id bigint NOT NULL, source_id bigint NOT NULL, record_key text NOT NULL,
 geography_id bigint, activity_id bigint NOT NULL REFERENCES dw.dim_economic_activity,
 activity_name_original text NOT NULL, size_category_original text NOT NULL,
 declared_geography text NOT NULL, point geometry(Point,4326),
 assignment_status text NOT NULL CHECK(assignment_status IN ('assigned','outside_selected_areas','invalid_coordinates','ambiguous')),
 match_count integer NOT NULL CHECK(match_count>=0),
 PRIMARY KEY(dataset_id,source_id,record_key),
 FOREIGN KEY(dataset_id,source_id,record_key) REFERENCES staging.source_record,
 FOREIGN KEY(dataset_id,geography_id) REFERENCES dw.dim_geography(dataset_id,geography_id),
 CHECK((assignment_status='assigned')=(geography_id IS NOT NULL)),
 CHECK((assignment_status='invalid_coordinates')=(point IS NULL)),
 CHECK((assignment_status='assigned' AND match_count=1) OR (assignment_status='ambiguous' AND match_count>1)
    OR (assignment_status IN ('outside_selected_areas','invalid_coordinates') AND match_count=0))
);
CREATE INDEX business_geography ON dw.fact_business_snapshot(dataset_id,geography_id);
CREATE INDEX business_point ON dw.fact_business_snapshot USING gist(point);
CREATE TABLE dw.fact_crime_record (
 dataset_id bigint NOT NULL, source_id bigint NOT NULL, record_key text NOT NULL,
 geography_id bigint, crime_type_id bigint NOT NULL REFERENCES dw.dim_crime_type,
 started_on date NOT NULL REFERENCES dw.dim_date, occurred_on date REFERENCES dw.dim_date,
 invalid_occurred_date boolean NOT NULL, occurred_after_start boolean NOT NULL,
 competence_original text NOT NULL, eligibility_reason text NOT NULL,
 is_candidate boolean NOT NULL, point geometry(Point,4326),
 assignment_status text NOT NULL CHECK(assignment_status IN ('assigned','outside_selected_areas','invalid_coordinates','ambiguous')),
 match_count integer NOT NULL CHECK(match_count>=0),
 PRIMARY KEY(dataset_id,source_id,record_key),
 FOREIGN KEY(dataset_id,source_id,record_key) REFERENCES staging.source_record,
 FOREIGN KEY(dataset_id,geography_id) REFERENCES dw.dim_geography(dataset_id,geography_id),
 CHECK((assignment_status='assigned')=(geography_id IS NOT NULL)),
 CHECK((assignment_status='invalid_coordinates')=(point IS NULL)),
 CHECK(invalid_occurred_date=(occurred_on IS NULL)),
 CHECK(occurred_after_start=coalesce(occurred_on>started_on,false)),
 CHECK(is_candidate=(eligibility_reason IN ('candidate_common_jurisdiction','candidate_unknown_competence'))),
 CHECK((assignment_status='assigned' AND match_count=1) OR (assignment_status='ambiguous' AND match_count>1)
    OR (assignment_status IN ('outside_selected_areas','invalid_coordinates') AND match_count=0))
);
CREATE INDEX crime_geography ON dw.fact_crime_record(dataset_id,geography_id);
CREATE INDEX crime_date_type ON dw.fact_crime_record(dataset_id,started_on,crime_type_id);
CREATE INDEX crime_point ON dw.fact_crime_record USING gist(point);
CREATE TABLE meta.quality_issue (
 dataset_id bigint NOT NULL, source_id bigint NOT NULL, record_key text NOT NULL,
 issue_code text NOT NULL, details jsonb NOT NULL DEFAULT '{}',
 PRIMARY KEY(dataset_id,source_id,record_key,issue_code),
 FOREIGN KEY(dataset_id,source_id,record_key) REFERENCES staging.source_record
);
-- Only known census sentinels may become NULL; unexpected tokens fail the load.
CREATE FUNCTION staging.census_integer(value text) RETURNS integer LANGUAGE plpgsql IMMUTABLE AS $$
BEGIN
 IF value IN ('*','') THEN RETURN NULL; END IF;
 IF value IS NULL OR value !~ '^[0-9]+$' THEN RAISE EXCEPTION 'Unexpected census token'; END IF;
 RETURN value::integer;
END $$;
CREATE FUNCTION staging.iso_date(value text) RETURNS date LANGUAGE sql IMMUTABLE AS $$
 SELECT CASE WHEN value ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' AND pg_input_is_valid(value,'date') THEN value::date END
$$;
CREATE FUNCTION staging.wgs84_point(lon text, lat text) RETURNS geometry LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE x double precision; y double precision;
BEGIN
 IF NOT coalesce(pg_input_is_valid(lon,'double precision'),false) OR NOT coalesce(pg_input_is_valid(lat,'double precision'),false) THEN RETURN NULL; END IF;
 x:=lon::double precision; y:=lat::double precision;
 IF NOT (x BETWEEN -180 AND 180 AND y BETWEEN -90 AND 90) OR (x=0 AND y=0) THEN RETURN NULL; END IF;
 RETURN ST_SetSRID(ST_Point(x,y),4326);
END $$;
