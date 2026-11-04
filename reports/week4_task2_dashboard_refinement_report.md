# CareFlow Power BI Dashboard Refinement & Polish (Week 4 Task 2 Report)

**Project:** CareFlow — Healthcare Process Mining & Clinical Intelligence  
**Module:** Week 4 – Task 2: Complete Power BI Dashboard Refinement and Polish  
**Target File:** `reports/CareFlow_Analytics_Final.pbip`  
**Semantic Model:** `reports/CareFlow_Analytics_Final.SemanticModel` (TMDL Format)  
**Report Canvas:** `reports/CareFlow_Analytics_Final.Report` (PBIR Format)  
**Verification Date:** November 4, 2026  
**Status:** **100% OPERATIONAL & VERIFIED**

---

## 1. Executive Summary

This deliverable accomplishes the official Week 4 Task 2 requirement:
> *"Dashboard Refinement & Polish: Polish the dashboard, adding drill-down capabilities so administrators can filter the process map by specific patient demographics or doctors."*

The Care Flow Power BI analytics suite has been audited, corrected, enhanced, and validated. The enhancements deliver:
1. **End-to-End Semantic Model Parity**: Integrated the Week 4 `Variants_Summary` table (from `data/processed/conformance_summary.csv`) with bidirectional cross-filtering to `Visits_Conformance`. Expanded the measure catalogue to **28 validated DAX measures**.
2. **Process Flow Visual Correction**: Resolved the category projection defect on Page 2 (`chart_stage_progression`), replacing the individual event ID grouping with clinical station aggregation (`Events.activity_name`) and `Total Events`, correctly plotting throughput across the 6 core stations.
3. **Clinical Process Variant Registry**: Transformed Page 4's pattern table into an authoritative 11-variant process registry (`V01` through `V11`), detailing exact trace sequences, case counts, percentages, loop counts, primary deviations, and duration penalties.
4. **Interactive Patient Investigation & Drill-Down (Page 6)**: Created a dedicated right-hand search and filtering pane on Page 6 with `slicer_patient_search` (`Visits_Conformance.patient_id`) and `slicer_dept_p6` (`Visits_Conformance.department`), enabling hospital administrators to isolate any individual patient (`P0001`–`P0420`), inspect specific visits without cross-visit conflation, and trace the granular step-by-step clinical event trail.
5. **Departmental & Stage Slicers**: Verified cross-filtering across all 6 pages. Hospital administrators can segment by department, clinical station, conformance category, or individual patient entity.
6. **Data Integrity & Clinical Slicing Dimensions**: Confirmed via source audits that the underlying healthcare event logs do not contain physician/doctor names or patient age/gender attributes. In strict compliance with clinical data governance and internship integrity standards, no ungrounded data was fabricated; instead, comprehensive multi-dimensional drill-down is provided by Patient Entity ID, Encounter Case ID, Clinical Department (13 units), and Clinical Activity Stage.

---

## 2. 6-Page Architecture & Enhancements

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              CareFlow Refined Executive & Clinical Suite (6 Pages)                    │
├──────────────────────────────┬──────────────────────────────┬──────────────────────────────────────────┤
│ Page 1: Executive Overview   │ Page 2: Patient Journey      │ Page 3: Operational Bottlenecks          │
│ • 6 Core Executive KPIs      │ • Discovered process graph   │ • Stage queue dwell times                │
│ • Clean vs Rework cohorts    │ • Stage throughput funnel    │ • Delay penalty metrics (+108.4m)        │
│ • Department & status slicers│ • Station handover latency   │ • Stage selection slicer                 │
├──────────────────────────────┼──────────────────────────────┼──────────────────────────────────────────┤
│ Page 4: Workflow Rework      │ Page 5: Dept Performance     │ Page 6: Patient Drill-Down & Audit       │
│ • 154 Non-compliant visits   │ • 13 Hospital units analyzed │ • Patient ID search slicer               │
│ • 11 Process variant catalog │ • Departmental queue times   │ • Department filter slicer               │
│ • 3 Major rework loops       │ • Workload & case volume     │ • Step-by-step event audit trail         │
└──────────────────────────────┴──────────────────────────────┴──────────────────────────────────────────┘
```

### Page 1: Executive Overview (`Section_Overview`)
* **KPI Header Cards**: Total Visits (500), Total Events (3,030), Unique Patients (420), Rework Rate (30.8%), Avg Waiting Time (20.3 min), Avg Length of Stay (4.23 hrs).
* **Visuals**:
  * `p1_chart_cohorts`: Donut chart showing breakdown between Conformant Standard (35.0%), Conformant Diagnostic (34.2%), and Non-Conformant Rework (30.8%).
  * `p1_chart_activities`: Clustered column chart showing activity workload across the 6 care stations.
* **Slicers**: Interactive Department Slicer (`slicer_department`) and Conformance Status Slicer (`slicer_conformance_status`).
* **Canvas Quality**: 0 overlaps, 100% grid alignment, Segoe UI typography, Navy `#1B365D` theme.

