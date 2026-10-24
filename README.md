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

## Official Week 2 Deliverables: Process Discovery & As-Is Process Mining (PM4Py)

This section documents the deliverables for **Week 2** of the official internship requirements: As-Is process discovery, event log standardization, pathway variant analysis, rework loop quantification, workflow inefficiency identification, and directed process map visualization.

> [!NOTE]
> **Implementation Architecture & Technology Stack:**
> The complete Week 2 analysis was executed locally using Python (`.venv`), **SQLite** (`database/careflow.db`), PM4Py (Process Mining for Python), and Graphviz. As in Week 1, Google BigQuery was not used in the active data pipeline and dbt transformations were not executed in the cloud. All process-mining metrics and inefficiency statistics are mathematically derived and verified from the local SQLite database and standardized CSV event logs.

### Week 2 Workflow Execution Commands

1. **Run As-Is Process Discovery & Visualization Pipeline:**
   ```powershell
   .\.venv\Scripts\python.exe src/process_discovery.py
   ```
2. **Run Workflow Inefficiencies & Disparities Analysis Pipeline:**
   ```powershell
   .\.venv\Scripts\python.exe src/workflow_inefficiencies.py
   ```
3. **Run Comprehensive Week 2 Verification Suite (Days 1–6):**
   ```powershell
   .\.venv\Scripts\python.exe src/verify_week2.py
   ```

### Week 2 Key Findings & Process Mining Metrics

* **Canonical Event Standardization:** Standardized event log created at `data/processed/standardized_event_log_v2.csv` with standard process mining fields: `Case_ID`, `Activity_Name`, and `Timestamp`, preserving 100% of event metadata (`patient_id`, `department`, `waiting_time_minutes`, `is_loopback`).
* **Process Scale:** Exactly 500 patient cases, 420 unique patients, 3,030 total events, and 2,530 observed consecutive transitions ($3,030 \text{ events} - 500 \text{ cases} = 2,530$).
* **Clinical Boundary Adherence:**
  * **Start Activity:** 100% of patient journeys (500 cases) start at `Registration`.
  * **End Activity:** 100% of patient journeys (500 cases) conclude at `Discharge`.
* **Clinical Activities (6 Stages):** `Registration`, `Triage`, `Consultation`, `Diagnostics`, `Treatment`, `Discharge`.
* **Discovered Pathway Variants:** 11 unique patient journey variants discovered via PM4Py trace extraction:
  * **Clean Cohort (Variants V1 & V2):** 346 visits (**69.2%**) follow standard linear paths with zero loop-backs.
  * **Rework Cohort (Variants V3–V11):** 154 visits (**30.8%**) encounter 1, 2, or 3 loop-backs.
* **Directly-Follows Graph (DFG) Transitions (9 Distinct Types):**
  | Transition | Volume | % of Source Stage | % of All Transitions | Pathway Classification |
  | :--- | :---: | :---: | :---: | :--- |
  | `Registration -> Triage` | 527 | 100.0% | 20.83% | Standard Forward Flow |
  | `Treatment -> Discharge` | 500 | 94.52% | 19.76% | Standard Forward Flow |
  | `Triage -> Consultation` | 500 | 94.88% | 19.76% | Standard Forward Flow |
  | `Consultation -> Treatment` | 314 | 50.97% | 12.41% | Direct Treatment Path |
  | `Consultation -> Diagnostics` | 302 | 49.03% | 11.94% | Diagnostic Workup Path |
  | `Diagnostics -> Treatment` | 215 | 64.95% | 8.50% | Post-Diagnostic Treatment |
  | `Diagnostics -> Consultation` | 116 | 35.05% | 4.58% | **Clinical Loop-Back (Lab/imaging review)** |
  | `Treatment -> Diagnostics` | 29 | 5.48% | 1.15% | **Clinical Loop-Back (In-treatment diagnostic workup)** |
  | `Triage -> Registration` | 27 | 5.12% | 1.07% | **Operational Loop-Back (Admin/triage rework)** |

### Identified Workflow Inefficiencies & Disparities

The Week 2 Day 5 analysis quantified the operational friction introduced by the 172 loop-back transitions across the 154 rework visits:
* **Administrative Intake Rework (`Triage -> Registration`):** 27 visits (5.4% of cases), generating 54 extra events (27 repeat registrations + 27 repeat triages).
* **Diagnostic Review Queue Contention (`Diagnostics -> Consultation`):** 116 visits (23.2% of cases), generating 116 extra consultations and inflating consultation demand to 616 events (+23.2% physician load on the primary hospital bottleneck).
* **In-Treatment Diagnostic Escalation (`Treatment -> Diagnostics`):** 29 visits (5.8% of cases), generating 58 extra events (29 secondary diagnostics + 29 resumed treatments).
* **Stage Queue Waiting-Time Penalty:** Rework visits endure **150.52 min** of queue delays vs. **100.66 min** for clean visits (**+49.85 min / +49.5% delay**).
* **Elapsed Journey Length-of-Stay Penalty:** Rework visits average **328.53 min (5.48h)** vs. **220.12 min (3.67h)** for clean visits (**+108.40 min / +49.2% longer stay**).

### Visual, Analytical & Data Artifacts Produced

