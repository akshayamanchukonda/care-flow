-- 04_bottleneck_ranking.sql
-- Ranking healthcare process stages by average waiting time to highlight operational bottlenecks
-- Note: Represents queue delays recorded before care; does not claim clinical causation.

WITH StageAggregates AS (
    SELECT
        event_name,
        COUNT(*) AS total_events,
        ROUND(AVG(waiting_time_minutes), 2) AS avg_waiting_time_mins,
        SUM(waiting_time_minutes) AS total_wait_mins
    FROM events
    GROUP BY event_name
),
TotalHospitalWait AS (
    SELECT SUM(waiting_time_minutes) AS hospital_total_wait_mins FROM events
)
SELECT
    RANK() OVER (ORDER BY s.avg_waiting_time_mins DESC) AS bottleneck_rank,
    s.event_name AS stage,
    s.total_events,
    s.avg_waiting_time_mins,
    s.total_wait_mins,
    ROUND(100.0 * s.total_wait_mins / t.hospital_total_wait_mins, 2) AS pct_of_total_wait_time
FROM StageAggregates s
CROSS JOIN TotalHospitalWait t
ORDER BY bottleneck_rank ASC;
