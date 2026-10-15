"""Unit tests for CareFlow Day 6 SQLite staging and healthcare data validation.

Validates:
1. SQLite database and schema configuration.
2. Staging table (stg_healthcare_events_v2) existence, column definitions, and constraints.
3. Performance indexes on staging table (case_id, activity_name, timestamp, sequence).
4. Data loading completeness and row count parity (3,030 records, 500 cases, 420 patients).
5. Non-null constraints on all staging columns.
6. Primary key uniqueness (zero duplicate event_id values).
7. Activity name validation against clinical domain standards.
8. Event timestamp formatting (%Y-%m-%d %H:%M:%S) and chronological monotonicity.
9. Clinical journey boundaries (Registration at seq 1, Discharge at max seq).
10. Loop-back quantification and recurrence logic.
11. Check constraint enforcement (rejecting negative waits and invalid loopback flags).
"""

from pathlib import Path
import sqlite3
import unittest
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "database" / "careflow.db"
SCHEMA_PATH = REPO_ROOT / "database" / "schema.sql"
RAW_V2_CSV = REPO_ROOT / "data" / "raw" / "healthcare_event_log_v2.csv"
CLEANED_CSV = REPO_ROOT / "data" / "processed" / "cleaned_healthcare_event_log_v2.csv"

VALID_CLINICAL_ACTIVITIES = {
    "Registration",
    "Triage",
    "Consultation",
    "Diagnostics",
    "Treatment",
    "Discharge",
}

EXPECTED_STAGING_COLUMNS = {
    "case_id": "TEXT",
    "activity_name": "TEXT",
    "event_timestamp": "TEXT",
    "activity_sequence": "INTEGER",
    "is_loopback": "INTEGER",
    "patient_id": "TEXT",
    "event_id": "TEXT",
    "department": "TEXT",
    "status": "TEXT",
    "waiting_time_minutes": "INTEGER",
}

EXPECTED_INDEXES = {
    "idx_stg_case",
    "idx_stg_activity",
    "idx_stg_time",
    "idx_stg_seq",
}


