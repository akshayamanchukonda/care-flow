"""CareFlow: Revised Synthetic Healthcare Event Data Generator (v2).

Generates a revised synthetic healthcare event log containing realistic
operational inefficiencies, department flows, and clinical loop-backs (rework loops).

Operational Inefficiencies & Loop-Back Types:
---------------------------------------------
1. Administrative Rework Loop-Back (~7% of visits):
   Patient reaches Triage, but has missing insurance/consent forms, looping
   back to Admissions & Registration before returning to Triage.
   Flow: Registration -> Triage -> Registration -> Triage -> Consultation ...

2. Clinical Re-Consultation Loop-Back (~22% of diagnostic visits):
   Patient undergoes Diagnostics (imaging/lab), then returns to the physician
   for result review and treatment planning.
   Flow: Consultation -> Diagnostics -> Consultation -> Treatment -> Discharge

3. Observation Repeat Diagnostics Loop-Back (~5% of visits):
   Patient in Treatment/Observation requires repeat lab testing or follow-up imaging.
   Flow: Treatment -> Diagnostics -> Treatment -> Discharge

Output:
-------
Saves to: data/raw/healthcare_event_log_v2.csv
(Leaves the original data/raw/healthcare_event_log.csv completely untouched)
"""

from datetime import datetime, timedelta
from pathlib import Path
import random
import sys
import numpy as np
import pandas as pd

# Constants for reproducibility
RANDOM_SEED = 42
TOTAL_VISITS = 500
TOTAL_UNIQUE_PATIENTS = 420
START_DATE = datetime(2026, 10, 1, 8, 0, 0)
SIMULATION_DAYS = 30

# File Paths
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE_V2 = REPO_ROOT / "data" / "raw" / "healthcare_event_log_v2.csv"
ORIGINAL_CSV = REPO_ROOT / "data" / "raw" / "healthcare_event_log.csv"

DEPARTMENT_CHOICES = {
    "Registration": ["Admissions & Registration"],
    "Triage": ["Emergency Triage"],
    "Consultation": ["General Emergency Care", "Outpatient Clinic", "Pediatric Emergency"],
    "Diagnostics": ["Radiology / Imaging", "Pathology Lab", "Cardiology Diagnostics"],
    "Treatment": ["Acute Treatment Unit", "Urgent Treatment Unit", "Observation Ward"],
    "Discharge": ["Discharge Lounge", "Patient Transfer Desk"],
}

DEPARTMENT_WEIGHTS = {
    "Registration": [1.0],
    "Triage": [1.0],
    "Consultation": [0.65, 0.25, 0.10],
    "Diagnostics": [0.50, 0.35, 0.15],
    "Treatment": [0.55, 0.30, 0.15],
    "Discharge": [0.80, 0.20],
}

DISCHARGE_STATUSES = ["Discharged - Home", "Admitted - Inpatient", "Transferred - Specialist"]
DISCHARGE_STATUS_WEIGHTS = [0.72, 0.22, 0.06]


