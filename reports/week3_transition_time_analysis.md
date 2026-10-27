# CareFlow: Week 3 Process Transition Time Analysis Report

**Project:** CareFlow — Clinical Pathway Process Mining & Healthcare Analytics
**Phase:** Week 3 Deliverable Summary
**Author:** Data Analytics Intern
**Environment:** Local Python (`.venv`) & SQLite (`database/careflow.db`)
**Artifact Dependencies:**
- `data/processed/transition_time_analysis.csv` (Process Mining 9-pathway metrics)
- `data/processed/baseline_transition_times.csv` (Baseline 6-pathway metrics)
- `data/processed/visit_transitions_detail.csv` (Granular 2,530 transition records)
- `sql/queries/11_transition_times.sql` & `sql/queries/12_process_mining_transition_times.sql`
- `sql/views/v_transition_times.sql` & `sql/views/v_process_mining_transition_times.sql`

---

## 1. Executive Summary & Purpose of Week 3

In **Week 2**, process discovery reconstructed the topological structure and transition frequencies of patient journeys using PM4Py (identifying 9 pathway types and 214 loop-backs). However, frequency alone cannot reveal **how much time patients spend in handover between consecutive clinical stages**.

The purpose of **Week 3** is to transition from process topology to **temporal performance analysis**:
1. Calculate the exact **elapsed transition times (in minutes)** between consecutive clinical stages (e.g., Triage $\rightarrow$ Consultation, Consultation $\rightarrow$ Diagnostics, Treatment $\rightarrow$ Discharge) using SQL window functions and Python.
2. Quantify statistical distributions across every pathway (Observation Count, Mean, Median, Standard Deviation, Min, Max, and Interquartile Range).
3. Evaluate the **temporal penalty imposed by clinical and operational rework loops** (`Diagnostics -> Consultation`, `Treatment -> Diagnostics`, `Triage -> Registration`).
4. Establish clean analytical datasets to feed into operational KPI dashboards and conformance checking.

---

## 2. Methodology & Mathematical Formulation

### 2.1 Transition Duration Definition
For any patient visit $V$, let $E_i = (A_i, T_i)$ represent the $i$-th clinical event with activity name $A_i$ and event start timestamp $T_i$. The transition duration $\Delta t_{(i \rightarrow i+1)}$ from activity $A_i$ to activity $A_{i+1}$ within the same visit is defined as:

$$\Delta t_{(i \rightarrow i+1)} = \frac{T_{i+1} - T_i}{60} \quad \text{(in minutes)}$$

### 2.2 SQL Window Function Implementation (`LEAD()`)
To ensure that transitions are calculated **strictly within the same patient visit** and avoid cross-visit cartesian joins, SQL window functions partition the event stream by `case_id` (or `visit_id`) and sort chronologically:

```sql
WITH ConsecutiveEvents AS (
    SELECT
        case_id,
        activity_name AS from_activity,
        event_timestamp AS from_timestamp,
        LEAD(activity_name) OVER (
            PARTITION BY case_id
            ORDER BY event_timestamp, activity_sequence
        ) AS to_activity,
        LEAD(event_timestamp) OVER (
            PARTITION BY case_id
            ORDER BY event_timestamp, activity_sequence
        ) AS to_timestamp
    FROM stg_healthcare_events_v2
)
SELECT
    from_activity,
    to_activity,
    COUNT(*) AS transition_count,
    ROUND(AVG((strftime('%s', to_timestamp) - strftime('%s', from_timestamp)) / 60.0), 2) AS avg_transition_time_minutes,
    ROUND(MIN((strftime('%s', to_timestamp) - strftime('%s', from_timestamp)) / 60.0), 2) AS min_transition_time_minutes,
    ROUND(MAX((strftime('%s', to_timestamp) - strftime('%s', from_timestamp)) / 60.0), 2) AS max_transition_time_minutes
FROM ConsecutiveEvents
WHERE to_activity IS NOT NULL
GROUP BY from_activity, to_activity;
```

### 2.3 Mathematical Conservation Property
For every visit, the sum of all stepwise transition durations equals the total journey duration:

