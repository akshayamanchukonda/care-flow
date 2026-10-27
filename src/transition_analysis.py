"""CareFlow: Week 3 Pathway Transition Time Analysis.

This module calculates the elapsed transition and handover times between
consecutive clinical process stages (e.g., Triage -> Consultation,
Consultation -> Diagnostics, etc.) using SQLite window functions and Python.

It exports:
  1. data/processed/transition_time_analysis.csv (Summary statistics for all 9 pathways)
  2. data/processed/baseline_transition_times.csv (Summary statistics for 6 baseline pathways)
  3. data/processed/visit_transitions_detail.csv (Granular event-pair transition records)
"""

from pathlib import Path
import sqlite3
import sys

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "database" / "careflow.db"
PROCESSED_DIR = REPO_ROOT / "data" / "processed"
OUTPUT_SUMMARY_CSV = PROCESSED_DIR / "transition_time_analysis.csv"
OUTPUT_BASELINE_CSV = PROCESSED_DIR / "baseline_transition_times.csv"
OUTPUT_DETAIL_CSV = PROCESSED_DIR / "visit_transitions_detail.csv"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Connect to SQLite database."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at: {db_path}. Run src/db_manager.py first.")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def calculate_process_mining_transitions(conn: sqlite3.Connection) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate transition times for all 9 process mining pathways (with loop-backs)."""
    # Granular transition records using SQLite window function
    detail_query = """
    WITH ConsecutiveEvents AS (
        SELECT
            case_id,
            patient_id,
            activity_name AS from_activity,
            event_timestamp AS from_timestamp,
            is_loopback AS from_is_loopback,
            LEAD(activity_name) OVER (
                PARTITION BY case_id
                ORDER BY event_timestamp, activity_sequence, event_id
            ) AS to_activity,
            LEAD(event_timestamp) OVER (
                PARTITION BY case_id
                ORDER BY event_timestamp, activity_sequence, event_id
            ) AS to_timestamp,
            LEAD(is_loopback) OVER (
                PARTITION BY case_id
                ORDER BY event_timestamp, activity_sequence, event_id
            ) AS to_is_loopback
        FROM stg_healthcare_events_v2
    )
    SELECT
        case_id,
        patient_id,
        from_activity,
        to_activity,
        from_timestamp,
        to_timestamp,
        ROUND((strftime('%s', to_timestamp) - strftime('%s', from_timestamp)) / 60.0, 2) AS transition_time_minutes,
        CASE
            WHEN (from_activity = 'Triage' AND to_activity = 'Registration')
              OR (from_activity = 'Diagnostics' AND to_activity = 'Consultation')
              OR (from_activity = 'Treatment' AND to_activity = 'Diagnostics') THEN 1
            ELSE 0
        END AS is_rework_loop
    FROM ConsecutiveEvents
    WHERE to_activity IS NOT NULL
      AND to_timestamp IS NOT NULL
    ORDER BY case_id, from_timestamp;
    """
    df_detail = pd.read_sql_query(detail_query, conn)

    # Statistical aggregations across each distinct pathway
    total_transitions = len(df_detail)
    summary_rows = []

    for (src, tgt), grp in df_detail.groupby(["from_activity", "to_activity"]):
        durations = grp["transition_time_minutes"].values
        is_loop = int(grp["is_rework_loop"].iloc[0])
        q1 = np.percentile(durations, 25)
        q3 = np.percentile(durations, 75)

        summary_rows.append({
            "from_activity": src,
            "to_activity": tgt,
            "transition_count": len(durations),
            "is_loopback": is_loop,
            "pct_of_total_transitions": round((len(durations) / total_transitions) * 100.0, 2),
            "avg_transition_time_minutes": round(float(np.mean(durations)), 2),
            "median_transition_time_minutes": round(float(np.median(durations)), 2),
            "std_dev_minutes": round(float(np.std(durations, ddof=1)), 2) if len(durations) > 1 else 0.0,
            "min_transition_time_minutes": round(float(np.min(durations)), 2),
            "max_transition_time_minutes": round(float(np.max(durations)), 2),
            "p25_minutes": round(float(q1), 2),
            "p75_minutes": round(float(q3), 2),
            "iqr_minutes": round(float(q3 - q1), 2),
        })

    df_summary = pd.DataFrame(summary_rows)
    df_summary = df_summary.sort_values(
        by=["transition_count", "avg_transition_time_minutes"],
        ascending=[False, False]
    ).reset_index(drop=True)
    return df_detail, df_summary


def calculate_baseline_transitions(conn: sqlite3.Connection) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate transition times for the 6 baseline relational pathways (events table)."""
    base_query = """
    WITH ConsecutiveEvents AS (
        SELECT
            visit_id,
            patient_id,
            event_name AS from_activity,
            event_timestamp AS from_timestamp,
            LEAD(event_name) OVER (
                PARTITION BY visit_id
                ORDER BY event_timestamp, event_id
            ) AS to_activity,
            LEAD(event_timestamp) OVER (
                PARTITION BY visit_id
                ORDER BY event_timestamp, event_id
            ) AS to_timestamp
        FROM events
    )
    SELECT
        visit_id,
        patient_id,
        from_activity,
        to_activity,
        from_timestamp,
        to_timestamp,
        ROUND((strftime('%s', to_timestamp) - strftime('%s', from_timestamp)) / 60.0, 2) AS transition_time_minutes
    FROM ConsecutiveEvents
    WHERE to_activity IS NOT NULL
      AND to_timestamp IS NOT NULL
    ORDER BY visit_id, from_timestamp;
    """
    df_base_detail = pd.read_sql_query(base_query, conn)
    total_transitions = len(df_base_detail)
    summary_rows = []

    for (src, tgt), grp in df_base_detail.groupby(["from_activity", "to_activity"]):
        durations = grp["transition_time_minutes"].values
        q1 = np.percentile(durations, 25)
        q3 = np.percentile(durations, 75)

        summary_rows.append({
            "from_activity": src,
            "to_activity": tgt,
            "transition_count": len(durations),
            "pct_of_total_transitions": round((len(durations) / total_transitions) * 100.0, 2),
            "avg_transition_time_minutes": round(float(np.mean(durations)), 2),
            "median_transition_time_minutes": round(float(np.median(durations)), 2),
            "std_dev_minutes": round(float(np.std(durations, ddof=1)), 2) if len(durations) > 1 else 0.0,
            "min_transition_time_minutes": round(float(np.min(durations)), 2),
            "max_transition_time_minutes": round(float(np.max(durations)), 2),
            "p25_minutes": round(float(q1), 2),
            "p75_minutes": round(float(q3), 2),
            "iqr_minutes": round(float(q3 - q1), 2),
        })

    df_base_summary = pd.DataFrame(summary_rows)
    df_base_summary = df_base_summary.sort_values(
        by=["transition_count", "avg_transition_time_minutes"],
        ascending=[False, False]
    ).reset_index(drop=True)
    return df_base_detail, df_base_summary


