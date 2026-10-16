-- 03_department_waiting_times.sql
-- Waiting-time statistics aggregated across hospital departments

SELECT
    department,
    COUNT(*) AS total_events,
    MIN(waiting_time_minutes) AS min_waiting_time_mins,
    ROUND(AVG(waiting_time_minutes), 2) AS avg_waiting_time_mins,
    MAX(waiting_time_minutes) AS max_waiting_time_mins,
    SUM(waiting_time_minutes) AS total_waiting_time_mins
FROM events
GROUP BY department
ORDER BY avg_waiting_time_mins DESC;
