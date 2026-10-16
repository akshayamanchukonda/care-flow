"""CareFlow: Python Statistical and Process Analysis Pipeline.

This module performs statistical and operational process analysis on the
CareFlow SQLite database (database/careflow.db) using Pandas and NumPy.

It generates 6 clean, standardized analytical datasets in data/processed/
ready for interactive dashboarding in Power BI Desktop.

Analyses Performed:
-------------------
1. Data Quality Assurance:
   - Verifies row counts, missing values, duplicates, and non-negative values.
   - Validates timestamp parsing and chronological sequence.
2. Descriptive Statistics:
   - Computes count, mean, median, min, max, std dev, and percentiles (25th, 75th, 90th).
   - Broken down by care stage, hospital department, and discharge disposition.
3. Stage & Bottleneck Analysis:
   - Ranks stages by average queue delay and calculates % share of total hospital waiting.
4. Department Performance:
   - Evaluates patient volume, queue distributions, and wait loads per department.
5. Visit-Level Analysis:
   - Calculates observed journey durations and wait metrics per visit (500 rows).
6. Long-Wait & Statistical Outlier Analysis:
   - Identifies delays > 30 min, > 60 min, and statistical outliers using the 1.5x IQR rule.
7. Diagnostics Utilization:
   - Compares patient throughput and wait times between visits with vs. without diagnostics.
"""

from pathlib import Path
import sqlite3
import sys
import numpy as np
import pandas as pd

# Paths relative to repository root
REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "database" / "careflow.db"
OUTPUT_DIR = REPO_ROOT / "data" / "processed"


