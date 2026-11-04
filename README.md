# CareFlow — Healthcare Process Intelligence & Clinical Pathway Optimization

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Google BigQuery](https://img.shields.io/badge/Google%20BigQuery-Cloud%20Data%20Warehouse-4285F4.svg?logo=google-cloud&logoColor=white)](https://cloud.google.com/bigquery)
[![dbt Core 1.13](https://img.shields.io/badge/dbt--Core-1.13-FF694B.svg?logo=dbt&logoColor=white)](https://www.getdbt.com/)
[![PM4Py 2.7](https://img.shields.io/badge/PM4Py-2.7%20Process%20Mining-2E7D32.svg)](https://pm4py.fit.fraunhofer.de/)
[![Microsoft Power BI](https://img.shields.io/badge/Power%20BI-PBIP%20Analytics%20Suite-F2C811.svg?logo=power-bi&logoColor=black)](https://powerbi.microsoft.com/)
[![SQLite 3](https://img.shields.io/badge/SQLite-3.40+-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Unit%20Tests-87%2F87%20Passing-brightgreen.svg)]()
[![dbt Tests](https://img.shields.io/badge/dbt%20Tests-52%2F52%20Passing-brightgreen.svg)]()

> **Enterprise Healthcare Data Analytics & Process Mining Internship Project**
> An end-to-end clinical workflow intelligence platform analyzing 500 patient encounters and 3,030 events across emergency and outpatient care to discover As-Is clinical pathways, quantify queue bottlenecks, analyze rework loops, and deliver an interactive 6-page Power BI executive suite.

---

## Table of Contents
1. [Executive Summary & Key Findings](#executive-summary--key-findings)
2. [Problem Statement & Project Objectives](#problem-statement--project-objectives)
3. [Technology Stack](#technology-stack)
4. [Dual-Workflow Architecture](#dual-workflow-architecture)
5. [Process Discovery & Clinical Rework Analysis](#process-discovery--clinical-rework-analysis)
6. [Cloud Pipeline: Google BigQuery & dbt Core](#cloud-pipeline-google-bigquery--dbt-core)
7. [Power BI Executive & Clinical Dashboard](#power-bi-executive--clinical-dashboard)
8. [Streamlit Interactive Clinical Intelligence Suite](#streamlit-interactive-clinical-intelligence-suite)
9. [Milestone Deliverables & Verification](#milestone-deliverables--verification)
10. [Installation & Execution Guide](#installation--execution-guide)
11. [Repository Structure](#repository-structure)
12. [Operational Architecture & Future Scope](#operational-architecture--future-scope)

---

## Executive Summary & Key Findings

CareFlow processes hospital emergency and outpatient encounter logs across a 6-stage clinical pathway:
$$\text{Registration} \longrightarrow \text{Triage} \longrightarrow \text{Consultation} \longrightarrow \text{Diagnostics} \longrightarrow \text{Treatment} \longrightarrow \text{Discharge}$$

By combining **relational SQL analytics**, **cloud data warehousing (Google BigQuery + dbt)**, **process mining algorithms (PM4Py)**, and **interactive BI reporting (Microsoft Power BI)**, CareFlow converts unstructured timestamped logs into actionable operational intelligence.

### Key Operational Findings

| Metric Dimension | Baseline Cohort (Clean) | Rework Cohort (Non-Conformant) | Impact / Disparity |
| :--- | :---: | :---: | :---: |
| **Patient Population** | **346 visits (69.2%)** | **154 visits (30.8%)** | 154 patients impacted by rework |
| **Average Length of Stay (ALOS)** | **220.1 min (3.67 hrs)** | **328.5 min (5.48 hrs)** | **+108.4 min (+49.2% longer stay)** |
| **Average Queue Waiting Time** | **100.7 minutes** | **150.5 minutes** | **+49.8 min (+49.5% queue penalty)** |
| **Handover Transitions** | 2,358 forward transitions | 172 reverse loop transitions | 6.8% of transitions are backward rework |
| **Primary Queue Bottleneck** | `Consultation` | **34.3 min avg wait** (median 31.0m) | Represents **32.6%** of total hospital wait |
| **Secondary Queue Bottleneck**| `Diagnostics` | **29.0 min avg wait** (median 27.0m) | 64.6% utilization; +73.8m visit duration |
| **Clinical Journey Variants** | Variant 1 & Variant 2 (346 cases) | Variants 3 through 11 (154 cases) | 11 discovered empirical process paths |

---

## Problem Statement & Project Objectives

### The Healthcare Challenge
Hospital emergency and outpatient departments face chronic patient overcrowding, erratic queue dwell times, and hidden clinical rework. Traditional aggregate reporting (such as average visit duration) obscures stage-level delays, fails to identify why patients return to consultation after diagnostics, and cannot measure the operational delay penalty incurred by process non-conformance.

### Core Objectives
1. **Event Log Standardization:** Ingest and clean synthetic healthcare event logs into canonical process-mining schemas with 100% relational integrity, zero chronological inversions, and deterministic sequencing.
2. **Dual-Layer Analytics Architecture:** Build both a local, zero-credential SQLite/Python pipeline for offline reproducibility and a cloud BigQuery/dbt pipeline for scalable enterprise data warehousing.
3. **Automated Process Discovery:** Reconstruct the As-Is clinical process map using PM4Py Directly-Follows Graphs (DFG), discovering empirical transition frequencies, variant distributions, and reverse rework corridors.
4. **Queue & Bottleneck Quantification:** Execute SQL and Python statistical models to identify queue spikes, calculate IQR outliers, and evaluate handover latency across all 9 clinical pathways.
5. **Interactive Executive Reporting:** Deliver a fully interactive, 6-page Microsoft Power BI report (`.pbip`) adhering to clinical visualization standards, equipped with 28 verified DAX measures across 10 tables, explanatory metrics, and zero layout overlaps.

---

## Technology Stack

```
Data Ingestion & Synthesis ──> Data Warehousing & ETL ──> Process Mining & Analytics ──> Interactive BI Suite
       [Python 3.10]               [Google BigQuery]                 [PM4Py 2.7]              [Microsoft Power BI]
       [SQLite 3.40]                  [dbt Core 1.13]                [pandas / numpy]          [PBIP / TMDL / DAX]
```

* **Programming & Statistical Modeling:** Python 3.10+, `pandas`, `numpy`, `matplotlib`, `unittest`, `streamlit`, `plotly`.
* **Relational Database & Local Storage:** SQLite 3 with enforced foreign keys, cascading constraints, and indexed views.
* **Cloud Data Warehouse:** Google Cloud BigQuery (`care-flow-analytics` project, `asia-south1` region).
* **Data Transformation & Testing:** dbt Core 1.13 (`dbt-bigquery` adapter) managing staging views, canonical process mining marts, and 52 automated schema tests.
* **Process Mining Library:** PM4Py 2.7 (Directly-Follows Graph discovery, Petri net token replay, variant extraction).
* **Business Intelligence & Dashboards:** Microsoft Power BI Desktop (Power BI Project format `.pbip`, Fabric PBIR report metadata, TMDL semantic model with 10 tables and 28 verified DAX measures) and interactive Streamlit Clinical Intelligence Suite (`src/dashboard.py`).

---

## Dual-Workflow Architecture

CareFlow implements a **dual-layer architecture** providing both offline development reproducibility and enterprise cloud scalability:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                         CAREFLOW SYSTEM ARCHITECTURE                                    │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────┘
                                       │                                         │
                 ┌─────────────────────┴────────────────────┐   ┌────────────────┴────────────────────┐
                 │        OFFLINE LOCAL ENGINE              │   │       ENTERPRISE CLOUD PIPELINE     │
                 │   (Zero-Credential Reproducibility)      │   │   (Google BigQuery + dbt Core)      │
                 └──────────────────────────────────────────┘   └─────────────────────────────────────┘
                                       │                                         │
                       • Synthetic Data Generation               • Raw Ingestion Pipeline
                         src/data_generator_v2.py                  src/upload_to_bigquery.py
                         (3,030 standardized events)                             │
                                       │                                         ▼
                                       ▼                         • Google BigQuery Data Store
                       • Relational SQLite Storage                 Dataset: Careflow_raw
                         database/careflow.db                      - healthcare_event_log_raw (2,823)
                         - raw_healthcare_events_v2                - healthcare_event_log_v2_raw (3,030)
                         - stg_healthcare_events_v2                              │
                                       │                                         ▼
                                       ▼                         • dbt Transformation Pipeline
                       • Analytical SQL Engine                     dbt run --project-dir dbt
                         sql/queries/ (01 to 10)                   - Staging: stg_healthcare_events_v2
                         sql/views/ (4 reusable views)             - Marts: fct_standardized_event_log_v2
                                       │                           - Marts: fct_pathway_transitions_v2
                                       ▼                                         │
                       • Local Process Discovery                                 ▼
                         src/process_discovery.py                • Automated dbt Data Testing
                         src/workflow_inefficiencies.py            dbt test --project-dir dbt
                         (PM4Py DFG & Variant Models)              (52/52 Schema Constraints Passing)
                                       │                                         │
                                       └────────────────────┬────────────────────┘
                                                            │
                                                            ▼
                                        • Interactive Power BI Executive Suite
                                          reports/CareFlow_Analytics_Final.pbip
                                          - 6 Pages | 28 DAX Measures | TMDL Schema
                                          - Balanced 4-Quadrant Process-Flow Engine
```

### Architectural Implementation Clarification
* **Cloud Layer (Google BigQuery + dbt):** The cloud pipeline was developed and executed using dbt Core connected to Google BigQuery. 6 modular models and 52 data quality tests were built and validated in BigQuery.
* **Local Layer (SQLite + Python):** To ensure internship evaluators can verify and run all tests immediately without needing Google Cloud credentials or incurring cloud billing, a parallel SQLite engine (`database/careflow.db`) and Python data pipeline mirror all staging transformations and calculations offline with exact numerical parity.

---

## Process Discovery & Clinical Rework Analysis

Using PM4Py, CareFlow reconstructs the **As-Is Directly-Follows Graph (DFG)** from 3,030 timestamped clinical events, mapping 2,530 sequential transitions across 9 pathways:

### Discovered Transition Matrix & Pathway Breakdown

| Source Station ➔ Target Station | Handover Volume | % of Source Stage | Pathway Classification | Clinical Operational Context |
| :--- | :---: | :---: | :--- | :--- |
| **`Registration ➔ Triage`** | 300 | 60.0% | Standard Forward | Acuity assessment intake |
| **`Registration ➔ Consultation`** | 200 | 40.0% | Direct Fast-Track | Low-acuity direct clinical review |
| **`Triage ➔ Consultation`** | 300 | 100.0% | Standard Forward | Post-triage medical consultation |
| **`Consultation ➔ Diagnostics`** | 438 | 71.1% | Diagnostic Pathway | Lab work, ECG, or radiological imaging |
| **`Consultation ➔ Treatment`** | 178 | 28.9% | Direct Care Pathway | Medication or procedural intervention |
| **`Diagnostics ➔ Treatment`** | 382 | 76.7% | Standard Forward | Post-diagnostic medical care |
| **`Diagnostics ➔ Consultation`** | **116** | **23.3%** | **Clinical Loopback** | **Test review & secondary consultation** |
| **`Treatment ➔ Diagnostics`** | **29** | **4.7%** | **Clinical Loopback** | **In-treatment escalation / re-testing** |
| **`Triage ➔ Registration`** | **27** | **9.0%** | **Admin Loopback** | **Demographic / insurance correction** |
| **`Treatment ➔ Discharge`** | 500 | 100.0% | Absorbing Exit | Encounter conclusion (100% case exit) |

### The Three Reverse Rework Corridors
1. **`Diagnostics ➔ Consultation` (116 transitions):** Represents 67.4% of all rework loops. Patients receive preliminary consultation, undergo imaging/labs, and must return to physician queues for results evaluation.
2. **`Treatment ➔ Diagnostics` (29 transitions):** In-treatment complications or secondary evaluations requiring mid-procedure diagnostic orders.
3. **`Triage ➔ Registration` (27 transitions):** Administrative non-conformance where patient information, consent, or intake data required re-registration.

---

## Cloud Pipeline: Google BigQuery & dbt Core

The cloud warehouse pipeline is structured in `dbt/` with production configurations:
* **GCP Project:** `care-flow-analytics` (Region: `asia-south1`)
* **Raw Ingestion Store:** `Careflow_raw.healthcare_event_log_v2_raw` (3,030 records)
* **dbt Target Schema:** `careflow_staging`

### Model Lineage & Transformation Hierarchy
1. **Staging Layer (`dbt/models/staging/`):**
   - `stg_healthcare_events.sql`: Baseline log cleansing, timestamp casting, and deduplication via `QUALIFY ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY event_timestamp)`.
   - `stg_healthcare_events_v2.sql`: Cleans enhanced event log with loop-back tracking flags.
2. **Marts Layer (`dbt/models/marts/`):**
   - `fct_standardized_event_log_v2.sql`: Conforms event logs to open process-mining standards (`case_id`, `activity_name`, `event_timestamp`, `is_loopback`).
   - `fct_pathway_transitions_v2.sql`: Computes transition frequencies, average latency, and loop-back rates using SQL window functions (`LEAD() OVER (PARTITION BY case_id ORDER BY event_timestamp)`).
3. **Data Quality Tests (`schema.yml`):**
   - 52 comprehensive assertions validating `unique`, `not_null`, `relationships` (referential integrity), and `accepted_values` across all stages and departments.

---

## Power BI Executive & Clinical Dashboard

The official final Power BI project is delivered in modern Fabric PBIR format:
📁 **`reports/CareFlow_Analytics_Final.pbip`**
Supported by Tabular Model Definition Language: 📁 **`reports/CareFlow_Analytics_Final.SemanticModel/`**

### Design System & Theme
* **Palette:** Deep Navy (`#1E3A8A`), Clinical Teal (`#0D9488`), Sky Blue (`#0284C7`), Amber Warning (`#D97706`), Off-White (`#F8FAFC`).
* **Typography:** Segoe UI Bold (16pt headers), Segoe UI Semibold (11pt chart titles), Segoe UI (9.5pt descriptive subtitles).
* **Layout Standards:** Standard 16:9 canvas (1280 × 720), 16px grid alignment, **0 overlapping visuals**, high-contrast accessible formatting.

### Dedicated 6-Page Breakdown

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              CareFlow Executive & Clinical Dashboard (6 Pages)                        │
├──────────────────────────────┬──────────────────────────────┬──────────────────────────────────────────┤
│ Page 1: Executive Overview   │ Page 2: Patient Journey      │ Page 3: Operational Bottlenecks          │
│ • Hospital volume baseline   │ • 4-Quadrant workflow console│ • Consultation & Diagnostic queue spikes │
│ • 6 Core operational KPIs    │ • Stage progression funnel   │ • Handover latency rankings              │
│ • Daily admission trends     │ • Activity & rework matrix   │ • Delay penalty breakdown (+49.2%)       │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────────────────────┤
│ Page 4: Workflow Rework      │ Page 5: Dept Performance     │ Page 6: Data Quality & Insights          │
│ • 154 Rework cases analysis  │ • 13 Hospital units compared │ • Pipeline audit: 0 nulls, 0 inversions  │
│ • 3 Reverse loop corridors   │ • Queue dwell by department  │ • Stage conformance validation           │
│ • Patient-level audit matrix │ • Outpatient vs Urgent Care  │ • Actionable clinical recommendations    │
└──────────────────────────────┴──────────────────────────────┴──────────────────────────────────────────┘
```

1. **Page 1: Executive Overview**
   Presents the hospital-wide performance baseline across 500 visits and 3,030 events. Features 6 primary KPI cards (Total Visits, Events, Rework Rate, Clean ALOS, Rework ALOS, Delay Penalty), daily encounter time series, pathway distribution, and departmental volume rankings.
2. **Page 2: Patient Journey & Process Flow**
   A balanced 4-quadrant operational workflow console. The left column displays the *Stage Progression Event Volume Flow* and *Clinical Activity Flow & Rework Sequence Matrix* (binding `activity_sequence`, `activity_name`, `department`, `Total Visits`, `Total Events`, `Avg Waiting Time Mins`, and `Total Loopback Events`). The right column features *Handover Pathway Volumes* and the *Station-to-Station Latency Matrix*.
3. **Page 3: Operational Bottlenecks & Waiting Time**
   Isolates queue dwell times across care stations. Highlights `Consultation` (34.3m) and `Diagnostics` (29.0m) as the primary hospital queue drivers, comparing waiting time vs active service duration and detailing the +108.4-minute delay penalty.
4. **Page 4: Workflow Rework & Loop-back Analysis**
   Investigates the 154 non-conformant visits (30.8% rework rate). Provides visual breakdowns of the 3 reverse loop corridors (Diagnostics ➔ Consult, Treatment ➔ Diagnostics, Triage ➔ Registration), pathway rework proportions, and an individual patient-case audit table.
5. **Page 5: Department Performance & Workload**
   Evaluates clinical activity volume, patient coverage, and waiting times across all 13 hospital departments (Outpatient Clinic, Emergency, Radiology, General Surgery, Pediatrics, etc.), highlighting operational workload disparities.
6. **Page 6: Patient Journey Drill-Down & Clinical Audit Explorer**
   Enables deep administrator investigation into individual patients and visits. Features a dedicated right-hand filter pane with Patient Search Slicer (`slicer_patient_search` for `Visits_Conformance.patient_id`) and Department Slicer (`slicer_dept_p6`). Selecting a patient filters the *Patient Visit Registry*, and selecting an individual visit filters the *Sequential Clinical Event Trail* to show that visit's step-by-step journey, duration, waiting times, and loopback flags without mixing multi-visit data.

---

## Streamlit Interactive Clinical Intelligence Suite

In addition to the Power BI Desktop project, CareFlow includes an interactive web application built with Streamlit and Plotly:
📁 **`src/dashboard.py`**

The web suite directly mirrors the 6-page Power BI dashboard, enabling browser-based exploration, dynamic cross-filtering, and granular patient trace investigation across standard web browsers.

```powershell
# Launch the Streamlit dashboard
streamlit run src/dashboard.py
```

### 6 Specialized Analytical Tabs

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                          Streamlit Clinical Intelligence Suite (src/dashboard.py)                     │
├──────────────────────────────┬──────────────────────────────┬──────────────────────────────────────────┤
│ Tab 1: 📊 Executive Overview │ Tab 2: 🔄 Patient Journey    │ Tab 3: ⏱️ Operational Bottlenecks        │
│ • 6 Metric KPI cards         │ • Interactive Sankey diagram │ • Queue wait vs handover latency         │
│ • Conformance cohort donut   │ • 9 DFG pathway volume bars  │ • Stage queue dwell ranking              │
│ • 6-Stage throughput volume  │ • 300 DPI PM4Py process map  │ • Duration distributions (IQR)           │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────────────────────┤
│ Tab 4: ⚖️ Conformance Variant│ Tab 5: 🏥 Dept Performance   │ Tab 6: 🔍 Patient Drill-Down             │
│ • Full 11-variant registry   │ • 13 Hospital units compared │ • Patient ID search (P0001–P0420)        │
│ • Fitness & delay metrics    │ • Median queue wait rankings │ • Encounter selector (V0001–V0500)       │
│ • 3 Reverse loop corridors   │ • Department audit table     │ • Chronological clinical event trail     │
└──────────────────────────────┴──────────────────────────────┴──────────────────────────────────────────┘
```

1. **📊 Executive Overview:**
   Presents high-level operational benchmarks across 500 patient encounters and 3,030 events: Total Visits (500), Total Events (3,030), Unique Patients (420), Conformance Rate (69.2%), Rework Rate (30.8%), and Average ALOS (253.5 min / 4.23 hrs). Includes an interactive conformance donut chart and stage progression volume bar chart.
2. **🔄 Patient Journey & Flow:**
   Provides multi-angle workflow discovery: an interactive Plotly Sankey diagram mapping patient flow across stages, a bar chart of the 9 empirical Directly-Follows Graph (DFG) transitions, the high-resolution 300 DPI PM4Py As-Is process map, and a station-to-station latency benchmark table.
3. **⏱️ Operational Bottlenecks:**
   Strictly disambiguates station queue dwell time from handover transit latency. Details stage-level queue wait rankings (`Consultation`: 34.3m, `Diagnostics`: 29.0m), quantifies the +108.4 min (+49.2%) delay penalty incurred by rework, and visualizes length-of-stay distributions with box plots.
4. **⚖️ Conformance Analysis:**
   Integrates `conformance_analysis.csv` and `conformance_summary.csv` to catalog all 11 discovered process variants (V01–V11). Contrasts clean pathways (V01, V02) against non-compliant rework pathways (V03–V11), reporting trace fitness and detailing the 3 reverse loop corridors (Diagnostics ➔ Consultation: 116, Treatment ➔ Diagnostics: 29, Triage ➔ Registration: 27).
5. **🏥 Department Performance:**
   Evaluates clinical activity volume, patient coverage, and median queue waiting times across all 13 hospital units (Emergency, Radiology, Outpatient Clinic, General Surgery, Pediatrics, etc.), accompanied by a searchable department performance registry.
6. **🔍 Patient Drill-Down:**
   Enables fine-grained clinical audit: search for any patient (`P0001`–`P0420`), view all associated visits, select a specific encounter (`V0001`–`V0500`), inspect visit-level KPIs (conformance status, duration, queue time, loop count, fitness, and primary deviation), and inspect that encounter's complete chronological clinical event trail table with exact timestamps and rework flags.

### Multi-Dimensional Sidebar Controls
* **Department Slicer:** Multi-select filter covering all 13 hospital departments.
* **Conformance Status Filter:** Filter across All, Conformant (Clean), or Non-Conformant (Rework).
* **Clinical Pathway Slicer:** Filter by specific DFG handover transitions.
* **Stage Slicer:** Filter by individual clinical stages.
* **Arrival Window Slider:** Interactive time-of-day filter (0:00 to 23:00).
* **Reset Filters Button:** One-click restoration of default global filter state.
* **Data Transparency Disclosure:** Explanatory sidebar banner clarifying available schema dimensions (`patient_id`, `case_id`, `department`, `activity_name`, `variant_id`) and noting that doctor and demographic attributes are absent in the source data.

---

## Milestone Deliverables & Verification

All project requirements spanning Weeks 1, 2, and 3 were verified using automated regression scripts:

| Requirement Milestone | Core Deliverable | Target Metric | Verified Empirical Result | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Week 1: Data Synthesis** | Raw Event Log Generator (`src/data_generator.py`) | 2,823 events | 2,823 events generated, 0 nulls | **PASS** |
| **Week 1: Enhanced Data** | Rework Generator (`src/data_generator_v2.py`) | 3,030 events | 3,030 events, 214 loop-backs | **PASS** |
| **Week 1: Relational Store** | SQLite Database (`database/careflow.db`) | 500 cases | 500 cases, 420 patients ingested | **PASS** |
| **Week 1: Staging Pipeline** | Staging Script (`src/clean_events_pipeline.py`) | 3,030 rows | Deduplicated, sequenced, 0 errors | **PASS** |
| **Week 2: Process Mining** | PM4Py Discovery (`src/process_discovery.py`) | 9 DFG edges | 9 pathways, 2,530 transitions | **PASS** |
| **Week 2: Variant Catalog** | Variant Analysis (`reports/week2_process_analysis_summary.md`)| 11 variants | 11 variants mapped (V1 to V11) | **PASS** |
| **Week 2: Inefficiencies** | Inefficiency Catalog (`reports/workflow_inefficiencies.csv`) | 4 categories | 154 rework cases, +49.85m wait penalty | **PASS** |
| **Week 3: Transition Latency** | Transition Engine (`src/transition_analysis.py`) | 2,530 handovers | Query 11 (2,323) & Query 12 (2,530) match | **PASS** |
| **Week 3: Duration Parity** | Mathematical Duration Conservation | Exact match | Sample visit V0001 (330.0m = 330.0m) | **PASS** |
| **Week 3: Conformance** | Conformance Checking (`src/conformance_checking.py`) | 346 / 154 | 346 clean (69.2%), 154 rework (30.8%) | **PASS** |
| **Week 4: Conformance Engine** | Normative Pathway Logic & Testing (`src/conformance_checking.py`) | 10 Scenarios | 11/11 tests pass, deviations detail, non-compliant summary | **PASS** |
| **Week 4: Dashboard Polish** | Final Power BI Suite (`reports/CareFlow_Analytics_Final.pbip`) | 6 Pages / Drill-Down | 6 pages, 10 TMDL tables, 28 measures, patient drill-down | **PASS** |
| **Final: Power BI PBIP** | Final Report (`reports/CareFlow_Analytics_Final.pbip`) | 6 pages | 6 pages, 28 measures, 0 overlaps | **PASS** |

### Automated Test Execution Evidence
* **Python Regression Suite:** `87 / 87 tests passing` (`test_cleaning_pipeline`, `test_conformance_checking`, `test_pathway_transitions`, `test_pbip_export`, `test_staging_validation`, `test_standardized_event_log`, `test_transition_analysis`, `test_workflow_inefficiencies`).
* **dbt Cloud Test Suite:** `52 / 52 schema tests passing` in BigQuery.
* **Layout Bounds & Overlap Validator:** `0 visual overlaps` across all 6 pages (1280 × 720 canvas).

---

## Installation & Execution Guide

### Prerequisites
* **Python:** Version 3.10 or higher.
* **Git:** Version 2.30 or higher.
* **Power BI Desktop:** Required to open and view `.pbip` files (Windows).
* *(Optional Cloud):* Google Cloud SDK (`gcloud`) and active GCP project for cloud BigQuery dbt execution.

### 1. Clone Repository & Setup Virtual Environment
```powershell
# Clone repository
git clone https://github.com/akshayamanchukonda/care-flow.git
cd care-flow

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

### 2. Run Local Verification & Tests
```powershell
# Run complete 87-test regression test suite
$env:PYTHONPATH="."
python -m unittest discover -s tests -p "test_*.py"

# Run individual milestone verifiers
python src/verify_week1.py
python src/verify_week2.py
python src/verify_week3.py
```

### 3. Run Local Process Discovery Pipeline
```powershell
# Generate data and build local SQLite database
python src/data_generator_v2.py
python src/clean_events_pipeline.py

# Run SQL operational analysis (10 queries & 4 views)
python src/run_sql_analysis.py

# Discover As-Is process model via PM4Py
python src/process_discovery.py
python src/workflow_inefficiencies.py
```

### 4. Open the Power BI Dashboard
1. Open **Power BI Desktop**.
2. Navigate to `reports/` and open:
   ```
   reports/CareFlow_Analytics_Final.pbip
   ```
3. All 6 pages load immediately with verified measures, high-contrast visual styling, and complete interactive cross-filtering.

### 5. Launch the Streamlit Interactive Dashboard
```powershell
streamlit run src/dashboard.py
```
This serves the application locally at `http://localhost:8501`, featuring all 6 interactive clinical tabs, patient drill-down explorer, and dynamic cross-filtering.

---

## Repository Structure

```text
care-flow/
├── README.md                                             (Comprehensive documentation & project guide)
├── requirements.txt                                      (Python package dependencies)
├── build_pbip.py                                         (Automated 6-page Power BI PBIP generator)
├── validate_pbip.py                                      (Power BI project structure validator)
├── CARE_FLOW_FINAL_COMPLETION_AND_POWER_BI_AUDIT.md       (Comprehensive technical audit report)
│
├── data/
│   ├── raw/
│   │   ├── healthcare_event_log.csv                      (2,823 rows baseline raw dataset)
│   │   └── healthcare_event_log_v2.csv                   (3,030 rows enhanced dataset with loop-backs)
│   └── processed/
│       ├── cleaned_healthcare_event_log_v2.csv           (3,030 rows standardized log)
│       ├── visit_transitions_detail.csv                  (2,530 granular handover transitions)
│       ├── conformance_analysis.csv                      (500 patient cases classified by variant)
│       └── conformance_summary.csv                       (11 discovered empirical trace variants)
│
├── database/
│   └── schema.sql                                        (Relational SQLite DDL schema)
│
├── dbt/                                                  (Cloud Data Warehouse Transformation Models)
│   ├── dbt_project.yml                                   (dbt project configuration)
│   ├── profiles.yml.example                              (Sanitized profile connection template)
│   └── models/
│       ├── staging/                                      (Deduplicated event staging views)
│       └── marts/                                        (Canonical event logs & pathway transitions)
│
├── reports/
│   ├── CareFlow_Analytics_Final.pbip                     (Official final 6-page Power BI project)
│   ├── CareFlow_Analytics_Final.Report/                  (Fabric PBIR visual containers & pages)
│   ├── CareFlow_Analytics_Final.SemanticModel/           (TMDL semantic model & 28 DAX measures across 10 tables)
│   ├── power_bi_dashboard_report.md                      (Technical BI architecture & metric guide)
│   ├── as_is_process_map.png                             (Discovered 9-transition process map)
│   ├── week1_week2_final_completion_report.md            (Audit & mathematical verification report)
│   ├── week2_process_analysis_summary.md                 (Clinical pathway & variant discovery report)
│   ├── conformance_checking_report.md                    (Trace variant & normative pathway report)
│   └── week4_task2_dashboard_refinement_report.md        (Week 4 final BI refinement & drill-down report)
│
├── sql/
│   ├── queries/                                          (Analytical KPI queries 01 through 10)
│   └── views/                                            (Reusable analytical views)
│
├── src/
│   ├── dashboard.py                                      (6-tab interactive Streamlit web dashboard)
│   ├── data_generator.py                                 (Baseline mock data generator)
│   ├── data_generator_v2.py                              (Enhanced generator with loop-backs)
│   ├── clean_events_pipeline.py                          (Staging & cleaning ETL pipeline)
│   ├── process_discovery.py                              (Local PM4Py discovery engine)
│   ├── process_discovery_bigquery.py                     (BigQuery -> PM4Py cloud discovery)
│   ├── transition_analysis.py                            (Pathway handover latency engine)
│   ├── conformance_checking.py                           (Trace variant & rework conformance)
│   ├── workflow_inefficiencies.py                        (Queue penalty & disparity modeling)
│   ├── verify_week1.py                                   (Week 1 automated verification runner)
│   ├── verify_week2.py                                   (Week 2 automated verification runner)
│   └── verify_week3.py                                   (Week 3 automated verification runner)
│
└── tests/                                                (87 automated Python unit regression tests)
    ├── test_cleaning_pipeline.py
    ├── test_conformance_checking.py
    ├── test_pathway_transitions.py
    ├── test_pbip_export.py
    ├── test_staging_validation.py
    ├── test_standardized_event_log.py
    ├── test_transition_analysis.py
    └── test_workflow_inefficiencies.py
```

---

## Operational Architecture & Future Scope

### Enterprise Design Highlights
1. **Dual-Layer Analytics Architecture:** CareFlow provides both an enterprise Google BigQuery cloud data warehouse layer with dbt Core data transformation models and an offline relational SQLite engine. This guarantees zero-barrier local evaluation and 100% numerical parity across environments.
2. **Privacy-Preserving Clinical Modeling:** Clinical event logs model authentic hospital operations (Poisson arrival rates, log-normal queue dwell distributions, and clinical rework loops) while ensuring complete data privacy with synthetic patient entities free of Protected Health Information (PHI).
3. **Native High-Fidelity Process Mining:** Rather than relying on external visual dependencies, CareFlow delivers an end-to-end, native 4-quadrant workflow console in Power BI and an interactive Plotly Sankey and PM4Py Directly-Follows Graph (DFG) in Streamlit. This provides robust, responsive, and seamless clinical process visualization across all analytical views.
4. **Multi-Dimensional Clinical Exploration:** Filtering and administrative drill-down operate dynamically across 13 hospital departments, 6 clinical stages, 9 empirical pathways, 11 process variants, and individual patient encounter timelines (420 patients, 500 cases), delivering comprehensive operational oversight with absolute data integrity.

### Future Enhancements
* **Real-Time Streaming Ingestion:** Extending the BigQuery ingestion pipeline using Apache Kafka / Google Pub/Sub for real-time patient tracking.
* **Predictive Length-of-Stay Modeling:** Training a supervised machine learning model (e.g., XGBoost) to predict patient triage rework probabilities at the time of initial registration.
* **FHIR / HL7 Integration:** Supporting standard Fast Healthcare Interoperability Resources (FHIR) JSON inputs for direct electronic health record (EHR) interoperability.

---

## License & Attribution

Developed as an **Enterprise Healthcare Data Analytics & Clinical Process Mining Internship Project**.
All code, models, and documentation are structured in accordance with healthcare data governance, reproducible analytics, and open data science standards.
