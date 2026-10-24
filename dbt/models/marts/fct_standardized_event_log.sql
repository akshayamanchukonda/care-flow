-- Mart model: fct_standardized_event_log
-- Canonical process mining event log transformed from staged healthcare events
-- Provides standardized case_id, activity_name, event_timestamp, and activity_sequence
-- for PM4Py process discovery and preserves operational metadata (is_loopback, waiting_time_minutes)

WITH staged_events AS (
    SELECT
        case_id,
        patient_id,
        event_id,
        activity_name,
        event_timestamp,
        department,
        status,
        waiting_time_minutes,
        activity_sequence
    FROM {{ ref('stg_healthcare_events') }}
),

annotated_event_log AS (
    SELECT
        -- Process Mining Core Identifiers & Sequencing
        case_id,
        activity_name,
        event_timestamp,
        activity_sequence,

        -- Operational Loop-Back Indicator (1 if activity previously executed within case)
        CASE
            WHEN ROW_NUMBER() OVER (
                PARTITION BY case_id, activity_name
                ORDER BY event_timestamp ASC, event_id ASC
            ) > 1 THEN 1
            ELSE 0
        END AS is_loopback,

        -- Journey Attributes & Metadata
        patient_id,
        event_id,
        department,
        status,
        waiting_time_minutes

    FROM staged_events
)

SELECT * FROM annotated_event_log
ORDER BY case_id ASC, activity_sequence ASC
