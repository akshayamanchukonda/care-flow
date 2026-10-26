# CareFlow: Week 2 Cloud-to-Process-Mining Discovery Report (Baseline)

**Pipeline Architecture:** Google BigQuery (`Careflow_raw`) -> dbt Core (`careflow_staging`) -> PM4Py Process Mining
**Environment:** Google Cloud Platform (`care-flow-analytics`, `asia-south1`)
**Materialized dbt Mart:** `care-flow-analytics.careflow_staging.fct_standardized_event_log`

---

## 1. Executive Summary & Verification Evidence

The end-to-end cloud process-mining pipeline has been successfully executed with zero local substitutes. Raw healthcare event logs stored in Google BigQuery were cleaned and transformed into a standardized Event Log via dbt Core, then ingested into PM4Py to empirically reconstruct the hospital's clinical pathway.

- **Total Staged Events:** 2,823 events
- **Total Patient Cases:** 500 cases
- **Total Patients:** 420 unique patients
- **Directly-Follows Graph Transitions:** 2,323 total handovers across 6 edges
- **Clinical Process Variants:** 2 discovered pathways
- **Boundary Integrity:** 100% of cases initiate at `Registration` (500) and conclude at `Discharge` (500)

---

## 2. Discovered Pathway Variants

| Variant ID | Case Count | % of Cases | Clinical Pathway Description |
| :---: | :---: | :---: | :--- |
| **Variant 1** | 323 | 64.60% | `Registration -> Triage -> Consultation -> Diagnostics -> Treatment -> Discharge` (Diagnostic Workup) |
| **Variant 2** | 177 | 35.40% | `Registration -> Triage -> Consultation -> Treatment -> Discharge` (Direct Treatment, Diagnostics Skipped) |

---

## 3. Empirical DFG Transition Metrics (Direct from BigQuery)

| source_activity   | target_activity   |   transition_count |   is_loopback_transition |   pct_of_source_activity |   pct_of_total_transitions |
|:------------------|:------------------|-------------------:|-------------------------:|-------------------------:|---------------------------:|
| Registration      | Triage            |                500 |                        0 |                    100   |                      21.52 |
| Treatment         | Discharge         |                500 |                        0 |                    100   |                      21.52 |
| Triage            | Consultation      |                500 |                        0 |                    100   |                      21.52 |
| Consultation      | Diagnostics       |                323 |                        0 |                     64.6 |                      13.9  |
| Diagnostics       | Treatment         |                323 |                        0 |                    100   |                      13.9  |
| Consultation      | Treatment         |                177 |                        0 |                     35.4 |                       7.62 |

---

## 4. Verification & Agreement Assessment

The discovered cloud transitions show **100.0% exact numerical agreement across all 6 baseline clinical pathway transition aggregates** compared to the local baseline benchmark (data/processed/baseline_transition_times.csv):
- Treatment -> Discharge: 500 transitions
- Registration -> Triage: 500 transitions
- Triage -> Consultation: 500 transitions
- Consultation -> Diagnostics: 323 transitions (64.6%)
- Diagnostics -> Treatment: 323 transitions (64.6%)
- Consultation -> Treatment: 177 transitions (35.4%)

Generated Artifacts:
- Process Map PNG: `as_is_process_map_bigquery_baseline.png`
- Graphviz DOT: `as_is_process_map_bigquery_baseline.dot`
- Transition Metrics: `dfg_transitions_bigquery_baseline.csv`
- Cloud Event Log CSV: `bigquery_standardized_event_log_baseline.csv`