$$\sum_{i=1}^{k-1} \Delta t_{(i \rightarrow i+1)} = T_{\text{end}} - T_{\text{start}}$$

This was verified on empirical test cases (e.g. Case `V0001` with 6 transition steps totaling $330.0 \text{ minutes} = 22:04:42 - 16:34:42$).

---

## 3. Discovered Transition Time Metrics (Process Mining Pathways)

The empirical analysis evaluated all **2,530 observed transitions** across all 500 patient visits from `data/processed/transition_time_analysis.csv`:

| From Activity | To Activity | Count | % of All | Loop? | Mean (min) | Median (min) | Std Dev (min) | Min (min) | Max (min) | IQR (min) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Registration` | `Triage` | 527 | 20.83% | No | **19.64** | 18.0 | 8.55 | 6.0 | 55.0 | 11.00 |
| `Treatment` | `Discharge` | 500 | 19.76% | No | **71.32** | 73.0 | 21.35 | 29.0 | 130.0 | 35.00 |
| `Triage` | `Consultation` | 500 | 19.76% | No | **46.71** | 43.0 | 18.98 | 13.0 | 129.0 | 24.00 |
| `Consultation` | `Treatment` | 314 | 12.41% | No | **48.39** | 47.0 | 14.34 | 21.0 | 87.0 | 21.00 |
| `Consultation` | `Diagnostics` | 302 | 11.94% | No | **59.25** | 57.0 | 18.72 | 21.0 | 123.0 | 23.75 |
| `Diagnostics` | `Treatment` | 215 | 8.50% | No | **59.74** | 59.0 | 16.27 | 26.0 | 120.0 | 21.00 |
| `Diagnostics` | `Consultation` | 116 | 4.58% | **Yes** | **73.20** | 71.5 | 24.14 | 25.0 | 149.0 | 29.25 |
| `Treatment` | `Diagnostics` | 29 | 1.15% | **Yes** | **86.34** | 91.0 | 23.95 | 48.0 | 141.0 | 42.00 |
| `Triage` | `Registration` | 27 | 1.07% | **Yes** | **17.22** | 17.0 | 3.80 | 11.0 | 24.0 | 4.00 |

---

## 4. Baseline Relational Transition Times (6 Pathways)

For cross-validation against the baseline relational database schema (`events` table, 2,823 events, 2,323 transitions from `data/processed/baseline_transition_times.csv`):

| From Activity | To Activity | Count | % of All | Mean (min) | Median (min) | Std Dev (min) | Min (min) | Max (min) | IQR (min) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Treatment` | `Discharge` | 500 | 21.52% | **70.80** | 72.0 | 21.41 | 29.0 | 126.0 | 37.00 |
| `Triage` | `Consultation` | 500 | 21.52% | **46.87** | 43.0 | 21.48 | 15.0 | 134.0 | 27.00 |
| `Registration` | `Triage` | 500 | 21.52% | **18.99** | 18.0 | 7.78 | 6.0 | 55.0 | 9.00 |
| `Consultation` | `Diagnostics` | 323 | 13.90% | **59.89** | 56.0 | 19.23 | 23.0 | 125.0 | 25.00 |
| `Diagnostics` | `Treatment` | 323 | 13.90% | **59.40** | 59.0 | 16.39 | 28.0 | 116.0 | 21.50 |
| `Consultation` | `Treatment` | 177 | 7.62% | **50.12** | 48.0 | 14.41 | 23.0 | 98.0 | 19.00 |

---

## 5. Key Operational Findings & Handover Insights

### 5.1 Rework Loops Impose the Heaviest Handover Delays
* **In-Treatment Diagnostic Escalation (`Treatment -> Diagnostics`, 29 cases):**
  Averages **86.34 minutes** (median 91.0 min). This is the longest transition in the hospital. When a patient in treatment develops complications requiring urgent secondary diagnostics, organizing the test, sample transport, and imaging slot causes substantial delays.
* **Diagnostic Physician Review (`Diagnostics -> Consultation`, 116 cases):**
  Averages **73.20 minutes** (median 71.5 min, max 149.0 min). Patients whose diagnostic results require physician re-evaluation wait an additional 1.2 hours before their treatment plan can be revised.