def get_database_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Connect to SQLite database with foreign keys enabled."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at: {db_path}. Run src/db_manager.py first.")
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def load_raw_data(conn: sqlite3.Connection) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load relational tables into pandas DataFrames."""
    df_patients = pd.read_sql_query("SELECT * FROM patients;", conn)
    df_visits = pd.read_sql_query("SELECT * FROM visits;", conn)
    df_events = pd.read_sql_query("SELECT * FROM events;", conn)

    # Convert timestamps to datetime
    df_events["event_timestamp"] = pd.to_datetime(df_events["event_timestamp"], format="%Y-%m-%d %H:%M:%S")
    df_visits["visit_start_time"] = pd.to_datetime(df_visits["visit_start_time"], format="%Y-%m-%d %H:%M:%S")
    df_visits["visit_end_time"] = pd.to_datetime(df_visits["visit_end_time"], format="%Y-%m-%d %H:%M:%S")

    return df_patients, df_visits, df_events


# =====================================================================
# 1. DATA QUALITY ASSURANCE
# =====================================================================
def run_data_quality_checks(
    df_patients: pd.DataFrame,
    df_visits: pd.DataFrame,
    df_events: pd.DataFrame,
) -> dict:
    """Validate data integrity, completeness, and value bounds."""
    results = {}

    # Check 1: Row counts
    p_cnt, v_cnt, e_cnt = len(df_patients), len(df_visits), len(df_events)
    counts_valid = (p_cnt == 420) and (v_cnt == 500) and (e_cnt == 2823)
    results["row_counts"] = {
        "passed": counts_valid,
        "detail": f"Patients: {p_cnt} (420), Visits: {v_cnt} (500), Events: {e_cnt} (2823)",
    }

    # Check 2: Missing values
    missing_events = int(df_events.isnull().sum().sum())
    missing_visits = int(df_visits.isnull().sum().sum())
    results["missing_values"] = {
        "passed": (missing_events == 0) and (missing_visits == 0),
        "detail": f"0 missing values (Events nulls: {missing_events}, Visits nulls: {missing_visits})",
    }

    # Check 3: Unique event IDs
    dup_events = int(df_events["event_id"].duplicated().sum())
    results["duplicate_events"] = {
        "passed": dup_events == 0,
        "detail": f"0 duplicate event IDs ({len(df_events)} unique IDs)",
    }

    # Check 4: Non-negative waiting times
    neg_waits = int((df_events["waiting_time_minutes"] < 0).sum())
    min_wait = int(df_events["waiting_time_minutes"].min())
    max_wait = int(df_events["waiting_time_minutes"].max())
    results["waiting_times_bounds"] = {
        "passed": neg_waits == 0,
        "detail": f"0 negative waiting times (Range: {min_wait} to {max_wait} mins)",
    }

    # Check 5: Timestamp parsing
    nat_events = int(df_events["event_timestamp"].isna().sum())
    results["timestamp_parsing"] = {
        "passed": nat_events == 0,
        "detail": f"All {len(df_events)} timestamps parsed as valid datetimes",
    }

    # Check 6: Visit start and end chronology
    duration_secs = (df_visits["visit_end_time"] - df_visits["visit_start_time"]).dt.total_seconds()
    neg_durations = int((duration_secs < 0).sum())
    min_duration_mins = round(float(duration_secs.min() / 60.0), 2)
    results["visit_chronology"] = {
        "passed": neg_durations == 0,
        "detail": f"0 negative durations across all visits (Min: {min_duration_mins} mins)",
    }

    return results


# =====================================================================
# 2. STAGE WAITING-TIME ANALYSIS
# =====================================================================
def analyze_stage_waiting_times(df_events: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive statistics and bottleneck rankings by stage."""
    total_hospital_wait = df_events["waiting_time_minutes"].sum()

    records = []
    for stage, group in df_events.groupby("event_name"):
        waits = group["waiting_time_minutes"]
        total_wait = int(waits.sum())
        mean_wait = round(float(waits.mean()), 2)
        med_wait = round(float(waits.median()), 2)
        q25 = round(float(waits.quantile(0.25)), 2)
        q75 = round(float(waits.quantile(0.75)), 2)
        p90 = round(float(waits.quantile(0.90)), 2)
        std_wait = round(float(waits.std()), 2)
        min_wait = int(waits.min())
        max_wait = int(waits.max())
        count = len(group)
        pct_wait = round((total_wait / total_hospital_wait) * 100.0, 2)

        records.append({
            "stage": stage,
            "event_count": count,
            "min_wait_minutes": min_wait,
            "q25_wait_minutes": q25,
            "median_wait_minutes": med_wait,
            "mean_wait_minutes": mean_wait,
            "q75_wait_minutes": q75,
            "p90_wait_minutes": p90,
            "max_wait_minutes": max_wait,
            "std_dev_minutes": std_wait,
            "total_waiting_minutes": total_wait,
            "pct_of_total_waiting_time": pct_wait,
        })

    df_stage = pd.DataFrame(records)
    # Rank by mean waiting time descending
    df_stage = df_stage.sort_values(by="mean_wait_minutes", ascending=False).reset_index(drop=True)
    df_stage["bottleneck_rank"] = df_stage.index + 1
    return df_stage


# =====================================================================
# 3. DEPARTMENT WAITING-TIME ANALYSIS
# =====================================================================
def analyze_department_waiting_times(df_events: pd.DataFrame) -> pd.DataFrame:
    """Compute descriptive statistics and operational loads by department."""
    total_hospital_wait = df_events["waiting_time_minutes"].sum()

    records = []
    for dept, group in df_events.groupby("department"):
        waits = group["waiting_time_minutes"]
        total_wait = int(waits.sum())
        mean_wait = round(float(waits.mean()), 2)
        med_wait = round(float(waits.median()), 2)
        q25 = round(float(waits.quantile(0.25)), 2)
        q75 = round(float(waits.quantile(0.75)), 2)
        p90 = round(float(waits.quantile(0.90)), 2)
        std_wait = round(float(waits.std()), 2)
        min_wait = int(waits.min())
        max_wait = int(waits.max())
        count = len(group)
        unique_visits = int(group["visit_id"].nunique())
        pct_wait = round((total_wait / total_hospital_wait) * 100.0, 2)

        records.append({
            "department": dept,
            "event_count": count,
            "unique_visits_served": unique_visits,
            "min_wait_minutes": min_wait,
            "q25_wait_minutes": q25,
            "median_wait_minutes": med_wait,
            "mean_wait_minutes": mean_wait,
            "q75_wait_minutes": q75,
            "p90_wait_minutes": p90,
            "max_wait_minutes": max_wait,
            "std_dev_minutes": std_wait,
            "total_waiting_minutes": total_wait,
            "pct_of_total_waiting_time": pct_wait,
        })

    df_dept = pd.DataFrame(records)
    df_dept = df_dept.sort_values(by="mean_wait_minutes", ascending=False).reset_index(drop=True)
    df_dept["department_rank"] = df_dept.index + 1
    return df_dept


