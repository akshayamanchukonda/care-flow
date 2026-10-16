-- 05_arrivals_by_hour.sql
-- Patient arrival volume grouped by hour of the day

SELECT
    CAST(strftime('%H', visit_start_time) AS INTEGER) AS arrival_hour,
    COUNT(visit_id) AS total_arrivals,
    ROUND(100.0 * COUNT(visit_id) / (SELECT COUNT(*) FROM visits), 2) AS pct_of_total_arrivals
FROM visits
GROUP BY arrival_hour
ORDER BY arrival_hour ASC;
