-- psql: pass -v dataset_id=<ID returned by src/list_datasets.py>.
-- Always select one dataset; no implicit sum over editions.
SELECT cvegeo,population,business_count,crime_record_count,crime_records_per_1000,
       pea_input_status,dominant_sectors
FROM analytics.kpi_ageb WHERE dataset_id=:'dataset_id' ORDER BY cvegeo LIMIT 10;
SELECT initiation_month,sum(crime_record_count) AS recorded_rows,
       sum(unknown_competence_count) AS unknown_competence
FROM analytics.crime_by_type_month WHERE dataset_id=:'dataset_id'
GROUP BY initiation_month ORDER BY initiation_month;
SELECT issue_code,count(*) FROM meta.quality_issue WHERE dataset_id=:'dataset_id'
GROUP BY issue_code ORDER BY issue_code;