### Page 2: Patient Journey & Process Flow (`Section_Journey`)
* **KPI Header Cards**: Total Transitions (2,530), Total Events (3,030), Median Journey Duration (249.5 min), Avg Length of Stay (4.23 hrs).
* **Corrected Visual**: `chart_stage_progression` was corrected from erroneous `event_id` grouping to `Events.activity_name` by `CareFlow_Measures.Total Events`, correctly displaying Registration (500), Triage (300), Consultation (616), Diagnostics (498), Treatment (616), Discharge (500).
* **Process Flow Visuals**:
  * `chart_pathway_volume`: Clustered bar chart of all 9 discovered DFG pathways, highlighting both forward handovers and reverse rework loops.
  * `table_stage_flow`: Detailed chronological stage sequence matrix with waiting times and loopback flags.
  * `table_transition_latency`: Station-to-station empirical latency benchmarks (mean, median, IQR).

### Page 3: Operational Bottlenecks (`Section_Inefficiencies`)
* **KPI Header Cards**: Avg Waiting Time (20.3 min), Median Waiting Time (18.0 min), Delay Penalty Mins (+108.4 min), Delay Penalty Pct (+49.2%), Non-Conformant ALOS (5.48 hrs).
* **Visuals**:
  * `chart_stage_wait`: Clustered column chart identifying `Consultation` (34.3m) and `Diagnostics` (29.0m) as primary queue dwell drivers.
  * `chart_cohort_los`: Duration comparison illustrating the impact of rework (328.5 min for non-conformant vs 220.1 min for conformant).
  * `slicer_stage`: Dedicated stage slicer allowing administrators to isolate specific clinical bottlenecks.

### Page 4: Workflow Rework & Process Conformance (`Section_Rework`)
* **KPI Header Cards**: Rework Cases (154), Rework Rate (30.8%), Rework Loop Transitions (172), Total Loopback Events (214), Rework Transition Pct (6.8%).
* **Enhanced Visuals**:
  * `table_rework_patterns`: Upgraded to project `Variants_Summary` (`variant_id`, `trace_pattern`, `case_count`, `primary_deviation`, `rework_loops_per_case`, `avg_journey_minutes`). Administrators can explore all 11 variants and cross-filter the page by clicking any variant.
  * `p4_chart_rework_donut`: Visual breakdown of non-compliant case categories.
  * `chart_rework_pathways`: Volume of the 3 reverse loop corridors (Diagnostics ➔ Consultation: 116, Treatment ➔ Diagnostics: 29, Triage ➔ Registration: 27).

### Page 5: Department Performance (`Section_Departments`)
* **KPI Header Cards**: Department Visits, Department Events, Department Wait Time, Department Rework Cases.
* **Visual Polish**: Added missing card description `desc_card_dept_events` at coordinates (x: 332, y: 112) to ensure 100% subtitle consistency across all 4 KPI cards.
* **Visuals & Slicers**:
  * `chart_dept_events`: Activity workload across 13 hospital departments.
  * `chart_dept_waiting`: Mean waiting time ranking across clinical units.
  * `table_dept_cases`: Granular patient case roster for the active department.
  * `slicer_dept_select`: Interactive single/multi-select department slicer.

### Page 6: Patient Journey Drill-Down & Clinical Audit Explorer (`Section_DataQuality`)
* **Header**: "Patient Journey Drill-Down & Clinical Investigation Audit — Individual Patient & Visit Audit Trail — Filter by Patient ID or Department to Trace End-to-End Care Delivery".
* **KPI Header Cards**: Total Visits (500), Total Patients (420), Total Events (3,030), Total Transitions (2,530).
* **New Drill-Down & Filter Pane**:
  * `slicer_patient_search`: Slicer for `Visits_Conformance.patient_id` (x: 990, y: 186, w: 274, h: 234). Allows typing or selecting patient entities (`P0001`–`P0420`).
  * `slicer_dept_p6`: Slicer for `Visits_Conformance.department` (x: 990, y: 464, w: 274, h: 240).
* **Multi-Visit Separation**:
  * `table_case_explorer` (x: 16, y: 190, w: 470, h: 514): Lists visits with `patient_id`, `case_id`, `department`, `conformance_status`, `primary_deviation`, `journey_duration_minutes`, `rework_loop_count`, and `trace_fitness`.
  * When a patient has multiple visits, each visit appears as an independent row with its unique `case_id`, preventing conflation.
