-- 09_event_counts_and_avg_wait.sql
-- Event volume, unique visits and patients served, and average waiting time per stage

SELECT
    e.event_name AS stage,
    COUNT(e.event_id) AS total_events,
    COUNT(DISTINCT e.visit_id) AS unique_visits,
    COUNT(DISTINCT e.patient_id) AS unique_patients,
    MIN(e.waiting_time_minutes) AS min_waiting_time_mins,
    ROUND(AVG(e.waiting_time_minutes), 2) AS avg_waiting_time_mins,
    MAX(e.waiting_time_minutes) AS max_waiting_time_mins,
    SUM(e.waiting_time_minutes) AS total_waiting_time_mins
FROM events e
GROUP BY e.event_name
ORDER BY total_events DESC, avg_waiting_time_mins DESC;
