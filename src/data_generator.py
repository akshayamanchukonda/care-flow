"""CareFlow: Synthetic Healthcare Event Data Generator.

This module generates a reproducible synthetic healthcare event log for 500
fictional patient visits, simulating patient journeys through an Emergency
and Outpatient care department.

Clinical & Operational Modeling Assumptions:
--------------------------------------------
1. Stages:
   - Registration: Initial administrative check-in upon arrival.
   - Triage: Clinical acuity evaluation by nursing staff.
   - Consultation: Evaluation and diagnosis by an attending physician.
   - Diagnostics: Optional diagnostic imaging or laboratory testing.
     Skipped for ~35% of lower-acuity visits where testing is unnecessary.
   - Treatment: Medical therapy, procedures, or nursing care.
   - Discharge: Final disposition (Home, Inpatient Admission, or Transfer).

2. Departments & Pathways:
   - Registration -> Admissions & Registration
   - Triage -> Emergency Triage
   - Consultation -> General Emergency Care (65%), Outpatient Clinic (25%), Pediatric Emergency (10%)
   - Diagnostics -> Radiology / Imaging (50%), Pathology Lab (35%), Cardiology Diagnostics (15%)
   - Treatment -> Acute Treatment Unit (55%), Urgent Treatment Unit (30%), Observation Ward (15%)
   - Discharge -> Discharge Lounge (routine) or Administrative Desk (transfers/admissions)

3. Waiting Times & Chronology:
   - Waiting times represent the queue time elapsed before receiving care at each stage.
   - All waiting times are strictly non-negative (>= 0 minutes).
   - Events for each visit are strictly chronological (each subsequent event occurs after the prior event).
   - A fixed random seed (42) ensures 100% reproducible data generation.
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
TOTAL_UNIQUE_PATIENTS = 420  # Allows realistic repeat visits for some patients
START_DATE = datetime(2026, 10, 1, 8, 0, 0)
SIMULATION_DAYS = 30

# File Paths (relative to repository root)
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = REPO_ROOT / "data" / "raw" / "healthcare_event_log.csv"

# Stage definitions and department options
STAGES = ["Registration", "Triage", "Consultation", "Diagnostics", "Treatment", "Discharge"]

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


def generate_synthetic_event_log(seed: int = RANDOM_SEED, total_visits: int = TOTAL_VISITS) -> pd.DataFrame:
    """Generate a reproducible healthcare event log dataset.

    Args:
        seed: Random seed for reproducibility.
        total_visits: Number of unique patient journeys to generate.

    Returns:
        pd.DataFrame containing the generated event log.
    """
    random.seed(seed)
    np.random.seed(seed)

    # Create patient ID pool (some patients have multiple visits)
    patient_pool = [f"P{i:04d}" for i in range(1, TOTAL_UNIQUE_PATIENTS + 1)]

    # Assign patient IDs to visits (sampling with replacement for return visits)
    assigned_patients = []
    # Ensure every patient in pool has at least one visit
    assigned_patients.extend(patient_pool)
    # Remaining visits are return visits from the existing pool
    remaining_count = total_visits - len(patient_pool)
    if remaining_count > 0:
        assigned_patients.extend(random.choices(patient_pool, k=remaining_count))
    random.shuffle(assigned_patients)

    records = []
    global_event_counter = 1

    for visit_index in range(1, total_visits + 1):
        visit_id = f"V{visit_index:04d}"
        patient_id = assigned_patients[visit_index - 1]

        # Stagger visit start times across the 30-day simulation window
        day_offset = random.randint(0, SIMULATION_DAYS - 1)
        # Weight arrivals towards daytime/evening hours (08:00 to 22:00)
        arrival_hour = int(np.clip(np.random.normal(loc=14.0, scale=4.5), 8, 23))
        arrival_minute = random.randint(0, 59)
        arrival_second = random.randint(0, 59)
        current_time = START_DATE + timedelta(
            days=day_offset,
            hours=arrival_hour - 8,
            minutes=arrival_minute,
            seconds=arrival_second,
        )

        # Decide whether this journey includes Diagnostics (~65% require, ~35% skip)
        requires_diagnostics = random.random() < 0.65

        # Build list of stages for this visit
        journey_stages = ["Registration", "Triage", "Consultation"]
        if requires_diagnostics:
            journey_stages.append("Diagnostics")
        journey_stages.extend(["Treatment", "Discharge"])

        for stage in journey_stages:
            event_id = f"EVT{global_event_counter:05d}"
            global_event_counter += 1

            # Determine waiting time (in minutes) before service starts
            if stage == "Registration":
                # Initial check-in wait at the front desk
                wait_minutes = int(np.clip(np.random.gamma(shape=2.0, scale=4.0), 1, 30))
                duration_minutes = random.randint(4, 10)
            elif stage == "Triage":
                # Waiting time between registration and triage nurse
                wait_minutes = int(np.clip(np.random.gamma(shape=2.5, scale=5.0), 2, 45))
                duration_minutes = random.randint(8, 16)
            elif stage == "Consultation":
                # Waiting time between triage and doctor consultation (common bottleneck)
                wait_minutes = int(np.clip(np.random.gamma(shape=3.0, scale=12.0), 5, 120))
                duration_minutes = random.randint(15, 45)
            elif stage == "Diagnostics":
                # Waiting time for imaging / lab tests
                wait_minutes = int(np.clip(np.random.gamma(shape=3.0, scale=10.0), 5, 90))
                duration_minutes = random.randint(20, 60)
            elif stage == "Treatment":
                # Waiting time before treatment administration
                wait_minutes = int(np.clip(np.random.gamma(shape=2.5, scale=8.0), 5, 60))
                duration_minutes = random.randint(25, 90)
            elif stage == "Discharge":
                # Administrative wait for discharge paperwork/transport
                wait_minutes = int(np.clip(np.random.gamma(shape=2.0, scale=7.0), 3, 45))
                duration_minutes = random.randint(5, 15)

            # Advance current time by the waiting time to reach event start
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

            # Advance time by service duration so subsequent stage starts after this stage completes
            current_time = current_time + timedelta(minutes=duration_minutes)

    df = pd.DataFrame(records)
    return df


def validate_event_log(df: pd.DataFrame) -> dict:
    """Validate data integrity and business rules on the generated event log.

    Checks:
      1. Presence of all 8 required columns.
      2. No missing or null values in any required field.
      3. Global uniqueness of event_id.
      4. Valid ISO datetime format for event_timestamp.
      5. Non-negative waiting times (waiting_time_minutes >= 0).
      6. Chronological ordering of events within every visit.

    Args:
        df: DataFrame containing the event log.

    Returns:
        dict of validation check results (bool and detail string).
    """
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

    # Check 1: Required columns
    missing_cols = [col for col in required_columns if col not in df.columns]
    results["required_columns"] = {
        "passed": len(missing_cols) == 0,
        "detail": f"All {len(required_columns)} columns present" if not missing_cols else f"Missing: {missing_cols}",
    }

    # Check 2: Missing values
    null_counts = df[required_columns].isnull().sum().sum()
    results["no_missing_values"] = {
        "passed": null_counts == 0,
        "detail": "0 missing values across all required columns" if null_counts == 0 else f"{null_counts} null values found",
    }

    # Check 3: Unique event IDs
    total_events = len(df)
    unique_events = df["event_id"].nunique()
    results["unique_event_ids"] = {
        "passed": total_events == unique_events,
        "detail": f"{unique_events} unique event IDs out of {total_events} rows",
    }

    # Check 4: Valid timestamps
    try:
        parsed_timestamps = pd.to_datetime(df["event_timestamp"], format="%Y-%m-%d %H:%M:%S", errors="raise")
        invalid_ts_count = parsed_timestamps.isnull().sum()
        results["valid_timestamps"] = {
            "passed": invalid_ts_count == 0,
            "detail": f"All {total_events} timestamps parsed successfully into valid datetimes",
        }
    except Exception as exc:
        results["valid_timestamps"] = {
            "passed": False,
            "detail": f"Timestamp parsing failed: {exc}",
        }

    # Check 5: Non-negative waiting times
    neg_waits = (df["waiting_time_minutes"] < 0).sum()
    min_wait = df["waiting_time_minutes"].min()
    max_wait = df["waiting_time_minutes"].max()
    results["non_negative_waiting_times"] = {
        "passed": neg_waits == 0,
        "detail": f"All waiting times >= 0 min (Range: {min_wait} to {max_wait} mins)",
    }

    # Check 6: Chronological ordering within each visit
    chronology_failures = 0
    df_sorted = df.copy()
    df_sorted["parsed_time"] = pd.to_datetime(df_sorted["event_timestamp"])

    for _, group in df_sorted.groupby("visit_id"):
        timestamps = group["parsed_time"].tolist()
        for i in range(len(timestamps) - 1):
            if timestamps[i] >= timestamps[i + 1]:
                chronology_failures += 1

    results["chronological_ordering"] = {
        "passed": chronology_failures == 0,
        "detail": "Strict chronological sequencing verified across all visits" if chronology_failures == 0 else f"{chronology_failures} sequencing inversions detected",
    }

    return results


def print_summary(df: pd.DataFrame, validation_results: dict, output_path: Path):
    """Print a beginner-friendly summary of the generated dataset and validation."""
    total_visits = df["visit_id"].nunique()
    total_patients = df["patient_id"].nunique()
    total_events = len(df)
    stage_counts = df["event_name"].value_counts()

    print("\n" + "=" * 65)
    print("         CareFlow - Healthcare Event Log Generation Summary")
    print("=" * 65)
    print(f" Output File Path    : {output_path}")
    print(f" Unique Visits       : {total_visits}")
    print(f" Unique Patients     : {total_patients}")
    print(f" Total Events        : {total_events:,}")
    print(f" Diagnostics Rate    : {stage_counts.get('Diagnostics', 0)} / {total_visits} visits "
          f"({stage_counts.get('Diagnostics', 0) / total_visits * 100:.1f}%)")

    print("\n--- Event Counts by Stage ---")
    for stage in STAGES:
        count = stage_counts.get(stage, 0)
        print(f"  {stage:<15} : {count:>5} events")

    print("\n--- Data Validation Results ---")
    all_passed = True
    for check_name, res in validation_results.items():
        status_label = "[PASS]" if res["passed"] else "[FAIL]"
        if not res["passed"]:
            all_passed = False
        readable_name = check_name.replace("_", " ").title()
        print(f"  {status_label} {readable_name:<28}: {res['detail']}")

    print("=" * 65)
    if all_passed:
        print(" SUCCESS: Event log is fully validated and ready for analysis.")
    else:
        print(" WARNING: One or more validation checks failed. Inspect errors above.")
    print("=" * 65 + "\n")


def main():
    """Execute event generation, validate results, and save to CSV."""
    print(f"Generating synthetic healthcare event log ({TOTAL_VISITS} visits)...")
    df = generate_synthetic_event_log(seed=RANDOM_SEED, total_visits=TOTAL_VISITS)

    print("Running data validation checks...")
    validation_results = validate_event_log(df)

    # Ensure parent output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Save to CSV
    df.to_csv(OUTPUT_FILE, index=False)

    # Print friendly summary report
    print_summary(df, validation_results, OUTPUT_FILE)

    # Fail fast if any check failed
    if not all(res["passed"] for res in validation_results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()

