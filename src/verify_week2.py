"""CareFlow: Week 2 Deliverables Verification Runner.

Comprehensive verification of:
  1. Virtual environment dependencies (PM4Py, matplotlib, networkx).
  2. Standardized process-mining event log (canonical fields: Case_ID, Activity_Name, Timestamp).
  3. Data integrity & chronology (3,030 events, 500 cases, 420 patients, 214 loop-backs).
  4. Discovered As-Is process model (DFG 9 transitions, 2,530 instances, 100% start/end alignment).
  5. Rework loop-back quantification (Triage->Reg: 27, Diag->Cons: 116, Treat->Diag: 29).
  6. Deliverable artifacts (standardized CSV, DFG transitions CSV, DOT model, high-res PNG map).
  7. Clinical pathway analysis summary report (reports/week2_process_analysis_summary.md).
  8. Healthcare workflow inefficiency catalog and disparities (reports/workflow_inefficiencies.csv).
  9. Week 2 unit test suites execution (41 tests across Days 1, 2, and 5).
 10. Week 1 baseline integrity preservation (SHA-256 hash match on original CSV).
"""

import hashlib
import os
from pathlib import Path
import sys
import unittest

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "database" / "careflow.db"
ORIGINAL_CSV = REPO_ROOT / "data" / "raw" / "healthcare_event_log.csv"
V2_RAW_CSV = REPO_ROOT / "data" / "raw" / "healthcare_event_log_v2.csv"
CLEANED_CSV = REPO_ROOT / "data" / "processed" / "cleaned_healthcare_event_log_v2.csv"
STANDARDIZED_CSV = REPO_ROOT / "data" / "processed" / "standardized_event_log_v2.csv"
TRANSITIONS_CSV = REPO_ROOT / "reports" / "dfg_transitions.csv"
DOT_PATH = REPO_ROOT / "reports" / "as_is_process_map.dot"
PNG_PATH = REPO_ROOT / "reports" / "as_is_process_map.png"
SUMMARY_REPORT = REPO_ROOT / "reports" / "week2_process_analysis_summary.md"
INEFFICIENCIES_CSV = REPO_ROOT / "reports" / "workflow_inefficiencies.csv"

ORIGINAL_EXPECTED_SHA256 = "03cb807a7e48fa9f5c0d7d6936f289d9654b76c1dbfaca0b02fb526172a565d5"


def check_original_dataset() -> tuple[bool, str]:
    if not ORIGINAL_CSV.exists():
        return False, "File not found"
    with open(ORIGINAL_CSV, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest()
    matches = actual_hash.lower() == ORIGINAL_EXPECTED_SHA256.lower()
    return matches, f"SHA-256: {actual_hash[:16]}... ({'UNTOUCHED' if matches else 'MODIFIED'})"


def check_dependencies() -> tuple[bool, dict]:
    results = {}
    try:
        import pm4py
        results["pm4py"] = f"v{pm4py.__version__}"
    except ImportError:
        results["pm4py"] = "MISSING"

    try:
        import matplotlib
        results["matplotlib"] = f"v{matplotlib.__version__}"
    except ImportError:
        results["matplotlib"] = "MISSING"

    try:
        import networkx
        results["networkx"] = f"v{networkx.__version__}"
    except ImportError:
        results["networkx"] = "MISSING"

    all_passed = all(v != "MISSING" for v in results.values())
    return all_passed, results


def check_standardized_event_log() -> tuple[bool, dict]:
    if not STANDARDIZED_CSV.exists():
        return False, {"error": "Standardized CSV missing"}

    df = pd.read_csv(STANDARDIZED_CSV)
    df.columns = df.columns.str.strip()

    canonical_present = all(c in df.columns for c in ["Case_ID", "Activity_Name", "Timestamp"])
    metadata_present = all(c in df.columns for c in ["patient_id", "event_id", "is_loopback", "waiting_time_minutes"])

    total_events = len(df)
    total_cases = df["Case_ID"].nunique()
    total_patients = df["patient_id"].nunique()
    loopbacks = int(df["is_loopback"].astype(int).sum())
    null_canonical = int(df[["Case_ID", "Activity_Name", "Timestamp"]].isnull().sum().sum())

    # Chronology validation
    df["dt"] = pd.to_datetime(df["Timestamp"])
    chronology_errors = 0
    for _, grp in df.groupby("Case_ID"):
        times = grp["dt"].tolist()
        for i in range(len(times) - 1):
            if times[i] >= times[i + 1]:
                chronology_errors += 1

    passed = (
        canonical_present
        and metadata_present
        and total_events == 3030
        and total_cases == 500
        and total_patients == 420
        and loopbacks == 214
        and null_canonical == 0
        and chronology_errors == 0
    )

    return passed, {
        "canonical_columns": canonical_present,
        "metadata_columns": metadata_present,
        "events": total_events,
        "cases": total_cases,
        "patients": total_patients,
        "loopbacks": loopbacks,
        "null_canonical": null_canonical,
        "chronology_errors": chronology_errors,
    }


def check_dfg_and_process_mining() -> tuple[bool, dict]:
    import pm4py

    df = pd.read_csv(STANDARDIZED_CSV)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])

    dfg, sa, ea = pm4py.discover_dfg(
        df,
        case_id_key="Case_ID",
        activity_key="Activity_Name",
        timestamp_key="Timestamp",
    )

    total_transitions = sum(dfg.values())
    unique_transitions = len(dfg)

    triage_to_reg = dfg.get(("Triage", "Registration"), 0)
    diag_to_cons = dfg.get(("Diagnostics", "Consultation"), 0)
    treat_to_diag = dfg.get(("Treatment", "Diagnostics"), 0)

    start_correct = (sa == {"Registration": 500})
    end_correct = (ea == {"Discharge": 500})

    passed = (
        unique_transitions == 9
        and total_transitions == 2530
        and triage_to_reg == 27
        and diag_to_cons == 116
        and treat_to_diag == 29
        and start_correct
        and end_correct
    )

    return passed, {
        "unique_transitions": unique_transitions,
        "total_transitions": total_transitions,
        "triage_to_reg": triage_to_reg,
        "diag_to_cons": diag_to_cons,
        "treat_to_diag": treat_to_diag,
        "start_activities": sa,
        "end_activities": ea,
    }