def validate_results(
    df_detail: pd.DataFrame,
    df_summary: pd.DataFrame,
    df_base_detail: pd.DataFrame,
    df_base_summary: pd.DataFrame,
) -> dict:
    """Validate observation counts, non-negativity, and consistency across both logs."""
    total_obs = len(df_detail)
    unique_cases = df_detail["case_id"].nunique()
    negative_transitions = (df_detail["transition_time_minutes"] < 0).sum()
    null_times = df_detail["transition_time_minutes"].isnull().sum()
    pathway_count = len(df_summary)

    # Process mining assertions (v2)
    if total_obs != 2530:
        raise AssertionError(f"Expected 2,530 total transitions, got {total_obs}")
    if unique_cases != 500:
        raise AssertionError(f"Expected 500 cases, got {unique_cases}")
    if negative_transitions != 0:
        raise AssertionError(f"Found {negative_transitions} negative transition durations!")
    if null_times != 0:
        raise AssertionError(f"Found {null_times} null transition durations!")
    if pathway_count != 9:
        raise AssertionError(f"Expected 9 distinct pathways, got {pathway_count}")

    # Baseline assertions (relational)
    base_obs = len(df_base_detail)
    base_cases = df_base_detail["visit_id"].nunique()
    base_negative = (df_base_detail["transition_time_minutes"] < 0).sum()
    base_nulls = df_base_detail["transition_time_minutes"].isnull().sum()
    base_pathways = len(df_base_summary)

    if base_obs != 2323:
        raise AssertionError(f"Expected 2,323 baseline transitions, got {base_obs}")
    if base_cases != 500:
        raise AssertionError(f"Expected 500 baseline visits, got {base_cases}")
    if base_negative != 0:
        raise AssertionError(f"Found {base_negative} negative baseline durations!")
    if base_nulls != 0:
        raise AssertionError(f"Found {base_nulls} null baseline durations!")
    if base_pathways != 6:
        raise AssertionError(f"Expected 6 baseline pathways, got {base_pathways}")

    # Specific pathway reconciliation assertions
    pathway_map = df_summary.set_index(["from_activity", "to_activity"]).to_dict(orient="index")

    diag_consult = pathway_map.get(("Diagnostics", "Consultation"))
    if not diag_consult or diag_consult["transition_count"] != 116 or diag_consult["avg_transition_time_minutes"] != 73.20:
        raise AssertionError(f"Diagnostics -> Consultation mismatch: {diag_consult}")

    treat_diag = pathway_map.get(("Treatment", "Diagnostics"))
    if not treat_diag or treat_diag["transition_count"] != 29 or treat_diag["avg_transition_time_minutes"] != 86.34:
        raise AssertionError(f"Treatment -> Diagnostics mismatch: {treat_diag}")

    triage_reg = pathway_map.get(("Triage", "Registration"))
    if not triage_reg or triage_reg["transition_count"] != 27 or triage_reg["avg_transition_time_minutes"] != 17.22:
        raise AssertionError(f"Triage -> Registration mismatch: {triage_reg}")

    return {
        "proc_total_transitions": total_obs,
        "proc_unique_cases": unique_cases,
        "proc_negative_durations": int(negative_transitions),
        "proc_null_durations": int(null_times),
        "proc_pathway_count": pathway_count,
        "base_total_transitions": base_obs,
        "base_unique_cases": base_cases,
        "base_negative_durations": int(base_negative),
        "base_null_durations": int(base_nulls),
        "base_pathway_count": base_pathways,
    }


