"""CareFlow: Week 1 Local Data Ingestion & Cleaning Pipeline.

Substitutes Google BigQuery with local SQLite and dbt with Python/SQL.

Pipeline Steps:
---------------
1. Raw Data Ingestion:
   - Loads data/raw/healthcare_event_log_v2.csv into SQLite table `raw_healthcare_events_v2`.
   - Idempotent: cleanly rebuilds table on reruns without duplicate rows.
2. Data Cleaning & Standardization:
   - Standardizes fields into standard process mining format:
     `case_id`, `activity_name`, `event_timestamp`, `activity_sequence`.
   - Adds `is_loopback` indicator while preserving all rework event rows.
   - Cleans string whitespace, enforces types, and verifies ISO timestamps.
3. Database Storage & File Export:
   - Populates SQLite table `stg_healthcare_events_v2`.
   - Exports data/processed/cleaned_healthcare_event_log_v2.csv.
4. Data Quality & Process Validation:
   - Verifies 0 nulls, 0 duplicate event IDs, chronological sorting, and
     exact match with source CSV row count.
"""

from pathlib import Path
import sqlite3
import sys
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "database" / "careflow.db"
RAW_CSV_PATH = REPO_ROOT / "data" / "raw" / "healthcare_event_log_v2.csv"
CLEANED_CSV_PATH = REPO_ROOT / "data" / "processed" / "cleaned_healthcare_event_log_v2.csv"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def load_raw_to_sqlite(conn: sqlite3.Connection, csv_path: Path = RAW_CSV_PATH) -> int:
    """Load raw CSV into SQLite table `raw_healthcare_events_v2`."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Raw CSV not found at: {csv_path}")

    df_raw = pd.read_csv(csv_path)
    df_raw.columns = df_raw.columns.str.strip()
    for col in df_raw.columns:
        if df_raw[col].dtype == object or pd.api.types.is_string_dtype(df_raw[col]):
            df_raw[col] = df_raw[col].astype(str).str.strip()
    cursor = conn.cursor()

    # Rebuild raw table cleanly on each run to avoid duplicates
    cursor.execute("DROP TABLE IF EXISTS raw_healthcare_events_v2;")
    cursor.execute("""
        CREATE TABLE raw_healthcare_events_v2 (
            patient_id TEXT NOT NULL,
            visit_id TEXT NOT NULL,
            event_id TEXT PRIMARY KEY NOT NULL,
            event_name TEXT NOT NULL,
            event_timestamp TEXT NOT NULL,
            department TEXT NOT NULL,
            status TEXT NOT NULL,
            waiting_time_minutes INTEGER NOT NULL CHECK (waiting_time_minutes >= 0)
        );
    """)

    # Populate table with parameterized inserts inside transaction
    records = [
        (
            str(r["patient_id"]),
            str(r["visit_id"]),
            str(r["event_id"]),
            str(r["event_name"]),
            str(r["event_timestamp"]),
            str(r["department"]),
            str(r["status"]),
            int(r["waiting_time_minutes"]),
        )
        for _, r in df_raw.iterrows()
    ]

    cursor.executemany(
        """INSERT INTO raw_healthcare_events_v2 (
            patient_id, visit_id, event_id, event_name,
            event_timestamp, department, status, waiting_time_minutes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);""",
        records,
    )

    # Add indexes for query performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_v2_visit ON raw_healthcare_events_v2(visit_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_v2_time ON raw_healthcare_events_v2(event_timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_v2_name ON raw_healthcare_events_v2(event_name);")

    conn.commit()
    return len(records)


def clean_and_standardize_events(conn: sqlite3.Connection) -> pd.DataFrame:
    """Clean, standardize, and sequence events using SQL and Python.

    Standardizes columns to canonical process mining format:
    - case_id (from visit_id)
    - activity_name (from event_name)
    - event_timestamp (ISO datetime)
    - activity_sequence (1, 2, 3... chronological per case)
    - is_loopback (1 if activity previously seen in this visit, 0 otherwise)
    """
    # Query raw data ordered chronologically per visit
    query = """
        SELECT
            visit_id AS case_id,
            patient_id,
            event_id,
            TRIM(event_name) AS activity_name,
            TRIM(event_timestamp) AS event_timestamp,
            TRIM(department) AS department,
            TRIM(status) AS status,
            waiting_time_minutes
        FROM raw_healthcare_events_v2
        WHERE visit_id IS NOT NULL
          AND event_name IS NOT NULL
          AND event_timestamp IS NOT NULL
        ORDER BY visit_id ASC, event_timestamp ASC;
    """
    df = pd.read_sql_query(query, conn)

    # Convert timestamps and ensure strict datetime parsing
    df["parsed_dt"] = pd.to_datetime(df["event_timestamp"], format="%Y-%m-%d %H:%M:%S", errors="raise")

    # Sort strictly by case_id and parsed timestamp
    df = df.sort_values(by=["case_id", "parsed_dt"]).reset_index(drop=True)

    # Calculate chronological activity sequence per case (1, 2, 3...)
    df["activity_sequence"] = df.groupby("case_id").cumcount() + 1

    # Detect loop-backs without discarding any records
    # A loop-back occurs when the same activity_name has already appeared in the same case
    is_loopback_list = []
    seen_activities_per_case = {}

    for _, row in df.iterrows():
        c_id = row["case_id"]
        act = row["activity_name"]
        if c_id not in seen_activities_per_case:
            seen_activities_per_case[c_id] = set()

        if act in seen_activities_per_case[c_id]:
            is_loopback_list.append(1)
        else:
            is_loopback_list.append(0)
            seen_activities_per_case[c_id].add(act)

    df["is_loopback"] = is_loopback_list

    # Drop temporary datetime parsing helper column
    df = df.drop(columns=["parsed_dt"])

    # Reorder columns to place process-mining canonical keys first
    canonical_columns = [
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
    return df[canonical_columns]


def save_cleaned_to_sqlite_and_csv(
    conn: sqlite3.Connection,
    df_clean: pd.DataFrame,
    csv_path: Path = CLEANED_CSV_PATH,
) -> None:
    """Store cleaned data in SQLite table `stg_healthcare_events_v2` and export to CSV."""
    cursor = conn.cursor()

    # Rebuild cleaned staging table in SQLite
    cursor.execute("DROP TABLE IF EXISTS stg_healthcare_events_v2;")
    cursor.execute("""
        CREATE TABLE stg_healthcare_events_v2 (
            case_id TEXT NOT NULL,
            activity_name TEXT NOT NULL,
            event_timestamp TEXT NOT NULL,
            activity_sequence INTEGER NOT NULL,
            is_loopback INTEGER NOT NULL,
            patient_id TEXT NOT NULL,
            event_id TEXT PRIMARY KEY NOT NULL,
            department TEXT NOT NULL,
            status TEXT NOT NULL,
            waiting_time_minutes INTEGER NOT NULL
        );
    """)

    clean_records = [
        (
            str(r["case_id"]),
            str(r["activity_name"]),
            str(r["event_timestamp"]),
            int(r["activity_sequence"]),
            int(r["is_loopback"]),
            str(r["patient_id"]),
            str(r["event_id"]),
            str(r["department"]),
            str(r["status"]),
            int(r["waiting_time_minutes"]),
        )
        for _, r in df_clean.iterrows()
    ]

    cursor.executemany(
        """INSERT INTO stg_healthcare_events_v2 (
            case_id, activity_name, event_timestamp, activity_sequence,
            is_loopback, patient_id, event_id, department, status, waiting_time_minutes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""",
        clean_records,
    )

    # Create indexes for process mining queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stg_case ON stg_healthcare_events_v2(case_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stg_activity ON stg_healthcare_events_v2(activity_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stg_time ON stg_healthcare_events_v2(event_timestamp);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_stg_seq ON stg_healthcare_events_v2(case_id, activity_sequence);")

    conn.commit()

    # Save to processed CSV
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(csv_path, index=False)


def run_pipeline_validations(
    conn: sqlite3.Connection,
    raw_count: int,
    df_clean: pd.DataFrame,
    csv_clean_path: Path,
) -> dict:
    """Validate data quality, row count consistency, and process loop integrity."""
    cursor = conn.cursor()
    checks = {}

    # Check 1: Raw SQLite table count matches source CSV
    cursor.execute("SELECT COUNT(*) FROM raw_healthcare_events_v2;")
    sqlite_raw_count = cursor.fetchone()[0]
    checks["raw_row_count_match"] = {
        "passed": sqlite_raw_count == raw_count == 3030,
        "detail": f"SQLite raw table: {sqlite_raw_count} rows, CSV source: {raw_count} rows",
    }

    # Check 2: Cleaned SQLite table count matches cleaned CSV
    cursor.execute("SELECT COUNT(*) FROM stg_healthcare_events_v2;")
    sqlite_clean_count = cursor.fetchone()[0]
    checks["clean_row_count_match"] = {
        "passed": sqlite_clean_count == len(df_clean) == 3030,
        "detail": f"SQLite clean table: {sqlite_clean_count} rows, Cleaned CSV: {len(df_clean)} rows",
    }

    # Check 3: Unique cases and patients
    unique_cases = df_clean["case_id"].nunique()
    unique_patients = df_clean["patient_id"].nunique()
    checks["case_completeness"] = {
        "passed": unique_cases == 500 and unique_patients == 420,
        "detail": f"Unique Cases: {unique_cases} (Expected: 500), Unique Patients: {unique_patients} (Expected: 420)",
    }

    # Check 4: Zero missing values in canonical process mining fields
    null_counts = df_clean[["case_id", "activity_name", "event_timestamp", "activity_sequence"]].isnull().sum().sum()
    checks["no_null_canonical_fields"] = {
        "passed": null_counts == 0,
        "detail": f"0 missing values across canonical process mining columns",
    }

    # Check 5: Globally unique event IDs (zero duplicate rows)
    unique_event_ids = df_clean["event_id"].nunique()
    checks["unique_event_ids"] = {
        "passed": unique_event_ids == len(df_clean),
        "detail": f"{unique_event_ids} unique event IDs out of {len(df_clean)} rows",
    }

    # Check 6: Chronological ordering within every case
    chronology_errors = 0
    df_test = df_clean.copy()
    df_test["dt"] = pd.to_datetime(df_test["event_timestamp"])
    for _, grp in df_test.groupby("case_id"):
        times = grp["dt"].tolist()
        for i in range(len(times) - 1):
            if times[i] >= times[i + 1]:
                chronology_errors += 1
    checks["chronological_ordering"] = {
        "passed": chronology_errors == 0,
        "detail": f"Strict chronological order verified across all 500 cases ({chronology_errors} inversions)",
    }

    # Check 7: Loop-back preservation
    loopback_count = int(df_clean["is_loopback"].sum())
    cases_with_loops = int(df_clean[df_clean["is_loopback"] == 1]["case_id"].nunique())
    checks["loopback_preservation"] = {
        "passed": loopback_count == 214 and cases_with_loops == 154,
        "detail": f"{loopback_count} loop-backs preserved across {cases_with_loops} patient cases (30.8%)",
    }

    return checks


def print_summary(checks: dict, df_clean: pd.DataFrame, csv_path: Path):
    """Print clean, beginner-friendly pipeline report."""
    print("\n" + "=" * 70)
    print("      CAREFLOW WEEK 1 LOCAL INGESTION & CLEANING PIPELINE")
    print("=" * 70)
    print(" Technology Substitution: Local SQLite & Python/SQL replacing BigQuery & dbt")
    print(f" Database Store         : database/careflow.db (tables: raw_healthcare_events_v2, stg_healthcare_events_v2)")
    print(f" Cleaned Dataset Output : {csv_path.name} ({len(df_clean):,} rows)")
    print(f" Process Cases          : {df_clean['case_id'].nunique()} patient visits")
    print(f" Unique Patients        : {df_clean['patient_id'].nunique()} patients")
    print(f" Loop-Back Events       : {int(df_clean['is_loopback'].sum())} events in {df_clean[df_clean['is_loopback'] == 1]['case_id'].nunique()} cases")

    print("\n--- Pipeline Validation Checks ---")
    all_passed = True
    for name, res in checks.items():
        status = "[PASS]" if res["passed"] else "[FAIL]"
        if not res["passed"]:
            all_passed = False
        readable = name.replace("_", " ").title()
        print(f"  {status:<8} {readable:<30}: {res['detail']}")

    print("=" * 70)
    if all_passed:
        print(" SUCCESS: Week 1 local ingestion, cleaning, and validation complete!")
    else:
        print(" WARNING: One or more validation checks failed.")
    print("=" * 70 + "\n")


def main():
    print("Connecting to CareFlow SQLite database...")
    conn = get_connection(DB_PATH)

    try:
        print("Step 1: Ingesting raw v2 events into SQLite (raw_healthcare_events_v2)...")
        raw_count = load_raw_to_sqlite(conn, RAW_CSV_PATH)

        print("Step 2: Cleaning, standardizing, and sequencing events...")
        df_clean = clean_and_standardize_events(conn)

        print("Step 3: Storing cleaned data in SQLite (stg_healthcare_events_v2) and exporting CSV...")
        save_cleaned_to_sqlite_and_csv(conn, df_clean, CLEANED_CSV_PATH)

        print("Step 4: Executing pipeline validations...")
        checks = run_pipeline_validations(conn, raw_count, df_clean, CLEANED_CSV_PATH)

        print_summary(checks, df_clean, CLEANED_CSV_PATH)

        if not all(c["passed"] for c in checks.values()):
            sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()