def check_deliverable_artifacts() -> tuple[bool, dict]:
    transitions_ok = TRANSITIONS_CSV.exists() and TRANSITIONS_CSV.stat().st_size > 100
    dot_ok = DOT_PATH.exists() and DOT_PATH.stat().st_size > 500
    png_ok = PNG_PATH.exists() and PNG_PATH.stat().st_size > 50000

    passed = transitions_ok and dot_ok and png_ok
    return passed, {
        "transitions_csv": f"{TRANSITIONS_CSV.stat().st_size if transitions_ok else 0} bytes",
        "dot_model": f"{DOT_PATH.stat().st_size if dot_ok else 0} bytes",
        "process_map_png": f"{PNG_PATH.stat().st_size if png_ok else 0} bytes",
    }


def check_pathway_analysis_report() -> tuple[bool, dict]:
    if not SUMMARY_REPORT.exists():
        return False, {"error": "Report file missing"}

    size = SUMMARY_REPORT.stat().st_size
    text = SUMMARY_REPORT.read_text(encoding="utf-8")

    has_variants = all(f"V{i}" in text for i in range(1, 12))
    has_cohorts = "346" in text and "154" in text
    has_loops = (
        "Triage" in text
        and "Registration" in text
        and "Diagnostics" in text
        and "Consultation" in text
        and "Treatment" in text
    )

    passed = size > 5000 and has_variants and has_cohorts and has_loops
    return passed, {
        "size_bytes": size,
        "all_variants_documented": has_variants,
        "cohort_counts_verified": has_cohorts,
        "rework_loops_covered": has_loops,
    }


