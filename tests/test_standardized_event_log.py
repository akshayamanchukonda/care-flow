"""Unit tests for CareFlow Week 2, Day 1: Standardized Process Mining Event Log.

Validates:
1. Existence and integrity of data/processed/standardized_event_log_v2.csv.
2. Canonical process mining columns: Case_ID, Activity_Name, Timestamp.
3. Clean column headers without leading/trailing whitespace.
4. Metadata traceability: patient_id, event_id, department, status, waiting_time_minutes, is_loopback, activity_sequence.
5. Exact volume metrics: 3,030 events, 500 cases, 420 unique patients.
6. Loop-back retention: exactly 214 rework events across 154 patient cases.
7. Data cleanliness: zero NULL or blank values across canonical identifiers.
8. ISO-8601 timestamp validity and strict chronological order per case (0 inversions).
9. Activity sequencing: 1-indexed consecutive ordering per case.
10. Clinical pathway boundaries: 100% of journeys start at Registration and end at Discharge.
11. PM4Py compatibility: format_dataframe succeeds with canonical parameters.
"""

from pathlib import Path
import unittest
import pandas as pd
import pm4py

REPO_ROOT = Path(__file__).resolve().parent.parent
STANDARDIZED_CSV = REPO_ROOT / "data" / "processed" / "standardized_event_log_v2.csv"
CLEANED_CSV = REPO_ROOT / "data" / "processed" / "cleaned_healthcare_event_log_v2.csv"
ORIGINAL_CSV = REPO_ROOT / "data" / "raw" / "healthcare_event_log.csv"

VALID_CLINICAL_ACTIVITIES = {
    "Registration",
    "Triage",
    "Consultation",
    "Diagnostics",
    "Treatment",
    "Discharge",
}

CANONICAL_COLUMNS = ["Case_ID", "Activity_Name", "Timestamp"]
METADATA_COLUMNS = [
    "case_id",
    "activity_name",
    "event_timestamp",
    "activity_sequence",
    "is_loopback",
    "patient_id",
    "event_id",
    "department",
    "status",
    "waiting_time_minutes",
]


