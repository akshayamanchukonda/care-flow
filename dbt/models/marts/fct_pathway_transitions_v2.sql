-- Mart model: fct_pathway_transitions_v2
-- Calculates Directly-Follows Graph (DFG) pathway transitions from enhanced staging events (stg_healthcare_events_v2)
-- Includes both forward clinical stages and rework loop-back transitions

WITH consecutive_events AS (
    SELECT
        case_id,
        patient_id,
        activity_name AS from_activity,
        event_timestamp AS from_timestamp,
        activity_sequence AS from_sequence,
        LEAD(activity_name) OVER (
            PARTITION BY case_id
            ORDER BY activity_sequence ASC
        ) AS to_activity,
        LEAD(event_timestamp) OVER (
            PARTITION BY case_id
            ORDER BY activity_sequence ASC
        ) AS to_timestamp,
        LEAD(activity_sequence) OVER (
            PARTITION BY case_id
            ORDER BY activity_sequence ASC
        ) AS to_sequence
    FROM {{ ref('stg_healthcare_events_v2') }}
),

transitions_detail AS (
    SELECT
        case_id,
        patient_id,
        from_activity,
        to_activity,
        from_timestamp,
        to_timestamp,
        TIMESTAMP_DIFF(to_timestamp, from_timestamp, MINUTE) AS transition_time_minutes
    FROM consecutive_events
    WHERE to_activity IS NOT NULL
)

SELECT
    from_activity,
    to_activity,
    COUNT(*) AS transition_count,
    ROUND(AVG(transition_time_minutes), 2) AS avg_transition_time_minutes,
    ROUND(MIN(transition_time_minutes), 2) AS min_transition_time_minutes,
    ROUND(MAX(transition_time_minutes), 2) AS max_transition_time_minutes
FROM transitions_detail
GROUP BY from_activity, to_activity
