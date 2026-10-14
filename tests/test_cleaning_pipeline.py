"""Unit tests for CareFlow Day 5 healthcare event data cleaning and quality handling.

Verifies:
1. Raw dataset preservation and integrity.
2. Missing value handling rules.
3. Duplicate record detection and handling.
4. Timestamp formatting and chronological ordering.
5. Activity name validation against clinical domain standards.
6. Patient and visit identifier preservation.
7. Loopback identification and trace sequencing.
8. Cleaned dataset output quality.
"""

from pathlib import Path
import sqlite3
import unittest
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_V2_CSV = REPO_ROOT / "data" / "raw" / "healthcare_event_log_v2.csv"
CLEANED_CSV = REPO_ROOT / "data" / "processed" / "cleaned_healthcare_event_log_v2.csv"
ORIGINAL_CSV = REPO_ROOT / "data" / "raw" / "healthcare_event_log.csv"
DB_PATH = REPO_ROOT / "database" / "careflow.db"

VALID_CLINICAL_ACTIVITIES = {
    "Registration",
    "Triage",
    "Consultation",
    "Diagnostics",
    "Treatment",
    "Discharge",
}


class TestDataCleaningAndQualityHandling(unittest.TestCase):
    """Test suite for event log cleaning and data quality handling."""

    @classmethod
    def setUpClass(cls):
        """Load datasets once for assertions."""
        cls.raw_df = pd.read_csv(RAW_V2_CSV)
        cls.raw_df.columns = cls.raw_df.columns.str.strip()
        for col in cls.raw_df.columns:
            if cls.raw_df[col].dtype == object or pd.api.types.is_string_dtype(cls.raw_df[col]):
                cls.raw_df[col] = cls.raw_df[col].astype(str).str.strip()

        cls.clean_df = pd.read_csv(CLEANED_CSV)
        cls.clean_df.columns = cls.clean_df.columns.str.strip()

    def test_raw_dataset_preservation(self):
        """Test that raw datasets are preserved and exist."""
        self.assertTrue(ORIGINAL_CSV.exists(), "Original baseline CSV must exist.")
        self.assertTrue(RAW_V2_CSV.exists(), "Raw v2 CSV must exist.")
        self.assertEqual(len(self.raw_df), 3030, "Raw v2 dataset must contain 3,030 rows.")

    def test_missing_values_handling(self):
        """Test that canonical process mining columns have zero null or empty values."""
        canonical_cols = ["case_id", "activity_name", "event_timestamp", "activity_sequence", "is_loopback"]
        for col in canonical_cols:
            null_count = self.clean_df[col].isnull().sum()
            empty_count = (self.clean_df[col].astype(str).str.strip() == "").sum()
            self.assertEqual(null_count, 0, f"Column '{col}' must have 0 nulls, found {null_count}")
            self.assertEqual(empty_count, 0, f"Column '{col}' must have 0 empty strings, found {empty_count}")

    def test_duplicate_records_handling(self):
        """Test that event IDs are globally unique with zero duplicates."""
        dup_count = self.clean_df["event_id"].duplicated().sum()
        self.assertEqual(dup_count, 0, f"Expected 0 duplicate event IDs, found {dup_count}")
        self.assertEqual(self.clean_df["event_id"].nunique(), len(self.clean_df))

    def test_timestamp_validation(self):
        """Test that timestamps follow valid ISO format and strict chronological order per case."""
        # 1. Parse timestamps
        parsed_dt = pd.to_datetime(self.clean_df["event_timestamp"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        self.assertEqual(parsed_dt.isnull().sum(), 0, "All event timestamps must be valid ISO datetimes.")

        # 2. Chronological sequence per case
        temp_df = self.clean_df.copy()
        temp_df["dt"] = parsed_dt
        inversions = 0
        for _, grp in temp_df.groupby("case_id"):
            times = grp["dt"].tolist()
            for i in range(len(times) - 1):
                if times[i] >= times[i + 1]:
                    inversions += 1
        self.assertEqual(inversions, 0, f"Found {inversions} chronological inversions within cases.")

    def test_activity_name_validation(self):
        """Test that all activity names belong to the recognized clinical domain."""
        unique_acts = set(self.clean_df["activity_name"].unique())
        self.assertTrue(
            unique_acts.issubset(VALID_CLINICAL_ACTIVITIES),
            f"Unexpected activity names found: {unique_acts - VALID_CLINICAL_ACTIVITIES}",
        )
        self.assertEqual(len(unique_acts), 6, "Expected exactly 6 distinct clinical activities.")

    def test_identifier_preservation(self):
        """Test that 100% of patient IDs and visit cases from raw data are preserved."""
        raw_patients = set(self.raw_df["patient_id"].unique())
        clean_patients = set(self.clean_df["patient_id"].unique())
        self.assertEqual(raw_patients, clean_patients, "All patient IDs must be preserved.")
        self.assertEqual(len(clean_patients), 420)

        raw_visits = set(self.raw_df["visit_id"].unique())
        clean_cases = set(self.clean_df["case_id"].unique())
        self.assertEqual(raw_visits, clean_cases, "All visit/case IDs must be preserved.")
        self.assertEqual(len(clean_cases), 500)

    def test_loopback_handling_and_sequencing(self):
        """Test that loop-backs are identified and activity sequencing is 1-indexed."""
        # Loopbacks count
        loop_count = int(self.clean_df["is_loopback"].sum())
        cases_with_loops = self.clean_df[self.clean_df["is_loopback"] == 1]["case_id"].nunique()
        self.assertEqual(loop_count, 214, f"Expected 214 loopback events, found {loop_count}")
        self.assertEqual(cases_with_loops, 154, f"Expected 154 cases with loops, found {cases_with_loops}")

        # Activity sequence starting at 1
        min_seq = self.clean_df.groupby("case_id")["activity_sequence"].min()
        self.assertTrue((min_seq == 1).all(), "Every case must begin with activity_sequence = 1")

    def test_cleaned_dataset_file(self):
        """Test the exported cleaned dataset file structure and row counts."""
        self.assertTrue(CLEANED_CSV.exists(), "Cleaned dataset CSV must exist on disk.")
        expected_columns = [
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
        self.assertEqual(list(self.clean_df.columns), expected_columns)
        self.assertEqual(len(self.clean_df), 3030)

    def test_sqlite_staging_table_sync(self):
        """Test that SQLite staging table matches cleaned CSV."""
        if DB_PATH.exists():
            conn = sqlite3.connect(DB_PATH)
            try:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM stg_healthcare_events_v2;")
                stg_count = cur.fetchone()[0]
                self.assertEqual(stg_count, 3030, "SQLite staging table must contain 3,030 rows.")
            finally:
                conn.close()


if __name__ == "__main__":
    unittest.main()
