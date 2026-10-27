"""CareFlow: Unit Tests for Week 3 Python Transition Time Analysis.

Validates:
  1. Process mining transition volume: 2,530 transitions across 500 cases.
  2. Baseline transition volume: 2,323 transitions across 500 visits.
  3. Non-negativity and non-null guarantees for all transition durations.
  4. Specific rework loop pathway observation counts and mean durations.
  5. Deterministic sorting and trace duration conservation.
  6. Generated summary and detail CSV schema integrity.
"""

from pathlib import Path
import sqlite3
import unittest

import numpy as np
import pandas as pd

from src.transition_analysis import (
    DB_PATH,
    OUTPUT_BASELINE_CSV,
    OUTPUT_DETAIL_CSV,
    OUTPUT_SUMMARY_CSV,
    calculate_baseline_transitions,
    calculate_process_mining_transitions,
    validate_results,
)


class TestTransitionAnalysis(unittest.TestCase):
    """Unit test suite for Week 3 Python transition time analysis."""

    @classmethod
    def setUpClass(cls):
        if not DB_PATH.exists():
            raise FileNotFoundError(f"Missing SQLite database at {DB_PATH}")
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.execute("PRAGMA foreign_keys = ON;")

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_process_mining_transitions_volume_and_integrity(self):
        """Verify 2,530 process mining transitions, 500 cases, 0 negative, 0 nulls."""
        df_detail, df_summary = calculate_process_mining_transitions(self.conn)
        self.assertEqual(len(df_detail), 2530)
        self.assertEqual(df_detail["case_id"].nunique(), 500)
        self.assertEqual((df_detail["transition_time_minutes"] < 0).sum(), 0)
        self.assertEqual(df_detail["transition_time_minutes"].isnull().sum(), 0)
        self.assertEqual(len(df_summary), 9)

    def test_baseline_transitions_volume_and_integrity(self):
        """Verify 2,323 baseline transitions, 500 visits, 0 negative, 0 nulls."""
        df_base_detail, df_base_summary = calculate_baseline_transitions(self.conn)
        self.assertEqual(len(df_base_detail), 2323)
        self.assertEqual(df_base_detail["visit_id"].nunique(), 500)
        self.assertEqual((df_base_detail["transition_time_minutes"] < 0).sum(), 0)
        self.assertEqual(df_base_detail["transition_time_minutes"].isnull().sum(), 0)
        self.assertEqual(len(df_base_summary), 6)

    def test_rework_loop_reconciliation(self):
        """Verify counts and means for all 3 clinical rework loop pathways."""
        _, df_summary = calculate_process_mining_transitions(self.conn)
        pmap = df_summary.set_index(["from_activity", "to_activity"]).to_dict(orient="index")

        # Diagnostics -> Consultation
        diag_consult = pmap.get(("Diagnostics", "Consultation"))
        self.assertIsNotNone(diag_consult)
        self.assertEqual(diag_consult["transition_count"], 116)
        self.assertAlmostEqual(diag_consult["avg_transition_time_minutes"], 73.20, places=2)
        self.assertEqual(diag_consult["is_loopback"], 1)

        # Treatment -> Diagnostics
        treat_diag = pmap.get(("Treatment", "Diagnostics"))
        self.assertIsNotNone(treat_diag)
        self.assertEqual(treat_diag["transition_count"], 29)
        self.assertAlmostEqual(treat_diag["avg_transition_time_minutes"], 86.34, places=2)
        self.assertEqual(treat_diag["is_loopback"], 1)

        # Triage -> Registration
        triage_reg = pmap.get(("Triage", "Registration"))
        self.assertIsNotNone(triage_reg)
        self.assertEqual(triage_reg["transition_count"], 27)
        self.assertAlmostEqual(triage_reg["avg_transition_time_minutes"], 17.22, places=2)
        self.assertEqual(triage_reg["is_loopback"], 1)

    def test_validation_function_passes(self):
        """Verify validate_results returns consistent metadata dict without raising."""
        df_detail, df_summary = calculate_process_mining_transitions(self.conn)
        df_base_detail, df_base_summary = calculate_baseline_transitions(self.conn)
        stats = validate_results(df_detail, df_summary, df_base_detail, df_base_summary)
        self.assertEqual(stats["proc_total_transitions"], 2530)
        self.assertEqual(stats["base_total_transitions"], 2323)
        self.assertEqual(stats["proc_pathway_count"], 9)
        self.assertEqual(stats["base_pathway_count"], 6)

    def test_generated_csv_files_exist_and_schemas_match(self):
        """Verify all 3 output CSV files exist and contain required columns."""
        self.assertTrue(OUTPUT_SUMMARY_CSV.exists())
        self.assertTrue(OUTPUT_BASELINE_CSV.exists())
        self.assertTrue(OUTPUT_DETAIL_CSV.exists())

        df_sum = pd.read_csv(OUTPUT_SUMMARY_CSV)
        self.assertIn("from_activity", df_sum.columns)
        self.assertIn("to_activity", df_sum.columns)
        self.assertIn("transition_count", df_sum.columns)
        self.assertIn("avg_transition_time_minutes", df_sum.columns)
        self.assertIn("median_transition_time_minutes", df_sum.columns)
        self.assertIn("iqr_minutes", df_sum.columns)

        df_det = pd.read_csv(OUTPUT_DETAIL_CSV)
        self.assertIn("case_id", df_det.columns)
        self.assertIn("patient_id", df_det.columns)
        self.assertIn("transition_time_minutes", df_det.columns)
        self.assertIn("is_rework_loop", df_det.columns)


if __name__ == "__main__":
    unittest.main()
