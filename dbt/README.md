# CareFlow dbt Analytics Transformation

This folder contains the **dbt (data build tool)** project for CareFlow. It is configured to clean, normalize, and test raw healthcare event logs stored in **Google BigQuery**, preparing them for process mining analysis.

---

## Project Structure

```text
dbt/
├── dbt_project.yml                 # Core project configuration
├── profiles.yml.example            # Profile connection template for BigQuery
├── models/
│   ├── sources.yml                 # Source definition for raw BigQuery table
│   ├── staging/
│   │   ├── schema.yml              # Documentation & tests for staging models
│   │   └── stg_healthcare_events.sql # Staging transformation model (Week 1)
│   └── marts/
│       ├── schema.yml              # Documentation & tests for mart models
│       ├── fct_pathway_transitions.sql # Clinical pathway transitions model (Week 2)
│       └── fct_standardized_event_log.sql # Canonical PM4Py event log model (Week 2)
└── README.md                       # This documentation guide
```

---

## Staging Model: `stg_healthcare_events` (Week 1)

Standardizes the raw dataset into canonical process mining format:
* `case_id` (STRING): Normalized from `visit_id`. Represents the single patient journey instance.
* `activity_name` (STRING): Cleaned event/activity name (`Registration`, `Triage`, `Consultation`, `Diagnostics`, `Treatment`, `Discharge`).
* `event_timestamp` (TIMESTAMP): Standard ISO timestamp for process sequencing.
* `activity_sequence` (INT64): Ordered index (1, 2, 3...) calculated via `ROW_NUMBER() OVER (PARTITION BY case_id ORDER BY event_timestamp ASC)`.
* Supporting attributes: `patient_id`, `event_id`, `department`, `status`, and `waiting_time_minutes`.

---

## Mart Model: `fct_standardized_event_log` (Week 2)

Canonical process mining event log transformed from staged healthcare events:
* `case_id` (STRING): Unique patient journey identifier.
* `activity_name` (STRING): Standardized clinical stage name.
* `event_timestamp` (TIMESTAMP): Event commencement timestamp.
* `activity_sequence` (INT64): Deterministic chronological sequence number.
* `is_loopback` (INT64): Flag (0 or 1) identifying operational rework loops.
* Metadata attributes: `patient_id`, `event_id`, `department`, `status`, `waiting_time_minutes`.

---

## Mart Model: `fct_pathway_transitions` (Week 2)

Calculates Directly-Follows Graph (DFG) clinical pathway transitions and handover durations between consecutive activities:
* `from_activity` (STRING): Origin clinical stage.
* `to_activity` (STRING): Destination clinical stage.
* `transition_count` (INT64): Empirical frequency of patient handovers across the edge.
* `avg_transition_time_minutes` (FLOAT64): Average elapsed duration in minutes.
* `min_transition_time_minutes` (FLOAT64): Minimum elapsed duration in minutes.
* `max_transition_time_minutes` (FLOAT64): Maximum elapsed duration in minutes.

---

## Prerequisites to Execute dbt

1. Install `dbt-bigquery` in your virtual environment:
   ```powershell
   pip install dbt-bigquery
   ```
2. Configure your profile in `%USERPROFILE%\.dbt\profiles.yml`:
   * Copy the template from `dbt/profiles.yml.example` to `~/.dbt/profiles.yml`.
   * Fill in your GCP project ID.
3. Authenticate with Google Cloud:
   ```powershell
   gcloud auth application-default login
   ```

---

## Running dbt Commands (from `dbt/` folder)

* **Test Connection:**
  ```powershell
  dbt debug
  ```
* **Run Staging Model:**
  ```powershell
  dbt run
  ```
* **Run Data Quality Tests:**
  ```powershell
  dbt test
  ```
