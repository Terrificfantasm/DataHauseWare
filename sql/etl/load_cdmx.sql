INSERT INTO dw.fact_population(dataset_id,geography_id,source_id,record_key,census_year,pobtot,p_0a2,p_3a5,p_6a11,p_12a14,p_15a17,p_18a24,p_18ymas,p_60ymas,p_12ymas,pea,pe_inac,vivtot,tvivhab,vivpar_hab,vivparh_cv,vph_inter)
SELECT s.dataset_id,g.geography_id,s.source_id,s.record_key,2020,staging.census_integer(s.raw->>'POBTOT'),staging.census_integer(s.raw->>'P_0A2'),staging.census_integer(s.raw->>'P_3A5'),staging.census_integer(s.raw->>'P_6A11'),staging.census_integer(s.raw->>'P_12A14'),staging.census_integer(s.raw->>'P_15A17'),staging.census_integer(s.raw->>'P_18A24'),staging.census_integer(s.raw->>'P_18YMAS'),staging.census_integer(s.raw->>'P_60YMAS'),staging.census_integer(s.raw->>'P_12YMAS'),staging.census_integer(s.raw->>'PEA'),staging.census_integer(s.raw->>'PE_INAC'),staging.census_integer(s.raw->>'VIVTOT'),staging.census_integer(s.raw->>'TVIVHAB'),staging.census_integer(s.raw->>'VIVPAR_HAB'),staging.census_integer(s.raw->>'VIVPARH_CV'),staging.census_integer(s.raw->>'VPH_INTER')
FROM staging.source_record s JOIN dw.dim_geography g ON g.dataset_id=s.dataset_id AND g.cvegeo=s.record_key
WHERE s.dataset_id=%(dataset_id)s AND s.source_id=%(census)s;

INSERT INTO meta.quality_issue(dataset_id,source_id,record_key,issue_code)
SELECT s.dataset_id,s.source_id,s.record_key,'census_without_polygon' FROM staging.source_record s
WHERE s.dataset_id=%(dataset_id)s AND s.source_id=%(census)s
 AND NOT EXISTS(SELECT 1 FROM dw.dim_geography g WHERE g.dataset_id=s.dataset_id AND g.cvegeo=s.record_key);
INSERT INTO meta.quality_issue(dataset_id,source_id,record_key,issue_code,details)
SELECT dataset_id,source_id,record_key,'census_reserved_or_missing',jsonb_object_agg(k,v)
FROM staging.source_record s CROSS JOIN LATERAL jsonb_each_text(s.raw) e(k,v)
WHERE dataset_id=%(dataset_id)s AND source_id=%(census)s AND v IN ('*','')
GROUP BY dataset_id,source_id,record_key;

INSERT INTO dw.dim_economic_activity(scian_version,code,sector)
SELECT DISTINCT 2018,raw->>'codigo_act',CASE left(raw->>'codigo_act',2)
 WHEN '31' THEN '31-33' WHEN '32' THEN '31-33' WHEN '33' THEN '31-33'
 WHEN '48' THEN '48-49' WHEN '49' THEN '48-49' ELSE left(raw->>'codigo_act',2) END
FROM staging.source_record WHERE dataset_id=%(dataset_id)s AND source_id=%(businesses)s
ON CONFLICT(scian_version,code) DO NOTHING;

CREATE TEMP TABLE business_points ON COMMIT DROP AS
SELECT s.*,staging.wgs84_point(raw->>'longitud',raw->>'latitud') AS point
FROM staging.source_record s WHERE dataset_id=%(dataset_id)s AND source_id=%(businesses)s;
INSERT INTO dw.fact_business_snapshot(dataset_id,source_id,record_key,geography_id,activity_id,
 activity_name_original,size_category_original,declared_geography,point,assignment_status,match_count)
SELECT p.dataset_id,p.source_id,p.record_key,CASE WHEN m.n=1 THEN m.geo END,a.activity_id,
 p.raw->>'nombre_act',p.raw->>'per_ocu',lpad(p.raw->>'cve_ent',2,'0')||lpad(p.raw->>'cve_mun',3,'0')||lpad(p.raw->>'cve_loc',4,'0')||lpad(p.raw->>'ageb',4,'0'),p.point,
 CASE WHEN p.point IS NULL THEN 'invalid_coordinates' WHEN m.n=0 THEN 'outside_selected_areas' WHEN m.n=1 THEN 'assigned' ELSE 'ambiguous' END,m.n
FROM business_points p JOIN dw.dim_economic_activity a ON a.scian_version=2018 AND a.code=p.raw->>'codigo_act'
CROSS JOIN LATERAL (SELECT count(*)::integer n,min(g.geography_id) geo FROM dw.dim_geography g
 WHERE g.dataset_id=p.dataset_id AND p.point IS NOT NULL AND ST_Intersects(g.geom,p.point)) m;

