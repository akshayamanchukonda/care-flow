-- v_department_performance.sql
-- Reusable view: Department operational volumes, queue times, and total wait load

DROP VIEW IF EXISTS v_department_performance;

CREATE VIEW IF NOT EXISTS v_department_performance AS
SELECT
    department,
    COUNT(event_id) AS total_events_served,
    COUNT(DISTINCT visit_id) AS unique_visits_handled,
    MIN(waiting_time_minutes) AS min_waiting_time_mins,
    ROUND(AVG(waiting_time_minutes), 2) AS avg_waiting_time_mins,
    MAX(waiting_time_minutes) AS max_waiting_time_mins,
    SUM(waiting_time_minutes) AS total_waiting_time_mins
FROM events
GROUP BY department;
