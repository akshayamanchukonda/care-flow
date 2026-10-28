-- 12_process_mining_transition_times.sql
-- Calculates elapsed transition times across all 9 discovered clinical process pathways
-- including operational rework and loop-backs (from stg_healthcare_events_v2).

WITH ConsecutiveProcessEvents AS (
    SELECT
        case_id,
        activity_name AS from_activity,
        event_timestamp AS from_timestamp,
        LEAD(activity_name) OVER (
            PARTITION BY case_id
            ORDER BY event_timestamp, activity_sequence, event_id
        ) AS to_activity,
        LEAD(event_timestamp) OVER (
            PARTITION BY case_id
            ORDER BY event_timestamp, activity_sequence, event_id
        ) AS to_timestamp
    FROM stg_healthcare_events_v2
),
ProcessTransitions AS (
    SELECT
        from_activity,
        to_activity,
        (strftime('%s', to_timestamp) - strftime('%s', from_timestamp)) / 60.0 AS transition_time_minutes
    FROM ConsecutiveProcessEvents
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
FROM ProcessTransitions
GROUP BY from_activity, to_activity
ORDER BY transition_count DESC, avg_transition_time_minutes DESC;
