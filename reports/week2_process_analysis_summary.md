# CareFlow: Week 2 As-Is Process Mining & Clinical Pathway Discovery Summary

**Project:** CareFlow — Clinical Pathway Process Mining
**Phase:** Week 2 Deliverable Summary
**Author:** Data Analytics Intern
**Environment:** Local Python (`.venv`) & SQLite (`database/careflow.db`)
**Artifact Dependencies:** `reports/as_is_process_map.png`, `reports/as_is_process_map.dot`, `reports/dfg_transitions.csv`, `data/processed/standardized_event_log_v2.csv`

---

## 1. Executive Summary & Purpose of Week 2 Process Discovery

Traditional healthcare business intelligence relies on static summaries such as average waiting times and departmental headcounts. While useful, these aggregated metrics cannot reveal **how patients actually navigate through the hospital system**, where pathways branch, or where repetitive rework occurs.

The purpose of **Week 2 Process Discovery** is to transition from aggregated metrics to empirical **process mining**. Using the validated hospital event log from Week 1 (containing 500 patient visits and 3,030 clinical events), Week 2 applies open-source process mining algorithms (**PM4Py**) to:
1. Reconstruct the actual, unvarnished **As-Is clinical pathway** directly from recorded event timestamps.
2. Determine whether patient journeys adhere strictly to standard protocol or diverge into operational inefficiencies.
3. Quantify **pathway transitions, bifurcation rates, and operational loop-backs (rework loops)** with complete statistical precision.
4. Generate an intuitive, publication-quality directed process map visual for clinical and operational stakeholders.

---

## 2. Process Discovery Methodology (PM4Py Implementation)

### 2.1 Canonical Event Log Standardization
Process mining algorithms require an event log conforming to three fundamental dimensions:
* **Case Identifier (`Case_ID`):** Identifies the individual patient visit (500 distinct visits: `V0001`–`V0500`).
* **Activity Name (`Activity_Name`):** The clinical or operational stage executed (`Registration`, `Triage`, `Consultation`, `Diagnostics`, `Treatment`, `Discharge`).
* **Timestamp (`Timestamp`):** ISO-8601 datetime recording when each stage commenced.

The pipeline implemented in `src/process_discovery.py` extracts the cleaned dataset (`data/processed/cleaned_healthcare_event_log_v2.csv`), sanitizes whitespace, verifies chronological sorting per visit, and outputs the canonical event log to `data/processed/standardized_event_log_v2.csv` while preserving all original metadata (`patient_id`, `department`, `waiting_time_minutes`, `is_loopback`).

### 2.2 Data Integrity Verification
Before discovery, the event log underwent rigorous automated validation:
* **Total Events:** Exactly **3,030** rows.
* **Unique Cases:** Exactly **500** visits.
* **Unique Patients:** Exactly **420** individuals.
* **Missing Identifiers:** **0** nulls across `Case_ID`, `Activity_Name`, and `Timestamp`.
* **Chronological Inversions:** **0** timestamp ordering violations within any visit.
* **Loop-Back Events Retained:** Exactly **214** repeat events.

### 2.3 Process Discovery Technique: Directly-Follows Graph (DFG)
Process discovery was conducted using PM4Py's **Directly-Follows Graph (DFG)** algorithm (`pm4py.discover_dfg`).

**Methodology Rationale:**
* **Deterministic Completeness:** Unlike the classical Alpha Miner (which fails in the presence of short loops and concurrency) or Heuristic Miners (which filter out low-frequency edges based on dependency thresholds), DFG evaluates every observed consecutive event pair $(A \rightarrow B)$ across all traces.
* **Exact Frequency Tracking:** In clinical pathway governance, low-frequency deviations (such as 27 triage re-registrations or 29 secondary diagnostic workups) represent high-risk operational inefficiencies. DFG captures **100% of transitions** without artificial abstraction.
* **Clinical Interpretability:** Hospital leaders can directly interpret DFG directed graphs as intuitive workflow diagrams where edge weights reflect exact patient volumes.

---

## 3. Architecture of the As-Is Process Map

The discovered clinical pathway is captured in two project artifacts:
1. **Graphviz DOT Language Model:** `reports/as_is_process_map.dot` (standard graph specification).
2. **High-Resolution Visual Diagram:** `reports/as_is_process_map.png` (300 DPI directed process graph rendered using `matplotlib` and `networkx`).

### 3.1 Structural Components of the Visual Map
* **Boundary Nodes:**
  * **START Node:** 100% of patient journeys (**500 visits**) begin at `Registration`.
  * **END Node:** 100% of patient journeys (**500 visits**) conclude at `Discharge`.
