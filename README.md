# CareFlow — Hospital Patient Pathway Optimization & Clinical Process Mining

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![dbt Core 1.13](https://img.shields.io/badge/dbt--core-1.13-orange.svg)](https://www.getdbt.com/)
[![Google BigQuery](https://img.shields.io/badge/Google%20BigQuery-cloud%20warehouse-blue.svg)](https://cloud.google.com/bigquery)
[![PM4Py 2.7](https://img.shields.io/badge/PM4Py-2.7-green.svg)](https://pm4py.fit.fraunhofer.de/)
[![SQLite 3](https://img.shields.io/badge/SQLite-3-lightgrey.svg)](https://www.sqlite.org/)

CareFlow is an end-to-end healthcare data analytics and clinical process-mining platform designed to analyze patient journeys, identify operational bottlenecks, quantify queue waiting delays, and discover As-Is clinical pathways.

The platform processes emergency and outpatient encounters through a 6-stage clinical pathway (`Registration` $\rightarrow$ `Triage` $\rightarrow$ `Consultation` $\rightarrow$ `Diagnostics` $\rightarrow$ `Treatment` $\rightarrow$ `Discharge`) to uncover operational rework loops and length-of-stay disparities.

---

## Executive Summary & Quick Links

CareFlow operates with a **dual-layer architecture**:
1. **Local Analytics Engine (SQLite + Python + PM4Py):** A self-contained, offline environment for reproducible local analysis, SQL querying, and continuous integration testing.
2. **Cloud Analytics Pipeline (Google BigQuery + dbt Core + PM4Py):** A cloud data warehouse pipeline processing synthetic hospital logs through automated staging transformations, canonical marts, schema constraint tests, and direct PM4Py cloud ingestion.

### Key Operational & Clinical Findings

* **Primary Hospital Bottleneck:** `Consultation` exhibits the longest waiting delay, averaging **34.70 minutes** (median 31.0 mins), representing **32.58%** of total hospital queue time.
* **Diagnostics Queue:** `Diagnostics` is the second-longest waiting stage at **29.90 minutes** (median 27.0 mins) with a **64.6%** patient utilization rate.
* **Operational Rework Penalty:** Visits encountering rework loops endure **150.52 minutes** of queue delay vs. **100.66 minutes** for clean visits (**+49.85 min / +49.5% delay**), extending total length of stay from **3.67 hours** to **5.48 hours** (**+49.2% longer stay**).
* **Clinical Pathways Discovered:** PM4Py process discovery revealed **11 distinct clinical variants**: a clean cohort of 346 visits (69.2%) and a rework cohort of 154 visits (30.8%).

### Key Project Artifacts & Direct Links

| Deliverable Artifact | Category | Format | Description |
| :--- | :--- | :---: | :--- |
| [**Week 1 & 2 Final Completion Report**](reports/week1_week2_final_completion_report.md) | Audit & Handoff | Markdown | Comprehensive audit of all requirements, mathematical reconciliations, and test proofs. |
| [**Enhanced Cloud Process Map**](reports/as_is_process_map_bigquery.png) | Process Discovery | PNG (340 KB) | 9-transition As-Is process map with 3 highlighted rework loops generated from BigQuery. |
| [**Enhanced Cloud Process Model**](reports/as_is_process_map_bigquery.dot) | Process Discovery | Graphviz DOT | Machine-readable DOT specification for the 9-transition enhanced model. |
| [**Baseline Cloud Process Map**](reports/as_is_process_map_bigquery_baseline.png) | Process Discovery | PNG (291 KB) | 6-transition linear baseline process map generated from BigQuery. |
| [**Baseline Cloud Process Model**](reports/as_is_process_map_bigquery_baseline.dot) | Process Discovery | Graphviz DOT | Machine-readable DOT specification for the 6-transition baseline model. |
| [**Local As-Is Process Map**](reports/as_is_process_map.png) | Process Discovery | PNG (307 KB) | Local 9-transition process map discovered from SQLite via PM4Py. |
| [**Local Process Analysis Report**](reports/week2_process_analysis_summary.md) | Clinical Analysis | Markdown | Comprehensive 241-line clinical pathway report detailing all 11 variants and hypotheses. |
| [**Cloud Process Mining Summary**](reports/week2_bigquery_process_mining_summary.md) | Cloud Analysis | Markdown | Process discovery summary report derived directly from dbt BigQuery marts. |
| [**Cloud Baseline Mining Summary**](reports/week2_bigquery_process_mining_baseline_summary.md) | Cloud Analysis | Markdown | Baseline process discovery summary report from BigQuery baseline views. |
| [**Workflow Inefficiencies Catalog**](reports/workflow_inefficiencies.csv) | Process Mining | CSV | Structured catalog of 4 identified rework categories, affected visits, and wait penalties. |
| [**Cloud DFG Transitions Table**](reports/dfg_transitions_bigquery.csv) | Transition Metrics | CSV | Empirical transition volumes and source-activity percentages from BigQuery. |

---

## Dual-Workflow Architecture

CareFlow maintains two complementary, independently verified workflows:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   CARE FLOW ARCHITECTURE                               │
└────────────────────────────────────────────────────────────────────────────────────────┘
                               │                                       │
              ┌────────────────┴──────────────────┐   ┌────────────────┴──────────────────┐
              │          LOCAL WORKFLOW           │   │          CLOUD WORKFLOW           │
              │   (Offline Testing & Analysis)    │   │  (Cloud Data Warehouse & dbt)     │
              └───────────────────────────────────┘   └───────────────────────────────────┘
                               │                                       │
             • Python Simulation Generator           • Python Raw Uploader
               src/data_generator.py                   src/upload_to_bigquery.py
               src/data_generator_v2.py                                │
                               │                                       ▼
                               ▼                     • Google BigQuery Raw Store
             • Relational SQLite Storage               care-flow-analytics.Careflow_raw
               database/careflow.db                    - healthcare_event_log_raw (2,823)
               - raw_healthcare_events_v2              - healthcare_event_log_v2_raw (3,030)
               - stg_healthcare_events_v2                              │
                               │                                       ▼
                               ▼                     • dbt Core Staging Layer
             • SQL Operational Analytics               careflow_staging.stg_healthcare_events
               sql/queries/ (01..10)                   careflow_staging.stg_healthcare_events_v2
               sql/views/ (4 reusable views)           (event_id deduplication & sequencing)
                               │                                       │
                               ▼                                       ▼
             • Local Staging & Discovery             • dbt Core Marts Layer
               src/clean_events_pipeline.py            careflow_staging.fct_standardized_event_log*
               src/process_discovery.py                careflow_staging.fct_pathway_transitions*
               src/workflow_inefficiencies.py                          │
                               │                                       ▼
                               ▼                     • Direct BigQuery -> PM4Py Ingestion
             • Local Process Map & Reports             src/process_discovery_bigquery.py
               reports/as_is_process_map.png           reports/as_is_process_map_bigquery.png
               reports/week2_process_analysis_summary  reports/as_is_process_map_bigquery_baseline
```

### A. Local Workflow (Offline Testing & Analysis Engine)
- **Synthetic Simulation:** Python generators create raw event logs with realistic queues, clinical stages, and rework loops.
- **Relational Storage:** SQLite database at `database/careflow.db` enforces relational integrity, check constraints, foreign keys, and indexes across `patients`, `visits`, and `events`.
- **SQL Analysis:** 10 analytical SQL queries and 4 reusable views compute departmental queues, bottleneck rankings, arrival patterns, and journey durations.
- **Offline Process Mining:** Python engine cleans staging tables, computes process KPIs, discovers PM4Py Directly-Follows Graphs (DFGs), and exports local publication-ready maps.

### B. Cloud Workflow (Google BigQuery & dbt Core Pipeline)
- **Raw Data Ingestion:** Automated ingestion uploads raw event logs into Google BigQuery dataset `Careflow_raw`.
- **dbt Transformation Pipeline:** dbt Core manages modular transformations:
  - Staging views with native `QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ...)` deduplication and deterministic timestamp sequencing.
  - Standardized marts conforming to canonical process mining standards (`case_id`, `activity_name`, `event_timestamp`, `is_loopback`).
  - Transition marts computing handover durations (average, min, max) using SQL window functions (`LEAD()`).
- **Cloud-to-PM4Py Discovery:** Python client directly queries BigQuery views via the BigQuery REST API, formats event logs, and generates publication-quality As-Is process models with zero intermediate local shortcuts.

---

## Dataset Architecture: Baseline vs. Enhanced Datasets

CareFlow maintains a strict separation between two distinct datasets to support both forward-only baseline analysis and advanced rework loop discovery:

| Dataset Dimension | Baseline Dataset | Enhanced Dataset |
| :--- | :--- | :--- |
| **Total Event Records** | **2,823 events** | **3,030 events** |
| **Unique Patient Visits (Cases)** | 500 patient visits | 500 patient visits |
| **Unique Patients** | 420 unique patients | 420 unique patients |
| **Clinical Flow Pattern** | Forward-only linear pathways | Linear flow + 3 operational & clinical rework loops |
| **Rework Events (`is_loopback == 1`)**| 0 events | **214 repeat events** across **154 visits** (30.8% of cases) |
| **Discovered DFG Transitions** | **6 transition types** (2,323 handovers) | **9 transition types** (2,530 handovers) |
| **Clinical Journey Variants** | 2 variants | 11 variants |
| **Raw CSV File** | `data/raw/healthcare_event_log.csv` | `data/raw/healthcare_event_log_v2.csv` |
| **BigQuery Raw Table** | `Careflow_raw.healthcare_event_log_raw` | `Careflow_raw.healthcare_event_log_v2_raw` |
| **dbt Staging Model** | `stg_healthcare_events` | `stg_healthcare_events_v2` |
| **dbt Canonical Mart** | `fct_standardized_event_log` | `fct_standardized_event_log_v2` |
| **dbt Transitions Mart** | `fct_pathway_transitions` | `fct_pathway_transitions_v2` |
| **Standardized CSV Export** | `bigquery_standardized_event_log_baseline.csv` | `bigquery_standardized_event_log.csv` |
| **As-Is Process Map** | `as_is_process_map_bigquery_baseline.png` | `as_is_process_map_bigquery.png` |

### Precision Terminology for Loop-Back & Rework Metrics

To eliminate ambiguity, metrics are rigorously classified into three distinct concepts:
1. **Rework Event Records ($N = 214$):** The total count of activity rows flagged with `is_loopback == 1`. These occur across $154$ distinct patient visits ($30.8\%$ rework rate):
   - `Consultation`: 116 repeat events (from diagnostic review returns)
   - `Treatment`: 29 repeat events (from treatment resumption post-escalation)
   - `Registration`: 27 repeat events (from triage administrative returns)
   - `Triage`: 27 repeat events (from re-triage post-registration)
   - `Diagnostics`: 15 repeat events (from secondary diagnostic workups)
   - *Sum:* $116 + 29 + 27 + 27 + 15 = 214$ repeat records.
2. **Directed Backward DFG Transitions ($N = 172$):** The count of consecutive event-pair transitions that hand off from a later clinical stage back to an earlier stage:
   - `Diagnostics -> Consultation`: 116 transitions
   - `Treatment -> Diagnostics`: 29 transitions
   - `Triage -> Registration`: 27 transitions
   - *Sum:* $116 + 29 + 27 = 172$ directed backward transitions.
3. **Net Row Count Difference ($3,030 - 2,823 = 207$):**
   In `src/data_generator_v2.py`, evaluating `has_triage_loop` prior to `requires_diagnostics` shifted the pseudo-random sequence, causing 316 cases to receive initial diagnostics in v2 versus 323 in v1 ($323 - 316 = 7$).
   $$\text{Net Difference} = 214 \text{ (rework events)} - 7 \text{ (fewer initial diagnostics)} = 207$$

---

## Testing & Verification Suite

All local test suites and cloud verification runners have been executed and verified. The table below lists the exact commands, targets, checks performed, and empirical results:

| Verification Suite | Exact Command | Scope / Components Checked | Result & Status | Execution Evidence |
| :--- | :--- | :--- | :---: | :--- |
| **Python Unit Tests** | `python -m unittest discover tests` | Core algorithms, data generators, staging cleaners, sequencing, and loop-back flags across 5 modules. | **65 PASS / 0 FAIL**<br>`[OK]` | Freshly verified this session (3.44s) |
| **Week 1 Verification Runner** | `python src/verify_week1.py` | Baseline CSV preservation, SQLite tables (`raw_healthcare_events_v2`, `stg_healthcare_events_v2`), null checks, and loop-back counts. | **5 PASS / 0 FAIL**<br>`[100% OPERATIONAL]` | Freshly verified this session (~1.5s) |
| **Week 2 Verification Runner** | `python src/verify_week2.py` | PM4Py DFG discovery (9 edges), variants (11 paths), artifact existence, inefficiency catalog, and 41 internal unit tests. | **8 CHECKS (41 TESTS) PASS**<br>`[ALL 41 PASSED]` | Freshly verified this session (1.49s) |
| **dbt BigQuery Debug** | `dbt debug --project-dir dbt` | Profile validation (`profiles.yml`), project config (`dbt_project.yml`), Git dependency, and BigQuery connection test. | **ALL 4 CHECKS PASSED**<br>`[Connection OK]` | Verified this session (~19s, exit code 0) |
| **dbt DAG Compilation** | `dbt compile --project-dir dbt` | SQL syntax, Jinja templating, dependency graph, and model compilation for 6 models, 52 tests, and 2 sources. | **ALL COMPILED**<br>`[0 Errors]` | Verified this session (~14s, exit code 0) |
| **dbt Model Materialization** | `dbt run --project-dir dbt` | Recreates/updates 6 BigQuery staging and mart views in `care-flow-analytics.careflow_staging`. | **PASS=6 / TOTAL=6**<br>`[0 Errors]` | Verified this session (32.48s, exit code 0) |
| **dbt Schema Data Tests** | `dbt test --project-dir dbt` | Validates 52 schema tests (`not_null`, `unique`, `accepted_values`) across all 6 models in BigQuery. | **PASS=52 FAIL=0 ERROR=0**<br>`[TOTAL=52 PASS]` | Verified this session via BigQuery (151.49s, task-3543 log & `dbt/target/run_results.json`) |
| **Git Diff Whitespace Check** | `git diff --check` | Validates that no trailing whitespace or CRLF formatting corruptions exist in modified files. | **CLEAN**<br>`[Exit code: 0]` | Freshly verified this session (<1s) |

> [!NOTE]
> All commands use the project virtual environment (`.\.venv\Scripts\python.exe` or `.\.venv\Scripts\dbt.exe` on Windows). Cloud dbt commands require active Google Cloud Application Default Credentials (`gcloud auth application-default login`).

---

## Detailed Project Stages & Local Analytics Execution

### Stage 2: Synthetic Healthcare Event Data Generation
To generate the reproducible synthetic event log (500 patient journeys), run from the repository root:
```powershell
.\.venv\Scripts\python.exe src/data_generator.py
```
- Generates 500 patient journeys across emergency and outpatient care stages.
- Models queue waiting times, department pathways, and discharge dispositions.
- Saves output to `data/raw/healthcare_event_log.csv` (2,823 rows).
- Runs built-in validations: column completeness, zero missing values, unique IDs, non-negative wait times, chronological ordering.

### Stage 3: SQLite Database Schema & Data Ingestion
To build the relational SQLite database and ingest the baseline dataset:
```powershell
.\.venv\Scripts\python.exe src/db_manager.py
```
- Creates local database at `database/careflow.db`.
- Applies relational schema in `database/schema.sql` (defining `patients`, `visits`, `events` with keys, constraints, and indexes).
- Enforces foreign keys (`PRAGMA foreign_keys = ON`) and transactional atomic inserts.
- Ingests 420 patients, 500 visits, and 2,823 events without duplication upon reruns.

### Stage 4: SQL Operational Analysis
To run all analytical SQL queries and apply reusable views against `database/careflow.db`:
```powershell
.\.venv\Scripts\python.exe src/run_sql_analysis.py
```
* **Queries (`sql/queries/`):**
  1. `01_overall_summary.sql`: Operational dataset totals and averages.
  2. `02_waiting_time_by_stage.sql`: Average and exact median waiting time by stage.
  3. `03_department_waiting_times.sql`: Waiting statistics across all 13 hospital units.
  4. `04_bottleneck_ranking.sql`: Care stages ranked by average queue delay and total wait share.
  5. `05_arrivals_by_hour.sql`: Hourly patient arrival distribution.
  6. `06_visit_outcomes.sql`: Visit outcomes and disposition breakdown.
  7. `07_visit_durations.sql`: Total observed journey duration from arrival to discharge.
  8. `08_diagnostics_rate.sql`: Diagnostics utilization and skip rates.
  9. `09_event_counts_and_avg_wait.sql`: Stage volumes and patient coverage.
  10. `10_visit_level_summary.sql`: Consolidated visit-level metrics for BI reporting.
* **Reusable Views (`sql/views/`):** `v_stage_waiting_times`, `v_department_performance`, `v_visit_summary`, `v_visit_outcomes`.

### Stage 5: Python Statistical & Queue Analysis
To execute statistical queue analysis and export BI-ready datasets:
```powershell
.\.venv\Scripts\python.exe src/process_analysis.py
```
* **Calculations:** Mean, median, standard deviation, and percentiles (25th, 75th, 90th) across care stages and departments; 1.5x IQR outlier detection (>50.5 min threshold); diagnostics duration impact (257.6 min with diagnostics vs. 183.8 min without).
* **Exported Datasets (`data/processed/`):** `stage_waiting_time_analysis.csv`, `department_waiting_time_analysis.csv`, `visit_level_analysis.csv`, `long_wait_analysis.csv`, `diagnostics_analysis.csv`, `overall_kpis.csv`.

---

## Official Week 1 & Week 2 Deliverables: Process Mining & Inefficiencies

### Week 1 Workflow Execution Commands
1. **Generate Revised Event Log with Loop-Backs:**
   ```powershell
   .\.venv\Scripts\python.exe src/data_generator_v2.py
   ```
2. **Execute Ingestion & Cleaning Pipeline (SQLite):**
   ```powershell
   .\.venv\Scripts\python.exe src/clean_events_pipeline.py
   ```
3. **Run Comprehensive Week 1 Verification Suite:**
   ```powershell
   .\.venv\Scripts\python.exe src/verify_week1.py
   ```

### Week 2 Workflow Execution Commands
1. **Run Local As-Is Process Discovery & Visualization Pipeline:**
   ```powershell
   .\.venv\Scripts\python.exe src/process_discovery.py
   ```
2. **Run Workflow Inefficiencies & Disparities Analysis Pipeline:**
   ```powershell
   .\.venv\Scripts\python.exe src/workflow_inefficiencies.py
   ```
3. **Run Comprehensive Week 2 Verification Suite:**
   ```powershell
   .\.venv\Scripts\python.exe src/verify_week2.py
   ```

### Discovered DFG Transitions (Local SQLite Engine)
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

---

## Cloud Analytics: Google BigQuery & dbt Integration (Weeks 1 & 2)

### Cloud Infrastructure & Warehouse Setup
* **GCP Project ID:** `care-flow-analytics` (Region: `asia-south1`)
* **Raw Data Store (`Careflow_raw`):**
  * `healthcare_event_log_raw`: Baseline events (2,823 rows, 500 cases, 420 patients).
  * `healthcare_event_log_v2_raw`: Enhanced events with rework loops (3,030 rows, 214 loop-backs, 154 affected cases).
* **dbt Transformations:** Managed under `dbt/` and executed using `dbt-bigquery`.

### Materialized Cloud Models (`careflow_staging`)
1. **Staging Event Logs:**
   * `stg_healthcare_events`: Cleans, deduplicates by `event_id`, and sequences baseline events (2,823 rows).
   * `stg_healthcare_events_v2`: Cleans, deduplicates by `event_id`, and sequences enhanced events with loop-backs (3,030 rows).
2. **Canonical Process Mining Event Logs:**
   * `fct_standardized_event_log`: Canonical event log conforming to PM4Py standards for baseline flow (2,823 rows).
   * `fct_standardized_event_log_v2`: Canonical event log conforming to PM4Py standards for enhanced flow with rework (3,030 rows).
3. **Clinical Pathway Transitions Marts:**
   * `fct_pathway_transitions`: Baseline DFG handover metrics (2,323 handovers across 6 clinical stages).
   * `fct_pathway_transitions_v2`: Enhanced DFG handover metrics (2,530 handovers across 9 pathways including 3 rework loops).

### Cloud-to-Process-Mining Workflow Execution
```powershell
# 1. Test BigQuery connectivity and profile
dbt debug --project-dir dbt

# 2. Compile and execute dbt transformations in BigQuery
dbt run --project-dir dbt

# 3. Execute all 52 data quality tests against BigQuery views
dbt test --project-dir dbt

# 4. Execute cloud-to-PM4Py discovery pipeline (both baseline and enhanced)
.\.venv\Scripts\python.exe src/process_discovery_bigquery.py --dataset all
```

---

## Roadmap & Upcoming Modules

* **Week 3 (Pathway Transition Time Analysis):** Handover duration quantifications between clinical stages, granular event-pair transitions, and Streamlit dashboard exploration are under active local development and scheduled for the next release.
* **Week 4 (Process Conformance & Optimization):** Advanced bottleneck resolution modeling.

---

## Repository Structure (Weeks 1 & 2 Deliverables)

```text
care-flow/
├── README.md                                             (Project documentation & architecture guide)
├── requirements.txt                                      (Python package dependencies)
├── data/
│   ├── raw/
│   │   ├── healthcare_event_log.csv                      (2,823 rows baseline raw dataset)
│   │   └── healthcare_event_log_v2.csv                   (3,030 rows enhanced dataset with loop-backs)
│   └── processed/
│       ├── cleaned_healthcare_event_log_v2.csv           (3,030 rows local cleaned log)
│       ├── standardized_event_log_v2.csv                 (3,030 rows local standardized log)
│       ├── bigquery_standardized_event_log.csv           (3,030 rows extracted from BigQuery v2)
│       └── bigquery_standardized_event_log_baseline.csv  (2,823 rows extracted from BigQuery baseline)
├── database/
│   ├── careflow.db                                       (Local SQLite database - excluded from Git via .gitignore)
│   └── schema.sql                                        (Relational schema definitions)
├── dbt/
│   ├── dbt_project.yml                                   (dbt project configuration)
│   ├── profiles.yml.example                              (Sanitized profile configuration template)
│   └── models/
│       ├── sources.yml                                   (BigQuery source definitions: baseline & v2)
│       ├── staging/
│       │   ├── schema.yml                                (Staging constraint tests)
│       │   ├── stg_healthcare_events.sql                 (Baseline staging view)
│       │   └── stg_healthcare_events_v2.sql              (Enhanced staging view with event_id deduplication)
│       └── marts/
│           ├── schema.yml                                (Mart constraint tests)
│           ├── fct_standardized_event_log.sql            (Baseline standardized event log)
│           ├── fct_standardized_event_log_v2.sql         (Enhanced standardized event log)
│           ├── fct_pathway_transitions.sql               (Baseline pathway transitions)
│           └── fct_pathway_transitions_v2.sql            (Enhanced pathway transitions)
├── reports/
│   ├── as_is_process_map.png                             (Local 9-edge As-Is process map PNG)
│   ├── as_is_process_map.dot                             (Local 9-edge As-Is process map DOT)
│   ├── as_is_process_map_bigquery.png                    (Cloud 9-edge enhanced process map PNG)
│   ├── as_is_process_map_bigquery.dot                    (Cloud 9-edge enhanced process map DOT)
│   ├── as_is_process_map_bigquery_baseline.png           (Cloud 6-edge baseline process map PNG)
│   ├── as_is_process_map_bigquery_baseline.dot          (Cloud 6-edge baseline process map DOT)
│   ├── dfg_transitions.csv                               (Local transition frequency table)
│   ├── dfg_transitions_bigquery.csv                      (Cloud enhanced transition frequency table)
│   ├── dfg_transitions_bigquery_baseline.csv             (Cloud baseline transition frequency table)
│   ├── week2_process_analysis_summary.md                 (Local clinical pathway discovery report)
│   ├── week2_bigquery_process_mining_summary.md          (Cloud enhanced process discovery report)
│   ├── week2_bigquery_process_mining_baseline_summary.md (Cloud baseline process discovery report)
│   ├── workflow_inefficiencies.csv                       (Workflow inefficiencies catalog)
│   └── week1_week2_final_completion_report.md            (Definitive audit and verification report)
├── sql/
│   ├── queries/                                          (Analytical KPI queries 01 to 10)
│   └── views/                                            (Reusable analytical views)
├── src/
│   ├── data_generator.py                                 (Baseline mock data generator)
│   ├── data_generator_v2.py                              (Enhanced generator with loop-backs)
│   ├── upload_to_bigquery.py                             (BigQuery raw table ingestion script)
│   ├── clean_events_pipeline.py                          (Local staging & cleaning pipeline)
│   ├── process_analysis.py                               (Statistical queue & bottleneck analysis)
│   ├── process_discovery.py                              (Local PM4Py discovery engine)
│   ├── process_discovery_bigquery.py                     (Cloud BigQuery -> dbt -> PM4Py engine)
│   ├── workflow_inefficiencies.py                        (Workflow inefficiency calculations)
│   ├── verify_week1.py                                   (Week 1 automated verification runner)
│   └── verify_week2.py                                   (Week 2 automated verification runner)
└── tests/                                                (65 automated Python unit tests)
```
