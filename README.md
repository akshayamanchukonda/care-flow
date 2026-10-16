# care-flow
CareFlow – Healthcare Data Analytics

CareFlow is a healthcare data analytics project that uses Python and process mining to analyze patient journeys, identify bottlenecks, and understand hospital waiting times. It aims to help healthcare professionals gain insights into hospital workflows and improve operational efficiency.

## Stage 2: Synthetic Healthcare Event Data Generation

To generate the reproducible synthetic event log (500 patient journeys), run the following command from the repository root:

```powershell
.\.venv\Scripts\python.exe src/data_generator.py
```

This script:
- Generates 500 patient journeys across emergency and outpatient care stages (`Registration`, `Triage`, `Consultation`, `Diagnostics`, `Treatment`, `Discharge`).
- Models realistic queue waiting times, department pathways, and discharge dispositions.
- Saves the output to `data/raw/healthcare_event_log.csv`.
- Runs built-in data validation checks for column completeness, missing values, unique identifiers, non-negative wait times, and chronological order.

## Stage 3: SQLite Database Schema and Data Ingestion

To build the relational SQLite database and ingest the validated event log dataset, run the following command from the repository root:

```powershell
.\.venv\Scripts\python.exe src/db_manager.py
```

This script:
- Creates the local database file at `database/careflow.db`.
- Applies the relational schema in `database/schema.sql` (defining `patients`, `visits`, and `events` tables with primary/foreign keys, check constraints, and performance indexes).
- Enforces SQLite foreign keys (`PRAGMA foreign_keys = ON`) and performs all inserts within an atomic transaction.
- Ingests 420 patients, 500 visits, and 2,823 events without data loss or duplication upon reruns.
- Verifies row counts, foreign key integrity, and absence of unexpected nulls.

## Stage 4: SQL Operational Analysis

To run all analytical SQL queries and apply reusable views against `database/careflow.db`, run:

```powershell
.\.venv\Scripts\python.exe src/run_sql_analysis.py
```

### Analytical Queries & Views Created

* **Queries (`sql/queries/`):**
  1. `01_overall_summary.sql`: High-level operational dataset statistics.
  2. `02_waiting_time_by_stage.sql`: Average and exact median waiting time by care stage.
  3. `03_department_waiting_times.sql`: Waiting-time statistics across all hospital departments.
  4. `04_bottleneck_ranking.sql`: Stages ranked by average queue delay and share of total hospital wait time.
  5. `05_arrivals_by_hour.sql`: Hourly patient arrival distribution.
  6. `06_visit_outcomes.sql`: Visit outcomes and disposition breakdown.
  7. `07_visit_durations.sql`: Total observed journey duration from arrival to discharge.
  8. `08_diagnostics_rate.sql`: Diagnostics utilization and skip rates.
  9. `09_event_counts_and_avg_wait.sql`: Stage volumes and patient coverage.
  10. `10_visit_level_summary.sql`: Consolidated visit-level metrics prepared for BI dashboarding.
* **Reusable Views (`sql/views/`):**
  * `v_stage_waiting_times`: Stage volume and waiting time metrics.
  * `v_department_performance`: Department operational volume and wait load.
  * `v_visit_summary`: Complete visit-level operational metrics.
  * `v_visit_outcomes`: Disposition volume and duration averages.

### Key Operational Findings

1. **Dataset Totals:** 420 unique patients, 500 visits, and 2,823 process events recorded between Oct 1 and Oct 31, 2026.
2. **Primary Bottleneck:** `Consultation` has the longest queue delay, averaging **34.70 minutes** (median 31.0 mins), representing **32.58%** of all recorded waiting time in the hospital.
3. **Diagnostics Queue:** `Diagnostics` is the second-longest waiting stage at **29.90 minutes** (median 27.0 mins).
4. **Diagnostics Utilization:** 64.6% of visits (323 visits) utilized Diagnostics; 35.4% (177 visits) safely skipped Diagnostics.
5. **Observed Journey Durations:** The average patient journey lasts **231.5 minutes (~3.86 hours)** from check-in to discharge.
6. **Patient Outcomes:** 73.8% Discharged Home, 19.8% Admitted to Inpatient Ward, 6.4% Transferred to Specialist Care.

