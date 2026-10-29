# CareFlow: Power BI Hospital Process Mining & Operational Intelligence Dashboard

**Project Title:** CareFlow — Clinical Pathway Process Mining & Healthcare Analytics  
**Module:** Official Evaluator Deliverable — Power BI Interactive Report  
**Format:** Power BI Project (`.pbip`) + Tabular Semantic Model (`.bim`) + PBIR Definition (`.pbir`)  
**Project Path:** [`reports/CareFlow_Analytics.pbip`](file:///C:/Users/Dell/OneDrive/Documents/GitHub/care-flow/reports/CareFlow_Analytics.pbip)  
**Verification Date:** October 29, 2026  
**Status:** **READY FOR EVALUATION & POWER BI DESKTOP OPENING**

---

## 1. Executive Summary & Design System

The CareFlow Power BI report provides an executive and clinical operations analytics dashboard analyzing patient flow, process bottlenecks, handover latency, and formal pathway conformance. It is structured using Microsoft's modern **Power BI Project (`.pbip`)** architecture to ensure git-traceability, transparent schemas, and automated validation.

### Theme & Palette Specifications
Following the professional hospital workflow design standards, the visual hierarchy uses an intentional clinical palette:
- **Primary Navy (`#1E3A8A`):** Executive cards, table headers, standard linear activity bars.
- **Teal Accent (`#0D9488`):** Conformance rate indicators, median transition times, positive benchmarks.
- **Sky Blue (`#0284C7`):** Secondary metrics, active filter status, consultation metrics.
- **Amber / Bottleneck (`#D97706`):** High-latency queue dwell times, triage return loops, warning thresholds.
- **Coral / Rework Alert (`#E11D48`):** Process loops (`Diagnostics -> Consultation`, `Treatment -> Diagnostics`), non-conforming patient cohorts.
- **Canvas & Background (`#FFFFFF` / `#F8FAFC`):** Crisp white visual containers on light slate canvas.

---

## 2. Power BI Project Architecture (`.pbip`)

The report is organized into the official Microsoft Power BI Project structure:

```
reports/
├── CareFlow_Analytics.pbip               <-- Open this file in Power BI Desktop
├── CareFlow_Analytics.Report/
│   ├── definition.pbir                  <-- Links report canvas to semantic model
│   └── report.json                      <-- Visual canvas layout, theme, and 3-page definitions
└── CareFlow_Analytics.SemanticModel/
    ├── definition.pbism                 <-- Model version configuration (v1.0 TMSL)
    └── model.bim                        <-- 5 Tables, 18 DAX measures, 2 active cross-filtering relationships
```

---

## 3. Data Model & Exact Verified Schemas

The Tabular Semantic Model (`model.bim`) contains **5 dedicated tables** mapped directly to the verified CareFlow datasets:

### 1. `Events` Table (3,030 rows)
- **Source:** [`data/processed/cleaned_healthcare_event_log_v2.csv`](file:///C:/Users/Dell/OneDrive/Documents/GitHub/care-flow/data/processed/cleaned_healthcare_event_log_v2.csv)
- **Cloud Equivalence:** `care-flow-analytics.careflow_staging.fct_standardized_event_log_v2`
- **Fields:** `event_id` (PK), `case_id`, `patient_id`, `activity_name`, `activity_sequence`, `event_timestamp`, `department`, `status`, `waiting_time_minutes`, `is_loopback`.

### 2. `Transitions` Table (2,530 rows)
- **Source:** [`data/processed/visit_transitions_detail.csv`](file:///C:/Users/Dell/OneDrive/Documents/GitHub/care-flow/data/processed/visit_transitions_detail.csv)
- **Cloud Equivalence:** `care-flow-analytics.careflow_staging.fct_pathway_transitions_v2` (Granular handovers)
- **Fields:** `case_id`, `patient_id`, `from_activity`, `to_activity`, `pathway`, `from_timestamp`, `to_timestamp`, `transition_time_minutes`, `is_rework_loop`.

### 3. `Visits_Conformance` Table (500 rows)
- **Source:** [`data/processed/conformance_analysis.csv`](file:///C:/Users/Dell/OneDrive/Documents/GitHub/care-flow/data/processed/conformance_analysis.csv)
- **Fields:** `case_id` (PK), `patient_id`, `department`, `is_conformant`, `conformance_status`, `conformance_category`, `trace_pattern`, `event_count`, `transition_count`, `rework_loop_count`, `primary_deviation`, `trace_fitness`, `journey_duration_minutes`, `total_waiting_minutes`.

### 4. `Pathway_Benchmark` Table (9 rows)
- **Source:** [`data/processed/transition_time_analysis.csv`](file:///C:/Users/Dell/OneDrive/Documents/GitHub/care-flow/data/processed/transition_time_analysis.csv)
- **Fields:** `from_activity`, `to_activity`, `pathway`, `transition_count`, `is_loopback`, `pct_of_total_transitions`, `avg_transition_time_minutes`, `median_transition_time_minutes`, `std_dev_minutes`, `min_transition_time_minutes`, `max_transition_time_minutes`, `iqr_minutes`.

### 5. `CareFlow_Measures` Table
Dedicated measure table containing 18 validated DAX calculations:

| Measure Name | DAX Expression | Verified Value / Format |
| :--- | :--- | :---: |
| **Total Events** | `COUNTROWS('Events')` | `3,030` |
| **Total Visits** | `DISTINCTCOUNT('Events'[case_id])` | `500` |
| **Unique Patients** | `DISTINCTCOUNT('Events'[patient_id])` | `420` |
| **Conformant Visits** | `CALCULATE(COUNTROWS('Visits_Conformance'), 'Visits_Conformance'[is_conformant] = 1)` | `346` |
| **Conformance Rate** | `DIVIDE([Conformant Visits], [Total Visits], 0)` | `69.2%` |
| **Rework Visits** | `CALCULATE(COUNTROWS('Visits_Conformance'), 'Visits_Conformance'[is_conformant] = 0)` | `154` |
| **Rework Rate** | `DIVIDE([Rework Visits], [Total Visits], 0)` | `30.8%` |
| **Total Transitions** | `COUNTROWS('Transitions')` | `2,530` |
| **Rework Loop Transitions** | `CALCULATE(COUNTROWS('Transitions'), 'Transitions'[is_rework_loop] = 1)` | `214` |
| **Rework Transition Pct** | `DIVIDE([Rework Loop Transitions], [Total Transitions], 0)` | `8.5%` |
| **Avg Journey Duration Mins** | `AVERAGE('Visits_Conformance'[journey_duration_minutes])` | `253.5 min` |
| **Median Journey Duration Mins** | `MEDIAN('Visits_Conformance'[journey_duration_minutes])` | `247.3 min` |
| **Avg Waiting Time Mins** | `AVERAGE('Events'[waiting_time_minutes])` | `15.9 min` |
| **Median Waiting Time Mins** | `MEDIAN('Events'[waiting_time_minutes])` | `14.0 min` |
| **Conformant Avg Journey Mins** | `CALCULATE(AVERAGE('Visits_Conformance'[journey_duration_minutes]), 'Visits_Conformance'[is_conformant] = 1)` | `220.1 min` |
| **Non-Conformant Avg Journey Mins**| `CALCULATE(AVERAGE('Visits_Conformance'[journey_duration_minutes]), 'Visits_Conformance'[is_conformant] = 0)` | `328.5 min` |
| **Delay Penalty Mins** | `[Non-Conformant Avg Journey Mins] - [Conformant Avg Journey Mins]` | `+108.4 min` |
| **Delay Penalty Pct** | `DIVIDE([Delay Penalty Mins], [Conformant Avg Journey Mins], 0)` | `+49.3%` |

---

## 4. Multi-Page Canvas Layouts

The report definition specifies three distinct, evaluator-ready analytical pages:

### Page 1: Executive Overview & KPIs
1. **Top KPI Ribbon:**
   - Card 1: `Total Events` (`3,030`)
   - Card 2: `Total Visits` (`500`)
   - Card 3: `Unique Patients` (`420`)
   - Card 4: `Conformance Rate` (`69.2%`)
   - Card 5: `Rework Rate` (`30.8%`)
   - Card 6: `Non-Conformance Delay Penalty` (`+108.4 min / +49.3%`)
2. **Left Panel — Clinical Activity Volumes:**
   - Horizontal Clustered Bar Chart: Activity Volume (`Registration` 527, `Triage` 527, `Consultation` 616, `Diagnostics` 420, `Treatment` 440, `Discharge` 500).
3. **Right Panel — Conformance Distribution:**
   - Donut Chart / Matrix: Patient volume by `conformance_category`:
     - *Conformant - Ideal Standard Flow:* 175 visits (35.0%)
     - *Conformant - Permitted Diagnostic Flow:* 171 visits (34.2%)
     - *Non-Conformant - Rework Loops:* 154 visits (30.8%)
4. **Slicers:**
   - `department` (Admissions, Triage, Consultation, Diagnostics, Treatment, Discharge)
   - `is_conformant` (1 = Conformant, 0 = Non-Conformant)

### Page 2: Process Flow & Handover Analysis
1. **Transition Latency Matrix:**
   - Table / Matrix displaying all 9 observed pathway transitions with:
     - `Pathways` (`Registration -> Triage`, `Triage -> Consultation`, `Consultation -> Diagnostics`, etc.)
     - `Transition Count`
     - `Median Transition Time (min)`
     - `IQR (min)`
     - `Loop-Back Indicator` (Highlighted in Coral `#E11D48`)
2. **Rework Loop Deep-Dive:**
   - Clustered Bar Chart quantifying the 3 clinical rework loop-backs:
     - `Diagnostics -> Consultation` (116 handovers, median: 71.5 min)
     - `Treatment -> Diagnostics` (29 handovers, median: 91.0 min — hospital's slowest transition)
     - `Triage -> Registration` (27 handovers, median: 17.0 min)

### Page 3: Bottlenecks & Queue Waiting Times
1. **Queue Dwell Time by Stage:**
   - Clustered Column Chart: Average & Median `waiting_time_minutes` across clinical activities.
2. **Department Queue Latency:**
   - Department-level waiting time benchmarks.
3. **Length of Stay Disparity (Cohort Comparison):**
   - Box-plot / Column chart contrasting the total visit duration:
     - Conformant Cohort: 220.1 min average (3.67 hrs)
     - Non-Conformant Cohort: 328.5 min average (5.48 hrs)
     - Highlighting the **+108.4 min operational penalty**.

---

## 5. Verification & Integrity Checklist

- **PBIP Automated Test Suite:** 5 unit tests in [`tests/test_pbip_export.py`](file:///C:/Users/Dell/OneDrive/Documents/GitHub/care-flow/tests/test_pbip_export.py) pass in 0.006s.
- **Full Repository Test Suite:** **81 tests pass** in 2.86s (`python -m unittest discover tests`).
- **Streamlit Isolation:** [`src/dashboard.py`](file:///C:/Users/Dell/OneDrive/Documents/GitHub/care-flow/src/dashboard.py) remains completely decoupled and independently functional.
- **Git State:** Untouched working tree, branch `main` at commit `b2a9a25`.
- **Database & CSV Integrity:** `database/careflow.db` and all raw/processed CSVs are intact.

---

## 6. Exact Steps to Open & Check in Power BI Desktop

To open and finalize the dashboard in Power BI Desktop:

1. **Open the Project:**
   - Navigate to `reports/` in Windows File Explorer.
   - Double-click [`CareFlow_Analytics.pbip`](file:///C:/Users/Dell/OneDrive/Documents/GitHub/care-flow/reports/CareFlow_Analytics.pbip).
   - Alternatively, open **Power BI Desktop** &rarr; **File** &rarr; **Open report** &rarr; Browse to `reports/CareFlow_Analytics.pbip`.
2. **Refresh Data:**
   - On the **Home** ribbon, click **Refresh**. Power BI Desktop will read the processed tables and compute all 18 DAX measures.
3. **Inspect the Data Pane:**
   - Confirm all 5 tables (`CareFlow_Measures`, `Events`, `Pathway_Benchmark`, `Transitions`, `Visits_Conformance`) appear with their respective columns and measures.
4. **Export `.pbix` (Optional Deliverable Binary):**
   - In Power BI Desktop, click **File** &rarr; **Save As** &rarr; Select `Power BI (.pbix)` &rarr; Save to `reports/careflow_process_analytics.pbix`.

