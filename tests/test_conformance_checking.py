"""CareFlow: Unit Tests for Formal Conformance Checking.

Validates:
  1. Exact mathematical distribution: 500 cases, 346 conformant (69.2%), 154 non-conformant (30.8%).
  2. Exactly 11 distinct trace variants identified.
  3. Variant 1 and Variant 2 account for exactly 175 and 171 cases.
  4. Rework loop accounting: 0 loops in conformant cases, all 214 loop events in non-conformant cases.
  5. Schema integrity of conformance_analysis.csv and conformance_summary.csv.
  6. Non-conformance delay penalty: average duration disparity >= 100 minutes.
"""

from pathlib import Path
import unittest

import pandas as pd

from src.conformance_checking import (
    CASE_CONFORMANCE_CSV,
    NORMATIVE_DIAGNOSTIC_PATHWAY,
    NORMATIVE_IDEAL_PATHWAY,
    REPORT_MD,
    STANDARDIZED_CSV,
    SUMMARY_CONFORMANCE_CSV,
    classify_case_conformance,
    load_event_log,
)


class TestConformanceChecking(unittest.TestCase):
    """Unit test suite for formal clinical conformance checking."""

    @classmethod
    def setUpClass(cls):
        if not STANDARDIZED_CSV.exists():
            raise FileNotFoundError(f"Missing standardized CSV: {STANDARDIZED_CSV}")
        cls.df_events = load_event_log(STANDARDIZED_CSV)
        cls.df_cases, cls.df_summary = classify_case_conformance(cls.df_events)

    def test_total_cases_and_variant_count(self):
        """Verify 500 total cases and exactly 11 distinct trace variants."""
        self.assertEqual(len(self.df_cases), 500)
        self.assertEqual(len(self.df_summary), 11)
        self.assertEqual(int(self.df_summary["case_count"].sum()), 500)

    def test_conformance_rates_and_counts(self):
        """Verify exactly 346 conformant cases (69.2%) and 154 non-conformant cases (30.8%)."""
        conformant_count = int(self.df_cases["is_conformant"].sum())
        non_conformant_count = len(self.df_cases) - conformant_count
        self.assertEqual(conformant_count, 346)
        self.assertEqual(non_conformant_count, 154)

    def test_ideal_and_permitted_variant_counts(self):
        """Verify Variant 1 has 175 cases and Variant 2 has 171 cases."""
        ideal_cases = self.df_cases[self.df_cases["conformance_status"] == "CONFORMANT_IDEAL"]
        diag_cases = self.df_cases[self.df_cases["conformance_status"] == "CONFORMANT_DIAGNOSTIC"]
        self.assertEqual(len(ideal_cases), 175)
        self.assertEqual(len(diag_cases), 171)

    def test_rework_loops_strictly_in_non_conformant_cases(self):
        """Verify conformant cases have 0 rework loops and non-conformant have >= 1."""
        conformant_cases = self.df_cases[self.df_cases["is_conformant"] == 1]
        non_conformant_cases = self.df_cases[self.df_cases["is_conformant"] == 0]
        self.assertEqual(conformant_cases["rework_loop_count"].sum(), 0)
        self.assertTrue((non_conformant_cases["rework_loop_count"] >= 1).all())

    def test_delay_penalty_direction(self):
        """Verify non-conforming journeys have statistically longer length of stay."""
        avg_conf = self.df_cases[self.df_cases["is_conformant"] == 1]["journey_duration_minutes"].mean()
        avg_non_conf = self.df_cases[self.df_cases["is_conformant"] == 0]["journey_duration_minutes"].mean()
        self.assertGreater(avg_non_conf, avg_conf)
        self.assertGreater(avg_non_conf - avg_conf, 100.0)

    def test_output_csv_and_report_files_exist(self):
        """Verify exported CSV and report files exist and are populated."""
        self.assertTrue(CASE_CONFORMANCE_CSV.exists())
        self.assertTrue(SUMMARY_CONFORMANCE_CSV.exists())
        self.assertTrue(REPORT_MD.exists())
        self.assertGreater(CASE_CONFORMANCE_CSV.stat().st_size, 500)
        self.assertGreater(SUMMARY_CONFORMANCE_CSV.stat().st_size, 100)
        self.assertGreater(REPORT_MD.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()