## Stage 5: Python Statistical and Process Analysis

To execute the statistical process analysis and export the 6 Power BI-ready datasets, run:

```powershell
.\.venv\Scripts\python.exe src/process_analysis.py
```

### What This Script Calculates

1. **Data Quality Assurance:** Verifies database completeness (420 patients, 500 visits, 2,823 events), zero missing values, non-negative wait times, and chronological integrity.
2. **Descriptive Statistics:** Calculates count, mean, median, standard deviation, and percentiles (25th, 75th, 90th) for waiting times across care stages and departments.
3. **Stage & Bottleneck Analysis:** Ranks stages by average waiting time and determines each stage's percentage of total hospital waiting time.
4. **Department Load & Queue Patterns:** Analyzes patient volume, queue distributions, and waiting loads across all 13 hospital units.
5. **Visit-Level Metrics:** Synthesizes journey durations, total waiting minutes, and arrival hours for each of the 500 individual visits.
6. **Long-Wait & Outlier Detection:** Identifies events with wait times exceeding 30 minutes, 60 minutes, and statistical outliers using the standard 1.5x IQR rule (threshold: 50.5 minutes).
7. **Diagnostics Impact:** Quantifies how diagnostics utilization affects overall journey duration (visits requiring diagnostics average 257.6 mins vs. 183.8 mins for visits skipping diagnostics).

### Exported Datasets (`data/processed/`)

| Exported File | Rows | Description |
| :--- | :---: | :--- |
| `stage_waiting_time_analysis.csv` | 6 | Care stages ranked by bottleneck severity with full percentile distributions. |
| `department_waiting_time_analysis.csv` | 13 | Department-level operational volumes, queues, and percentage wait load. |
| `visit_level_analysis.csv` | 500 | Consolidated visit table (1 row per visit) with duration, arrival hour, and outcomes. |
| `long_wait_analysis.csv` | 6 | Care stages broken down by moderate delays (>30m), severe delays (>60m), and statistical outliers. |
| `diagnostics_analysis.csv` | 2 | Comparison of visits with vs. without diagnostics and their duration impact. |
| `overall_kpis.csv` | 13 | Executive KPI summary table (Volume, Queues, Bottlenecks, Delays, Throughput). |

## Official Week 1 Deliverables: Clinical Pathway Process Mining

This section documents the deliverables for **Week 1** of the official internship requirements.

> [!NOTE]
> **Technology Substitution Notice:** Due to cloud resource constraints on Google Cloud project creation, **SQLite** was utilized as the queryable data store (substituting Google BigQuery) and a **Python/SQL pipeline** was used for data cleaning and standardization (substituting dbt). Full dbt and BigQuery configurations are prepared in `dbt/` and `src/upload_to_bigquery.py` for future cloud deployment.

### Week 1 Workflow Execution Commands

1. **Generate Revised Event Log with Loop-Backs (Rework Loops):**
   ```powershell
   .\.venv\Scripts\python.exe src/data_generator_v2.py
   ```
2. **Execute Ingestion & Cleaning Pipeline (SQLite & Python/SQL):**
   ```powershell
   .\.venv\Scripts\python.exe src/clean_events_pipeline.py
   ```
3. **Run Comprehensive Week 1 Verification Suite:**
   ```powershell
   .\.venv\Scripts\python.exe src/verify_week1.py
   ```

### Week 1 Outputs & Process Mining Standardization

* **Revised Raw Event Log:** `data/raw/healthcare_event_log_v2.csv` (500 visits, 420 patients, 3,030 events, 214 loop-backs across 154 cases).
* **Cleaned Standardized Event Log:** `data/processed/cleaned_healthcare_event_log_v2.csv` (3,030 events normalized with canonical process mining fields: `case_id`, `activity_name`, `event_timestamp`, `activity_sequence`, `is_loopback`).
* **SQLite Relational Storage:** `database/careflow.db`:
  * `raw_healthcare_events_v2`: Raw event storage table.
  * `stg_healthcare_events_v2`: Cleaned and standardized staging table.
* **Preservation:** The original baseline dataset (`data/raw/healthcare_event_log.csv`) remains untouched with verified SHA-256 integrity.