def check_workflow_inefficiencies() -> tuple[bool, dict]:
    if not INEFFICIENCIES_CSV.exists():
        return False, {"error": "Inefficiencies CSV missing"}

    df_ineff = pd.read_csv(INEFFICIENCIES_CSV)
    expected_cols = [
        "inefficiency_category",
        "pathway_transition",
        "clinical_operational_nature",
        "affected_cases",
        "transition_instances",
        "extra_events_generated",
        "share_of_total_cases_pct",
        "observed_queue_impact",
    ]
    cols_ok = list(df_ineff.columns) == expected_cols
    rows_count = len(df_ineff)

    # Calculate dynamically from event log
    df_events = pd.read_csv(STANDARDIZED_CSV)
    df_events["dt"] = pd.to_datetime(df_events["Timestamp"])
    df_events = df_events.sort_values(["Case_ID", "dt"]).reset_index(drop=True)
    df_events["prev_act"] = df_events.groupby("Case_ID")["Activity_Name"].shift(1)

    t_reg = set(df_events[(df_events["prev_act"] == "Triage") & (df_events["Activity_Name"] == "Registration")]["Case_ID"])
    d_cons = set(df_events[(df_events["prev_act"] == "Diagnostics") & (df_events["Activity_Name"] == "Consultation")]["Case_ID"])
    t_diag = set(df_events[(df_events["prev_act"] == "Treatment") & (df_events["Activity_Name"] == "Diagnostics")]["Case_ID"])
    rework_cases = t_reg | d_cons | t_diag

    clean_wait = df_events[~df_events["Case_ID"].isin(rework_cases)].groupby("Case_ID")["waiting_time_minutes"].sum().mean()
    rework_wait = df_events[df_events["Case_ID"].isin(rework_cases)].groupby("Case_ID")["waiting_time_minutes"].sum().mean()
    wait_penalty = rework_wait - clean_wait
    wait_pct = (wait_penalty / clean_wait) * 100.0

    passed = (
        cols_ok
        and rows_count == 4
        and len(t_reg) == 27
        and len(d_cons) == 116
        and len(t_diag) == 29
        and len(rework_cases) == 154
        and round(wait_penalty, 2) == 49.85
        and round(wait_pct, 1) == 49.5
    )
    return passed, {
        "columns_verified": cols_ok,
        "rows_count": rows_count,
        "affected_rework_cases": len(rework_cases),
        "stage_wait_penalty_min": round(wait_penalty, 2),
        "stage_wait_penalty_pct": round(wait_pct, 1),
    }


def check_week2_unit_tests() -> tuple[bool, dict]:
    sys.path.insert(0, str(REPO_ROOT))
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for mod in [
        "tests.test_standardized_event_log",
        "tests.test_pathway_transitions",
        "tests.test_workflow_inefficiencies",
    ]:
        suite.addTests(loader.loadTestsFromName(mod))

    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    passed = result.wasSuccessful() and result.testsRun == 41
    return passed, {
        "tests_executed": result.testsRun,
        "errors": len(result.errors),
        "failures": len(result.failures),
        "all_passed": result.wasSuccessful(),
    }


