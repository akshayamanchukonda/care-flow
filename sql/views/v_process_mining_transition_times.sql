-- v_process_mining_transition_times.sql
-- Reusable SQL view providing transition duration aggregations across the 9 process mining pathways

DROP VIEW IF EXISTS v_process_mining_transition_times;

CREATE VIEW v_process_mining_transition_times AS
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
)
SELECT
    from_activity,
    to_activity,
    COUNT(*) AS transition_count,
    ROUND(AVG((strftime('%s', to_timestamp) - strftime('%s', from_timestamp)) / 60.0), 2) AS avg_transition_time_minutes,
    ROUND(MIN((strftime('%s', to_timestamp) - strftime('%s', from_timestamp)) / 60.0), 2) AS min_transition_time_minutes,
    ROUND(MAX((strftime('%s', to_timestamp) - strftime('%s', from_timestamp)) / 60.0), 2) AS max_transition_time_minutes
FROM ConsecutiveProcessEvents
WHERE to_activity IS NOT NULL
GROUP BY from_activity, to_activity;
