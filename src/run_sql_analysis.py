"""CareFlow: SQL Operational Analysis Runner & Verifier.

Executes all analytical queries in sql/queries/ and applies reusable views
in sql/views/ against the SQLite database (database/careflow.db).

Verifies:
  1. Successful execution of all SQL query files.
  2. Total visits == 500.
  3. Total events == 2,823.
  4. Total patients == 420.
  5. Diagnostics count matches expected (323 visits).
  6. Non-negative visit durations across all visits.
  7. Correct handling of visits that skip Diagnostics (177 visits).
"""

from pathlib import Path
import sqlite3
import sys
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "database" / "careflow.db"
QUERIES_DIR = REPO_ROOT / "sql" / "queries"
VIEWS_DIR = REPO_ROOT / "sql" / "views"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at: {db_path}. Run src/db_manager.py first.")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def apply_views(conn: sqlite3.Connection):
    """Apply all reusable SQL views in sql/views/."""
    view_files = sorted(VIEWS_DIR.glob("*.sql"))
    print(f"\n--- Applying Reusable SQL Views ({len(view_files)} files) ---")
    for view_file in view_files:
        with open(view_file, "r", encoding="utf-8") as f:
            sql_text = f.read()
        conn.executescript(sql_text)
        print(f"  [OK] Applied view: {view_file.name}")


def run_queries(conn: sqlite3.Connection) -> dict:
    """Execute each SQL query file and return results as DataFrames."""
    query_files = sorted(QUERIES_DIR.glob("*.sql"))
    results = {}
    print(f"\n--- Executing Analytical Queries ({len(query_files)} files) ---")
    for q_file in query_files:
        with open(q_file, "r", encoding="utf-8") as f:
            sql_text = f.read()
        try:
            df = pd.read_sql_query(sql_text, conn)
            results[q_file.stem] = df
            print(f"  [SUCCESS] {q_file.name} ({len(df)} rows returned)")
        except Exception as exc:
            print(f"  [FAILED] {q_file.name}: {exc}")
            raise exc
    return results


def print_actual_results(results: dict):
    """Print formatted actual results for each analytical query."""
    print("\n" + "=" * 70)
    print("                 CAREFLOW ACTUAL QUERY RESULTS")
    print("=" * 70)

    # 1. Overall Summary
    print("\n[Query 1: Overall Summary]")
    print(results["01_overall_summary"].to_string(index=False))

    # 2. Stage Waiting Times (Avg & Median)
    print("\n[Query 2: Waiting Times by Stage (Avg & Median)]")
    print(results["02_waiting_time_by_stage"].to_string(index=False))

    # 3. Department Waiting Times
    print("\n[Query 3: Department Waiting Times]")
    print(results["03_department_waiting_times"].to_string(index=False))

    # 4. Bottleneck Ranking
    print("\n[Query 4: Bottleneck Ranking by Average Wait Time]")
    print(results["04_bottleneck_ranking"].to_string(index=False))

    # 5. Arrivals by Hour
    print("\n[Query 5: Arrivals by Hour (Sample Peak Hours)]")
    print(results["05_arrivals_by_hour"].head(10).to_string(index=False))

    # 6. Visit Outcomes
    print("\n[Query 6: Visit Outcomes & Average Journey Duration]")
    print(results["06_visit_outcomes"].to_string(index=False))

    # 7. Visit Durations (Preview)
    print("\n[Query 7: Calculated Journey Durations (Top 5 Longest Visits)]")
    print(results["07_visit_durations"].head(5).to_string(index=False))

    # 8. Diagnostics Usage Rate
    print("\n[Query 8: Diagnostics Usage & Skip Rate]")
    print(results["08_diagnostics_rate"].to_string(index=False))

    # 9. Event Counts and Average Wait
    print("\n[Query 9: Event Counts and Average Waiting Times by Stage]")
    print(results["09_event_counts_and_avg_wait"].to_string(index=False))

    # 10. Visit Level Summary (Preview)
    print("\n[Query 10: Visit-Level Summary for Power BI (Preview First 5 Visits)]")
    print(results["10_visit_level_summary"].head(5).to_string(index=False))


def verify_analysis(results: dict) -> bool:
    """Verify business rules, row counts, and non-negative constraints."""
    print("\n" + "=" * 70)
    print("                 STAGE 4 VERIFICATION CHECKS")
    print("=" * 70)

    checks = []

    # Check 1: Patients == 420
    summary_df = results["01_overall_summary"]
    total_patients = int(summary_df["total_patients"].iloc[0])
    checks.append((
        "Total Patients Count",
        total_patients == 420,
        f"{total_patients} patients (Expected: 420)",
    ))

    # Check 2: Visits == 500
    total_visits = int(summary_df["total_visits"].iloc[0])
    checks.append((
        "Total Visits Count",
        total_visits == 500,
        f"{total_visits} visits (Expected: 500)",
    ))

    # Check 3: Events == 2,823
    total_events = int(summary_df["total_events"].iloc[0])
    checks.append((
        "Total Events Count",
        total_events == 2823,
        f"{total_events} events (Expected: 2823)",
    ))

    # Check 4: Diagnostics visits == 323, Skips == 177
    diag_df = results["08_diagnostics_rate"]
    diag_count = int(diag_df["visits_with_diagnostics"].iloc[0])
    skip_count = int(diag_df["visits_without_diagnostics"].iloc[0])
    diag_match = (diag_count == 323) and (skip_count == 177)
    checks.append((
        "Diagnostics Usage Consistency",
        diag_match,
        f"{diag_count} with Diagnostics, {skip_count} skipped (Sum: {diag_count + skip_count})",
    ))

    # Check 5: Visit durations are non-negative
    durations_df = results["07_visit_durations"]
    min_duration = durations_df["duration_minutes"].min()
    negative_durations = (durations_df["duration_minutes"] < 0).sum()
    checks.append((
        "Non-Negative Visit Durations",
        negative_durations == 0,
        f"Min observed duration: {min_duration} mins, 0 negative durations",
    ))

    # Check 6: Visit-level summary matches 500 visits
    v_summary_df = results["10_visit_level_summary"]
    checks.append((
        "Visit-Level Summary Completeness",
        len(v_summary_df) == 500,
        f"{len(v_summary_df)} rows in BI summary (Expected: 500)",
    ))

    all_passed = True
    for name, passed, detail in checks:
        status_label = "[PASS]" if passed else "[FAIL]"
        if not passed:
            all_passed = False
        print(f"  {status_label} {name:<35}: {detail}")

    print("=" * 70)
    if all_passed:
        print(" SUCCESS: All Stage 4 SQL analysis and verification checks passed.")
    else:
        print(" WARNING: One or more checks failed.")
    print("=" * 70 + "\n")

    return all_passed


def main():
    conn = get_connection(DB_PATH)
    try:
        apply_views(conn)
        results = run_queries(conn)
        print_actual_results(results)
        passed = verify_analysis(results)
        if not passed:
            sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