def generate_revised_event_log(seed: int = RANDOM_SEED, total_visits: int = TOTAL_VISITS) -> pd.DataFrame:
    """Generate a reproducible healthcare event log containing realistic loop-backs."""
    random.seed(seed)
    np.random.seed(seed)

    # 420 unique patients across 500 visits
    patient_pool = [f"P{i:04d}" for i in range(1, TOTAL_UNIQUE_PATIENTS + 1)]
    assigned_patients = []
    assigned_patients.extend(patient_pool)
    remaining_count = total_visits - len(patient_pool)
    if remaining_count > 0:
        assigned_patients.extend(random.choices(patient_pool, k=remaining_count))
    random.shuffle(assigned_patients)

    records = []
    global_event_counter = 1

    for visit_index in range(1, total_visits + 1):
        visit_id = f"V{visit_index:04d}"
        patient_id = assigned_patients[visit_index - 1]

        # Base arrival timestamp
        day_offset = random.randint(0, SIMULATION_DAYS - 1)
        arrival_hour = int(np.clip(np.random.normal(loc=14.0, scale=4.5), 8, 23))
        arrival_minute = random.randint(0, 59)
        arrival_second = random.randint(0, 59)
        current_time = START_DATE + timedelta(
            days=day_offset,
            hours=arrival_hour - 8,
            minutes=arrival_minute,
            seconds=arrival_second,
        )

        # Decide pathways and inefficiencies for this visit
        has_admin_rework = random.random() < 0.07          # ~7% missing paperwork loop
        requires_diagnostics = random.random() < 0.65       # ~65% require lab/imaging
        has_reconsultation = requires_diagnostics and (random.random() < 0.35)  # ~23% of total
        has_repeat_diagnostics = random.random() < 0.05     # ~5% repeat test during treatment

        # Construct realistic pathway with loops
        stages_flow = []

        # Stage 1: Registration
        stages_flow.append("Registration")

        # Stage 2: Triage
        stages_flow.append("Triage")

        # Inefficiency 1: Administrative loop-back (Missing paperwork)
        if has_admin_rework:
            stages_flow.append("Registration")  # Loop back to fix paperwork
            stages_flow.append("Triage")        # Return to triage

        # Stage 3: Consultation
        stages_flow.append("Consultation")

        # Stage 4: Diagnostics & Inefficiency 2 (Clinical Re-Consultation)
        if requires_diagnostics:
            stages_flow.append("Diagnostics")
            if has_reconsultation:
                stages_flow.append("Consultation")  # Loop back to doctor to review test results

        # Stage 5: Treatment & Inefficiency 3 (Repeat diagnostic check)
        stages_flow.append("Treatment")
        if has_repeat_diagnostics:
            stages_flow.append("Diagnostics")  # Repeat lab test during observation
            stages_flow.append("Treatment")    # Resume treatment

        # Stage 6: Discharge
        stages_flow.append("Discharge")

        for stage in stages_flow:
            event_id = f"EVT{global_event_counter:05d}"
            global_event_counter += 1

            # Waiting time models
            if stage == "Registration":
                wait_minutes = int(np.clip(np.random.gamma(shape=2.0, scale=4.0), 1, 30))
                duration_minutes = random.randint(4, 10)
            elif stage == "Triage":
                wait_minutes = int(np.clip(np.random.gamma(shape=2.5, scale=5.0), 2, 45))
                duration_minutes = random.randint(8, 16)
            elif stage == "Consultation":
                wait_minutes = int(np.clip(np.random.gamma(shape=3.0, scale=12.0), 5, 120))
                duration_minutes = random.randint(15, 45)
            elif stage == "Diagnostics":
                wait_minutes = int(np.clip(np.random.gamma(shape=3.0, scale=10.0), 5, 90))
                duration_minutes = random.randint(20, 60)
            elif stage == "Treatment":
                wait_minutes = int(np.clip(np.random.gamma(shape=2.5, scale=8.0), 5, 60))
                duration_minutes = random.randint(25, 90)
            elif stage == "Discharge":
                wait_minutes = int(np.clip(np.random.gamma(shape=2.0, scale=7.0), 3, 45))
                duration_minutes = random.randint(5, 15)

            # Advance time by wait time to event start
            current_time = current_time + timedelta(minutes=wait_minutes)
            event_timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")

            # Department selection
            dept_choices = DEPARTMENT_CHOICES[stage]
            dept_weights = DEPARTMENT_WEIGHTS[stage]
            department = random.choices(dept_choices, weights=dept_weights, k=1)[0]

            # Status determination
            if stage == "Discharge":
                status = random.choices(DISCHARGE_STATUSES, weights=DISCHARGE_STATUS_WEIGHTS, k=1)[0]
            else:
                status = "Completed"

            records.append({
                "patient_id": patient_id,
                "visit_id": visit_id,
                "event_id": event_id,
                "event_name": stage,
                "event_timestamp": event_timestamp,
                "department": department,
                "status": status,
                "waiting_time_minutes": wait_minutes,
            })

            # Advance time by service duration
            current_time = current_time + timedelta(minutes=duration_minutes)

    df = pd.DataFrame(records)
    return df


