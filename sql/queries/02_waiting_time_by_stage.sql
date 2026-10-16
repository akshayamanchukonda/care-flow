-- 02_waiting_time_by_stage.sql
-- Average and median waiting time by event stage in SQLite
-- Note: SQLite does not provide a built-in MEDIAN function; exact median is calculated
-- using ROW_NUMBER() and COUNT() window functions over stage partitions.

WITH RankedEvents AS (
    SELECT
        event_name,
        waiting_time_minutes,
        ROW_NUMBER() OVER (PARTITION BY event_name ORDER BY waiting_time_minutes) AS row_num,
        COUNT(*) OVER (PARTITION BY event_name) AS total_count
    FROM events
),
MedianPerStage AS (
    SELECT
        event_name,
        ROUND(AVG(waiting_time_minutes), 2) AS median_waiting_time_mins
    FROM RankedEvents
    WHERE row_num IN ((total_count + 1) / 2, (total_count + 2) / 2)
    GROUP BY event_name
),
StageStats AS (
    SELECT
        event_name,
        COUNT(*) AS event_count,
        MIN(waiting_time_minutes) AS min_waiting_time_mins,
        ROUND(AVG(waiting_time_minutes), 2) AS avg_waiting_time_mins,
        MAX(waiting_time_minutes) AS max_waiting_time_mins
    FROM events
    GROUP BY event_name
)
SELECT
    s.event_name AS stage,
    s.event_count,
    s.min_waiting_time_mins,
    s.avg_waiting_time_mins,
    m.median_waiting_time_mins,
    s.max_waiting_time_mins
FROM StageStats s
JOIN MedianPerStage m ON s.event_name = m.event_name
ORDER BY s.avg_waiting_time_mins DESC;