# =====================================================================
# 4. VISIT-LEVEL ANALYSIS (ONE ROW PER VISIT)
# =====================================================================
def analyze_visit_level_data(df_visits: pd.DataFrame, df_events: pd.DataFrame) -> pd.DataFrame:
    """Aggregate event metrics to create one record per patient visit."""
    # Compute wait sums, wait averages, and diagnostics flag per visit
    diag_visit_ids = set(df_events[df_events["event_name"] == "Diagnostics"]["visit_id"])

    # Extract treatment department for each visit
    treatment_events = df_events[df_events["event_name"] == "Treatment"].drop_duplicates(subset=["visit_id"])
    treatment_map = dict(zip(treatment_events["visit_id"], treatment_events["department"]))

    wait_aggregates = df_events.groupby("visit_id")["waiting_time_minutes"].agg(
        total_wait_mins="sum",
        avg_wait_mins="mean",
    ).reset_index()

    # Merge with visits table
    df_visit_summary = pd.merge(df_visits, wait_aggregates, on="visit_id", how="left")

    # Calculate journey durations
    duration_mins = (df_visit_summary["visit_end_time"] - df_visit_summary["visit_start_time"]).dt.total_seconds() / 60.0
    df_visit_summary["journey_duration_minutes"] = duration_mins.round(2)
    df_visit_summary["journey_duration_hours"] = (duration_mins / 60.0).round(2)

    df_visit_summary["arrival_date"] = df_visit_summary["visit_start_time"].dt.strftime("%Y-%m-%d")
    df_visit_summary["arrival_hour"] = df_visit_summary["visit_start_time"].dt.hour
    df_visit_summary["diagnostics_performed"] = df_visit_summary["visit_id"].apply(
        lambda vid: "Yes" if vid in diag_visit_ids else "No"
    )
    df_visit_summary["treatment_department"] = df_visit_summary["visit_id"].map(treatment_map).fillna("N/A")

    # Rename and order columns for clarity
    df_visit_summary = df_visit_summary.rename(columns={
        "total_events": "event_count",
        "total_wait_mins": "total_recorded_waiting_minutes",
        "avg_wait_mins": "average_recorded_waiting_minutes",
    })

    df_visit_summary["average_recorded_waiting_minutes"] = df_visit_summary["average_recorded_waiting_minutes"].round(2)

    cols = [
        "visit_id",
        "patient_id",
        "visit_start_time",
        "visit_end_time",
        "arrival_date",
        "arrival_hour",
        "journey_duration_minutes",
        "journey_duration_hours",
        "discharge_disposition",
        "event_count",
        "total_recorded_waiting_minutes",
        "average_recorded_waiting_minutes",
        "diagnostics_performed",
        "treatment_department",
    ]
    return df_visit_summary[cols].sort_values(by="visit_start_time").reset_index(drop=True)