* **Activity Nodes:** Six rectangular nodes displaying the clinical activity title and total execution count:
  * `Registration`: 527 events
  * `Triage`: 527 events
  * `Consultation`: 616 events
  * `Diagnostics`: 331 events
  * `Treatment`: 529 events
  * `Discharge`: 500 events
* **Forward Transitions (Solid Navy Arrows):** Primary clinical care progression displaying transition counts in blue badges.
* **Loop-Back Transitions (Curved Dashed Crimson Arcs):** Operational rework and repeat activities highlighted with red badges to immediately signal process friction to auditors.

---

## 4. Empirical Transition Analysis

The discovery pipeline identified **9 distinct transition types** comprising **2,530 total transition instances** ($3,030 \text{ events} - 500 \text{ cases} = 2,530 \text{ transitions}$). The table below details the exact data extracted from `reports/dfg_transitions.csv`:

| Source Activity | Target Activity | Transition Volume | % of Source Stage | % of All Transitions | Pathway Classification |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `Registration` | `Triage` | **527** | 100.00% | 20.83% | Standard Forward Clinical Flow |
| `Treatment` | `Discharge` | **500** | 94.52% | 19.76% | Standard Forward Clinical Flow |
| `Triage` | `Consultation` | **500** | 94.88% | 19.76% | Standard Forward Clinical Flow |
| `Consultation` | `Treatment` | **314** | 50.97% | 12.41% | Direct Treatment Path (Diagnostics Skipped) |
| `Consultation` | `Diagnostics` | **302** | 49.03% | 11.94% | Diagnostic Workup Pathway |
| `Diagnostics` | `Treatment` | **215** | 64.95% | 8.50% | Post-Diagnostic Treatment Pathway |
| `Diagnostics` | `Consultation` | **116** | 35.05% | 4.58% | **Clinical Rework Loop (Lab/Imaging Review)** |
| `Treatment` | `Diagnostics` | **29** | 5.48% | 1.15% | **Clinical Rework Loop (In-Treatment Testing)** |
| `Triage` | `Registration` | **27** | 5.12% | 1.07% | **Operational Rework Loop (Admin/Triage Error)** |

### 4.1 Key Flow Dynamics Revealed by the Data

1. **Intake Progression (`Registration` & `Triage`):**
   * Every single patient begins at `Registration` (500 initial visits).
   * 100% of registrations (527 total, including 27 repeat registrations) move directly into `Triage`.
   * From triage, 500 transitions move forward into `Consultation`, while 27 loop back to `Registration`.

2. **The Clinical Decision Bifurcation at `Consultation`:**
   * After arriving at general consultation, the clinical pathway splits into two paths:
     * **Direct Treatment Path (50.97% / 314 transitions):** Patients whose clinical assessment indicates no laboratory tests or diagnostic imaging is needed move directly from `Consultation` to `Treatment`.
     * **Diagnostic Workup Path (49.03% / 302 transitions):** Patients requiring pathology testing, imaging, or specialized diagnostics transition from `Consultation` to `Diagnostics`.

3. **Resolution of Diagnostics:**
   * Of the 331 total diagnostic encounters (302 from consultation + 29 from treatment):
     * **215 transitions (64.95%)** proceed directly to `Treatment` once results are available.
     * **116 transitions (35.05%)** loop back to `Consultation` for physician re-evaluation.

---

## 5. Process Loops & Rework Analysis

A critical strength of process mining is its empirical ability to detect and quantify **unplanned repetition, circular flows, and rework**. Across the 500 patient journeys, the dataset records **214 loop-back events** (`is_loopback == 1`) distributed across **154 distinct visits (30.8% of all hospital encounters)**.

When analyzing directly-follows sequence transitions between consecutive events, these rework patterns manifest as **172 loop-back transition instances** across three distinct operational and clinical loops:

```
[Loop 1: Administrative Intake]   Triage (5.12%) ------------> Registration (27 transitions)
[Loop 2: Diagnostic Review]       Diagnostics (35.05%) ------> Consultation (116 transitions)
[Loop 3: Treatment Escalation]    Treatment (5.48%) ---------> Diagnostics (29 transitions)
```

> [!IMPORTANT]
> **Methodological Note on Cause vs. Observation:**
> Process discovery strictly identifies *where* and *how often* repeat transitions occur in recorded data. While operational hypotheses are provided below to explain typical hospital workflows, timestamp data alone does not prove clinical error, administrative fault, or specific operational root causes. Rather, these patterns highlight high-priority targets for operational audit.

