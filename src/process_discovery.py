"""CareFlow: Week 2 As-Is Process Discovery and Visualization using PM4Py.

This script executes the official Week 2 process mining pipeline:
  1. Loads and standardizes the cleaned hospital event log with canonical fields:
     - Case_ID
     - Activity_Name
     - Timestamp
  2. Runs comprehensive quality validations (chronology, complete cases, loop-back preservation).
  3. Discovers the As-Is patient process model using PM4Py (Directly-Follows Graph & Variants).
  4. Exports transition frequency metrics (reports/dfg_transitions.csv).
  5. Exports Graphviz DOT definition (reports/as_is_process_map.dot).
  6. Renders a publication-quality directed process map (reports/as_is_process_map.png).
"""

import argparse
from datetime import datetime
import hashlib
import os
from pathlib import Path
import shutil
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import networkx as nx
import pandas as pd
import pm4py
from pm4py.visualization.dfg import visualizer as dfg_visualizer


# ---------------------------------------------------------------------------
# Path Configuration
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
CLEANED_CSV_PATH = REPO_ROOT / "data" / "processed" / "cleaned_healthcare_event_log_v2.csv"
STANDARDIZED_CSV_PATH = REPO_ROOT / "data" / "processed" / "standardized_event_log_v2.csv"
REPORTS_DIR = REPO_ROOT / "reports"
TRANSITIONS_CSV_PATH = REPORTS_DIR / "dfg_transitions.csv"
PROCESS_MAP_DOT_PATH = REPORTS_DIR / "as_is_process_map.dot"
PROCESS_MAP_PNG_PATH = REPORTS_DIR / "as_is_process_map.png"

# Known loop-back transitions in CareFlow clinical pathways
LOOPBACK_TRANSITIONS = {
    ("Triage", "Registration"),
    ("Diagnostics", "Consultation"),
    ("Treatment", "Diagnostics"),
}


