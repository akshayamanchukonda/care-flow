-- 01_overall_summary.sql
-- High-level operational summary of the CareFlow dataset

SELECT
    (SELECT COUNT(*) FROM patients) AS total_patients,
    (SELECT COUNT(*) FROM visits) AS total_visits,
    (SELECT COUNT(*) FROM events) AS total_events,
    MIN(event_timestamp) AS earliest_event,
    MAX(event_timestamp) AS latest_event,
    ROUND(AVG(waiting_time_minutes), 2) AS overall_avg_waiting_time_mins,
    MIN(waiting_time_minutes) AS min_waiting_time_mins,
    MAX(waiting_time_minutes) AS max_waiting_time_mins
FROM events;
