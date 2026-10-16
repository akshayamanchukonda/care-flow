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
│   └── staging/
│       ├── schema.yml              # Documentation & automated data quality tests
│       └── stg_healthcare_events.sql # Staging transformation model
└── README.md                       # This documentation guide
```

---

## Staging Model: `stg_healthcare_events`

Standardizes the raw dataset into canonical process mining format:
* `case_id` (STRING): Normalized from `visit_id`. Represents the single patient journey instance.
* `activity_name` (STRING): Cleaned event/activity name (`Registration`, `Triage`, `Consultation`, `Diagnostics`, `Treatment`, `Discharge`).
* `event_timestamp` (TIMESTAMP): Standard ISO timestamp for process sequencing.
* `activity_sequence` (INT64): Ordered index (1, 2, 3...) calculated via `ROW_NUMBER() OVER (PARTITION BY case_id ORDER BY event_timestamp ASC)`.
* Supporting attributes: `patient_id`, `event_id`, `department`, `status`, and `waiting_time_minutes`.

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
