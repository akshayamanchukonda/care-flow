# CareFlow: Week 2 Cloud-to-Process-Mining Discovery Report (Enhanced As-Is)

**Pipeline Architecture:** Google BigQuery (`Careflow_raw`) -> dbt Core (`careflow_staging`) -> PM4Py Process Mining
**Environment:** Google Cloud Platform (`care-flow-analytics`, `asia-south1`)
**Materialized dbt Mart:** `care-flow-analytics.careflow_staging.fct_standardized_event_log_v2`

---

## 1. Executive Summary & Verification Evidence

The end-to-end cloud process-mining pipeline has been successfully executed with zero local substitutes. Raw healthcare event logs stored in Google BigQuery were cleaned and transformed into a standardized Event Log via dbt Core, then ingested into PM4Py to empirically reconstruct the hospital's clinical pathway.

- **Total Staged Events:** 3,030 events
- **Total Patient Cases:** 500 cases
- **Total Patients:** 420 unique patients
- **Directly-Follows Graph Transitions:** 2,530 total handovers across 9 edges
- **Clinical Process Variants:** 11 discovered pathways
- **Boundary Integrity:** 100% of cases initiate at `Registration` (500) and conclude at `Discharge` (500)

- **Loop-Back Rework Events:** 214 events across 154 affected cases (30.8% of visits)
- **Empirical Backward Loop Transitions:** 172 total transitions (`Diagnostics -> Consultation`: 116, `Treatment -> Diagnostics`: 29, `Triage -> Registration`: 27)

---

## 2. Discovered Pathway Variants

A total of 11 unique clinical pathway variants were discovered in the enhanced dataset, comprising 346 clean linear visits (69.2%) and 154 rework visits (30.8%) encountering 1, 2, or 3 loop-backs.

| Variant Rank | Case Count | % of Cases | Clinical Pathway Description |
| :---: | :---: | :---: | :--- |
| **V1** | 175 | 35.00% | `Registration -> Triage -> Consultation -> Treatment -> Discharge` |
| **V2** | 171 | 34.20% | `Registration -> Triage -> Consultation -> Diagnostics -> Treatment -> Discharge` |
| **V3** | 102 | 20.40% | `Registration -> Triage -> Consultation -> Diagnostics -> Consultation -> Treatment -> Discharge` |
| **V4** | 12 | 2.40% | `Registration -> Triage -> Consultation -> Treatment -> Diagnostics -> Treatment -> Discharge` |
| **V5** | 9 | 1.80% | `Registration -> Triage -> Registration -> Triage -> Consultation -> Treatment -> Discharge` |

*(Full 11-variant taxonomy is detailed in reports/week2_process_analysis_summary.md)*

---

## 3. Empirical DFG Transition Metrics (Direct from BigQuery)

| source_activity   | target_activity   |   transition_count |   is_loopback_transition |   pct_of_source_activity |   pct_of_total_transitions |
|:------------------|:------------------|-------------------:|-------------------------:|-------------------------:|---------------------------:|
| Registration      | Triage            |                527 |                        0 |                   100    |                      20.83 |
| Treatment         | Discharge         |                500 |                        0 |                    94.52 |                      19.76 |
| Triage            | Consultation      |                500 |                        0 |                    94.88 |                      19.76 |
| Consultation      | Treatment         |                314 |                        0 |                    50.97 |                      12.41 |
| Consultation      | Diagnostics       |                302 |                        0 |                    49.03 |                      11.94 |
| Diagnostics       | Treatment         |                215 |                        0 |                    64.95 |                       8.5  |
| Diagnostics       | Consultation      |                116 |                        1 |                    35.05 |                       4.58 |
| Treatment         | Diagnostics       |                 29 |                        1 |                     5.48 |                       1.15 |
| Triage            | Registration      |                 27 |                        1 |                     5.12 |                       1.07 |

---

## 4. Verification & Agreement Assessment

The discovered cloud transitions show **100.0% exact numerical agreement across all 9 enhanced transitions** (including the 3 operational loop-back transitions) compared to the local benchmark (data/processed/transition_time_analysis.csv):
- Registration -> Triage: 527 transitions
- Triage -> Consultation: 500 transitions
- Treatment -> Discharge: 500 transitions
- Consultation -> Treatment: 314 transitions
- Consultation -> Diagnostics: 302 transitions
- Diagnostics -> Treatment: 215 transitions
- **Diagnostics -> Consultation (Loop-Back):** 116 transitions
- **Treatment -> Diagnostics (Loop-Back):** 29 transitions
- **Triage -> Registration (Loop-Back):** 27 transitions

Generated Artifacts:
- Process Map PNG: `as_is_process_map_bigquery.png`
- Graphviz DOT: `as_is_process_map_bigquery.dot`
- Transition Metrics: `dfg_transitions_bigquery.csv`
- Cloud Event Log CSV: `bigquery_standardized_event_log.csv`
