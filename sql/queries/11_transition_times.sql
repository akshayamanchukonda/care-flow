-- 11_transition_times.sql
-- Calculates elapsed handover and transition times between consecutive clinical stages
-- partitioned by patient visit and ordered chronologically by event timestamp.

WITH ConsecutiveEvents AS (
    SELECT
        visit_id,
        event_name AS from_activity,
        event_timestamp AS from_timestamp,
        LEAD(event_name) OVER (
            PARTITION BY visit_id
            ORDER BY event_timestamp, event_id
        ) AS to_activity,
        LEAD(event_timestamp) OVER (
            PARTITION BY visit_id
            ORDER BY event_timestamp, event_id
        ) AS to_timestamp
    FROM events
),
TransitionCalculations AS (
    SELECT
        from_activity,
        to_activity,
        (strftime('%s', to_timestamp) - strftime('%s', from_timestamp)) / 60.0 AS transition_time_minutes
    FROM ConsecutiveEvents
    WHERE to_activity IS NOT NULL
      AND to_timestamp IS NOT NULL
)
SELECT
    from_activity,
    to_activity,
    COUNT(*) AS transition_count,
    ROUND(AVG(transition_time_minutes), 2) AS avg_transition_time_minutes,
    ROUND(MIN(transition_time_minutes), 2) AS min_transition_time_minutes,
    ROUND(MAX(transition_time_minutes), 2) AS max_transition_time_minutes
FROM TransitionCalculations
GROUP BY from_activity, to_activity
ORDER BY transition_count DESC, avg_transition_time_minutes DESC;
