"""CareFlow: Unit Tests for Formal Conformance Checking (Week 4 Task 1).

Validates:
  1. Fully compliant patient journeys (Ideal 5-stage and Permitted Diagnostic 6-stage).
  2. Missing required activities (Registration, Discharge, Consultation, Treatment).
  3. Incorrect activity sequence / order inversions.
  4. Unexpected / unmapped activities outside clinical vocabulary.
  5. Repeated activities and clinical/operational rework loop-backs.
  6. Multiple patient cases grouping and aggregation.
  7. Timestamp chronological ordering and sorting.
  8. Missing or invalid data handling.
  9. Empty event log handling.
 10. Deterministic reproducibility of results.
 11. Full dataset-level mathematical conservation (500 cases, 346 conformant, 154 non-conformant, 11 variants).
"""

from pathlib import Path
import unittest

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

from src.conformance_checking import (
    CASE_CONFORMANCE_CSV,
    DEVIATIONS_DETAIL_CSV,
    NON_COMPLIANT_CASES_CSV,
    NORMATIVE_DIAGNOSTIC_PATHWAY,
    NORMATIVE_IDEAL_PATHWAY,
    REPORT_MD,
    STANDARDIZED_CSV,
    SUMMARY_CONFORMANCE_CSV,
    analyze_trace_deviations,
    classify_case_conformance,
    extract_deviations_detail,
    generate_non_compliant_summary,
    load_event_log,
)