* **Event Trail Investigation**:
  * `table_event_trail` (x: 502, y: 190, w: 472, h: 514): Shows the chronological sequence (`activity_sequence`, `activity_name`, `department`, `waiting_time_minutes`, `is_loopback`) for the selected visit.

---

## 3. Semantic Model Architecture & DAX Measures

### Tables in Semantic Model (`CareFlow_Analytics_Final.SemanticModel`)

| Table Name | Source File | Rows | Columns | Semantic Role |
| :--- | :--- | :---: | :---: | :--- |
| `Events` | `data/processed/cleaned_healthcare_event_log_v2.csv` | 3,030 | 10 | Fact Table (Clinical Event Log) |
| `Visits_Conformance` | `data/processed/conformance_analysis.csv` | 500 | 14 | Dimension / Aggregate (Patient Encounter Level) |
| `Transitions` | `data/processed/visit_transitions_detail.csv` | 2,530 | 9 | Fact Table (Station-to-Station Handovers) |
| `Pathway_Benchmark` | `data/processed/transition_time_analysis.csv` | 9 | 14 | Reference Dimension (Empirical Pathway Benchmarks) |
| `Variants_Summary` | `data/processed/conformance_summary.csv` | 11 | 11 | Reference Dimension (11 Discovered Trace Variants) |
| `CareFlow_Measures` | Calculated In-Memory | 1 | 28 | DAX Calculation Repository |
| `LocalDateTable_*` (4 tables) | Power BI Engine | Auto | 4 | Date Hierarchy Support |

### Complete 28 DAX Measure Catalog

| # | Measure Name | DAX Expression | Format | Verified Result |
| :-: | :--- | :--- | :---: | :---: |
| 1 | **Total Events** | `COUNTROWS('Events')` | `#,0` | 3,030 |
| 2 | **Total Visits** | `DISTINCTCOUNT('Events'[case_id])` | `#,0` | 500 |
| 3 | **Unique Patients** | `DISTINCTCOUNT('Events'[patient_id])` | `#,0` | 420 |
| 4 | **Conformant Visits** | `CALCULATE(COUNTROWS('Visits_Conformance'), 'Visits_Conformance'[is_conformant] = 1)` | `#,0` | 346 |
| 5 | **Conformance Rate** | `DIVIDE([Conformant Visits], [Total Visits], 0)` | `0.0%` | 69.2% |
| 6 | **Rework Visits** | `CALCULATE(COUNTROWS('Visits_Conformance'), 'Visits_Conformance'[is_conformant] = 0)` | `#,0` | 154 |
| 7 | **Rework Rate** | `DIVIDE([Rework Visits], [Total Visits], 0)` | `0.0%` | 30.8% |
| 8 | **Total Transitions** | `COUNTROWS('Transitions')` | `#,0` | 2,530 |
| 9 | **Rework Loop Transitions** | `CALCULATE(COUNTROWS('Transitions'), 'Transitions'[is_rework_loop] = 1)` | `#,0` | 172 |
| 10 | **Rework Transition Pct** | `DIVIDE([Rework Loop Transitions], [Total Transitions], 0)` | `0.0%` | 6.8% |
| 11 | **Avg Journey Duration Mins** | `AVERAGE('Visits_Conformance'[journey_duration_minutes])` | `0.0` | 253.5 |
| 12 | **Median Journey Duration Mins** | `MEDIAN('Visits_Conformance'[journey_duration_minutes])` | `0.0` | 249.5 |
| 13 | **Avg Waiting Time Mins** | `AVERAGE('Events'[waiting_time_minutes])` | `0.0` | 20.3 |
| 14 | **Median Waiting Time Mins** | `MEDIAN('Events'[waiting_time_minutes])` | `0.0` | 18.0 |
| 15 | **Conformant Avg Journey Mins** | `CALCULATE(AVERAGE('Visits_Conformance'[journey_duration_minutes]), 'Visits_Conformance'[is_conformant] = 1)` | `0.0` | 220.1 |
| 16 | **Non-Conformant Avg Journey Mins** | `CALCULATE(AVERAGE('Visits_Conformance'[journey_duration_minutes]), 'Visits_Conformance'[is_conformant] = 0)` | `0.0` | 328.5 |
| 17 | **Delay Penalty Mins** | `[Non-Conformant Avg Journey Mins] - [Conformant Avg Journey Mins]` | `+0.0;-0.0;0.0` | +108.4 |
| 18 | **Delay Penalty Pct** | `DIVIDE([Delay Penalty Mins], [Conformant Avg Journey Mins], 0)` | `0.0%` | +49.2% |
| 19 | **Avg Length of Stay Hours** | `DIVIDE([Avg Journey Duration Mins], 60, 0)` | `0.00` | 4.23 |
| 20 | **Median Length of Stay Hours** | `DIVIDE([Median Journey Duration Mins], 60, 0)` | `0.00` | 4.16 |
| 21 | **Conformant ALOS Hours** | `DIVIDE([Conformant Avg Journey Mins], 60, 0)` | `0.00` | 3.67 |
| 22 | **Non-Conformant ALOS Hours** | `DIVIDE([Non-Conformant Avg Journey Mins], 60, 0)` | `0.00` | 5.48 |
| 23 | **Total Loopback Events** | `CALCULATE(COUNTROWS('Events'), 'Events'[is_loopback] = 1)` | `#,0` | 214 |
| 24 | **Loopback Event Rate** | `DIVIDE([Total Loopback Events], [Total Events], 0)` | `0.0%` | 7.1% |
| 25 | **Conformant Cases Count** | `CALCULATE(DISTINCTCOUNT('Visits_Conformance'[case_id]), 'Visits_Conformance'[is_conformant] = 1)` | `#,0` | 346 |
| 26 | **Non-Conformant Cases Count** | `CALCULATE(DISTINCTCOUNT('Visits_Conformance'[case_id]), 'Visits_Conformance'[is_conformant] = 0)` | `#,0` | 154 |
| 27 | **Avg Trace Fitness** | `AVERAGE('Visits_Conformance'[trace_fitness])` | `0.00` | 0.95 |
| 28 | **Total Journey Duration Hours** | `DIVIDE(SUM('Visits_Conformance'[journey_duration_minutes]), 60, 0)` | `#,0.0` | 2,112.6 |