### 5.1 Loop 1: Triage to Registration (`27 transitions` / `5.12%` of triage sessions)
* **Observed Data:** 27 patient encounters transition directly from `Triage` back to `Registration`.
* **Operational Hypothesis:** In emergency care, patients frequently arrive at triage where clinical staff identify incomplete demographic intake, unverified insurance, or missing identification details, necessitating a return to the Admissions desk for clerical completion before triage can be finalized.
* **Process Impact:** Generates 27 repeat registrations and 27 repeat triages (54 extra events across 27 patient journeys).

### 5.2 Loop 2: Diagnostics to Consultation (`116 transitions` / `35.05%` of diagnostic tests)
* **Observed Data:** Out of 331 total diagnostic encounters, 116 transitions (35.05%) route back to `Consultation`.
* **Operational Hypothesis:** When laboratory tests, pathology panels, or radiology imaging return complex or abnormal findings, clinical protocol requires an in-person physician re-evaluation to discuss findings and formulate an adjusted treatment strategy.
* **Process Impact:** Represents the largest single volume of process rework in the hospital, adding 116 repeat consultations and inflating total consultation volume to 616 events.

### 5.3 Loop 3: Treatment to Diagnostics (`29 transitions` / `5.48%` of treatment sessions)
* **Observed Data:** 29 patient encounters transition from `Treatment` back to `Diagnostics`.
* **Operational Hypothesis:** Patients already undergoing emergency treatment experience evolving clinical symptoms, adverse medication responses, or procedural complications requiring secondary diagnostic imaging or rapid laboratory reassessment.
* **Process Impact:** Triggers 29 secondary diagnostic workups followed by secondary treatments.

### 5.4 Granular Patient Journey Variants (PM4Py Variant Analysis)
Using PM4Py trace extraction, the 500 patient journeys collapse into **11 unique pathway variants**:

| Variant | Patient Volume | Share | Pathway Description | Loop Count |
| :---: | :---: | :---: | :--- | :---: |
| **V1** | 175 | 35.0% | `Reg -> Triage -> Cons -> Treat -> Disch` (Direct Treatment Flow) | 0 |
| **V2** | 171 | 34.2% | `Reg -> Triage -> Cons -> Diag -> Treat -> Disch` (Standard Diagnostic Flow) | 0 |
| **V3** | 102 | 20.4% | `Reg -> Triage -> Cons -> Diag -> Cons -> Treat -> Disch` (Diagnostic Re-consultation) | 1 |
| **V4** | 12 | 2.4% | `Reg -> Triage -> Cons -> Treat -> Diag -> Treat -> Disch` (In-treatment Diagnostic Workup) | 1 |
| **V5** | 9 | 1.8% | `Reg -> Triage -> Reg -> Triage -> Cons -> Treat -> Disch` (Intake Rework Flow) | 1 |
| **V6** | 8 | 1.6% | `Reg -> Triage -> Reg -> Triage -> Cons -> Diag -> Treat -> Disch` (Intake Rework + Diagnostics) | 1 |
| **V7** | 7 | 1.4% | `Reg -> Triage -> Cons -> Diag -> Treat -> Diag -> Treat -> Disch` (Dual Diagnostic Escalation) | 1 |
| **V8** | 6 | 1.2% | Double Loop: Diag Re-consultation + In-treatment Diag | 2 |
| **V9** | 6 | 1.2% | Double Loop: Triage Admin Loop + Diag Re-consultation | 2 |
| **V10** | 2 | 0.4% | Double Loop: Triage Admin Loop + In-treatment Diag | 2 |
| **V11** | 2 | 0.4% | Triple Loop: Triage Admin + Diag Re-cons + In-treatment Diag | 3 |

**Summary of Pathway Stability:**
* **Clean Linear Journeys:** 346 patients (**69.2%**) follow standard linear pathways (Variants 1 and 2) with zero loop-backs.
* **Single Rework Journeys:** 138 patients (**27.6%**) encounter exactly one rework loop.
* **Multiple Rework Journeys:** 16 patients (**3.2%**) encounter two or three concurrent rework loops.

---

## 6. Operational Bottlenecks, Process Risks & Actionable Recommendations

### 6.1 Identified Operational Bottlenecks & Process Risks

1. **Consultation Queue Pressure & Workload Inflation:**
   * **Data Finding:** Consultation is the highest-volume clinical stage in the facility (**616 events** across 500 patient visits).
   * **Risk Factor:** The 116 diagnostic review re-consultations converge into the same clinical stage as initial arrivals, creating potential queue contention between incoming urgent patients and returning patients waiting for lab review.

2. **Diagnostics Workload Concentration:**
   * **Data Finding:** 331 total diagnostic encounters occur, comprising 302 initial consultation referrals and 29 secondary treatment escalations.
   * **Risk Factor:** While 64.95% (215 transitions) move directly to treatment, more than one-third (35.05%) re-enter consultation, indicating that diagnostic result interpretation represents a major branching juncture.

