"""CareFlow: Unit Tests for Week 2 Day 2 Pathway Transition Discovery.

Validates:
  1. DFG transitions file existence and schema integrity.
  2. Exact mathematical volume: 2,530 transitions (3,030 events - 500 cases).
  3. Case boundary preservation: 0 transitions originate from terminal stage (Discharge).
  4. Loop-back rework transition classification and counts (172 loop-back instances across 3 edges).
  5. Forward clinical flow transition counts across all 6 forward edges.
  6. Source and total percentage distributions.
  7. Exact parity between PM4Py DFG discovery and direct per-case trace extraction.
"""

from pathlib import Path
import unittest

import pandas as pd

from src.process_discovery import (
    LOOPBACK_TRANSITIONS,
    extract_trace_transitions,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
STANDARDIZED_CSV_PATH = REPO_ROOT / "data" / "processed" / "standardized_event_log_v2.csv"
TRANSITIONS_CSV_PATH = REPO_ROOT / "reports" / "dfg_transitions.csv"

CLINICAL_STAGES = {
    "Registration",
    "Triage",
    "Consultation",
    "Diagnostics",
    "Treatment",
    "Discharge",
}

EXPECTED_TRANSITIONS = {
    ("Registration", "Triage"): 527,
    ("Treatment", "Discharge"): 500,
    ("Triage", "Consultation"): 500,
    ("Consultation", "Treatment"): 314,
    ("Consultation", "Diagnostics"): 302,
    ("Diagnostics", "Treatment"): 215,
    ("Diagnostics", "Consultation"): 116,
    ("Treatment", "Diagnostics"): 29,
    ("Triage", "Registration"): 27,
}


class TestPathwayTransitionDiscovery(unittest.TestCase):
    """Unit test suite for Week 2 Day 2 clinical pathway transition discovery."""

    @classmethod
    def setUpClass(cls):
        if not STANDARDIZED_CSV_PATH.exists():
            raise FileNotFoundError(f"Missing standardized event log: {STANDARDIZED_CSV_PATH}")
        if not TRANSITIONS_CSV_PATH.exists():
            raise FileNotFoundError(f"Missing transitions CSV: {TRANSITIONS_CSV_PATH}")

        cls.event_df = pd.read_csv(STANDARDIZED_CSV_PATH)
        cls.event_df["dt"] = pd.to_datetime(cls.event_df["Timestamp"])
        cls.trans_df = pd.read_csv(TRANSITIONS_CSV_PATH)

    def test_transitions_file_exists_and_non_empty(self):
        """Verify reports/dfg_transitions.csv exists and has positive size."""
        self.assertTrue(TRANSITIONS_CSV_PATH.exists())
        self.assertGreater(TRANSITIONS_CSV_PATH.stat().st_size, 100)

    def test_transitions_file_schema(self):
        """Verify all canonical transition summary columns are present."""
        expected_cols = [
            "source_activity",
            "target_activity",
            "transition_count",
            "is_loopback_transition",
            "pct_of_source_activity",
            "pct_of_total_transitions",
        ]
        self.assertEqual(list(self.trans_df.columns), expected_cols)

    def test_exact_transition_volume(self):
        """Verify total transition count matches formula: 3,030 events - 500 cases = 2,530."""
        total_transitions = int(self.trans_df["transition_count"].sum())
        expected_volume = len(self.event_df) - self.event_df["Case_ID"].nunique()
        self.assertEqual(total_transitions, 2530)
        self.assertEqual(total_transitions, expected_volume)

    def test_distinct_transition_count(self):
        """Verify exactly 9 distinct transition pairs were discovered."""
        self.assertEqual(len(self.trans_df), 9)

    def test_case_boundary_integrity_no_terminal_outflow(self):
        """Verify zero transitions originate from Discharge (no cross-case leakage)."""
        discharge_sources = self.trans_df[self.trans_df["source_activity"] == "Discharge"]
        self.assertEqual(len(discharge_sources), 0, "Found invalid outgoing transition from Discharge!")

    def test_trace_iteration_parity(self):
        """Verify PM4Py transition counts perfectly match trace-by-trace iteration."""
        trace_counts = extract_trace_transitions(self.event_df)
        csv_counts = {
            (row["source_activity"], row["target_activity"]): int(row["transition_count"])
            for _, row in self.trans_df.iterrows()
        }
        self.assertEqual(trace_counts, csv_counts)
        self.assertEqual(trace_counts, EXPECTED_TRANSITIONS)

    def test_clinical_activity_domain(self):
        """Verify all sources and targets belong to the recognized clinical stages."""
        sources = set(self.trans_df["source_activity"].unique())
        targets = set(self.trans_df["target_activity"].unique())
        self.assertTrue(sources.issubset(CLINICAL_STAGES))
        self.assertTrue(targets.issubset(CLINICAL_STAGES))

    def test_loopback_transitions_quantification(self):
        """Verify loop-back transitions are accurately identified and quantified."""
        loopback_rows = self.trans_df[self.trans_df["is_loopback_transition"] == 1]
        self.assertEqual(len(loopback_rows), 3)

        loop_dict = {
            (r["source_activity"], r["target_activity"]): int(r["transition_count"])
            for _, r in loopback_rows.iterrows()
        }
        self.assertEqual(loop_dict.get(("Diagnostics", "Consultation")), 116)
        self.assertEqual(loop_dict.get(("Treatment", "Diagnostics")), 29)
        self.assertEqual(loop_dict.get(("Triage", "Registration")), 27)

        total_loopback_transitions = loopback_rows["transition_count"].sum()
        self.assertEqual(total_loopback_transitions, 172)

    def test_forward_clinical_transitions(self):
        """Verify forward transitions match expected clinical counts."""
        forward_rows = self.trans_df[self.trans_df["is_loopback_transition"] == 0]
        self.assertEqual(len(forward_rows), 6)

        forward_dict = {
            (r["source_activity"], r["target_activity"]): int(r["transition_count"])
            for _, r in forward_rows.iterrows()
        }
        self.assertEqual(forward_dict.get(("Registration", "Triage")), 527)
        self.assertEqual(forward_dict.get(("Treatment", "Discharge")), 500)
        self.assertEqual(forward_dict.get(("Triage", "Consultation")), 500)
        self.assertEqual(forward_dict.get(("Consultation", "Treatment")), 314)
        self.assertEqual(forward_dict.get(("Consultation", "Diagnostics")), 302)
        self.assertEqual(forward_dict.get(("Diagnostics", "Treatment")), 215)

    def test_source_percentage_totals(self):
        """Verify outgoing percentage per source activity sums to 100%."""
        for src, grp in self.trans_df.groupby("source_activity"):
            pct_sum = grp["pct_of_source_activity"].sum()
            self.assertAlmostEqual(pct_sum, 100.0, places=1, msg=f"Source {src} pct sum is {pct_sum}")

    def test_total_percentage_sum(self):
        """Verify sum of pct_of_total_transitions equals 100.0%."""
        total_pct = self.trans_df["pct_of_total_transitions"].sum()
        self.assertAlmostEqual(total_pct, 100.0, places=1)

    def test_no_null_or_empty_values(self):
        """Verify 0 null, NaN, or blank values in transition metrics."""
        null_count = self.trans_df.isnull().sum().sum()
        self.assertEqual(null_count, 0)

    def test_is_loopback_transition_binary(self):
        """Verify is_loopback_transition column is strictly binary {0, 1}."""
        unique_vals = set(self.trans_df["is_loopback_transition"].unique())
        self.assertTrue(unique_vals.issubset({0, 1}))

    def test_chronological_ordering_guarantee(self):
        """Verify all cases have strictly non-decreasing timestamps before transitions."""
        violations = 0
        for _, grp in self.event_df.groupby("Case_ID"):
            times = grp["dt"].tolist()
            for i in range(len(times) - 1):
                if times[i] > times[i + 1]:
                    violations += 1
        self.assertEqual(violations, 0)


if __name__ == "__main__":
    unittest.main()
