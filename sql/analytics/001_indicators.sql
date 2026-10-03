-- Views preserve dataset_id: never aggregate different releases implicitly.
CREATE VIEW analytics.population_by_ageb AS
SELECT p.*,g.cvegeo,g.area_km2,
 CASE WHEN p.p_18ymas-p.p_18a24-p.p_60ymas>=0 THEN p.p_18ymas-p.p_18a24-p.p_60ymas END AS p_25a59
FROM dw.fact_population p JOIN dw.dim_geography g USING(dataset_id,geography_id);

CREATE VIEW analytics.business_by_ageb AS
WITH totals AS (
 SELECT b.dataset_id,b.geography_id,count(*) AS business_count,
 count(*) FILTER(WHERE a.sector='46') AS retail_count,
 count(*) FILTER(WHERE a.sector IN ('48-49','51','52','53','54','55','56','61','62','71','72','81')) AS services_count
 FROM dw.fact_business_snapshot b JOIN dw.dim_economic_activity a USING(activity_id)
 WHERE b.assignment_status='assigned' GROUP BY b.dataset_id,b.geography_id
), sectors AS (
 SELECT b.dataset_id,b.geography_id,a.sector,count(*) AS sector_count
 FROM dw.fact_business_snapshot b JOIN dw.dim_economic_activity a USING(activity_id)
 WHERE b.assignment_status='assigned' GROUP BY b.dataset_id,b.geography_id,a.sector
), ranked AS (
 SELECT *,max(sector_count) OVER(PARTITION BY dataset_id,geography_id) AS largest FROM sectors
), dominant AS (
 SELECT dataset_id,geography_id,array_agg(sector ORDER BY sector) AS dominant_sectors
 FROM ranked WHERE sector_count=largest GROUP BY dataset_id,geography_id
)
SELECT g.dataset_id,g.geography_id,g.cvegeo,coalesce(t.business_count,0) AS business_count,
 coalesce(t.retail_count,0) AS retail_count,coalesce(t.services_count,0) AS services_count,d.dominant_sectors
FROM dw.dim_geography g LEFT JOIN totals t USING(dataset_id,geography_id)
LEFT JOIN dominant d USING(dataset_id,geography_id);

CREATE VIEW analytics.crime_by_ageb AS
WITH counts AS (
 SELECT dataset_id,geography_id,count(*) FILTER(WHERE is_candidate) AS crime_record_count,
 count(*) FILTER(WHERE is_candidate AND eligibility_reason='candidate_unknown_competence') AS unknown_competence_count,
 count(*) FILTER(WHERE NOT is_candidate) AS excluded_record_count
 FROM dw.fact_crime_record WHERE assignment_status='assigned' GROUP BY dataset_id,geography_id
)
SELECT g.dataset_id,g.geography_id,g.cvegeo,coalesce(c.crime_record_count,0) AS crime_record_count,
 coalesce(c.unknown_competence_count,0) AS unknown_competence_count,coalesce(c.excluded_record_count,0) AS excluded_record_count
FROM dw.dim_geography g LEFT JOIN counts c USING(dataset_id,geography_id);

CREATE VIEW analytics.kpi_ageb AS
SELECT p.dataset_id,p.geography_id,p.cvegeo,d.cohort_year,d.rule_version,p.census_year,
 p.area_km2,p.pobtot AS population,p.pobtot/p.area_km2 AS population_density,
 100.0*p.pea/nullif(p.p_12ymas,0) AS pea_percent,
 b.business_count,b.business_count/p.area_km2 AS business_density,
 1000.0*b.business_count/nullif(p.pobtot,0) AS businesses_per_1000,
 b.retail_count/p.area_km2 AS retail_density,b.services_count/p.area_km2 AS services_density,
 b.dominant_sectors,c.crime_record_count,
 1000.0*c.crime_record_count/nullif(p.pobtot,0) AS crime_records_per_1000,
 100.0*c.crime_record_count/nullif(b.business_count,0) AS crime_records_per_100_businesses,
 c.unknown_competence_count,c.excluded_record_count,
 CASE WHEN p.pobtot IS NULL THEN 'missing' WHEN p.pobtot=0 THEN 'zero' ELSE 'valid' END AS population_denominator_status,
 CASE WHEN p.pea IS NULL OR p.p_12ymas IS NULL THEN 'missing' WHEN p.p_12ymas=0 THEN 'zero' ELSE 'valid' END AS pea_input_status,
 CASE WHEN b.business_count=0 THEN 'zero' ELSE 'valid' END AS business_denominator_status
FROM analytics.population_by_ageb p JOIN analytics.business_by_ageb b USING(dataset_id,geography_id)
JOIN analytics.crime_by_ageb c USING(dataset_id,geography_id) JOIN dw.dataset d USING(dataset_id);

CREATE VIEW analytics.age_distribution AS
SELECT p.dataset_id,p.geography_id,p.cvegeo,a.age_group,a.population,
 100.0*a.population/nullif(p.pobtot,0) AS percent_of_total,
 CASE WHEN a.population IS NULL THEN 'missing' ELSE 'known' END AS value_status
FROM analytics.population_by_ageb p CROSS JOIN LATERAL (VALUES
 ('0-2',p.p_0a2),('3-5',p.p_3a5),('6-11',p.p_6a11),('12-14',p.p_12a14),('15-17',p.p_15a17),
 ('18-24',p.p_18a24),('25-59',p.p_25a59),('60+',p.p_60ymas)) a(age_group,population);

CREATE VIEW analytics.crime_by_type_month AS
SELECT f.dataset_id,f.geography_id,g.cvegeo,date_trunc('month',f.started_on)::date AS initiation_month,
 t.crime_type_id,t.type_original,t.category_original,count(*) AS crime_record_count,
 count(*) FILTER(WHERE f.eligibility_reason='candidate_unknown_competence') AS unknown_competence_count
FROM dw.fact_crime_record f JOIN dw.dim_geography g USING(dataset_id,geography_id)
JOIN dw.dim_crime_type t USING(crime_type_id)
WHERE f.is_candidate AND f.assignment_status='assigned'
GROUP BY f.dataset_id,f.geography_id,g.cvegeo,date_trunc('month',f.started_on)::date,
 t.crime_type_id,t.type_original,t.category_original;
COMMENT ON VIEW analytics.kpi_ageb IS 'Closed urban scope only. FGJ initiation cohort, candidate-v1. Ratios are recorded rows, not actual incident risk. Always filter dataset_id.';
COMMENT ON VIEW analytics.crime_by_type_month IS 'Sparse observed groups; absence of a row is not evidence of complete reporting. Dates are initiation dates, not occurrence dates.';