class TestConformanceChecking(unittest.TestCase):
    """Comprehensive test suite for clinical process conformance checking."""

    @classmethod
    def setUpClass(cls):
        if not STANDARDIZED_CSV.exists():
            raise FileNotFoundError(f"Missing standardized CSV: {STANDARDIZED_CSV}")
        cls.df_events = load_event_log(STANDARDIZED_CSV)
        cls.df_cases, cls.df_summary = classify_case_conformance(cls.df_events)

    # -------------------------------------------------------------------------
    # 1. Fully Compliant Patient Journeys
    # -------------------------------------------------------------------------
    def test_01_fully_compliant_patient_journeys(self):
        """Verify Ideal 5-stage and Diagnostic 6-stage pathways achieve 100% compliance."""
        # Ideal flow
        res_ideal = analyze_trace_deviations(NORMATIVE_IDEAL_PATHWAY)
        self.assertEqual(res_ideal["is_conformant"], 1)
        self.assertEqual(res_ideal["conformance_status"], "CONFORMANT_IDEAL")
        self.assertEqual(res_ideal["trace_fitness"], 1.0)
        self.assertEqual(res_ideal["rework_loop_count"], 0)
        self.assertEqual(len(res_ideal["deviation_list"]), 0)

        # Permitted diagnostic flow
        res_diag = analyze_trace_deviations(NORMATIVE_DIAGNOSTIC_PATHWAY)
        self.assertEqual(res_diag["is_conformant"], 1)
        self.assertEqual(res_diag["conformance_status"], "CONFORMANT_DIAGNOSTIC")
        self.assertEqual(res_diag["trace_fitness"], 1.0)
        self.assertEqual(res_diag["rework_loop_count"], 0)
        self.assertEqual(len(res_diag["deviation_list"]), 0)

    # -------------------------------------------------------------------------
    # 2. Missing Required Activities
    # -------------------------------------------------------------------------
    def test_02_missing_required_activities(self):
        """Verify traces missing Registration, Discharge, Consultation, or Treatment are flagged."""
        # Missing Registration
        t_no_reg = ("Triage", "Consultation", "Treatment", "Discharge")
        res = analyze_trace_deviations(t_no_reg)
        self.assertEqual(res["is_conformant"], 0)
        self.assertTrue(any("Missing Required Start Activity" in d for d in res["deviation_list"]))

        # Missing Discharge
        t_no_disch = ("Registration", "Triage", "Consultation", "Treatment")
        res = analyze_trace_deviations(t_no_disch)
        self.assertEqual(res["is_conformant"], 0)
        self.assertTrue(any("Missing Required Terminal Activity" in d for d in res["deviation_list"]))

        # Missing Consultation
        t_no_consult = ("Registration", "Triage", "Treatment", "Discharge")
        res = analyze_trace_deviations(t_no_consult)
        self.assertEqual(res["is_conformant"], 0)
        self.assertTrue(any("Missing Core Clinical Activity (Consultation)" in d for d in res["deviation_list"]))

        # Missing Treatment
        t_no_treat = ("Registration", "Triage", "Consultation", "Discharge")
        res = analyze_trace_deviations(t_no_treat)
        self.assertEqual(res["is_conformant"], 0)
        self.assertTrue(any("Missing Core Clinical Activity (Treatment)" in d for d in res["deviation_list"]))

    # -------------------------------------------------------------------------
    # 3. Incorrect Activity Order
    # -------------------------------------------------------------------------
    def test_03_incorrect_activity_order(self):
        """Verify inverted activity sequences are flagged as non-conforming deviations."""
        # Treatment before Consultation
        t_inverted = ("Registration", "Triage", "Treatment", "Consultation", "Discharge")
        res = analyze_trace_deviations(t_inverted)
        self.assertEqual(res["is_conformant"], 0)
        self.assertIn("NON_CONFORMANT", res["conformance_status"])
        self.assertGreater(res["rework_loop_count"], 0)

        # Discharge before Treatment
        t_premature_disch = ("Registration", "Triage", "Consultation", "Discharge", "Treatment")
        res = analyze_trace_deviations(t_premature_disch)
        self.assertEqual(res["is_conformant"], 0)

    # -------------------------------------------------------------------------
    # 4. Unexpected Activities
    # -------------------------------------------------------------------------
    def test_04_unexpected_activities(self):
        """Verify unmapped/foreign activities are detected and flagged."""
        t_unknown = ("Registration", "Triage", "Surgery", "Treatment", "Discharge")
        res = analyze_trace_deviations(t_unknown)
        self.assertEqual(res["is_conformant"], 0)
        self.assertTrue(any("Unexpected Activity: Surgery" in d for d in res["deviation_list"]))

    # -------------------------------------------------------------------------
    # 5. Repeated Activities and Loop-Backs
    # -------------------------------------------------------------------------
    def test_05_repeated_activities_and_loop_backs(self):
        """Verify recognized rework loops and activity repetitions are correctly tracked."""
        # Diagnostics -> Consultation loop
        t_diag_loop = ("Registration", "Triage", "Consultation", "Diagnostics", "Consultation", "Treatment", "Discharge")
        res = analyze_trace_deviations(t_diag_loop)
        self.assertEqual(res["is_conformant"], 0)
        self.assertEqual(res["conformance_status"], "NON_CONFORMANT_REWORK")
        self.assertEqual(res["rework_loop_count"], 1)
        self.assertIn("Physician Review Rework", res["primary_deviation"])
        self.assertTrue(any("Repeated Activity (Consultation x2)" in d for d in res["deviation_list"]))

        # Treatment -> Diagnostics loop
        t_treat_loop = ("Registration", "Triage", "Consultation", "Diagnostics", "Treatment", "Diagnostics", "Treatment", "Discharge")
        res = analyze_trace_deviations(t_treat_loop)
        self.assertEqual(res["is_conformant"], 0)
        self.assertIn("In-Treatment Diagnostic Escalation", res["primary_deviation"])

        # Triage -> Registration loop
        t_triage_loop = ("Registration", "Triage", "Registration", "Triage", "Consultation", "Treatment", "Discharge")
        res = analyze_trace_deviations(t_triage_loop)
        self.assertEqual(res["is_conformant"], 0)
        self.assertIn("Administrative Rework", res["primary_deviation"])

    # -------------------------------------------------------------------------
    # 6. Multiple Patient Cases
    # -------------------------------------------------------------------------
    def test_06_multiple_patient_cases(self):
        """Verify batch evaluation across multiple heterogeneous patient cases."""
        df_multi = pd.DataFrame([
            {"case_id": "C1", "activity_name": "Registration", "event_timestamp": "2026-10-01 08:00:00", "waiting_time_minutes": 5},
            {"case_id": "C1", "activity_name": "Triage", "event_timestamp": "2026-10-01 08:10:00", "waiting_time_minutes": 5},
            {"case_id": "C1", "activity_name": "Consultation", "event_timestamp": "2026-10-01 08:30:00", "waiting_time_minutes": 10},
            {"case_id": "C1", "activity_name": "Treatment", "event_timestamp": "2026-10-01 09:00:00", "waiting_time_minutes": 5},
            {"case_id": "C1", "activity_name": "Discharge", "event_timestamp": "2026-10-01 09:30:00", "waiting_time_minutes": 0},

            {"case_id": "C2", "activity_name": "Registration", "event_timestamp": "2026-10-01 08:00:00", "waiting_time_minutes": 5},
            {"case_id": "C2", "activity_name": "Triage", "event_timestamp": "2026-10-01 08:10:00", "waiting_time_minutes": 5},
            {"case_id": "C2", "activity_name": "Consultation", "event_timestamp": "2026-10-01 08:30:00", "waiting_time_minutes": 10},
            {"case_id": "C2", "activity_name": "Diagnostics", "event_timestamp": "2026-10-01 09:00:00", "waiting_time_minutes": 15},
            {"case_id": "C2", "activity_name": "Treatment", "event_timestamp": "2026-10-01 09:45:00", "waiting_time_minutes": 5},
            {"case_id": "C2", "activity_name": "Discharge", "event_timestamp": "2026-10-01 10:15:00", "waiting_time_minutes": 0},

            {"case_id": "C3", "activity_name": "Registration", "event_timestamp": "2026-10-01 08:00:00", "waiting_time_minutes": 5},
            {"case_id": "C3", "activity_name": "Triage", "event_timestamp": "2026-10-01 08:10:00", "waiting_time_minutes": 5},
            {"case_id": "C3", "activity_name": "Consultation", "event_timestamp": "2026-10-01 08:30:00", "waiting_time_minutes": 10},
            {"case_id": "C3", "activity_name": "Diagnostics", "event_timestamp": "2026-10-01 09:00:00", "waiting_time_minutes": 15},
            {"case_id": "C3", "activity_name": "Consultation", "event_timestamp": "2026-10-01 09:30:00", "waiting_time_minutes": 10},
            {"case_id": "C3", "activity_name": "Treatment", "event_timestamp": "2026-10-01 10:00:00", "waiting_time_minutes": 5},
            {"case_id": "C3", "activity_name": "Discharge", "event_timestamp": "2026-10-01 10:30:00", "waiting_time_minutes": 0},
        ])
        cases, summary = classify_case_conformance(df_multi)
        self.assertEqual(len(cases), 3)
        self.assertEqual(int(cases["is_conformant"].sum()), 2)
        self.assertEqual(len(summary), 3)
        self.assertEqual(cases.loc[cases["case_id"] == "C1", "conformance_status"].iloc[0], "CONFORMANT_IDEAL")
        self.assertEqual(cases.loc[cases["case_id"] == "C2", "conformance_status"].iloc[0], "CONFORMANT_DIAGNOSTIC")
        self.assertEqual(cases.loc[cases["case_id"] == "C3", "conformance_status"].iloc[0], "NON_CONFORMANT_REWORK")

    # -------------------------------------------------------------------------
    # 7. Timestamp Ordering
    # -------------------------------------------------------------------------
    def test_07_timestamp_ordering(self):
        """Verify events scrambled in input order are sorted chronologically."""
        df_scrambled = pd.DataFrame([
            {"case_id": "C_TIME", "activity_name": "Treatment", "event_timestamp": "2026-10-01 09:00:00", "activity_sequence": 4, "event_id": "E4"},
            {"case_id": "C_TIME", "activity_name": "Registration", "event_timestamp": "2026-10-01 08:00:00", "activity_sequence": 1, "event_id": "E1"},
            {"case_id": "C_TIME", "activity_name": "Discharge", "event_timestamp": "2026-10-01 09:30:00", "activity_sequence": 5, "event_id": "E5"},
            {"case_id": "C_TIME", "activity_name": "Consultation", "event_timestamp": "2026-10-01 08:30:00", "activity_sequence": 3, "event_id": "E3"},
            {"case_id": "C_TIME", "activity_name": "Triage", "event_timestamp": "2026-10-01 08:10:00", "activity_sequence": 2, "event_id": "E2"},
        ])
        # Sort using standard sorting logic
        df_sorted = df_scrambled.sort_values(by=["case_id", "event_timestamp"]).reset_index(drop=True)
        cases, _ = classify_case_conformance(df_sorted)
        self.assertEqual(cases.iloc[0]["is_conformant"], 1)
        self.assertEqual(cases.iloc[0]["conformance_status"], "CONFORMANT_IDEAL")

        # Inversion detection
        inv_times = [
            pd.Timestamp("2026-10-01 08:00:00"),
            pd.Timestamp("2026-10-01 07:30:00"),  # Inversion
        ]
        res_inv = analyze_trace_deviations(["Registration", "Triage"], inv_times)
        self.assertTrue(any("Chronological Inversion" in d for d in res_inv["deviation_list"]))

    # -------------------------------------------------------------------------
    # 8. Missing or Invalid Data
    # -------------------------------------------------------------------------
    def test_08_missing_or_invalid_data(self):
        """Verify graceful handling of missing optional fields and NaN values."""
        df_sparse = pd.DataFrame([
            {"case_id": "C_SPARSE", "activity_name": "Registration", "event_timestamp": "2026-10-01 08:00:00"},
            {"case_id": "C_SPARSE", "activity_name": "Triage", "event_timestamp": "2026-10-01 08:10:00"},
            {"case_id": "C_SPARSE", "activity_name": "Consultation", "event_timestamp": "2026-10-01 08:30:00"},
            {"case_id": "C_SPARSE", "activity_name": "Treatment", "event_timestamp": "2026-10-01 09:00:00"},
            {"case_id": "C_SPARSE", "activity_name": "Discharge", "event_timestamp": "2026-10-01 09:30:00"},
        ])
        cases, _ = classify_case_conformance(df_sparse)
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases.iloc[0]["patient_id"], "UNKNOWN")
        self.assertEqual(cases.iloc[0]["department"], "General")
        self.assertEqual(cases.iloc[0]["total_waiting_minutes"], 0)

    # -------------------------------------------------------------------------
    # 9. Empty Event Logs
    # -------------------------------------------------------------------------
    def test_09_empty_event_logs(self):
        """Verify empty event logs return empty outputs with schema intact."""
        df_empty = pd.DataFrame()
        cases, summary = classify_case_conformance(df_empty)
        self.assertTrue(cases.empty)
        self.assertTrue(summary.empty)
        self.assertEqual(len(cases.columns), 14)
        self.assertEqual(len(summary.columns), 11)

    # -------------------------------------------------------------------------
    # 10. Reproducibility of Results
    # -------------------------------------------------------------------------
    def test_10_reproducibility_of_results(self):
        """Verify running the classification engine multiple times produces identical results."""
        cases_run1, summary_run1 = classify_case_conformance(self.df_events)
        cases_run2, summary_run2 = classify_case_conformance(self.df_events)
        assert_frame_equal(cases_run1, cases_run2)
        assert_frame_equal(summary_run1, summary_run2)

    # -------------------------------------------------------------------------
    # 11. Full Dataset Mathematical Conservation & Regression Parity
    # -------------------------------------------------------------------------
    def test_11_dataset_level_mathematical_conservation(self):
        """Verify 500 cases, 346 conformant, 154 non-conformant, 11 variants, and file sizes."""
        # Exact counts
        self.assertEqual(len(self.df_cases), 500)
        self.assertEqual(len(self.df_summary), 11)
        self.assertEqual(int(self.df_summary["case_count"].sum()), 500)

        conformant_count = int(self.df_cases["is_conformant"].sum())
        non_conformant_count = len(self.df_cases) - conformant_count
        self.assertEqual(conformant_count, 346)
        self.assertEqual(non_conformant_count, 154)

        ideal_cases = self.df_cases[self.df_cases["conformance_status"] == "CONFORMANT_IDEAL"]
        diag_cases = self.df_cases[self.df_cases["conformance_status"] == "CONFORMANT_DIAGNOSTIC"]
        self.assertEqual(len(ideal_cases), 175)
        self.assertEqual(len(diag_cases), 171)

        # Rework loop accounting
        conformant_cases = self.df_cases[self.df_cases["is_conformant"] == 1]
        non_conformant_cases = self.df_cases[self.df_cases["is_conformant"] == 0]
        self.assertEqual(conformant_cases["rework_loop_count"].sum(), 0)
        self.assertTrue((non_conformant_cases["rework_loop_count"] >= 1).all())

        # Non-conformance delay penalty
        avg_conf = self.df_cases[self.df_cases["is_conformant"] == 1]["journey_duration_minutes"].mean()
        avg_non_conf = self.df_cases[self.df_cases["is_conformant"] == 0]["journey_duration_minutes"].mean()
        self.assertGreater(avg_non_conf, avg_conf)
        self.assertGreater(avg_non_conf - avg_conf, 100.0)

        # Output files exist and are populated
        self.assertTrue(CASE_CONFORMANCE_CSV.exists())
        self.assertTrue(SUMMARY_CONFORMANCE_CSV.exists())
        self.assertTrue(DEVIATIONS_DETAIL_CSV.exists())
        self.assertTrue(NON_COMPLIANT_CASES_CSV.exists())
        self.assertTrue(REPORT_MD.exists())
        self.assertGreater(CASE_CONFORMANCE_CSV.stat().st_size, 500)
        self.assertGreater(SUMMARY_CONFORMANCE_CSV.stat().st_size, 100)
        self.assertGreater(DEVIATIONS_DETAIL_CSV.stat().st_size, 500)
        self.assertGreater(NON_COMPLIANT_CASES_CSV.stat().st_size, 500)
        self.assertGreater(REPORT_MD.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