3. **Intake Process Friction:**
   * **Data Finding:** 27 patient journeys encounter a reverse transition from `Triage` to `Registration`.
   * **Risk Factor:** Any return to admissions duplicates effort for both triage nursing staff and registration clerks, introducing unnecessary workflow friction at the front door of the hospital.

### 6.2 Actionable Recommendations for Clinical & Operational Audit

Each recommendation is grounded directly in observed empirical transition patterns:

1. **Registration & Intake Data Verification Checklist (Addressing 27 Triage -> Registration Loops):**
   * *Target:* Eliminate the 27 administrative rework transitions.
   * *Proposed Action:* Implement a mandatory digital checklist at initial Registration (verifying insurance eligibility, identification, and reason for visit) to ensure complete intake packets before patients proceed to Triage.

2. **Standardized Diagnostic Results Communication Protocol (Addressing 116 Diagnostics -> Consultation Loops):**
   * *Target:* Streamline the 35.05% of diagnostic cases returning to Consultation.
   * *Proposed Action:* Establish clinical guidelines where routine, normal test results can be communicated directly to treatment teams or via secure digital charting, reserving formal secondary physician consultations for complex, ambiguous, or critical findings.

3. **In-Treatment Clinical Escalation Audit (Addressing 29 Treatment -> Diagnostics Loops):**
   * *Target:* Understand clinical triggers behind the 29 mid-treatment diagnostic escalations.
   * *Proposed Action:* Conduct a focused departmental review of the specific diagnoses and treatment protocols associated with Variant 4 and Variant 7 to determine whether certain patient sub-populations should receive expanded upfront diagnostics during initial evaluation.

4. **Queue Segregation at Consultation:**
   * *Target:* Relieve workload congestion from 616 consultation encounters.
   * *Proposed Action:* Consider establishing separate clinical tracking queues for first-time evaluations versus brief diagnostic result reviews, preventing return consultations from delaying first-contact triage handoffs.

> [!NOTE]
> *Cost, duration, and clinical outcome estimates are intentionally omitted here.* Comprehensive measurement of transition delays, handover times, and queue waiting durations will be empirically calculated in Week 3 using SQL window functions and Python statistical modeling.

---

## 7. Study Limitations & Synthetic Dataset Context

To maintain scientific integrity and realistic interpretation, several contextual boundaries are acknowledged:

1. **Synthetic Healthcare Event Log:**
   * The CareFlow dataset is a controlled, synthetic event log designed for process analytics and process-mining training.
   * Frequencies, pathway distributions, and loop-back rates reflect the underlying probabilistic data generation model rather than verified clinical metrics from a real-world hospital.

2. **Process Topology vs. Root Cause Causality:**
   * Directly-Follows Graphs visualize *what sequence of events occurred*; they do not explain *why* individuals navigated those paths.
   * Observed loop-backs must be interpreted as workflow patterns warranting inquiry rather than proof of medical negligence, staff incompetence, or system failure.

3. **Sequence Order vs. Elapsed Time:**
   * The Week 2 discovery pipeline evaluates transition frequencies and pathway topology. It does not measure the actual duration or handover lag between stages.
   * Comprehensive transition duration metrics, stage handover statistics, and bottleneck severity calculations are addressed in the Week 3 analytics phase.

---

## 8. Next Steps for Week 3: Transition Time Matrix & Pathway Durations

Week 3 will address these limitations by transitioning from **process topology** to **performance and time-based process mining**:

1. **SQL Window Functions for Handover Durations:**
   * Construct analytical SQL queries against `database/careflow.db` (`stg_healthcare_events_v2`) using `LEAD()` and `LAG()` window functions partitioned by `case_id` and ordered by `event_timestamp`.
   * Compute exact elapsed time in minutes for each of the 2,530 observed transitions:
     $$\Delta t = \text{Timestamp}_{i+1} - \text{Timestamp}_i$$

2. **Transition Time Matrix (Python & SQLite):**
   * Calculate summary statistics for every transition pathway:
     * Mean transition time (minutes)
     * Median transition time (minutes)
     * Minimum and maximum transition time
     * Standard deviation and interquartile range (IQR)
   * Specifically quantify the time penalty incurred during the three loop-backs (`Diagnostics -> Consultation`, `Triage -> Registration`, `Treatment -> Diagnostics`).

3. **Preparation for Power BI Dashboarding:**
   * Export the transition time metrics into dedicated processed datasets (`data/processed/transition_time_analysis.csv`) to support flow-time visuals and operational KPI dashboards.