* **Triage Clerical Correction (`Triage -> Registration`, 27 cases):**
  Averages **17.22 minutes** (median 17.0 min). While relatively rapid, this administrative detour adds ~17 minutes of dead time before the patient can restart their intake journey.

### 5.2 Handover Delays at Standard Transitions
* **Discharge Process Bottleneck (`Treatment -> Discharge`):**
  Averages **71.32 minutes** (median 73.0 min). Completing nursing treatment to final discharge involves discharge paperwork, medication dispensing, transport coordination, and discharge lounge waiting.
* **Diagnostic Order-to-Execution (`Consultation -> Diagnostics`):**
  Averages **59.25 minutes** (median 57.0 min). Captures the patient transit and laboratory/imaging queue time after the physician orders diagnostic tests.
* **Triage to Consultation Handover (`Triage -> Consultation`):**
  Averages **46.71 minutes** (median 43.0 min), reflecting the acute doctor queue.

### 5.3 Clean Cohort vs. Rework Cohort Journey Disparities
Segmenting patient journeys into Clean visits ($N = 346$, 69.2%) vs. Rework visits ($N = 154$, 30.8%) reveals significant operational divergence:
* **Total Journey Handover Duration:** Clean visits average **220.12 minutes (3.67 hours)** (median 217.0 min, std 49.87 min), whereas Rework visits average **328.53 minutes (5.48 hours)** (median 324.0 min, std 63.37 min) — imposing an overall temporal penalty of **+108.41 minutes (+49.3% extended hospital stay)**.
* **Shared Transition Handover Parity:** On shared standard pathways, handover durations remain statistically comparable between cohorts:
  - `Registration -> Triage`: Clean = 19.45 min vs. Rework = 20.00 min.
  - `Triage -> Consultation`: Clean = 46.29 min vs. Rework = 47.64 min.
  - `Consultation -> Diagnostics`: Clean = 58.16 min vs. Rework = 60.68 min.
  - `Treatment -> Discharge`: Clean = 71.71 min vs. Rework = 70.45 min.
  This demonstrates that the length-of-stay disparity is driven almost exclusively by the execution of loop-back activities and their associated queue handovers, rather than systemic delays on baseline pathway legs.

---

## 6. Verification & Quality Assurance Summary

The test runner [`src/verify_week3.py`](file:///c:/Users/Dell/OneDrive/Documents/GitHub/care-flow/src/verify_week3.py) verified all analytical deliverables:
1. **SQL Execution Check:** Both queries executed cleanly, returning 6 pathways for baseline and 9 pathways for process mining.
2. **Observation Count Check:** Exactly **2,530 transitions** for process mining (matching $3,030 - 500$) and **2,323 transitions** for baseline ($2,823 - 500$).
3. **Non-Negativity Check:** **0** negative durations and **0** null values across all 2,530 records.
4. **Duration Conservation Check:** Individual trace validation confirmed that stepwise handover sums equal overall visit durations down to 0.001 minutes (e.g. Case `V0001` with 6 transition steps conserving exactly 330.0 minutes).
5. **PM4Py Performance DFG Parity Check:** Independent PM4Py performance graph discovery (`pm4py.discover_performance_dfg`) reconciled 9 out of 9 pathways against the SQL window function metrics with $\le 0.05$ minute tolerance.
6. **Regression Check:** All 10 prior verification checks across Week 1 and Week 2 continue to pass with 100% compliance.

---

## 7. Next Steps for Week 3 Days 4 & 5

With transition frequencies (Week 2) and transition durations (Week 3 Days 1–3) fully quantified and reconciled across SQL, Python, and PM4Py:
1. **Day 4: Performance Visualization & Interactive Dashboarding:** Implement rich Streamlit dashboard modules (`src/dashboard.py`) with cross-filtering by patient cohort, department queue distributions, and transition delay boxplots.
2. **Day 5: Operational Bottleneck Insights & SLA Thresholding:** Formulate clinical recommendations for triage Clerical Intake, Diagnostic Review turnaround, and Discharge lounge operational handovers.
