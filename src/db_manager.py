"""CareFlow: SQLite Database Manager & Ingestion Pipeline.

This module initializes the local CareFlow SQLite database (database/careflow.db),
applies the relational schema (database/schema.sql), and ingests the validated
synthetic healthcare event log (data/raw/healthcare_event_log.csv).

Features:
---------
1. Relational Integrity:
   - Enforces foreign keys (PRAGMA foreign_keys = ON).
   - Inserts records in topological order: patients -> visits -> events.
2. Idempotent & Re-runnable:
   - Uses a safe drop-and-rebuild strategy so rerunning will not duplicate data.
3. Atomic Transactions:
   - Uses parameterized SQL and commits all inserts in a single transaction.
4. Comprehensive Verification:
   - Validates patient, visit, and event row counts.
   - Executes PRAGMA foreign_key_check to verify relational integrity.
   - Asserts zero unexpected NULLs in required columns.
"""

from pathlib import Path
import sqlite3
import sys
import pandas as pd

# Paths relative to repository root
REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "raw" / "healthcare_event_log.csv"
SCHEMA_PATH = REPO_ROOT / "database" / "schema.sql"
DB_PATH = REPO_ROOT / "database" / "careflow.db"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Create and configure a SQLite connection with foreign key enforcement."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def apply_schema(conn: sqlite3.Connection, schema_path: Path = SCHEMA_PATH) -> None:
    """Execute the SQL schema script to rebuild tables and indexes cleanly."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)


def ingest_data(conn: sqlite3.Connection, csv_path: Path = CSV_PATH) -> dict:
    """Read CSV, extract relational entities, and insert them with parameterized queries.

    Returns:
        dict containing ingestion statistics.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Event log CSV not found at: {csv_path}")

    # 1. Load CSV dataset
    df = pd.read_csv(csv_path)

    # 2. Extract Patients (unique patient IDs)
    unique_patients = df["patient_id"].drop_duplicates().tolist()
    patients_data = [(pid,) for pid in unique_patients]

    # 3. Extract Visits (aggregated per visit_id)
    visits_records = []
    for visit_id, group in df.groupby("visit_id", sort=False):
        patient_id = group["patient_id"].iloc[0]
        visit_start_time = group["event_timestamp"].min()
        visit_end_time = group["event_timestamp"].max()
        total_events = len(group)

        # Extract discharge disposition from the Discharge stage if present
        discharge_rows = group[group["event_name"] == "Discharge"]
        if not discharge_rows.empty:
            discharge_disposition = discharge_rows["status"].iloc[0]
        else:
            discharge_disposition = group["status"].iloc[-1]

        visits_records.append((
            visit_id,
            patient_id,
            visit_start_time,
            visit_end_time,
            total_events,
            discharge_disposition,
        ))

    # 4. Extract Events (all rows preserving every original CSV column)
    events_records = []
    for _, row in df.iterrows():
        events_records.append((
            str(row["event_id"]),
            str(row["visit_id"]),
            str(row["patient_id"]),
            str(row["event_name"]),
            str(row["event_timestamp"]),
            str(row["department"]),
            str(row["status"]),
            int(row["waiting_time_minutes"]),
        ))

    # 5. Insert records inside a single transaction
    cursor = conn.cursor()
    try:
        # Parents first: patients
        cursor.executemany(
            "INSERT INTO patients (patient_id) VALUES (?);",
            patients_data,
        )

        # Children: visits
        cursor.executemany(
            """INSERT INTO visits (
                visit_id, patient_id, visit_start_time, visit_end_time,
                total_events, discharge_disposition
            ) VALUES (?, ?, ?, ?, ?, ?);""",
            visits_records,
        )

        # Granular events: events
        cursor.executemany(
            """INSERT INTO events (
                event_id, visit_id, patient_id, event_name,
                event_timestamp, department, status, waiting_time_minutes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);""",
            events_records,
        )

        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise RuntimeError(f"Database insertion failed and was rolled back: {exc}") from exc

    return {
        "csv_rows": len(df),
        "patients_inserted": len(patients_data),
        "visits_inserted": len(visits_records),
        "events_inserted": len(events_records),
    }


