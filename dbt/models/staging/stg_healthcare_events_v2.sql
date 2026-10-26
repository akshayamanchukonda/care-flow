-- Staging model: stg_healthcare_events_v2
-- Cleans and standardizes the enhanced healthcare event log (with rework loop-backs) from BigQuery

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

    FROM {{ source('careflow_raw', 'healthcare_event_log_v2_raw') }}
),

deduplicated_and_sequenced AS (
    SELECT
        case_id,
        patient_id,
        event_id,
        activity_name,
        event_timestamp,
        department,
        status,
        waiting_time_minutes,

        -- Process Mining Sequence Index (chronological ordering per case)
        ROW_NUMBER() OVER (
            PARTITION BY case_id
            ORDER BY event_timestamp ASC
        ) AS activity_sequence

    FROM source_data
    WHERE case_id IS NOT NULL
      AND activity_name IS NOT NULL
      AND event_timestamp IS NOT NULL
)

SELECT * FROM deduplicated_and_sequenced
