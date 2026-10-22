"""CareFlow: Unit Tests for Week 2 Day 5 Workflow Inefficiencies Analysis.

Validates:
  1. Existence and schema of reports/workflow_inefficiencies.csv.
  2. Exact case cohort partition: 346 clean (69.2%) vs. 154 rework (30.8%) across 500 cases.
  3. Exact loop-back counts: 27 admin rework, 116 diagnostic review, 29 treatment escalation (172 total).
  4. Extra events quantification (54 intake, 116 consultation, 58 treatment escalation).
  5. Empirical waiting time and elapsed journey duration disparities.
  6. Data integrity and absence of nulls or negative values.
"""

from pathlib import Path
import unittest

import pandas as pd

from src.workflow_inefficiencies import (
    load_event_log,
    calculate_case_inefficiencies,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
STANDARDIZED_CSV_PATH = REPO_ROOT / "data" / "processed" / "standardized_event_log_v2.csv"
OUTPUT_CSV_PATH = REPO_ROOT / "reports" / "workflow_inefficiencies.csv"


class TestWorkflowInefficiencies(unittest.TestCase):
    """Unit test suite for Week 2 Day 5 workflow inefficiencies identification."""

    @classmethod
    def setUpClass(cls):
        if not STANDARDIZED_CSV_PATH.exists():
            raise FileNotFoundError(f"Missing standardized event log: {STANDARDIZED_CSV_PATH}")
        if not OUTPUT_CSV_PATH.exists():
            raise FileNotFoundError(f"Missing workflow inefficiencies CSV: {OUTPUT_CSV_PATH}")

        cls.event_df = load_event_log(STANDARDIZED_CSV_PATH)
        cls.cases_df, cls.summary_df = calculate_case_inefficiencies(cls.event_df)
        cls.csv_df = pd.read_csv(OUTPUT_CSV_PATH)

    def test_output_csv_exists_and_non_empty(self):
        """Verify reports/workflow_inefficiencies.csv exists and has positive size."""
        self.assertTrue(OUTPUT_CSV_PATH.exists())
        self.assertGreater(OUTPUT_CSV_PATH.stat().st_size, 100)

    def test_output_csv_schema(self):
        """Verify all canonical inefficiency summary columns are present."""
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
        self.assertEqual(list(self.csv_df.columns), expected_cols)

    def test_case_cohort_partition(self):
        """Verify exact partition into 346 clean cases (69.2%) and 154 rework cases (30.8%)."""
        clean_count = (self.cases_df["is_rework"] == 0).sum()
        rework_count = (self.cases_df["is_rework"] == 1).sum()
        self.assertEqual(len(self.cases_df), 500)
        self.assertEqual(clean_count, 346)
        self.assertEqual(rework_count, 154)
        self.assertAlmostEqual(clean_count / 500 * 100.0, 69.2, places=1)
        self.assertAlmostEqual(rework_count / 500 * 100.0, 30.8, places=1)

    def test_rework_loop_distribution(self):
        """Verify exactly 138 single-loop cases and 16 multi-loop cases."""
        single_loop = (self.cases_df["total_loops"] == 1).sum()
        multi_loop = (self.cases_df["total_loops"] > 1).sum()
        self.assertEqual(single_loop, 138)
        self.assertEqual(multi_loop, 16)
        self.assertEqual(single_loop + multi_loop, 154)

    def test_admin_intake_rework_metrics(self):
        """Verify Triage -> Registration metrics: 27 cases, 27 transitions, 54 extra events."""
        row = self.csv_df[self.csv_df["pathway_transition"] == "Triage -> Registration"].iloc[0]
        self.assertEqual(int(row["affected_cases"]), 27)
        self.assertEqual(int(row["transition_instances"]), 27)
        self.assertEqual(int(row["extra_events_generated"]), 54)
        self.assertAlmostEqual(float(row["share_of_total_cases_pct"]), 5.4, places=1)

    def test_diagnostic_review_metrics(self):
        """Verify Diagnostics -> Consultation metrics: 116 cases, 116 transitions, 116 extra consultations."""
        row = self.csv_df[self.csv_df["pathway_transition"] == "Diagnostics -> Consultation"].iloc[0]
        self.assertEqual(int(row["affected_cases"]), 116)
        self.assertEqual(int(row["transition_instances"]), 116)
        self.assertEqual(int(row["extra_events_generated"]), 116)
        self.assertAlmostEqual(float(row["share_of_total_cases_pct"]), 23.2, places=1)

    def test_treatment_escalation_metrics(self):
        """Verify Treatment -> Diagnostics metrics: 29 cases, 29 transitions, 58 extra events."""
        row = self.csv_df[self.csv_df["pathway_transition"] == "Treatment -> Diagnostics"].iloc[0]
        self.assertEqual(int(row["affected_cases"]), 29)
        self.assertEqual(int(row["transition_instances"]), 29)
        self.assertEqual(int(row["extra_events_generated"]), 58)
        self.assertAlmostEqual(float(row["share_of_total_cases_pct"]), 5.8, places=1)

    def test_total_loopback_transitions(self):
        """Verify sum of rework transition instances equals exactly 172."""
        total_loop_transitions = int(self.cases_df["total_loops"].sum())
        self.assertEqual(total_loop_transitions, 172)

    def test_waiting_time_disparity_metrics(self):
        """Verify clean mean wait (~100.7 min) vs rework mean wait (~150.5 min) with +49.5% penalty."""
        clean_wait = self.cases_df[self.cases_df["is_rework"] == 0]["total_stage_waiting_minutes"].mean()
        rework_wait = self.cases_df[self.cases_df["is_rework"] == 1]["total_stage_waiting_minutes"].mean()
        self.assertAlmostEqual(clean_wait, 100.66, places=1)
        self.assertAlmostEqual(rework_wait, 150.52, places=1)
        wait_penalty = rework_wait - clean_wait
        self.assertAlmostEqual(wait_penalty, 49.85, places=1)
        self.assertAlmostEqual((wait_penalty / clean_wait) * 100.0, 49.5, places=1)

    def test_journey_duration_disparity_metrics(self):
        """Verify clean mean duration (~220.1 min) vs rework mean duration (~328.5 min) with +49.2% penalty."""
        clean_dur = self.cases_df[self.cases_df["is_rework"] == 0]["elapsed_journey_minutes"].mean()
        rework_dur = self.cases_df[self.cases_df["is_rework"] == 1]["elapsed_journey_minutes"].mean()
        self.assertAlmostEqual(clean_dur, 220.12, places=1)
        self.assertAlmostEqual(rework_dur, 328.53, places=1)
        dur_penalty = rework_dur - clean_dur
        self.assertAlmostEqual(dur_penalty, 108.41, places=1)
        self.assertAlmostEqual((dur_penalty / clean_dur) * 100.0, 49.2, places=1)

    def test_no_null_or_empty_values(self):
        """Verify 0 null, NaN, or blank values in workflow inefficiencies summary."""
        self.assertEqual(int(self.csv_df.isnull().sum().sum()), 0)


if __name__ == "__main__":
    unittest.main()