class TestStandardizedEventLog(unittest.TestCase):
    """Test suite for Week 2 Day 1 standardized healthcare event log."""

    @classmethod
    def setUpClass(cls):
        """Load standardized event log once for all test assertions."""
        cls.assertTrue(STANDARDIZED_CSV.exists(), f"Standardized event log missing at {STANDARDIZED_CSV}")
        cls.df = pd.read_csv(STANDARDIZED_CSV)

    def test_file_exists_and_non_empty(self):
        """Verify standardized event log exists and has positive size."""
        self.assertTrue(STANDARDIZED_CSV.exists(), "standardized_event_log_v2.csv must exist.")
        self.assertGreater(STANDARDIZED_CSV.stat().st_size, 100000, "File size must be greater than 100 KB.")

    def test_column_headers_clean_no_whitespace(self):
        """Verify column headers have zero leading or trailing whitespace."""
        for col in self.df.columns:
            self.assertEqual(col, col.strip(), f"Column header '{col}' has unstripped whitespace.")

    def test_canonical_process_mining_columns_present(self):
        """Verify required canonical columns (Case_ID, Activity_Name, Timestamp) exist."""
        for col in CANONICAL_COLUMNS:
            self.assertIn(col, self.df.columns, f"Required canonical column '{col}' is missing.")

    def test_metadata_traceability_columns_present(self):
        """Verify all original event metadata columns are preserved."""
        for col in METADATA_COLUMNS:
            self.assertIn(col, self.df.columns, f"Metadata traceability column '{col}' is missing.")

    def test_exact_row_and_entity_counts(self):
        """Verify exact record counts: 3,030 events, 500 cases, 420 unique patients."""
        self.assertEqual(len(self.df), 3030, "Standardized event log must contain exactly 3,030 rows.")
        self.assertEqual(self.df["Case_ID"].nunique(), 500, "Must contain exactly 500 unique cases.")
        self.assertEqual(self.df["patient_id"].nunique(), 420, "Must contain exactly 420 unique patients.")

    def test_parity_with_cleaned_v2_dataset(self):
        """Verify event_id and row parity with cleaned_healthcare_event_log_v2.csv."""
        if CLEANED_CSV.exists():
            clean_df = pd.read_csv(CLEANED_CSV)
            self.assertEqual(len(self.df), len(clean_df), "Row count must match cleaned v2 dataset.")
            self.assertEqual(
                set(self.df["event_id"]),
                set(clean_df["event_id"]),
                "Event IDs must match cleaned v2 dataset exactly.",
            )

    def test_no_null_or_empty_values_in_canonical_columns(self):
        """Verify canonical columns contain zero NULL or blank values."""
        for col in CANONICAL_COLUMNS:
            null_count = int(self.df[col].isnull().sum())
            self.assertEqual(null_count, 0, f"Column '{col}' contains {null_count} nulls.")
            if self.df[col].dtype == object or pd.api.types.is_string_dtype(self.df[col]):
                blank_count = int((self.df[col].astype(str).str.strip() == "").sum())
                self.assertEqual(blank_count, 0, f"Column '{col}' contains {blank_count} empty strings.")

    def test_unique_event_ids(self):
        """Verify event_id primary keys are globally unique with zero duplicates."""
        duplicates = int(self.df["event_id"].duplicated().sum())
        self.assertEqual(duplicates, 0, f"Found {duplicates} duplicate event_id values.")

    def test_activity_names_clinical_domain(self):
        """Verify all activity names belong to the recognized clinical stages."""
        unique_activities = set(self.df["Activity_Name"].unique())
        self.assertTrue(
            unique_activities.issubset(VALID_CLINICAL_ACTIVITIES),
            f"Unexpected activities found: {unique_activities - VALID_CLINICAL_ACTIVITIES}",
        )

    def test_timestamp_iso_format_and_parsing(self):
        """Verify all timestamps strictly follow ISO format %Y-%m-%d %H:%M:%S."""
        parsed = pd.to_datetime(self.df["Timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        invalid_count = int(parsed.isnull().sum())
        self.assertEqual(invalid_count, 0, f"Found {invalid_count} unparseable timestamps.")

    def test_chronological_ordering_per_case(self):
        """Verify event timestamps are strictly non-decreasing within every case."""
        df_copy = self.df.copy()
        df_copy["dt"] = pd.to_datetime(df_copy["Timestamp"])
        inversions = 0
        for _, grp in df_copy.groupby("Case_ID"):
            times = grp["dt"].tolist()
            for i in range(len(times) - 1):
                if times[i] > times[i + 1]:
                    inversions += 1
        self.assertEqual(inversions, 0, f"Detected {inversions} chronological inversions within cases.")

    def test_activity_sequence_consecutive(self):
        """Verify activity_sequence starts at 1 and increments by 1 per case without gaps."""
        for _, grp in self.df.groupby("Case_ID"):
            seqs = grp["activity_sequence"].astype(int).tolist()
            expected = list(range(1, len(seqs) + 1))
            self.assertEqual(seqs, expected, "Activity sequence must be consecutive starting at 1.")

    def test_clinical_journey_boundaries(self):
        """Verify 100% of cases start with Registration and end with Discharge."""
        first_activities = self.df.groupby("Case_ID").first()["Activity_Name"]
        last_activities = self.df.groupby("Case_ID").last()["Activity_Name"]
        self.assertTrue(
            (first_activities == "Registration").all(),
            "100% of patient journeys must start at Registration.",
        )
        self.assertTrue(
            (last_activities == "Discharge").all(),
            "100% of patient journeys must conclude at Discharge.",
        )

    def test_loopback_rework_quantification(self):
        """Verify exactly 214 loop-back rework events across 154 cases."""
        loopback_sum = int(self.df["is_loopback"].astype(int).sum())
        cases_with_loops = int(self.df[self.df["is_loopback"].astype(int) == 1]["Case_ID"].nunique())
        self.assertEqual(loopback_sum, 214, f"Expected 214 loop-backs, found {loopback_sum}.")
        self.assertEqual(cases_with_loops, 154, f"Expected 154 cases with loop-backs, found {cases_with_loops}.")

    def test_waiting_time_non_negative(self):
        """Verify waiting_time_minutes contains zero negative values."""
        negative_waits = int((self.df["waiting_time_minutes"].astype(int) < 0).sum())
        self.assertEqual(negative_waits, 0, f"Found {negative_waits} negative waiting times.")

    def test_pm4py_format_dataframe_compatibility(self):
        """Verify PM4Py format_dataframe successfully converts the event log."""
        formatted_df = pm4py.format_dataframe(
            self.df,
            case_id="Case_ID",
            activity_key="Activity_Name",
            timestamp_key="Timestamp",
        )
        self.assertEqual(len(formatted_df), 3030, "PM4Py formatted dataframe must retain 3,030 rows.")
        self.assertIn("case:concept:name", formatted_df.columns, "PM4Py must assign case:concept:name.")
        self.assertIn("concept:name", formatted_df.columns, "PM4Py must assign concept:name.")
        self.assertIn("time:timestamp", formatted_df.columns, "PM4Py must assign time:timestamp.")


if __name__ == "__main__":
    unittest.main()