INSERT INTO dw.dim_crime_type(origin,type_original,category_original)
SELECT DISTINCT 'FGJ',raw->>'delito',raw->>'categoria_delito' FROM staging.source_record
WHERE dataset_id=%(dataset_id)s AND source_id=%(crime)s ON CONFLICT DO NOTHING;
CREATE TEMP TABLE crime_points ON COMMIT DROP AS
SELECT s.*,staging.wgs84_point(raw->>'longitud',raw->>'latitud') AS point,
 staging.iso_date(raw->>'fecha_inicio') started,staging.iso_date(raw->>'fecha_hecho') occurred,
 CASE WHEN raw->>'categoria_delito'='HECHO NO DELICTIVO' OR raw->>'competencia'='HECHO NO DELICTIVO' THEN 'excluded_noncriminal'
 WHEN raw->>'competencia'='INCOMPETENCIA' THEN 'excluded_incompetence'
 WHEN raw->>'delito' IN ('DENUNCIA DE HECHOS','DDH INCOMPETENCIA') THEN 'excluded_report_of_facts'
 WHEN raw->>'competencia'='FUERO COMUN' THEN 'candidate_common_jurisdiction'
 WHEN raw->>'competencia' IN ('NA','') THEN 'candidate_unknown_competence' ELSE 'review_other_competence' END eligibility
FROM staging.source_record s WHERE dataset_id=%(dataset_id)s AND source_id=%(crime)s;
INSERT INTO dw.dim_date(calendar_date,calendar_year,calendar_month,calendar_day,quarter)
SELECT d,extract(year FROM d),extract(month FROM d),extract(day FROM d),extract(quarter FROM d)
FROM (SELECT started d FROM crime_points UNION SELECT occurred FROM crime_points) t WHERE d IS NOT NULL ON CONFLICT DO NOTHING;
INSERT INTO dw.fact_crime_record(dataset_id,source_id,record_key,geography_id,crime_type_id,
 started_on,occurred_on,invalid_occurred_date,occurred_after_start,competence_original,eligibility_reason,is_candidate,
 point,assignment_status,match_count)
SELECT p.dataset_id,p.source_id,p.record_key,CASE WHEN m.n=1 THEN m.geo END,t.crime_type_id,
 p.started,p.occurred,p.occurred IS NULL,coalesce(p.occurred>p.started,false),p.raw->>'competencia',p.eligibility,
 p.eligibility IN ('candidate_common_jurisdiction','candidate_unknown_competence'),p.point,
 CASE WHEN p.point IS NULL THEN 'invalid_coordinates' WHEN m.n=0 THEN 'outside_selected_areas' WHEN m.n=1 THEN 'assigned' ELSE 'ambiguous' END,m.n
FROM crime_points p JOIN dw.dim_crime_type t ON t.origin='FGJ' AND t.type_original=p.raw->>'delito' AND t.category_original=p.raw->>'categoria_delito'
CROSS JOIN LATERAL (SELECT count(*)::integer n,min(g.geography_id) geo FROM dw.dim_geography g
 WHERE g.dataset_id=p.dataset_id AND p.point IS NOT NULL AND ST_Intersects(g.geom,p.point)) m;

INSERT INTO meta.quality_issue(dataset_id,source_id,record_key,issue_code)
SELECT dataset_id,source_id,record_key,'spatial_'||assignment_status FROM dw.fact_business_snapshot WHERE dataset_id=%(dataset_id)s AND assignment_status<>'assigned'
UNION ALL SELECT dataset_id,source_id,record_key,'spatial_'||assignment_status FROM dw.fact_crime_record WHERE dataset_id=%(dataset_id)s AND assignment_status<>'assigned';
INSERT INTO meta.quality_issue(dataset_id,source_id,record_key,issue_code)
SELECT dataset_id,source_id,record_key,eligibility_reason FROM dw.fact_crime_record WHERE dataset_id=%(dataset_id)s AND NOT is_candidate;
INSERT INTO meta.quality_issue(dataset_id,source_id,record_key,issue_code)
SELECT dataset_id,source_id,record_key,'invalid_occurred_date' FROM dw.fact_crime_record WHERE dataset_id=%(dataset_id)s AND invalid_occurred_date
UNION ALL SELECT dataset_id,source_id,record_key,'occurred_after_start' FROM dw.fact_crime_record WHERE dataset_id=%(dataset_id)s AND occurred_after_start;
INSERT INTO meta.quality_issue(dataset_id,source_id,record_key,issue_code)
SELECT dataset_id,source_id,record_key,'duplicate_public_attributes_not_deduplicated'
FROM (SELECT s.*,count(*) OVER(PARTITION BY raw-'_id') n FROM staging.source_record s
 WHERE dataset_id=%(dataset_id)s AND source_id=%(crime)s) s WHERE n>1;