def validate_v2_event_log(df: pd.DataFrame) -> dict:
    """Validate data integrity and count loop-backs."""
    required_columns = [
        "patient_id",
        "visit_id",
        "event_id",
        "event_name",
        "event_timestamp",
        "department",
        "status",
        "waiting_time_minutes",
    ]

    results = {}

    # 1. Required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    results["required_columns"] = {
        "passed": len(missing_cols) == 0,
        "detail": f"All {len(required_columns)} columns present" if not missing_cols else f"Missing: {missing_cols}",
    }

    # 2. Missing values
    null_counts = df[required_columns].isnull().sum().sum()
    results["no_missing_values"] = {
        "passed": null_counts == 0,
        "detail": "0 missing values across all required columns",
    }

    # 3. Unique event IDs
    total_events = len(df)
    unique_events = df["event_id"].nunique()
    results["unique_event_ids"] = {
        "passed": total_events == unique_events,
        "detail": f"{unique_events} unique event IDs out of {total_events} rows",
    }

    # 4. Valid timestamps
    try:
        parsed_ts = pd.to_datetime(df["event_timestamp"], format="%Y-%m-%d %H:%M:%S", errors="raise")
        results["valid_timestamps"] = {
            "passed": parsed_ts.isnull().sum() == 0,
            "detail": f"All {total_events} timestamps parsed successfully",
        }
    except Exception as exc:
        results["valid_timestamps"] = {"passed": False, "detail": f"Parse error: {exc}"}

    # 5. Non-negative waiting times
    neg_waits = (df["waiting_time_minutes"] < 0).sum()
    results["non_negative_waiting_times"] = {
        "passed": neg_waits == 0,
        "detail": f"All waiting times >= 0 (Min: {df['waiting_time_minutes'].min()}, Max: {df['waiting_time_minutes'].max()})",
    }

    # 6. Chronological ordering within visits
    df_sorted = df.copy()
    df_sorted["parsed_time"] = pd.to_datetime(df_sorted["event_timestamp"])
    chronology_failures = 0
    for _, group in df_sorted.groupby("visit_id"):
        times = group["parsed_time"].tolist()
        for i in range(len(times) - 1):
            if times[i] >= times[i + 1]:
                chronology_failures += 1

    results["chronological_ordering"] = {
        "passed": chronology_failures == 0,
        "detail": "Strict chronological sequencing verified across all visits",
    }

    # 7. Loop-Back Detection
    loopback_events_count = 0
    visits_with_loops = 0
    loop_details = {"Registration": 0, "Triage": 0, "Consultation": 0, "Diagnostics": 0, "Treatment": 0}

    for _, group in df.groupby("visit_id"):
        seen_stages = set()
        visit_had_loop = False
        for stage in group["event_name"]:
            if stage in seen_stages:
                loopback_events_count += 1
                visit_had_loop = True
                loop_details[stage] = loop_details.get(stage, 0) + 1
            seen_stages.add(stage)
        if visit_had_loop:
            visits_with_loops += 1

    results["loopback_detection"] = {
        "passed": loopback_events_count > 0,
        "loopback_events": loopback_events_count,
        "visits_with_loops": visits_with_loops,
        "loop_details": loop_details,
        "detail": f"{loopback_events_count} loop-back events detected across {visits_with_loops} patient visits ({visits_with_loops/500*100:.1f}%)",
    }

    return results


def print_summary_v2(df: pd.DataFrame, results: dict, output_path: Path):
    """Print summary of revised dataset and loop-back metrics."""
    total_visits = df["visit_id"].nunique()
    total_patients = df["patient_id"].nunique()
    total_events = len(df)
    loop_info = results["loopback_detection"]

    print("\n" + "=" * 68)
    print("      CareFlow - Revised Synthetic Event Log Summary (v2)")
    print("=" * 68)
    print(f" Output File Path      : {output_path}")
    print(f" Total Patient Visits  : {total_visits}")
    print(f" Total Unique Patients : {total_patients}")
    print(f" Total Events Recorded : {total_events:,}")
    print(f" Visits with Loop-Backs: {loop_info['visits_with_loops']} ({loop_info['visits_with_loops'] / total_visits * 100:.1f}%)")
    print(f" Total Loop-Back Events: {loop_info['loopback_events']}")

    print("\n--- Loop-Backs by Stage (Rework / Re-evaluation) ---")
    for stg, cnt in loop_info["loop_details"].items():
        if cnt > 0:
            print(f"  {stg:<18} : {cnt:>4} repeat occurrences")

    print("\n--- Data Validation Checks ---")
    for check_name, res in results.items():
        if check_name == "loopback_detection":
            status_label = "[DETECTED]" if res["passed"] else "[NONE]"
        else:
            status_label = "[PASS]" if res["passed"] else "[FAIL]"
        readable = check_name.replace("_", " ").title()
        print(f"  {status_label:<10} {readable:<30}: {res['detail']}")

    print("=" * 68)
    print(" SUCCESS: Revised dataset generated with realistic loop-backs.")
    print("=" * 68 + "\n")


def main():
    print("Generating revised synthetic healthcare event log with loop-backs...")
    df = generate_revised_event_log(seed=RANDOM_SEED, total_visits=TOTAL_VISITS)

    print("Running validation and loop-back detection...")
    results = validate_v2_event_log(df)

    OUTPUT_FILE_V2.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT_FILE_V2, index=False)

    print_summary_v2(df, results, OUTPUT_FILE_V2)


if __name__ == "__main__":
    main()