def main():
    print("\n" + "=" * 75)
    print("      CAREFLOW WEEK 3: PROCESS TRANSITION TIME ANALYSIS")
    print("=" * 75)

    conn = get_connection()
    try:
        # 1. Process Mining Pathways
        print("\n[1/3] Calculating transition times for process mining pathways (9 pathways)...")
        df_detail, df_summary = calculate_process_mining_transitions(conn)

        # 2. Baseline Pathways
        print("[2/3] Calculating baseline transition times (6 pathways)...")
        df_base_detail, df_base_summary = calculate_baseline_transitions(conn)

        # 3. Validation
        print("[3/3] Validating transition time calculations...")
        val_stats = validate_results(df_detail, df_summary, df_base_detail, df_base_summary)
        print(f"      Verified v2: {val_stats['proc_total_transitions']:,} transitions across {val_stats['proc_unique_cases']:,} visits.")
        print(f"      Verified Baseline: {val_stats['base_total_transitions']:,} transitions across {val_stats['base_unique_cases']:,} visits.")
        print(f"      Integrity: 0 negative durations, 0 nulls across both datasets.")

        # Save CSV files
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        df_summary.to_csv(OUTPUT_SUMMARY_CSV, index=False)
        df_base_summary.to_csv(OUTPUT_BASELINE_CSV, index=False)
        df_detail.to_csv(OUTPUT_DETAIL_CSV, index=False)

        print("\n--- Discovered Process Mining Pathway Transition Times ---")
        cols_to_print = ["from_activity", "to_activity", "transition_count", "is_loopback",
                         "avg_transition_time_minutes", "median_transition_time_minutes", "std_dev_minutes"]
        print(df_summary[cols_to_print].to_string(index=False))

        print("\n--- Baseline Transition Times ---")
        base_cols = ["from_activity", "to_activity", "transition_count",
                     "avg_transition_time_minutes", "median_transition_time_minutes", "std_dev_minutes"]
        print(df_base_summary[base_cols].to_string(index=False))

        print("\n" + "=" * 75)
        print("               WEEK 3 ANALYSIS COMPLETED SUCCESSFULLY")
        print("=" * 75)
        print(f"Summary Dataset (Process Mining) : {OUTPUT_SUMMARY_CSV}")
        print(f"Baseline Summary Dataset         : {OUTPUT_BASELINE_CSV}")
        print(f"Granular Transition Detail       : {OUTPUT_DETAIL_CSV}")
        print("=" * 75 + "\n")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
