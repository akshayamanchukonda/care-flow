-- v_transition_times.sql
-- Reusable SQL view providing transition-level metrics and duration aggregations

DROP VIEW IF EXISTS v_transition_times;

CREATE VIEW v_transition_times AS
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
)
SELECT
    from_activity,
    to_activity,
    COUNT(*) AS transition_count,
    ROUND(AVG((strftime('%s', to_timestamp) - strftime('%s', from_timestamp)) / 60.0), 2) AS avg_transition_time_minutes,
    ROUND(MIN((strftime('%s', to_timestamp) - strftime('%s', from_timestamp)) / 60.0), 2) AS min_transition_time_minutes,
    ROUND(MAX((strftime('%s', to_timestamp) - strftime('%s', from_timestamp)) / 60.0), 2) AS max_transition_time_minutes
FROM ConsecutiveEvents
WHERE to_activity IS NOT NULL
GROUP BY from_activity, to_activity;
