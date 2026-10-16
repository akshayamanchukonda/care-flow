-- 06_visit_outcomes.sql
-- Breakdown of final patient disposition/outcomes and observed journey duration

SELECT
    discharge_disposition,
    COUNT(*) AS total_visits,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM visits), 2) AS pct_of_total_visits,
    ROUND(AVG((strftime('%s', visit_end_time) - strftime('%s', visit_start_time)) / 60.0), 2) AS avg_journey_duration_mins
FROM visits
GROUP BY discharge_disposition
ORDER BY total_visits DESC;
