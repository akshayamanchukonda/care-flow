-- Staging model: stg_healthcare_events
-- Standardizes raw healthcare events into process mining format: case_id, activity_name, event_timestamp

WITH source_data AS (
    SELECT
        -- Process Mining Core Identifiers
        CAST(visit_id AS STRING) AS case_id,
        CAST(patient_id AS STRING) AS patient_id,
        CAST(event_id AS STRING) AS event_id,

        -- Standardized Activity & Timing
        TRIM(CAST(event_name AS STRING)) AS activity_name,
        CAST(event_timestamp AS TIMESTAMP) AS event_timestamp,

        -- Department & Operational Context
        TRIM(CAST(department AS STRING)) AS department,
        TRIM(CAST(status AS STRING)) AS status,
        CAST(waiting_time_minutes AS INT64) AS waiting_time_minutes

    FROM {{ source('careflow_raw', 'healthcare_event_log_raw') }}
),

deduplicated_events AS (
    SELECT
        case_id,
        patient_id,
        event_id,
        activity_name,
        event_timestamp,
        department,
        status,
        waiting_time_minutes

    FROM source_data
    WHERE case_id IS NOT NULL
      AND activity_name IS NOT NULL
      AND event_timestamp IS NOT NULL
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY event_id
        ORDER BY event_timestamp ASC
    ) = 1
),

sequenced_events AS (
    SELECT
        case_id,
        patient_id,
        event_id,
        activity_name,
        event_timestamp,
        department,
        status,
        waiting_time_minutes,

        -- Deterministic Process Mining Sequence Index (chronological ordering per case with event_id tie-breaker)
        ROW_NUMBER() OVER (
            PARTITION BY case_id
            ORDER BY event_timestamp ASC, event_id ASC
        ) AS activity_sequence

    FROM deduplicated_events
)

SELECT * FROM sequenced_events
