-- 10_visit_level_summary.sql
-- Consolidated visit-level operational metrics designed for BI reporting and analytics

WITH VisitTreatmentDept AS (
    SELECT
        visit_id,
        department AS treatment_department
    FROM events
    WHERE event_name = 'Treatment'
),
VisitWaitSums AS (
    SELECT
        visit_id,
        SUM(waiting_time_minutes) AS total_recorded_wait_mins,
        MAX(CASE WHEN event_name = 'Diagnostics' THEN 1 ELSE 0 END) AS had_diagnostics
    FROM events
    GROUP BY visit_id
)
SELECT
    v.visit_id,
    v.patient_id,
    v.visit_start_time AS arrival_timestamp,
    DATE(v.visit_start_time) AS arrival_date,
    CAST(strftime('%H', v.visit_start_time) AS INTEGER) AS arrival_hour,
    v.visit_end_time AS discharge_timestamp,
    v.total_events,
    CASE WHEN w.had_diagnostics = 1 THEN 'Yes' ELSE 'No' END AS had_diagnostics,
    w.total_recorded_wait_mins,
    ROUND((strftime('%s', v.visit_end_time) - strftime('%s', v.visit_start_time)) / 60.0, 2) AS observed_journey_duration_mins,
    ROUND((strftime('%s', v.visit_end_time) - strftime('%s', v.visit_start_time)) / 3600.0, 2) AS observed_journey_duration_hours,
    v.discharge_disposition,
    COALESCE(t.treatment_department, 'N/A') AS treatment_department
FROM visits v
JOIN VisitWaitSums w ON v.visit_id = w.visit_id
LEFT JOIN VisitTreatmentDept t ON v.visit_id = t.visit_id
ORDER BY v.visit_start_time ASC;
