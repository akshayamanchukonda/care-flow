-- v_stage_waiting_times.sql
-- Reusable view: Stage-level event volumes, waiting time averages, and bounds

DROP VIEW IF EXISTS v_stage_waiting_times;

CREATE VIEW IF NOT EXISTS v_stage_waiting_times AS
SELECT
    event_name AS stage,
    COUNT(event_id) AS total_events,
    COUNT(DISTINCT visit_id) AS unique_visits,
    COUNT(DISTINCT patient_id) AS unique_patients,
    MIN(waiting_time_minutes) AS min_waiting_time_mins,
    ROUND(AVG(waiting_time_minutes), 2) AS avg_waiting_time_mins,
    MAX(waiting_time_minutes) AS max_waiting_time_mins,
    SUM(waiting_time_minutes) AS total_waiting_time_mins
FROM events
GROUP BY event_name;
