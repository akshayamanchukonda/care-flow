-- 07_visit_durations.sql
-- Observed patient journey durations calculated from first to last event timestamp

WITH VisitDurations AS (
    SELECT
        v.visit_id,
        v.patient_id,
        v.visit_start_time,
        v.visit_end_time,
        v.discharge_disposition,
        v.total_events,
        ROUND((strftime('%s', v.visit_end_time) - strftime('%s', v.visit_start_time)) / 60.0, 2) AS duration_minutes,
        ROUND((strftime('%s', v.visit_end_time) - strftime('%s', v.visit_start_time)) / 3600.0, 2) AS duration_hours
    FROM visits v
)
SELECT
    visit_id,
    patient_id,
    visit_start_time,
    visit_end_time,
    total_events,
    discharge_disposition,
    duration_minutes,
    duration_hours
FROM VisitDurations
ORDER BY duration_minutes DESC;