# =====================================================================
# 5. LONG-WAIT & STATISTICAL OUTLIER ANALYSIS
# =====================================================================
def analyze_long_waits(df_events: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Analyze high wait times (>30m, >60m) and statistical outliers (1.5x IQR rule).

    Note: Statistical outliers represent notable observations for operational review,
    not clinical or procedural errors.
    """
    total_events = len(df_events)
    all_waits = df_events["waiting_time_minutes"]

    # Global 1.5x IQR rule calculation
    q1 = float(all_waits.quantile(0.25))
    q3 = float(all_waits.quantile(0.75))
    iqr = q3 - q1
    outlier_threshold = round(q3 + 1.5 * iqr, 2)
    p90 = round(float(all_waits.quantile(0.90)), 2)

    global_stats = {
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "outlier_threshold": outlier_threshold,
        "p90": p90,
        "waits_over_30": int((all_waits > 30).sum()),
        "pct_over_30": round(float((all_waits > 30).mean() * 100.0), 2),
        "waits_over_60": int((all_waits > 60).sum()),
        "pct_over_60": round(float((all_waits > 60).mean() * 100.0), 2),
        "outliers_count": int((all_waits > outlier_threshold).sum()),
        "outliers_pct": round(float((all_waits > outlier_threshold).mean() * 100.0), 2),
    }

    # Breakdown by care stage
    records = []
    for stage, group in df_events.groupby("event_name"):
        s_waits = group["waiting_time_minutes"]
        s_count = len(group)
        gt30 = int((s_waits > 30).sum())
        gt60 = int((s_waits > 60).sum())
        s_p90 = round(float(s_waits.quantile(0.90)), 2)

        # Stage-specific 1.5x IQR threshold
        s_q1 = float(s_waits.quantile(0.25))
        s_q3 = float(s_waits.quantile(0.75))
        s_iqr = s_q3 - s_q1
        s_threshold = round(s_q3 + 1.5 * s_iqr, 2)
        s_outliers = int((s_waits > s_threshold).sum())

        records.append({
            "stage": stage,
            "total_events": s_count,
            "waits_over_30_min_count": gt30,
            "waits_over_30_min_pct": round((gt30 / s_count) * 100.0, 2),
            "waits_over_60_min_count": gt60,
            "waits_over_60_min_pct": round((gt60 / s_count) * 100.0, 2),
            "p90_wait_minutes": s_p90,
            "iqr_outlier_threshold_minutes": s_threshold,
            "statistical_outliers_count": s_outliers,
            "statistical_outliers_pct": round((s_outliers / s_count) * 100.0, 2),
        })

    df_long_wait = pd.DataFrame(records).sort_values(by="waits_over_30_min_count", ascending=False).reset_index(drop=True)
    return df_long_wait, global_stats


# =====================================================================
# 6. DIAGNOSTICS UTILIZATION ANALYSIS
# =====================================================================
def analyze_diagnostics(df_visits_summary: pd.DataFrame) -> pd.DataFrame:
    """Compare patient volume and throughput for visits with vs. without diagnostics."""
    records = []
    total_visits = len(df_visits_summary)

    for diag_status in ["Yes", "No"]:
        grp = df_visits_summary[df_visits_summary["diagnostics_performed"] == diag_status]
        label = "Diagnostics Performed" if diag_status == "Yes" else "Diagnostics Skipped"
        v_count = len(grp)
        pct_visits = round((v_count / total_visits) * 100.0, 2)
        avg_dur = round(float(grp["journey_duration_minutes"].mean()), 2)
        med_dur = round(float(grp["journey_duration_minutes"].median()), 2)
        avg_wait = round(float(grp["total_recorded_waiting_minutes"].mean()), 2)
        med_wait = round(float(grp["total_recorded_waiting_minutes"].median()), 2)
        avg_events = round(float(grp["event_count"].mean()), 2)

        records.append({
            "diagnostics_category": label,
            "diagnostics_flag": diag_status,
            "visit_count": v_count,
            "pct_of_total_visits": pct_visits,
            "avg_journey_duration_minutes": avg_dur,
            "median_journey_duration_minutes": med_dur,
            "avg_total_waiting_minutes": avg_wait,
            "median_total_waiting_minutes": med_wait,
            "avg_events_per_visit": avg_events,
        })

    return pd.DataFrame(records)


# =====================================================================
# 7. OVERALL KPIS SUMMARY
# =====================================================================
def generate_overall_kpis(
    df_patients: pd.DataFrame,
    df_visits_summary: pd.DataFrame,
    df_events: pd.DataFrame,
    df_stage: pd.DataFrame,
    global_long_waits: dict,
) -> pd.DataFrame:
    """Consolidate high-level healthcare operational KPIs into a single summary table."""
    total_patients = len(df_patients)
    total_visits = len(df_visits_summary)
    total_events = len(df_events)

    all_waits = df_events["waiting_time_minutes"]
    all_durations = df_visits_summary["journey_duration_minutes"]
    top_bottleneck = df_stage.iloc[0]["stage"]
    top_bottleneck_wait = df_stage.iloc[0]["mean_wait_minutes"]

    diag_usage_pct = round(
        (len(df_visits_summary[df_visits_summary["diagnostics_performed"] == "Yes"]) / total_visits) * 100.0,
        2,
    )

    kpi_list = [
        ("Total Unique Patients", str(total_patients), "Patients", "Volume", "Total unique patients served in 30-day window"),
        ("Total Visits", str(total_visits), "Visits", "Volume", "Total patient visits completed"),
        ("Total Events Recorded", str(total_events), "Events", "Volume", "Total process stages executed across all visits"),
        ("Overall Average Waiting Time", str(round(float(all_waits.mean()), 2)), "Minutes", "Queues", "Average queue delay recorded across all process events"),
        ("Overall Median Waiting Time", str(round(float(all_waits.median()), 2)), "Minutes", "Queues", "Median queue delay across all process events"),
        ("Overall 90th Percentile Wait Time", str(global_long_waits["p90"]), "Minutes", "Queues", "90% of all events have wait times at or below this value"),
        ("Primary Bottleneck Stage", f"{top_bottleneck} ({top_bottleneck_wait}m avg)", "Stage", "Bottlenecks", "Care stage with the highest average queue waiting time"),
        ("Diagnostics Utilization Rate", f"{diag_usage_pct}%", "Percentage", "Pathways", "Proportion of visits requiring diagnostic imaging/labs"),
        ("Average Journey Duration", str(round(float(all_durations.mean()), 2)), "Minutes", "Throughput", "Average elapsed time from registration to discharge"),
        ("Median Journey Duration", str(round(float(all_durations.median()), 2)), "Minutes", "Throughput", "Median elapsed time from registration to discharge"),
        ("Events with Wait > 30 Mins", f"{global_long_waits['waits_over_30']} ({global_long_waits['pct_over_30']}%)", "Events", "Delays", "Process events experiencing moderate queue delay"),
        ("Events with Wait > 60 Mins", f"{global_long_waits['waits_over_60']} ({global_long_waits['pct_over_60']}%)", "Events", "Delays", "Process events experiencing severe queue delay"),
        ("Statistical Outlier Events (1.5x IQR)", f"{global_long_waits['outliers_count']} ({global_long_waits['outliers_pct']}%)", "Events", "Outliers", f"Events with wait > {global_long_waits['outlier_threshold']} mins (1.5x IQR rule)"),
    ]

    return pd.DataFrame(kpi_list, columns=["kpi_name", "value", "unit", "category", "description"])


# =====================================================================
# 8. EXPORTS & RECONCILIATION VALIDATIONS
# =====================================================================
def export_datasets(exports: dict[str, pd.DataFrame], output_dir: Path = OUTPUT_DIR) -> None:
    """Save all processed DataFrames to CSV in data/processed/."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, df in exports.items():
        file_path = output_dir / filename
        df.to_csv(file_path, index=False)


def run_pipeline_validations(
    exports: dict[str, pd.DataFrame],
    df_events: pd.DataFrame,
    df_visits: pd.DataFrame,
    df_patients: pd.DataFrame,
    quality_checks: dict,
) -> bool:
    """Validate all exported datasets against database facts and business logic."""
    print("\n" + "=" * 70)
    print("                 STAGE 5 PIPELINE VALIDATIONS")
    print("=" * 70)

    checks = []

    # 1. Quality checks from initial load
    all_quality_passed = all(check["passed"] for check in quality_checks.values())
    checks.append((
        "Initial Database Quality Checks",
        all_quality_passed,
        "All 6 database sanity checks passed" if all_quality_passed else "Database issues detected",
    ))

    # 2. Check visit_level_analysis has exactly 500 rows and 1 row per unique visit
    df_visit_out = exports["visit_level_analysis.csv"]
    v_rows = len(df_visit_out)
    v_unique = df_visit_out["visit_id"].nunique()
    checks.append((
        "Visit-Level Completeness & Uniqueness",
        (v_rows == 500) and (v_unique == 500),
        f"{v_rows} rows, {v_unique} unique visits (Expected: 500)",
    ))

    # 3. Diagnostics categories sum to total visits
    df_diag_out = exports["diagnostics_analysis.csv"]
    diag_sum = int(df_diag_out["visit_count"].sum())
    checks.append((
        "Diagnostics Categories Sum to Total Visits",
        diag_sum == 500,
        f"Sum of categories = {diag_sum} (Expected: 500)",
    ))

    # 4. Journey durations non-negative
    min_dur = df_visit_out["journey_duration_minutes"].min()
    neg_dur_count = (df_visit_out["journey_duration_minutes"] < 0).sum()
    checks.append((
        "Non-Negative Journey Durations",
        neg_dur_count == 0,
        f"Min observed duration = {min_dur} mins (0 negative durations)",
    ))

    # 5. Exported stage averages match independent calculation
    df_stage_out = exports["stage_waiting_time_analysis.csv"]
    stage_calc = df_events.groupby("event_name")["waiting_time_minutes"].mean().round(2).to_dict()
    stage_exported = dict(zip(df_stage_out["stage"], df_stage_out["mean_wait_minutes"]))
    stage_match = stage_calc == stage_exported
    checks.append((
        "Stage Averages Mathematical Match",
        stage_match,
        "Exact match between exported CSV and pandas calculation",
    ))

    # 6. Exported department averages match independent calculation
    df_dept_out = exports["department_waiting_time_analysis.csv"]
    dept_calc = df_events.groupby("department")["waiting_time_minutes"].mean().round(2).to_dict()
    dept_exported = dict(zip(df_dept_out["department"], df_dept_out["mean_wait_minutes"]))
    dept_match = dept_calc == dept_exported
    checks.append((
        "Department Averages Mathematical Match",
        dept_match,
        "Exact match between exported CSV and pandas calculation",
    ))

    # 7. Total events reconciliation
    total_events_in_db = len(df_events)
    stage_events_sum = int(df_stage_out["event_count"].sum())
    dept_events_sum = int(df_dept_out["event_count"].sum())
    events_match = (stage_events_sum == 2823) and (dept_events_sum == 2823) and (total_events_in_db == 2823)
    checks.append((
        "Event Count Reconciliation",
        events_match,
        f"Events: DB={total_events_in_db}, Stages Sum={stage_events_sum}, Depts Sum={dept_events_sum}",
    ))

    all_passed = True
    for name, passed, detail in checks:
        status_label = "[PASS]" if passed else "[WARNING]"
        if not passed:
            all_passed = False
        print(f"  {status_label} {name:<40}: {detail}")

    print("=" * 70)
    if all_passed:
        print(" SUCCESS: All Stage 5 calculations and exports verified successfully.")
    else:
        print(" WARNING: One or more validation checks failed.")
    print("=" * 70 + "\n")

    return all_passed


def print_summary_reports(
    exports: dict[str, pd.DataFrame],
    global_long_waits: dict,
    output_dir: Path,
):
    """Print beginner-friendly terminal summaries of the statistical analysis."""
    print("\n" + "=" * 70)
    print("         CAREFLOW STAGE 5: STATISTICAL & PROCESS ANALYSIS")
    print("=" * 70)
    print(f" Output Directory : {output_dir}")
    print(f" Exported Datasets: {len(exports)} CSV files generated\n")

    for fname, df in exports.items():
        print(f"  * {fname:<38} : {len(df):>4} rows, {len(df.columns):>2} columns")

    # 1. Stage Bottleneck Summary
    print("\n--- 1. Care Stage Waiting-Time & Bottleneck Summary ---")
    stage_df = exports["stage_waiting_time_analysis.csv"][
        ["bottleneck_rank", "stage", "event_count", "mean_wait_minutes", "median_wait_minutes", "p90_wait_minutes", "pct_of_total_waiting_time"]
    ]
    print(stage_df.to_string(index=False))

    # 2. Long Wait Analysis
    print("\n--- 2. Long-Wait & Statistical Outlier Summary (1.5x IQR Rule) ---")
    print(f"  Global 1.5x IQR Threshold : {global_long_waits['outlier_threshold']} minutes (Q1={global_long_waits['q1']}, Q3={global_long_waits['q3']})")
    print(f"  Events > 30 Mins Wait     : {global_long_waits['waits_over_30']} events ({global_long_waits['pct_over_30']}%)")
    print(f"  Events > 60 Mins Wait     : {global_long_waits['waits_over_60']} events ({global_long_waits['pct_over_60']}%)")
    print(f"  Statistical Outliers      : {global_long_waits['outliers_count']} events ({global_long_waits['outliers_pct']}%)")

    # 3. Diagnostics Impact
    print("\n--- 3. Diagnostics Utilization & Journey Duration Impact ---")
    diag_df = exports["diagnostics_analysis.csv"][
        ["diagnostics_category", "visit_count", "pct_of_total_visits", "avg_journey_duration_minutes", "avg_total_waiting_minutes"]
    ]
    print(diag_df.to_string(index=False))

    # 4. Overall KPIs
    print("\n--- 4. Overall Healthcare Operational KPIs ---")
    kpi_df = exports["overall_kpis.csv"][["category", "kpi_name", "value", "unit"]]
    print(kpi_df.to_string(index=False))


def main():
    """Main execution orchestrator."""
    print("Connecting to CareFlow database...")
    conn = get_database_connection(DB_PATH)

    try:
        print("Loading patients, visits, and events tables...")
        df_patients, df_visits, df_events = load_raw_data(conn)

        print("Executing data quality checks...")
        quality_checks = run_data_quality_checks(df_patients, df_visits, df_events)

        print("Performing stage waiting-time analysis...")
        df_stage = analyze_stage_waiting_times(df_events)

        print("Performing department waiting-time analysis...")
        df_dept = analyze_department_waiting_times(df_events)

        print("Performing visit-level duration analysis...")
        df_visits_summary = analyze_visit_level_data(df_visits, df_events)

        print("Performing long-wait and statistical outlier analysis...")
        df_long_wait, global_long_waits = analyze_long_waits(df_events)

        print("Performing diagnostics impact analysis...")
        df_diag = analyze_diagnostics(df_visits_summary)

        print("Consolidating overall operational KPIs...")
        df_kpis = generate_overall_kpis(df_patients, df_visits_summary, df_events, df_stage, global_long_waits)

        # Dictionary of all datasets to export
        exports = {
            "stage_waiting_time_analysis.csv": df_stage,
            "department_waiting_time_analysis.csv": df_dept,
            "visit_level_analysis.csv": df_visits_summary,
            "long_wait_analysis.csv": df_long_wait,
            "diagnostics_analysis.csv": df_diag,
            "overall_kpis.csv": df_kpis,
        }

        print("Exporting Power BI-ready datasets to data/processed/...")
        export_datasets(exports, OUTPUT_DIR)

        print_summary_reports(exports, global_long_waits, OUTPUT_DIR)

        print("Executing pipeline reconciliation and validations...")
        all_valid = run_pipeline_validations(exports, df_events, df_visits, df_patients, quality_checks)

        if not all_valid:
            sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