* **As-Is Directed Process Map:** `reports/as_is_process_map.png` (High-resolution publication-quality 300 DPI pathway diagram illustrating forward flow vs. loop-back arcs).
* **Graphviz DOT Language Model:** `reports/as_is_process_map.dot` (Standard Graphviz directed graph specification export).
* **Transition Metrics Table:** `reports/dfg_transitions.csv` (Tabular export of discovered DFG transition volumes and stage percentages).
* **Standardized Event Log:** `data/processed/standardized_event_log_v2.csv` (Standardized event log ready for advanced process mining and conformance checking).
* **Clinical Pathway Analysis Summary Report:** `reports/week2_process_analysis_summary.md` (Comprehensive 241-line Markdown report detailing all 11 pathway variants, bottlenecks, and clinical hypotheses).
* **Workflow Inefficiencies Summary:** `reports/workflow_inefficiencies.csv` (Structured catalog of identified rework categories, affected cases, and empirical queue impacts).
* **Week 2 Comprehensive Verification Runner:** `src/verify_week2.py` (Automated verification runner checking baseline preservation, dependencies, event log integrity, DFG discovery, deliverable artifacts, summary report, inefficiencies catalog, and unit tests).

## Cloud Analytics: Google BigQuery & dbt Integration (Weeks 1 & 2)

This section documents the end-to-end cloud data warehouse architecture implemented in **Google BigQuery** and **dbt Core**:

### Cloud Infrastructure & Warehouse Setup
* **GCP Project ID:** `care-flow-analytics` (Region: `asia-south1`)
* **Raw Data Store:** `care-flow-analytics.Careflow_raw.healthcare_event_log_raw` (2,823 verified events, 500 cases, 420 patients).
* **dbt Transformations:** Managed under `dbt/` and executed using `dbt-bigquery`.

### Materialized Cloud Models (`careflow_staging`)
1. **Staging Event Log (`stg_healthcare_events`):** Standardizes raw hospital events into process-mining format (`case_id`, `activity_name`, `event_timestamp`, `activity_sequence`, `waiting_time_minutes`).
2. **Canonical Process Mining Event Log (`fct_standardized_event_log`):** Canonical event log conforming to PM4Py standards (`case_id`, `activity_name`, `event_timestamp`, `activity_sequence`, `is_loopback`).
3. **Clinical Pathway Transitions Mart (`fct_pathway_transitions`):** Directly-Follows Graph (DFG) handover metrics between consecutive clinical activities (volumes, avg, min, and max handover minutes).

### Cloud-to-Process-Mining Workflow Execution
```powershell
# 1. Test BigQuery connectivity and profile
dbt debug --project-dir dbt

# 2. Compile and execute dbt transformations in BigQuery
dbt run --project-dir dbt

# 3. Execute cloud-to-PM4Py discovery pipeline
.\.venv\Scripts\python.exe src/process_discovery_bigquery.py
```

### Cloud Deliverable Artifacts Produced
* **Standardized Cloud Event Log:** `data/processed/bigquery_standardized_event_log.csv` (2,823 events extracted from BigQuery).
* **Cloud DFG Transitions Metric:** `reports/dfg_transitions_bigquery.csv` (100% exact numerical parity with baseline).
* **Cloud As-Is Process Map:** `reports/as_is_process_map_bigquery.png` and `reports/as_is_process_map_bigquery.dot`.
* **Cloud Process Discovery Report:** `reports/week2_bigquery_process_mining_summary.md`.

## Official Week 3 Deliverables: Pathway Transition Time Analysis (SQL & Python)

This section documents the deliverables for **Week 3** of the official internship requirements: calculating average transition and handover times between healthcare process stages using SQL and Python.

### Week 3 Workflow Execution Commands

1. **Run Transition Time Analysis Pipeline:**
   ```powershell
   .\.venv\Scripts\python.exe src/transition_analysis.py
   ```
2. **Run Comprehensive Week 3 Verification Suite:**
   ```powershell
   .\.venv\Scripts\python.exe src/verify_week3.py
   ```

### Week 3 Discovered Transition Times (Process Mining Pathways)

| Transition Pathway | Count | % of All | Loop? | Mean (min) | Median (min) | Std Dev (min) | Min (min) | Max (min) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Registration -> Triage` | 527 | 20.83% | No | **19.64** | 18.0 | 8.55 | 6.0 | 55.0 |
| `Triage -> Consultation` | 500 | 19.76% | No | **46.71** | 43.0 | 18.98 | 13.0 | 129.0 |
| `Treatment -> Discharge` | 500 | 19.76% | No | **71.32** | 73.0 | 21.35 | 29.0 | 130.0 |
| `Consultation -> Treatment` | 314 | 12.41% | No | **48.39** | 47.0 | 14.34 | 21.0 | 87.0 |
| `Consultation -> Diagnostics` | 302 | 11.94% | No | **59.25** | 57.0 | 18.72 | 21.0 | 123.0 |
| `Diagnostics -> Treatment` | 215 | 8.50% | No | **59.74** | 59.0 | 16.27 | 26.0 | 120.0 |
| `Diagnostics -> Consultation` | 116 | 4.58% | **Yes** | **73.20** | 71.5 | 24.14 | 25.0 | 149.0 |
| `Treatment -> Diagnostics` | 29 | 1.15% | **Yes** | **86.34** | 91.0 | 23.95 | 48.0 | 141.0 |
| `Triage -> Registration` | 27 | 1.07% | **Yes** | **17.22** | 17.0 | 3.80 | 11.0 | 24.0 |

### Week 3 Deliverable Artifacts Produced

* **Process Mining Transition Summary:** `data/processed/transition_time_analysis.csv` (Full statistical breakdown for all 9 discovered clinical pathways).
* **Baseline Transition Summary:** `data/processed/baseline_transition_times.csv` (Handover metrics across the 6 baseline relational pathways).
* **Granular Transition Records:** `data/processed/visit_transitions_detail.csv` (2,530 individual event-pair transition records).
* **SQL Query Files:** `sql/queries/11_transition_times.sql` and `sql/queries/12_process_mining_transition_times.sql`.
* **Reusable SQL Views:** `sql/views/v_transition_times.sql` and `sql/views/v_process_mining_transition_times.sql`.
* **Analysis Summary Report:** `reports/week3_transition_time_analysis.md`.