class TestSQLiteStagingAndDataValidation(unittest.TestCase):
    """Test suite for SQLite staging table integrity and healthcare data validation."""

    @classmethod
    def setUpClass(cls):
        """Establish database connection and load staging data once."""
        cls.assertTrue(DB_PATH.exists(), f"SQLite database not found at {DB_PATH}")
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.execute("PRAGMA foreign_keys = ON;")

    @classmethod
    def tearDownClass(cls):
        """Close database connection."""
        cls.conn.close()

    def test_schema_sql_defines_staging_table(self):
        """Verify schema.sql contains the DDL definition for stg_healthcare_events_v2."""
        self.assertTrue(SCHEMA_PATH.exists(), "database/schema.sql must exist.")
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_content = f.read()

        self.assertIn("stg_healthcare_events_v2", schema_content, "schema.sql must define stg_healthcare_events_v2.")
        self.assertIn("idx_stg_case", schema_content, "schema.sql must define idx_stg_case index.")
        self.assertIn("idx_stg_activity", schema_content, "schema.sql must define idx_stg_activity index.")
        self.assertIn("idx_stg_time", schema_content, "schema.sql must define idx_stg_time index.")
        self.assertIn("idx_stg_seq", schema_content, "schema.sql must define idx_stg_seq index.")

    def test_staging_table_exists_in_database(self):
        """Verify stg_healthcare_events_v2 table exists in SQLite database."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='stg_healthcare_events_v2';"
        )
        row = cur.fetchone()
        self.assertIsNotNone(row, "Table stg_healthcare_events_v2 must exist in careflow.db.")

    def test_staging_table_columns_and_types(self):
        """Verify column names, data types, and non-null constraints in stg_healthcare_events_v2."""
        cur = self.conn.cursor()
        cur.execute("PRAGMA table_info(stg_healthcare_events_v2);")
        columns_info = cur.fetchall()
        # columns_info: (cid, name, type, notnull, dflt_value, pk)

        actual_columns = {col[1]: col[2] for col in columns_info}
        self.assertEqual(
            set(actual_columns.keys()),
            set(EXPECTED_STAGING_COLUMNS.keys()),
            "Staging table columns do not match expected schema.",
        )

        for col_name, expected_type in EXPECTED_STAGING_COLUMNS.items():
            self.assertEqual(
                actual_columns[col_name].upper(),
                expected_type,
                f"Column {col_name} has unexpected type {actual_columns[col_name]} (expected {expected_type}).",
            )

        # Check primary key on event_id
        pk_cols = [col[1] for col in columns_info if col[5] > 0]
        self.assertEqual(pk_cols, ["event_id"], "event_id must be the primary key.")

        # Check NOT NULL constraint on all columns
        not_null_cols = [col[1] for col in columns_info if col[3] == 1]
        self.assertEqual(
            set(not_null_cols),
            set(EXPECTED_STAGING_COLUMNS.keys()),
            "All staging columns must have NOT NULL constraints.",
        )

    def test_staging_indexes_exist(self):
        """Verify required performance indexes exist on stg_healthcare_events_v2."""
        cur = self.conn.cursor()
        cur.execute("PRAGMA index_list(stg_healthcare_events_v2);")
        indexes = {row[1] for row in cur.fetchall()}
        for expected_idx in EXPECTED_INDEXES:
            self.assertIn(
                expected_idx,
                indexes,
                f"Index {expected_idx} missing from stg_healthcare_events_v2.",
            )

    def test_staging_row_count_and_parity(self):
        """Verify row count matches raw v2 dataset (3,030 rows)."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM stg_healthcare_events_v2;")
        count = cur.fetchone()[0]
        self.assertEqual(count, 3030, "Staging table must contain exactly 3,030 rows.")

        if RAW_V2_CSV.exists():
            raw_df = pd.read_csv(RAW_V2_CSV)
            self.assertEqual(count, len(raw_df), "Staging row count must match raw v2 CSV.")

    def test_distinct_cases_and_patients(self):
        """Verify distinct case and patient counts in SQLite staging."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT case_id), COUNT(DISTINCT patient_id) FROM stg_healthcare_events_v2;")
        unique_cases, unique_patients = cur.fetchone()
        self.assertEqual(unique_cases, 500, "Staging table must contain 500 distinct cases.")
        self.assertEqual(unique_patients, 420, "Staging table must contain 420 distinct patients.")

    def test_primary_key_uniqueness(self):
        """Verify event_id has zero duplicate records in staging table."""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT event_id, COUNT(*)
            FROM stg_healthcare_events_v2
            GROUP BY event_id
            HAVING COUNT(*) > 1;
        """)
        duplicates = cur.fetchall()
        self.assertEqual(len(duplicates), 0, f"Found duplicate event IDs in staging table: {duplicates}")

    def test_no_null_or_empty_values(self):
        """Verify no column in stg_healthcare_events_v2 contains NULL or blank text."""
        cur = self.conn.cursor()
        for col in EXPECTED_STAGING_COLUMNS:
            cur.execute(f"""
                SELECT COUNT(*) FROM stg_healthcare_events_v2
                WHERE {col} IS NULL OR (TYPEOF({col}) = 'text' AND TRIM({col}) = '');
            """)
            invalid_count = cur.fetchone()[0]
            self.assertEqual(invalid_count, 0, f"Column {col} contains {invalid_count} NULL or empty values.")

    def test_clinical_activity_domain_validity(self):
        """Verify all activity names belong to valid clinical stages."""
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT activity_name FROM stg_healthcare_events_v2;")
        activities = {row[0] for row in cur.fetchall()}
        self.assertTrue(
            activities.issubset(VALID_CLINICAL_ACTIVITIES),
            f"Found invalid clinical activities: {activities - VALID_CLINICAL_ACTIVITIES}",
        )

    def test_timestamp_iso_format(self):
        """Verify all event_timestamp values match standard ISO format %Y-%m-%d %H:%M:%S."""
        cur = self.conn.cursor()
        cur.execute("SELECT event_timestamp FROM stg_healthcare_events_v2;")
        timestamps = [row[0] for row in cur.fetchall()]
        parsed = pd.to_datetime(timestamps, format="%Y-%m-%d %H:%M:%S", errors="coerce")
        self.assertEqual(
            int(parsed.isnull().sum()),
            0,
            "Found unparseable or non-standard timestamps in staging table.",
        )

    def test_case_chronological_ordering(self):
        """Verify that event timestamps are monotonically non-decreasing within each case."""
        df = pd.read_sql_query(
            "SELECT case_id, event_timestamp, activity_sequence FROM stg_healthcare_events_v2 ORDER BY case_id, activity_sequence;",
            self.conn,
        )
        df["dt"] = pd.to_datetime(df["event_timestamp"])
        for _, grp in df.groupby("case_id"):
            times = grp["dt"].tolist()
            sequences = grp["activity_sequence"].tolist()
            # Sequence must start at 1 and increment by 1
            self.assertEqual(sequences, list(range(1, len(sequences) + 1)), "Activity sequences must be consecutive starting at 1.")
            # Timestamps must not invert
            for i in range(len(times) - 1):
                self.assertLessEqual(times[i], times[i + 1], "Chronological inversion detected within case.")

    def test_clinical_journey_boundaries(self):
        """Verify all cases start with Registration and conclude with Discharge."""
        df = pd.read_sql_query(
            "SELECT case_id, activity_name, activity_sequence FROM stg_healthcare_events_v2 ORDER BY case_id, activity_sequence;",
            self.conn,
        )
        first_events = df.groupby("case_id").first()["activity_name"]
        last_events = df.groupby("case_id").last()["activity_name"]

        self.assertTrue((first_events == "Registration").all(), "100% of cases must start with Registration.")
        self.assertTrue((last_events == "Discharge").all(), "100% of cases must conclude with Discharge.")

    def test_loopback_classification_integrity(self):
        """Verify is_loopback is strictly binary (0, 1) and correctly flags re-visited activities."""
        cur = self.conn.cursor()
        cur.execute("SELECT DISTINCT is_loopback FROM stg_healthcare_events_v2;")
        distinct_vals = {row[0] for row in cur.fetchall()}
        self.assertTrue(distinct_vals.issubset({0, 1}), f"is_loopback contains non-binary values: {distinct_vals}")

        cur.execute("SELECT SUM(is_loopback), COUNT(DISTINCT case_id) FROM stg_healthcare_events_v2 WHERE is_loopback = 1;")
        loop_count, cases_with_loops = cur.fetchone()
        self.assertEqual(loop_count, 214, "Expected exactly 214 loop-back events.")
        self.assertEqual(cases_with_loops, 154, "Expected loop-backs in exactly 154 cases.")

        # Verify logic: if is_loopback = 1, activity must have been seen earlier in the same case
        df = pd.read_sql_query(
            "SELECT case_id, activity_name, activity_sequence, is_loopback FROM stg_healthcare_events_v2 ORDER BY case_id, activity_sequence;",
            self.conn,
        )
        for _, grp in df.groupby("case_id"):
            seen = set()
            for _, row in grp.iterrows():
                act = row["activity_name"]
                flag = row["is_loopback"]
                if flag == 1:
                    self.assertIn(act, seen, f"Activity {act} flagged as loopback but not previously seen in case.")
                else:
                    self.assertNotIn(act, seen, f"Activity {act} previously seen but not flagged as loopback.")
                seen.add(act)

    def test_waiting_time_non_negative(self):
        """Verify waiting_time_minutes has no negative values."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM stg_healthcare_events_v2 WHERE waiting_time_minutes < 0;")
        negative_count = cur.fetchone()[0]
        self.assertEqual(negative_count, 0, "waiting_time_minutes must be >= 0.")

    def test_check_constraints_enforcement(self):
        """Verify that SQLite CHECK constraints reject invalid rows."""
        cur = self.conn.cursor()
        # Test 1: Negative waiting time should be rejected
        with self.assertRaises(sqlite3.IntegrityError):
            cur.execute("""
                INSERT INTO stg_healthcare_events_v2 (
                    case_id, activity_name, event_timestamp, activity_sequence,
                    is_loopback, patient_id, event_id, department, status, waiting_time_minutes
                ) VALUES (
                    'TEST_CASE', 'Triage', '2026-01-01 00:00:00', 1,
                    0, 'TEST_PATIENT', 'TEST_EVT_NEG', 'Emergency', 'Completed', -10
                );
            """)

        # Test 2: Invalid is_loopback (e.g. 2) should be rejected
        with self.assertRaises(sqlite3.IntegrityError):
            cur.execute("""
                INSERT INTO stg_healthcare_events_v2 (
                    case_id, activity_name, event_timestamp, activity_sequence,
                    is_loopback, patient_id, event_id, department, status, waiting_time_minutes
                ) VALUES (
                    'TEST_CASE', 'Triage', '2026-01-01 00:00:00', 1,
                    2, 'TEST_PATIENT', 'TEST_EVT_BAD_LOOP', 'Emergency', 'Completed', 10
                );
            """)

        # Test 3: Duplicate event_id should be rejected (PRIMARY KEY constraint)
        cur.execute("SELECT event_id FROM stg_healthcare_events_v2 LIMIT 1;")
        existing_event_id = cur.fetchone()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            cur.execute(f"""
                INSERT INTO stg_healthcare_events_v2 (
                    case_id, activity_name, event_timestamp, activity_sequence,
                    is_loopback, patient_id, event_id, department, status, waiting_time_minutes
                ) VALUES (
                    'TEST_CASE_DUP', 'Triage', '2026-01-01 00:00:00', 1,
                    0, 'TEST_PATIENT', '{existing_event_id}', 'Emergency', 'Completed', 10
                );
            """)


if __name__ == "__main__":
    unittest.main()