---

## 4. Technical Validation & Safety Results

* **Local TMDL Authoring Tool Verification**: Loaded directly via `powerbi-authoring-local` MCP server. Loaded 10 tables, 28 measures, 6 relationships with **0 errors**.
* **Visual JSON Parser Verification**: 100% of JSON files in `CareFlow_Analytics_Final.Report` parsed successfully with **0 syntax errors**.
* **Query Projection Reference Audit**: 100% of field references across all visuals map to valid entities and columns in the semantic model.
* **Visual Collisions & Bounds Audit**: 100% of visual containers conform to the standard 1280 × 720 canvas with **0 bounding box overlaps**.
* **Python Regression Test Suite**: `Ran 11 tests in 2.096s. OK` across all conformance scenarios. Full suite: `87 tests passing`.
* **Milestone Verifiers**: Week 1, Week 2, and Week 3 milestone scripts confirmed 100% operational.

---

## 5. Clinical Data Governance: Real Patient & Operational Slicing Dimensions

The assignment specification requests:
> *"adding drill-down capabilities so administrators can filter the process map by specific patient demographics or doctors."*

An exhaustive audit of the raw and processed hospital event logs confirmed:
* **Doctor Identifiers**: Not present in source data (`healthcare_event_log.csv`, `cleaned_healthcare_event_log_v2.csv`). No `doctor_id`, `doctor_name`, or `physician_id` columns exist.
* **Demographic Attributes**: Not present in source data. No `age`, `gender`, or `ethnicity` fields exist.

In accordance with strict healthcare data integrity guidelines and the safety rules of this project:
1. **Zero Fake Data**: Fake or synthetic doctor names and demographics were **not** fabricated.
2. **Comprehensive Alternatives Implemented**:
   * **Patient Entity Drill-Down**: Direct slicer and filtering on `patient_id` (420 real patients).
   * **Encounter Isolation**: Direct drill-down on `case_id` (500 real visits) preventing cross-visit conflation.
   * **Departmental Drill-Down**: Slicing across all 13 real hospital departments (`department`).
   * **Station-Level Drill-Down**: Slicing across all 6 clinical stages (`activity_name`).
   * **Variant-Level Drill-Down**: Direct selection across all 11 process variants (`variant_id`, `trace_pattern`).

---

## 6. How to Open and Review in Power BI Desktop

1. Navigate to the repository root: `C:\Users\Dell\OneDrive\Documents\GitHub\care-flow`.
2. Open the file: **`reports\CareFlow_Analytics_Final.pbip`** in Power BI Desktop.
3. Power BI Desktop will parse `reports/CareFlow_Analytics_Final.Report` and `reports/CareFlow_Analytics_Final.SemanticModel` directly.
4. Explore the 6 report pages:
   * **Executive Overview**: Use top-right slicers to filter by Department or Conformance Status.
   * **Patient Journey**: View stage progression volumes and handover latency.
   * **Operational Bottlenecks**: Select any stage in the right slicer to inspect specific queue dwell times.
   * **Workflow Rework**: Click any variant in the `Clinical Process Variant & Deviation Registry` table to cross-filter the page.
   * **Department Performance**: Use the department slicer to inspect unit-level performance.
   * **Patient Drill-Down & Quality**: Select a Patient ID (e.g. `P0001`) from the right-hand filter pane to inspect that patient's visits and step-by-step clinical event trail.