def load_and_standardize_event_log(input_path: Path) -> pd.DataFrame:
    """Load cleaned event log, strip whitespace, and create canonical process mining fields.

    Canonical columns required by process mining standard:
      - Case_ID: Unique identifier for each patient visit.
      - Activity_Name: Clinical action performed.
      - Timestamp: Datetime when activity was recorded.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input event log not found at: {input_path}")

    print(f"[1/5] Loading cleaned event log from {input_path.name}...")
    df = pd.read_csv(input_path)

    # Strip whitespace from column names and all string columns
    df.columns = df.columns.str.strip()
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()
        else:
            # Fallback for any other string representations
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    # Parse event_timestamp to datetime
    df["parsed_timestamp"] = pd.to_datetime(df["event_timestamp"])

    # Ensure sorting chronologically within each case
    df = df.sort_values(by=["case_id", "parsed_timestamp", "activity_sequence"]).reset_index(drop=True)

    # Build standardized dataframe with canonical fields at the front
    std_df = pd.DataFrame()
    std_df["Case_ID"] = df["case_id"]
    std_df["Activity_Name"] = df["activity_name"]
    std_df["Timestamp"] = df["parsed_timestamp"]

    # Preserve all original columns for full metadata traceability
    for col in df.columns:
        if col != "parsed_timestamp" and col not in std_df.columns:
            std_df[col] = df[col]

    print(f"      Standardized {len(std_df):,} events across {std_df['Case_ID'].nunique():,} cases.")
    return std_df


def validate_standardized_event_log(df: pd.DataFrame) -> dict:
    """Validate data integrity, chronology, and loop-back preservation."""
    print("[2/5] Validating standardized event log...")

    # Check 1: Required columns
    required_canonical = ["Case_ID", "Activity_Name", "Timestamp"]
    missing_cols = [c for c in required_canonical if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required canonical columns: {missing_cols}")

    # Check 2: Null checks
    null_counts = df[required_canonical].isnull().sum().to_dict()
    if any(count > 0 for count in null_counts.values()):
        raise ValueError(f"Null values detected in canonical columns: {null_counts}")

    # Check 3: Row, Case, Patient, and Loop-back counts
    total_events = len(df)
    total_cases = df["Case_ID"].nunique()
    total_patients = df["patient_id"].nunique()
    loopback_events = int(df["is_loopback"].astype(int).sum())

    if total_events != 3030:
        raise AssertionError(f"Expected 3,030 events, found {total_events}")
    if total_cases != 500:
        raise AssertionError(f"Expected 500 cases, found {total_cases}")
    if total_patients != 420:
        raise AssertionError(f"Expected 420 patients, found {total_patients}")
    if loopback_events != 214:
        raise AssertionError(f"Expected 214 loop-back events, found {loopback_events}")

    # Check 4: Chronological consistency per case
    chronology_violations = 0
    for case_id, grp in df.groupby("Case_ID"):
        timestamps = grp["Timestamp"].tolist()
        for i in range(len(timestamps) - 1):
            if timestamps[i] >= timestamps[i + 1]:
                chronology_violations += 1

    if chronology_violations > 0:
        raise AssertionError(f"Detected {chronology_violations} chronological ordering violations!")

    print(f"      Integrity Verified: 3,030 events, 500 cases, 420 patients, 214 loop-backs, 0 chronology errors.")
    return {
        "events": total_events,
        "cases": total_cases,
        "patients": total_patients,
        "loopbacks": loopback_events,
        "chronology_violations": chronology_violations,
    }


def extract_trace_transitions(df: pd.DataFrame) -> dict[tuple[str, str], int]:
    """Derive directly-follows transitions by trace iteration per case.

    Explicitly ensures case boundaries are respected and transitions never cross cases.
    """
    transitions: dict[tuple[str, str], int] = {}
    for _, grp in df.groupby("Case_ID", sort=False):
        activities = grp["Activity_Name"].tolist()
        for i in range(len(activities) - 1):
            pair = (activities[i], activities[i + 1])
            transitions[pair] = transitions.get(pair, 0) + 1
    return transitions


def discover_as_is_process(df: pd.DataFrame) -> tuple[dict, dict, dict, pd.DataFrame]:
    """Discover As-Is clinical process using PM4Py Directly-Follows Graph (DFG).

    Rationale for DFG Discovery:
      - Clinical processes exhibit both standard paths and rework loops.
      - DFG directly maps all observed transitions with exact event frequencies,
        ensuring complete transparency without filtering or artificial abstraction.
      - Loop-backs (e.g. Diagnostics -> Consultation) are explicitly quantified.
    """
    print("[3/5] Discovering As-Is process model using PM4Py...")

    # Ensure dataframe is sorted strictly by Case_ID and Timestamp before deriving transitions
    df_sorted = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_sorted["Timestamp"]):
        df_sorted["Timestamp"] = pd.to_datetime(df_sorted["Timestamp"])

    sort_cols = ["Case_ID", "Timestamp"]
    if "activity_sequence" in df_sorted.columns:
        sort_cols.append("activity_sequence")
    df_sorted = df_sorted.sort_values(by=sort_cols).reset_index(drop=True)

    # Format dataframe for PM4Py
    formatted_df = pm4py.format_dataframe(
        df_sorted,
        case_id="Case_ID",
        activity_key="Activity_Name",
        timestamp_key="Timestamp",
    )

    # Discover DFG, start activities, and end activities
    dfg, start_activities, end_activities = pm4py.discover_dfg(
        formatted_df,
        activity_key="Activity_Name",
        case_id_key="Case_ID",
        timestamp_key="Timestamp",
    )

    # Cross-verify PM4Py DFG against trace-level transition extraction
    trace_dfg = extract_trace_transitions(df_sorted)
    if dfg != trace_dfg:
        raise ValueError(f"Discrepancy detected between PM4Py DFG ({len(dfg)}) and trace extraction ({len(trace_dfg)})!")

    # Verify case boundary integrity: Terminal activity (Discharge) must never have outgoing transitions
    for (src, tgt) in dfg.keys():
        if src == "Discharge":
            raise ValueError(f"Boundary violation: Found outgoing transition from terminal stage Discharge -> {tgt}!")

    # Calculate activity execution frequencies
    activity_counts = df_sorted["Activity_Name"].value_counts().to_dict()

    # Build transitions summary DataFrame
    transitions_data = []
    total_transitions = sum(dfg.values())

    for (src, tgt), count in sorted(dfg.items(), key=lambda x: x[1], reverse=True):
        is_loop = (src, tgt) in LOOPBACK_TRANSITIONS
        src_total = activity_counts.get(src, count)
        pct_of_source = (count / src_total) * 100.0 if src_total > 0 else 0.0
        pct_of_all = (count / total_transitions) * 100.0

        transitions_data.append({
            "source_activity": src,
            "target_activity": tgt,
            "transition_count": count,
            "is_loopback_transition": 1 if is_loop else 0,
            "pct_of_source_activity": round(pct_of_source, 2),
            "pct_of_total_transitions": round(pct_of_all, 2),
        })

    transitions_df = pd.DataFrame(transitions_data)

    # Discover variants
    variants = pm4py.get_variants(formatted_df, activity_key="Activity_Name", case_id_key="Case_ID")
    print(f"      Discovered {len(dfg)} DFG transitions across {len(activity_counts)} activities.")
    print(f"      Total transition instances: {total_transitions:,}")
    print(f"      Discovered {len(variants)} unique patient journey variants.")
    print(f"      Start activities: {start_activities}")
    print(f"      End activities: {end_activities}")
    print(f"      Case boundary isolation verified (0 inter-case leaks, 0 transitions from Discharge).")

    return dfg, start_activities, end_activities, transitions_df


def export_dot_model(dfg: dict, start_activities: dict, end_activities: dict, output_path: Path):
    """Export standard Graphviz DOT file using PM4Py visualizer."""
    print(f"[4/5] Generating Graphviz DOT model at {output_path.name}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    gviz = dfg_visualizer.apply(
        dfg,
        activities_count=None,
        parameters={
            dfg_visualizer.Variants.FREQUENCY.value.Parameters.START_ACTIVITIES: start_activities,
            dfg_visualizer.Variants.FREQUENCY.value.Parameters.END_ACTIVITIES: end_activities,
        },
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(gviz.source)
    print(f"      Saved DOT graph model ({len(gviz.source.splitlines())} lines).")


def render_process_map_image(
    dfg: dict,
    start_activities: dict,
    end_activities: dict,
    activity_counts: dict,
    output_path: Path,
):
    """Render high-resolution As-Is Process Map image using matplotlib & networkx.

    Design principles:
      - Left-to-right clinical pathway flow.
      - Start & End milestones distinctly badged.
      - Activity nodes show name and execution frequency.
      - Forward clinical flows rendered with solid blue arrows.
      - Clinical rework loop-backs rendered with curved dashed crimson arrows.
    """
    print(f"[5/5] Rendering publication-quality process map to {output_path.name}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(15, 8.5), dpi=300)
    fig.patch.set_facecolor("#F8FAFC")
    ax.set_facecolor("#F8FAFC")

    # Logical clinical coordinates (X, Y)
    coords = {
        "Registration": (1.8, 4.0),
        "Triage": (4.2, 4.0),
        "Consultation": (6.8, 4.0),
        "Diagnostics": (9.3, 2.2),
        "Treatment": (9.3, 5.8),
        "Discharge": (12.0, 4.0),
    }

    # 1. Draw Start indicator
    ax.annotate(
        "START\n(500)",
        xy=(0.5, 4.0),
        xytext=(0.5, 4.0),
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color="white",
        bbox=dict(boxstyle="circle,pad=0.45", facecolor="#16A34A", edgecolor="#15803D", lw=1.8),
    )
    ax.annotate(
        "",
        xy=(1.15, 4.0),
        xytext=(0.75, 4.0),
        arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#16A34A", mutation_scale=15),
    )

    # 2. Draw End indicator
    ax.annotate(
        "END\n(500)",
        xy=(13.3, 4.0),
        xytext=(13.3, 4.0),
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color="white",
        bbox=dict(boxstyle="circle,pad=0.45", facecolor="#2563EB", edgecolor="#1D4ED8", lw=1.8),
    )
    ax.annotate(
        "",
        xy=(13.05, 4.0),
        xytext=(12.65, 4.0),
        arrowprops=dict(arrowstyle="-|>", lw=2.2, color="#2563EB", mutation_scale=15),
    )

    # 3. Draw Transitions (Edges)
    # Forward edges vs loop-back edges
    for (src, tgt), count in dfg.items():
        x1, y1 = coords[src]
        x2, y2 = coords[tgt]
        is_loop = (src, tgt) in LOOPBACK_TRANSITIONS

        if is_loop:
            # Highlight loopback with curved dashed arc in crimson
            if (src, tgt) == ("Triage", "Registration"):
                rad = -0.42
                label_x = (x1 + x2) / 2
                label_y = 3.20
            elif (src, tgt) == ("Diagnostics", "Consultation"):
                rad = -0.38
                label_x = 7.7
                label_y = 2.45
            elif (src, tgt) == ("Treatment", "Diagnostics"):
                rad = -0.35
                label_x = 10.0
                label_y = 4.0
            else:
                rad = 0.3
                label_x = (x1 + x2) / 2
                label_y = (y1 + y2) / 2

            ax.annotate(
                "",
                xy=(x2, y2),
                xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle="-|>",
                    connectionstyle=f"arc3,rad={rad}",
                    lw=2.2,
                    color="#DC2626",
                    linestyle="--",
                    mutation_scale=18,
                ),
            )
            ax.text(
                label_x,
                label_y,
                f"Loop: {count}",
                ha="center",
                va="center",
                fontsize=8.5,
                fontweight="bold",
                color="#DC2626",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#FEE2E2", edgecolor="#DC2626", lw=1.0),
                zorder=5,
            )
        else:
            # Forward clinical progression
            if (src, tgt) == ("Registration", "Triage"):
                label_pos = (3.0, 4.30)
            elif (src, tgt) == ("Triage", "Consultation"):
                label_pos = (5.5, 4.30)
            elif (src, tgt) == ("Consultation", "Treatment"):
                label_pos = (7.85, 5.25)
            elif (src, tgt) == ("Consultation", "Diagnostics"):
                label_pos = (8.25, 3.45)
            elif (src, tgt) == ("Diagnostics", "Treatment"):
                label_pos = (8.85, 4.0)
            elif (src, tgt) == ("Treatment", "Discharge"):
                label_pos = (10.85, 5.25)
            else:
                label_pos = ((x1 + x2) / 2, (y1 + y2) / 2 + 0.2)

            ax.annotate(
                "",
                xy=(x2, y2),
                xytext=(x1, y1),
                arrowprops=dict(
                    arrowstyle="-|>",
                    lw=2.0,
                    color="#1E3A8A",
                    mutation_scale=16,
                ),
            )
            ax.text(
                label_pos[0],
                label_pos[1],
                f"{count}",
                ha="center",
                va="center",
                fontsize=8.5,
                fontweight="bold",
                color="#1E3A8A",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="#DBEAFE", edgecolor="#93C5FD", lw=0.8),
                zorder=5,
            )

    # 4. Draw Activity Nodes
    for act, (x, y) in coords.items():
        cnt = activity_counts.get(act, 0)
        box = patches.FancyBboxPatch(
            (x - 0.75, y - 0.45),
            1.5,
            0.9,
            boxstyle="round,pad=0.08,rounding_size=0.15",
            facecolor="#FFFFFF",
            edgecolor="#0284C7",
            linewidth=2.2,
            zorder=3,
        )
        ax.add_patch(box)

        ax.text(
            x,
            y + 0.12,
            act,
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color="#0F172A",
            zorder=4,
        )
        ax.text(
            x,
            y - 0.20,
            f"{cnt:,} events",
            ha="center",
            va="center",
            fontsize=8.5,
            fontweight="semibold",
            color="#64748B",
            zorder=4,
        )

    # Title and Clinical KPI Header
    fig.suptitle(
        "CareFlow: As-Is Clinical Pathway Process Map (Discovered via PM4Py)",
        fontsize=15,
        fontweight="bold",
        color="#0F172A",
        y=0.97,
    )
    ax.text(
        0.5,
        0.985,
        "Dataset: 500 Patient Journeys | 3,030 Total Events | 2,530 Transitions | 214 Rework Loop-Backs",
        ha="center",
        va="top",
        transform=ax.transAxes,
        fontsize=10,
        color="#475569",
        fontweight="medium",
    )

    # Legend
    legend_elements = [
        patches.Patch(facecolor="#16A34A", edgecolor="#15803D", label="Pathway Start (100% Registration)"),
        patches.Patch(facecolor="#2563EB", edgecolor="#1D4ED8", label="Pathway End (100% Discharge)"),
        patches.Patch(facecolor="#DBEAFE", edgecolor="#1E3A8A", label="Standard Clinical Forward Transition"),
        patches.Patch(facecolor="#FEE2E2", edgecolor="#DC2626", label="Operational Rework Loop-Back (Repeat Activity)"),
    ]
    ax.legend(
        handles=legend_elements,
        loc="lower center",
        ncol=4,
        frameon=True,
        facecolor="#FFFFFF",
        edgecolor="#CBD5E1",
        fontsize=8.5,
        bbox_to_anchor=(0.5, -0.06),
    )

    ax.set_xlim(-0.2, 14.0)
    ax.set_ylim(0.8, 7.2)
    ax.axis("off")

    plt.savefig(output_path, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"      Rendered high-resolution process map: {output_path} ({os.path.getsize(output_path):,} bytes)")


def main():
    parser = argparse.ArgumentParser(
        description="CareFlow Week 2: Process Discovery & Transition Analysis"
    )
    parser.add_argument(
        "--transitions-only",
        action="store_true",
        help="Only discover and export DFG transitions without generating visualizations",
    )
    args = parser.parse_args()

    print("\n" + "=" * 75)
    print("      CAREFLOW WEEK 2: PROCESS DISCOVERY & VISUALIZATION (PM4PY)")
    print("=" * 75)

    # Step 1: Load and standardize
    std_df = load_and_standardize_event_log(CLEANED_CSV_PATH)

    # Step 2: Validate
    valid_stats = validate_standardized_event_log(std_df)

    # Save standardized event log
    std_df.to_csv(STANDARDIZED_CSV_PATH, index=False)
    print(f"      Saved standardized event log to: {STANDARDIZED_CSV_PATH.name}")

    # Step 3: Discover As-Is process
    activity_counts = std_df["Activity_Name"].value_counts().to_dict()
    dfg, start_activities, end_activities, transitions_df = discover_as_is_process(std_df)

    # Save transitions table
    transitions_df.to_csv(TRANSITIONS_CSV_PATH, index=False)
    print(f"      Exported DFG transitions table to: {TRANSITIONS_CSV_PATH.name}")

    if args.transitions_only:
        print("\n" + "=" * 75)
        print("          TRANSITION DISCOVERY COMPLETE (--transitions-only)")
        print("=" * 75)
        print(f"Standardized Event Log : {STANDARDIZED_CSV_PATH}")
        print(f"Transitions Metric CSV : {TRANSITIONS_CSV_PATH}")
        print("=" * 75 + "\n")
        return

    # Step 4: Export Graphviz DOT file
    export_dot_model(dfg, start_activities, end_activities, PROCESS_MAP_DOT_PATH)

    # Step 5: Render Process Map PNG
    render_process_map_image(dfg, start_activities, end_activities, activity_counts, PROCESS_MAP_PNG_PATH)

    print("\n" + "=" * 75)
    print("               WEEK 2 PROCESS DISCOVERY COMPLETE")
    print("=" * 75)
    print(f"Standardized Event Log : {STANDARDIZED_CSV_PATH}")
    print(f"Transitions Metric CSV : {TRANSITIONS_CSV_PATH}")
    print(f"DOT Language Model     : {PROCESS_MAP_DOT_PATH}")
    print(f"As-Is Process Map PNG  : {PROCESS_MAP_PNG_PATH}")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