def verify_database(conn: sqlite3.Connection, expected_events: int) -> dict:
    """Run verification checks on the populated SQLite database.

    Checks:
      1. Row counts: 420 patients, 500 visits, 2823 events.
      2. Event count matches CSV row count.
      3. Zero foreign key violations (PRAGMA foreign_key_check).
      4. Zero unexpected NULL values in required fields.
    """
    cursor = conn.cursor()
    results = {}

    # 1. Row counts
    cursor.execute("SELECT COUNT(*) FROM patients;")
    patient_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM visits;")
    visit_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM events;")
    event_count = cursor.fetchone()[0]

    results["patient_count"] = {
        "actual": patient_count,
        "expected": 420,
        "passed": patient_count == 420,
    }
    results["visit_count"] = {
        "actual": visit_count,
        "expected": 500,
        "passed": visit_count == 500,
    }
    results["event_count"] = {
        "actual": event_count,
        "expected": expected_events,
        "passed": event_count == expected_events,
    }

    # 2. Foreign Key Integrity Check
    cursor.execute("PRAGMA foreign_key_check;")
    fk_violations = cursor.fetchall()
    results["foreign_keys"] = {
        "violations": len(fk_violations),
        "passed": len(fk_violations) == 0,
    }

    # 3. NULL Value Checks
    cursor.execute("""
        SELECT COUNT(*) FROM events
        WHERE event_id IS NULL OR visit_id IS NULL OR patient_id IS NULL
           OR event_name IS NULL OR event_timestamp IS NULL
           OR department IS NULL OR status IS NULL OR waiting_time_minutes IS NULL;
    """)
    null_events = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM visits
        WHERE visit_id IS NULL OR patient_id IS NULL
           OR visit_start_time IS NULL OR visit_end_time IS NULL
           OR total_events IS NULL OR discharge_disposition IS NULL;
    """)
    null_visits = cursor.fetchone()[0]

    results["no_nulls"] = {
        "null_events": null_events,
        "null_visits": null_visits,
        "passed": (null_events == 0) and (null_visits == 0),
    }

    return results


def print_summary(stats: dict, verifications: dict, db_path: Path):
    """Print a beginner-friendly summary of database ingestion and checks."""
    print("\n" + "=" * 65)
    print("         CareFlow - SQLite Database Ingestion Summary")
    print("=" * 65)
    print(f" Database File       : {db_path}")
    print(f" Source CSV File     : {CSV_PATH.name} ({stats['csv_rows']:,} rows)")

    print("\n--- Ingested Relational Entities ---")
    p_stat = verifications["patient_count"]
    v_stat = verifications["visit_count"]
    e_stat = verifications["event_count"]
    print(f"  Patients Table     : {p_stat['actual']:>5} records (Expected: {p_stat['expected']}) "
          f"{'[PASS]' if p_stat['passed'] else '[FAIL]'}")
    print(f"  Visits Table       : {v_stat['actual']:>5} records (Expected: {v_stat['expected']}) "
          f"{'[PASS]' if v_stat['passed'] else '[FAIL]'}")
    print(f"  Events Table       : {e_stat['actual']:>5} records (Expected: {e_stat['expected']}) "
          f"{'[PASS]' if e_stat['passed'] else '[FAIL]'}")

    print("\n--- Integrity & Validation Checks ---")
    fk_res = verifications["foreign_keys"]
    null_res = verifications["no_nulls"]
    print(f"  {'[PASS]' if fk_res['passed'] else '[FAIL]'} Foreign Key Integrity : {fk_res['violations']} violations detected")
    print(f"  {'[PASS]' if null_res['passed'] else '[FAIL]'} Non-Null Constraints  : 0 unexpected NULL values")

    all_passed = all(check["passed"] for check in verifications.values())
    print("=" * 65)
    if all_passed:
        print(" SUCCESS: Database created, ingested, and verified successfully.")
    else:
        print(" WARNING: One or more validation checks failed.")
    print("=" * 65 + "\n")


def main():
    """Main execution function for schema setup and data ingestion."""
    print("Connecting to CareFlow SQLite database...")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_connection(DB_PATH)

    try:
        print("Applying schema from database/schema.sql...")
        apply_schema(conn, SCHEMA_PATH)

        print(f"Ingesting events from {CSV_PATH.name}...")
        stats = ingest_data(conn, CSV_PATH)

        print("Running database verification checks...")
        verifications = verify_database(conn, stats["csv_rows"])

        print_summary(stats, verifications, DB_PATH)

        if not all(check["passed"] for check in verifications.values()):
            sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