def main():
    print("\n" + "=" * 75)
    print("             CAREFLOW WEEK 2 COMPREHENSIVE VERIFICATION REPORT")
    print("=" * 75)

    all_tests_passed = True

    # Check 1: Baseline Preservation
    orig_ok, orig_msg = check_original_dataset()
    print(f"\n[CHECK 1] Original Baseline Dataset (Stage 2):")
    print(f"  - Status     : {'[PASS]' if orig_ok else '[FAIL]'}")
    print(f"  - Details    : {orig_msg}")
    all_tests_passed &= orig_ok

    # Check 2: Dependencies
    dep_ok, dep_details = check_dependencies()
    print(f"\n[CHECK 2] Python Environment & Dependencies:")
    print(f"  - Status     : {'[PASS]' if dep_ok else '[FAIL]'}")
    for k, v in dep_details.items():
        print(f"  - {k:<12}: {v}")
    all_tests_passed &= dep_ok

    # Check 3: Standardized Event Log
    log_ok, log_details = check_standardized_event_log()
    print(f"\n[CHECK 3] Standardized Process Mining Event Log:")
    print(f"  - Status     : {'[PASS]' if log_ok else '[FAIL]'}")
    print(f"  - Canonical Columns Present (Case_ID, Activity_Name, Timestamp): {log_details.get('canonical_columns')}")
    print(f"  - Metadata Traceability Preserved                             : {log_details.get('metadata_columns')}")
    print(f"  - Total Events Processed                                      : {log_details.get('events'):,} (Target: 3,030)")
    print(f"  - Unique Patient Visits (Cases)                               : {log_details.get('cases'):,} (Target: 500)")
    print(f"  - Unique Patients                                             : {log_details.get('patients'):,} (Target: 420)")
    print(f"  - Loop-Back Rework Events Retained                            : {log_details.get('loopbacks'):,} (Target: 214)")
    print(f"  - Nulls in Canonical Identifiers                              : {log_details.get('null_canonical')}")
    print(f"  - Chronological Inconsistencies                               : {log_details.get('chronology_errors')}")
    all_tests_passed &= log_ok

    # Check 4: DFG & Process Mining
    dfg_ok, dfg_details = check_dfg_and_process_mining()
    print(f"\n[CHECK 4] PM4Py As-Is Process Model Discovery:")
    print(f"  - Status     : {'[PASS]' if dfg_ok else '[FAIL]'}")
    print(f"  - Discovered DFG Transitions                                  : {dfg_details.get('unique_transitions')} (Target: 9)")
    print(f"  - Total Transition Volume                                     : {dfg_details.get('total_transitions'):,} (Target: 2,530)")
    print(f"  - Start Activity 100% Registration                            : {dfg_details.get('start_activities')}")
    print(f"  - End Activity 100% Discharge                                 : {dfg_details.get('end_activities')}")
    print(f"  - Triage -> Registration Loop-Back                            : {dfg_details.get('triage_to_reg')} (Target: 27)")
    print(f"  - Diagnostics -> Consultation Loop-Back                       : {dfg_details.get('diag_to_cons')} (Target: 116)")
    print(f"  - Treatment -> Diagnostics Loop-Back                          : {dfg_details.get('treat_to_diag')} (Target: 29)")
    all_tests_passed &= dfg_ok

    # Check 5: Deliverable Artifacts
    art_ok, art_details = check_deliverable_artifacts()
    print(f"\n[CHECK 5] Week 2 Visualization Deliverable Artifacts:")
    print(f"  - Status     : {'[PASS]' if art_ok else '[FAIL]'}")
    for k, v in art_details.items():
        print(f"  - {k:<18}: {v}")
    all_tests_passed &= art_ok

    # Check 6: Pathway Analysis Report
    rep_ok, rep_details = check_pathway_analysis_report()
    print(f"\n[CHECK 6] Clinical Pathway Analysis Summary Report:")
    print(f"  - Status     : {'[PASS]' if rep_ok else '[FAIL]'}")
    print(f"  - File Size                                                   : {rep_details.get('size_bytes', 0):,} bytes")
    print(f"  - All 11 Journey Variants Documented (V1-V11)                 : {rep_details.get('all_variants_documented')}")
    print(f"  - Clean (346) & Rework (154) Cohort Quantifications           : {rep_details.get('cohort_counts_verified')}")
    print(f"  - Rework Loop-Back Pathways Detailed                          : {rep_details.get('rework_loops_covered')}")
    all_tests_passed &= rep_ok

    # Check 7: Workflow Inefficiencies
    ineff_ok, ineff_details = check_workflow_inefficiencies()
    print(f"\n[CHECK 7] Healthcare Workflow Inefficiency Catalog & Disparities:")
    print(f"  - Status     : {'[PASS]' if ineff_ok else '[FAIL]'}")
    print(f"  - Catalog Schema & Row Count                                  : {ineff_details.get('rows_count')} rows (Cols OK: {ineff_details.get('columns_verified')})")
    print(f"  - Affected Rework Cases Verified                              : {ineff_details.get('affected_rework_cases')} cases (30.8%)")
    print(f"  - Dynamic Stage Wait Penalty Verified                         : +{ineff_details.get('stage_wait_penalty_min')} min (+{ineff_details.get('stage_wait_penalty_pct')}%)")
    all_tests_passed &= ineff_ok

    # Check 8: Unit Tests
    ut_ok, ut_details = check_week2_unit_tests()
    print(f"\n[CHECK 8] Automated Week 2 Unit Test Suites:")
    print(f"  - Status     : {'[PASS]' if ut_ok else '[FAIL]'}")
    print(f"  - Total Unit Tests Executed                                   : {ut_details.get('tests_executed')} tests")
    print(f"  - Test Failures / Errors                                      : {ut_details.get('failures')} / {ut_details.get('errors')}")
    print(f"  - Test Suite Result                                           : {'ALL 41 PASSED' if ut_ok else 'FAILURES DETECTED'}")
    all_tests_passed &= ut_ok

    print("\n" + "=" * 75)
    if all_tests_passed:
        print("          ALL 8 WEEK 2 VERIFICATION CHECKS PASSED SUCCESSFULLY!          ")
    else:
        print("          VERIFICATION FAILED: ONE OR MORE CHECKS DID NOT PASS          ")
    print("=" * 75 + "\n")

    if not all_tests_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
