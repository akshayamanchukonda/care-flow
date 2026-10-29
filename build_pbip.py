"""CareFlow: Power BI Project (.pbip) Generator.

Constructs an evaluator-ready Power BI Project containing:
  - CareFlow_Analytics.pbip (root pointer)
  - CareFlow_Analytics.Report/ (definition.pbir, report.json with Navy/Teal/Amber theme, layout, KPI cards, charts)
  - CareFlow_Analytics.SemanticModel/ (definition.pbism, model.bim with 4 tables, relationships, partitions, and 18 DAX measures)

All metrics, column names, and data structures match the verified CareFlow datasets.
"""

from pathlib import Path
import json

REPO_ROOT = Path(__file__).resolve().parent if (Path(__file__).resolve().parent / "reports").exists() else Path(__file__).resolve().parent.parent
REPORTS_DIR = REPO_ROOT / "reports"
PBIP_NAME = "CareFlow_Analytics"
PROJECT_DIR = REPORTS_DIR / PBIP_NAME

PBIP_FILE = REPORTS_DIR / f"{PBIP_NAME}.pbip"
REPORT_DIR = REPORTS_DIR / f"{PBIP_NAME}.Report"
SEMANTIC_DIR = REPORTS_DIR / f"{PBIP_NAME}.SemanticModel"

DATA_DIR = REPO_ROOT / "data" / "processed"
CSV_EVENTS = (DATA_DIR / "cleaned_healthcare_event_log_v2.csv").as_posix()
CSV_TRANSITIONS = (DATA_DIR / "visit_transitions_detail.csv").as_posix()
CSV_CONFORMANCE = (DATA_DIR / "conformance_analysis.csv").as_posix()
CSV_BENCHMARK = (DATA_DIR / "transition_time_analysis.csv").as_posix()

def create_pbip_entry() -> dict:
    return {
        "version": "1.0",
        "artifacts": [
            {
                "report": {
                    "path": f"{PBIP_NAME}.Report"
                }
            }
        ],
        "settings": {
            "enableAutoRecovery": True
        }
    }

def create_pbir_definition() -> dict:
    return {
        "version": "1.0",
        "datasetReference": {
            "byPath": {
                "path": f"../{PBIP_NAME}.SemanticModel"
            },
            "byConnection": None
        }
    }

def create_pbism_definition() -> dict:
    return {
        "version": "1.0"
    }

def create_model_bim() -> dict:
    """Builds Tabular Model Scripting Language (TMSL) model.bim."""
    
    # M Expression for Events table
    m_events = f"""let
    Source = Csv.Document(File.Contents("{CSV_EVENTS}"), [Delimiter=",", Columns=10, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{{{ "case_id", type text }}, {{ "activity_name", type text }}, {{ "event_timestamp", type datetime }}, {{ "activity_sequence", Int64.Type }}, {{ "is_loopback", Int64.Type }}, {{ "patient_id", type text }}, {{ "event_id", type text }}, {{ "department", type text }}, {{ "status", type text }}, {{ "waiting_time_minutes", Int64.Type }}}})
in
    #"Changed Type" """

    # M Expression for Transitions table
    m_transitions = f"""let
    Source = Csv.Document(File.Contents("{CSV_TRANSITIONS}"), [Delimiter=",", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{{{ "case_id", type text }}, {{ "patient_id", type text }}, {{ "from_activity", type text }}, {{ "to_activity", type text }}, {{ "from_timestamp", type datetime }}, {{ "to_timestamp", type datetime }}, {{ "transition_time_minutes", type number }}, {{ "is_rework_loop", Int64.Type }}}}),
    #"Added Pathway Column" = Table.AddColumn(#"Changed Type", "pathway", each [from_activity] & " -> " & [to_activity], type text)
in
    #"Added Pathway Column" """

    # M Expression for Visits Conformance table
    m_conformance = f"""let
    Source = Csv.Document(File.Contents("{CSV_CONFORMANCE}"), [Delimiter=",", Columns=14, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{{{ "case_id", type text }}, {{ "patient_id", type text }}, {{ "department", type text }}, {{ "is_conformant", Int64.Type }}, {{ "conformance_status", type text }}, {{ "conformance_category", type text }}, {{ "trace_pattern", type text }}, {{ "event_count", Int64.Type }}, {{ "transition_count", Int64.Type }}, {{ "rework_loop_count", Int64.Type }}, {{ "primary_deviation", type text }}, {{ "trace_fitness", type number }}, {{ "journey_duration_minutes", type number }}, {{ "total_waiting_minutes", Int64.Type }}}})
in
    #"Changed Type" """

    # M Expression for Benchmark table
    m_benchmark = f"""let
    Source = Csv.Document(File.Contents("{CSV_BENCHMARK}"), [Delimiter=",", Columns=13, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{{{ "from_activity", type text }}, {{ "to_activity", type text }}, {{ "transition_count", Int64.Type }}, {{ "is_loopback", Int64.Type }}, {{ "pct_of_total_transitions", type number }}, {{ "avg_transition_time_minutes", type number }}, {{ "median_transition_time_minutes", type number }}, {{ "std_dev_minutes", type number }}, {{ "min_transition_time_minutes", type number }}, {{ "max_transition_time_minutes", type number }}, {{ "p25_minutes", type number }}, {{ "p75_minutes", type number }}, {{ "iqr_minutes", type number }}}}),
    #"Added Pathway" = Table.AddColumn(#"Changed Type", "pathway", each [from_activity] & " -> " & [to_activity], type text)
in
    #"Added Pathway" """

    tables = [
        {
            "name": "Events",
            "columns": [
                {"name": "event_id", "dataType": "string", "sourceColumn": "event_id"},
                {"name": "case_id", "dataType": "string", "sourceColumn": "case_id"},
                {"name": "patient_id", "dataType": "string", "sourceColumn": "patient_id"},
                {"name": "activity_name", "dataType": "string", "sourceColumn": "activity_name"},
                {"name": "activity_sequence", "dataType": "int64", "sourceColumn": "activity_sequence"},
                {"name": "event_timestamp", "dataType": "dateTime", "sourceColumn": "event_timestamp"},
                {"name": "department", "dataType": "string", "sourceColumn": "department"},
                {"name": "status", "dataType": "string", "sourceColumn": "status"},
                {"name": "waiting_time_minutes", "dataType": "int64", "sourceColumn": "waiting_time_minutes"},
                {"name": "is_loopback", "dataType": "int64", "sourceColumn": "is_loopback"},
            ],
            "partitions": [
                {
                    "name": "Events_Partition",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": [line for line in m_events.split("\n")]
                    }
                }
            ]
        },
        {
            "name": "Transitions",
            "columns": [
                {"name": "case_id", "dataType": "string", "sourceColumn": "case_id"},
                {"name": "patient_id", "dataType": "string", "sourceColumn": "patient_id"},
                {"name": "from_activity", "dataType": "string", "sourceColumn": "from_activity"},
                {"name": "to_activity", "dataType": "string", "sourceColumn": "to_activity"},
                {"name": "pathway", "dataType": "string", "sourceColumn": "pathway"},
                {"name": "from_timestamp", "dataType": "dateTime", "sourceColumn": "from_timestamp"},
                {"name": "to_timestamp", "dataType": "dateTime", "sourceColumn": "to_timestamp"},
                {"name": "transition_time_minutes", "dataType": "double", "sourceColumn": "transition_time_minutes"},
                {"name": "is_rework_loop", "dataType": "int64", "sourceColumn": "is_rework_loop"},
            ],
            "partitions": [
                {
                    "name": "Transitions_Partition",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": [line for line in m_transitions.split("\n")]
                    }
                }
            ]
        },
        {
            "name": "Visits_Conformance",
            "columns": [
                {"name": "case_id", "dataType": "string", "sourceColumn": "case_id"},
                {"name": "patient_id", "dataType": "string", "sourceColumn": "patient_id"},
                {"name": "department", "dataType": "string", "sourceColumn": "department"},
                {"name": "is_conformant", "dataType": "int64", "sourceColumn": "is_conformant"},
                {"name": "conformance_status", "dataType": "string", "sourceColumn": "conformance_status"},
                {"name": "conformance_category", "dataType": "string", "sourceColumn": "conformance_category"},
                {"name": "trace_pattern", "dataType": "string", "sourceColumn": "trace_pattern"},
                {"name": "event_count", "dataType": "int64", "sourceColumn": "event_count"},
                {"name": "transition_count", "dataType": "int64", "sourceColumn": "transition_count"},
                {"name": "rework_loop_count", "dataType": "int64", "sourceColumn": "rework_loop_count"},
                {"name": "primary_deviation", "dataType": "string", "sourceColumn": "primary_deviation"},
                {"name": "trace_fitness", "dataType": "double", "sourceColumn": "trace_fitness"},
                {"name": "journey_duration_minutes", "dataType": "double", "sourceColumn": "journey_duration_minutes"},
                {"name": "total_waiting_minutes", "dataType": "int64", "sourceColumn": "total_waiting_minutes"},
            ],
            "partitions": [
                {
                    "name": "Visits_Conformance_Partition",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": [line for line in m_conformance.split("\n")]
                    }
                }
            ]
        },
        {
            "name": "Pathway_Benchmark",
            "columns": [
                {"name": "from_activity", "dataType": "string", "sourceColumn": "from_activity"},
                {"name": "to_activity", "dataType": "string", "sourceColumn": "to_activity"},
                {"name": "pathway", "dataType": "string", "sourceColumn": "pathway"},
                {"name": "transition_count", "dataType": "int64", "sourceColumn": "transition_count"},
                {"name": "is_loopback", "dataType": "int64", "sourceColumn": "is_loopback"},
                {"name": "pct_of_total_transitions", "dataType": "double", "sourceColumn": "pct_of_total_transitions"},
                {"name": "avg_transition_time_minutes", "dataType": "double", "sourceColumn": "avg_transition_time_minutes"},
                {"name": "median_transition_time_minutes", "dataType": "double", "sourceColumn": "median_transition_time_minutes"},
                {"name": "std_dev_minutes", "dataType": "double", "sourceColumn": "std_dev_minutes"},
                {"name": "min_transition_time_minutes", "dataType": "double", "sourceColumn": "min_transition_time_minutes"},
                {"name": "max_transition_time_minutes", "dataType": "double", "sourceColumn": "max_transition_time_minutes"},
                {"name": "iqr_minutes", "dataType": "double", "sourceColumn": "iqr_minutes"},
            ],
            "partitions": [
                {
                    "name": "Pathway_Benchmark_Partition",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": [line for line in m_benchmark.split("\n")]
                    }
                }
            ]
        },
        {
            "name": "CareFlow_Measures",
            "partitions": [
                {
                    "name": "CareFlow_Measures_Partition",
                    "mode": "import",
                    "source": {
                        "type": "calculated",
                        "expression": "ROW(\"Measure_Group\", \"CareFlow Operational Metrics\")"
                    }
                }
            ],
            "columns": [
                {
                    "name": "Measure_Group",
                    "dataType": "string",
                    "isDataTypeInferred": True,
                    "isHidden": True,
                    "sourceColumn": "[Measure_Group]",
                    "type": "calculatedTableColumn"
                }
            ],
            "measures": [
                {
                    "name": "Total Events",
                    "expression": "COUNTROWS('Events')",
                    "formatString": "#,0"
                },
                {
                    "name": "Total Visits",
                    "expression": "DISTINCTCOUNT('Events'[case_id])",
                    "formatString": "#,0"
                },
                {
                    "name": "Unique Patients",
                    "expression": "DISTINCTCOUNT('Events'[patient_id])",
                    "formatString": "#,0"
                },
                {
                    "name": "Conformant Visits",
                    "expression": "CALCULATE(COUNTROWS('Visits_Conformance'), 'Visits_Conformance'[is_conformant] = 1)",
                    "formatString": "#,0"
                },
                {
                    "name": "Conformance Rate",
                    "expression": "DIVIDE([Conformant Visits], [Total Visits], 0)",
                    "formatString": "0.0%"
                },
                {
                    "name": "Rework Visits",
                    "expression": "CALCULATE(COUNTROWS('Visits_Conformance'), 'Visits_Conformance'[is_conformant] = 0)",
                    "formatString": "#,0"
                },
                {
                    "name": "Rework Rate",
                    "expression": "DIVIDE([Rework Visits], [Total Visits], 0)",
                    "formatString": "0.0%"
                },
                {
                    "name": "Total Transitions",
                    "expression": "COUNTROWS('Transitions')",
                    "formatString": "#,0"
                },
                {
                    "name": "Rework Loop Transitions",
                    "expression": "CALCULATE(COUNTROWS('Transitions'), 'Transitions'[is_rework_loop] = 1)",
                    "formatString": "#,0"
                },
                {
                    "name": "Rework Transition Pct",
                    "expression": "DIVIDE([Rework Loop Transitions], [Total Transitions], 0)",
                    "formatString": "0.0%"
                },
                {
                    "name": "Avg Journey Duration Mins",
                    "expression": "AVERAGE('Visits_Conformance'[journey_duration_minutes])",
                    "formatString": "0.0"
                },
                {
                    "name": "Median Journey Duration Mins",
                    "expression": "MEDIAN('Visits_Conformance'[journey_duration_minutes])",
                    "formatString": "0.0"
                },
                {
                    "name": "Avg Waiting Time Mins",
                    "expression": "AVERAGE('Events'[waiting_time_minutes])",
                    "formatString": "0.0"
                },
                {
                    "name": "Median Waiting Time Mins",
                    "expression": "MEDIAN('Events'[waiting_time_minutes])",
                    "formatString": "0.0"
                },
                {
                    "name": "Conformant Avg Journey Mins",
                    "expression": "CALCULATE(AVERAGE('Visits_Conformance'[journey_duration_minutes]), 'Visits_Conformance'[is_conformant] = 1)",
                    "formatString": "0.0"
                },
                {
                    "name": "Non-Conformant Avg Journey Mins",
                    "expression": "CALCULATE(AVERAGE('Visits_Conformance'[journey_duration_minutes]), 'Visits_Conformance'[is_conformant] = 0)",
                    "formatString": "0.0"
                },
                {
                    "name": "Delay Penalty Mins",
                    "expression": "[Non-Conformant Avg Journey Mins] - [Conformant Avg Journey Mins]",
                    "formatString": "+0.0;-0.0;0.0"
                },
                {
                    "name": "Delay Penalty Pct",
                    "expression": "DIVIDE([Delay Penalty Mins], [Conformant Avg Journey Mins], 0)",
                    "formatString": "0.0%"
                }
            ]
        }
    ]

    relationships = [
        {
            "name": "rel_events_visits",
            "fromTable": "Events",
            "fromColumn": "case_id",
            "toTable": "Visits_Conformance",
            "toColumn": "case_id",
            "crossFilteringBehavior": "bothDirections"
        },
        {
            "name": "rel_transitions_visits",
            "fromTable": "Transitions",
            "fromColumn": "case_id",
            "toTable": "Visits_Conformance",
            "toColumn": "case_id",
            "crossFilteringBehavior": "bothDirections"
        }
    ]

    return {
        "name": "CareFlow_Analytics",
        "compatibilityLevel": 1550,
        "model": {
            "culture": "en-US",
            "dataAccessOptions": {
                "legacyRedirects": True,
                "returnErrorValuesAsNull": True
            },
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "relationships": relationships,
            "tables": tables
        }
    }

def make_card(name: str, x: float, y: float, width: float, height: float, table: str, measure: str, title: str = None, tab_order: int = 0) -> dict:
    """Builds a schema-valid Power BI Card visualContainer."""
    qref = f"{table}.{measure}"
    sv = {
        "visualType": "card",
        "projections": {
            "Values": [{"queryRef": qref}]
        },
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": "t", "Entity": table, "Type": 0}],
            "Select": [{
                "Measure": {
                    "Expression": {"SourceRef": {"Source": "t"}},
                    "Property": measure
                },
                "Name": qref,
                "NativeReferenceName": measure
            }]
        }
    }
    if title:
        sv["objects"] = {
            "title": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}}
                }
            }]
        }
    cfg = {
        "name": name,
        "layouts": [{
            "id": 0,
            "position": {
                "x": float(x),
                "y": float(y),
                "z": 0.0,
                "width": float(width),
                "height": float(height),
                "tabOrder": tab_order
            }
        }],
        "singleVisual": sv
    }
    return {
        "x": float(x),
        "y": float(y),
        "z": 0.0,
        "width": float(width),
        "height": float(height),
        "config": json.dumps(cfg)
    }

def make_chart(name: str, x: float, y: float, width: float, height: float, vtype: str, cat_tbl: str, cat_col: str, val_tbl: str, val_meas: str, title: str = None, tab_order: int = 0) -> dict:
    """Builds a schema-valid clusteredBarChart or clusteredColumnChart visualContainer."""
    cat_ref = f"{cat_tbl}.{cat_col}"
    val_ref = f"{val_tbl}.{val_meas}"
    sv = {
        "visualType": vtype,
        "projections": {
            "Category": [{"queryRef": cat_ref, "active": True}],
            "Y": [{"queryRef": val_ref}]
        },
        "prototypeQuery": {
            "Version": 2,
            "From": [
                {"Name": "c", "Entity": cat_tbl, "Type": 0},
                {"Name": "m", "Entity": val_tbl, "Type": 0}
            ],
            "Select": [
                {
                    "Column": {
                        "Expression": {"SourceRef": {"Source": "c"}},
                        "Property": cat_col
                    },
                    "Name": cat_ref,
                    "NativeReferenceName": cat_col
                },
                {
                    "Measure": {
                        "Expression": {"SourceRef": {"Source": "m"}},
                        "Property": val_meas
                    },
                    "Name": val_ref,
                    "NativeReferenceName": val_meas
                }
            ]
        }
    }
    if title:
        sv["objects"] = {
            "title": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}}
                }
            }]
        }
    cfg = {
        "name": name,
        "layouts": [{
            "id": 0,
            "position": {
                "x": float(x),
                "y": float(y),
                "z": 0.0,
                "width": float(width),
                "height": float(height),
                "tabOrder": tab_order
            }
        }],
        "singleVisual": sv
    }
    return {
        "x": float(x),
        "y": float(y),
        "z": 0.0,
        "width": float(width),
        "height": float(height),
        "config": json.dumps(cfg)
    }

def make_table(name: str, x: float, y: float, width: float, height: float, items: list, title: str = None, tab_order: int = 0) -> dict:
    """Builds a schema-valid tableEx visualContainer."""
    proj_vals = []
    from_map = {}
    select_items = []
    for idx, (tbl, prop, is_m) in enumerate(items):
        if tbl not in from_map:
            from_map[tbl] = f"t{len(from_map)}"
        src = from_map[tbl]
        qref = f"{tbl}.{prop}"
        proj_vals.append({"queryRef": qref})
        if is_m:
            select_items.append({
                "Measure": {
                    "Expression": {"SourceRef": {"Source": src}},
                    "Property": prop
                },
                "Name": qref,
                "NativeReferenceName": prop
            })
        else:
            select_items.append({
                "Column": {
                    "Expression": {"SourceRef": {"Source": src}},
                    "Property": prop
                },
                "Name": qref,
                "NativeReferenceName": prop
            })
    from_list = [{"Name": alias, "Entity": tbl, "Type": 0} for tbl, alias in from_map.items()]
    sv = {
        "visualType": "tableEx",
        "projections": {"Values": proj_vals},
        "prototypeQuery": {
            "Version": 2,
            "From": from_list,
            "Select": select_items
        }
    }
    if title:
        sv["objects"] = {
            "title": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}}
                }
            }]
        }
    cfg = {
        "name": name,
        "layouts": [{
            "id": 0,
            "position": {
                "x": float(x),
                "y": float(y),
                "z": 0.0,
                "width": float(width),
                "height": float(height),
                "tabOrder": tab_order
            }
        }],
        "singleVisual": sv
    }
    return {
        "x": float(x),
        "y": float(y),
        "z": 0.0,
        "width": float(width),
        "height": float(height),
        "config": json.dumps(cfg)
    }

def make_slicer(name: str, x: float, y: float, width: float, height: float, table: str, column: str, title: str = None, tab_order: int = 0) -> dict:
    """Builds a schema-valid slicer visualContainer."""
    qref = f"{table}.{column}"
    sv = {
        "visualType": "slicer",
        "projections": {
            "Values": [{"queryRef": qref, "active": True}]
        },
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": "s", "Entity": table, "Type": 0}],
            "Select": [{
                "Column": {
                    "Expression": {"SourceRef": {"Source": "s"}},
                    "Property": column
                },
                "Name": qref,
                "NativeReferenceName": column
            }]
        }
    }
    if title:
        sv["objects"] = {
            "title": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}}
                }
            }]
        }
    cfg = {
        "name": name,
        "layouts": [{
            "id": 0,
            "position": {
                "x": float(x),
                "y": float(y),
                "z": 0.0,
                "width": float(width),
                "height": float(height),
                "tabOrder": tab_order
            }
        }],
        "singleVisual": sv
    }
    return {
        "x": float(x),
        "y": float(y),
        "z": 0.0,
        "width": float(width),
        "height": float(height),
        "config": json.dumps(cfg)
    }

def create_report_json() -> dict:
    """Builds report.json with Navy, Teal, Amber theme and real visual containers across 3 pages."""
    theme = {
        "name": "CareFlow Healthcare Theme",
        "dataColors": [
            "#1E3A8A",  # Navy (Primary)
            "#0D9488",  # Teal (Accent)
            "#0284C7",  # Sky Blue (Secondary)
            "#D97706",  # Amber (Bottleneck/Warning)
            "#E11D48",  # Coral/Red (Rework loop)
            "#059669",  # Emerald (Conformant)
            "#64748B",  # Slate
            "#7C3AED"   # Purple
        ],
        "background": "#FFFFFF",
        "foreground": "#0F172A",
        "tableAccent": "#1E3A8A"
    }

    config_dict = {
        "version": "5.59",
        "themeCollection": {
            "baseTheme": {
                "name": "CareFlowTheme",
                "version": "5.59",
                "type": 2
            }
        },
        "activeSectionIndex": 0,
        "defaultDrillFilterOtherVisuals": True
    }

    # Page 1: Executive Overview & KPIs (5 Cards + 2 Charts + 2 Slicers = 9 visuals)
    visuals_page_1 = [
        make_card("card_total_events", 20, 25, 230, 115, "CareFlow_Measures", "Total Events", "Total Clinical Events", 1),
        make_card("card_total_visits", 270, 25, 230, 115, "CareFlow_Measures", "Total Visits", "Total Patient Visits", 2),
        make_card("card_unique_patients", 520, 25, 230, 115, "CareFlow_Measures", "Unique Patients", "Unique Patients", 3),
        make_card("card_conformance_rate", 770, 25, 230, 115, "CareFlow_Measures", "Conformance Rate", "Pathway Conformance Rate", 4),
        make_card("card_rework_rate", 1020, 25, 240, 115, "CareFlow_Measures", "Rework Rate", "Operational Rework Rate", 5),
        make_chart("chart_activity_volumes", 20, 160, 480, 530, "clusteredBarChart", "Events", "activity_name", "CareFlow_Measures", "Total Events", "Clinical Activity Volumes (Total Events)", 6),
        make_chart("chart_conformance_cohorts", 520, 160, 480, 530, "clusteredColumnChart", "Visits_Conformance", "conformance_category", "CareFlow_Measures", "Total Visits", "Patient Volume by Conformance Cohort", 7),
        make_slicer("slicer_department", 1020, 160, 240, 255, "Events", "department", "Filter: Department", 8),
        make_slicer("slicer_conformance_status", 1020, 435, 240, 255, "Visits_Conformance", "conformance_status", "Filter: Conformance Status", 9)
    ]

    # Page 2: Process Flow & Rework Analysis (4 Cards + 1 Latency Table + 1 Chart = 6 visuals)
    visuals_page_2 = [
        make_card("card_total_transitions", 20, 25, 290, 115, "CareFlow_Measures", "Total Transitions", "Total Handover Transitions", 1),
        make_card("card_rework_transitions", 330, 25, 290, 115, "CareFlow_Measures", "Rework Loop Transitions", "Rework Loop Transitions", 2),
        make_card("card_rework_share", 640, 25, 290, 115, "CareFlow_Measures", "Rework Transition Pct", "Rework Transition Share", 3),
        make_card("card_median_journey", 950, 25, 310, 115, "CareFlow_Measures", "Median Journey Duration Mins", "Median Journey Duration (min)", 4),
        make_table("table_transition_latency", 20, 160, 650, 530, [
            ("Pathway_Benchmark", "pathway", False),
            ("Pathway_Benchmark", "transition_count", False),
            ("Pathway_Benchmark", "median_transition_time_minutes", False),
            ("Pathway_Benchmark", "avg_transition_time_minutes", False),
            ("Pathway_Benchmark", "iqr_minutes", False)
        ], "Pathway Transition Latency Benchmark (min)", 5),
        make_chart("chart_rework_loops", 690, 160, 570, 530, "clusteredBarChart", "Transitions", "pathway", "CareFlow_Measures", "Rework Loop Transitions", "Rework Loop Pathway Volume", 6)
    ]

    # Page 3: Bottlenecks & Waiting Times (4 Cards + 2 Charts = 6 visuals)
    visuals_page_3 = [
        make_card("card_avg_wait", 20, 25, 290, 115, "CareFlow_Measures", "Avg Waiting Time Mins", "Average Queue Wait (min)", 1),
        make_card("card_median_wait", 330, 25, 290, 115, "CareFlow_Measures", "Median Waiting Time Mins", "Median Queue Wait (min)", 2),
        make_card("card_delay_penalty", 640, 25, 290, 115, "CareFlow_Measures", "Delay Penalty Mins", "Non-Conformance Delay Penalty (min)", 3),
        make_card("card_delay_penalty_pct", 950, 25, 310, 115, "CareFlow_Measures", "Delay Penalty Pct", "Delay Penalty Percentage", 4),
        make_chart("chart_stage_wait", 20, 160, 600, 530, "clusteredColumnChart", "Events", "activity_name", "CareFlow_Measures", "Avg Waiting Time Mins", "Queue Dwell Time by Clinical Stage (Avg min)", 5),
        make_chart("chart_cohort_los", 640, 160, 620, 530, "clusteredColumnChart", "Visits_Conformance", "conformance_category", "CareFlow_Measures", "Avg Journey Duration Mins", "Hospital Length of Stay by Conformance Cohort (Avg min)", 6)
    ]

    sections = [
        {
            "name": "Section_Overview",
            "displayName": "Executive Overview & KPIs",
            "filters": "[]",
            "ordinal": 0,
            "visualContainers": visuals_page_1,
            "width": 1280.0,
            "height": 720.0
        },
        {
            "name": "Section_Transitions",
            "displayName": "Process Flow & Rework Analysis",
            "filters": "[]",
            "ordinal": 1,
            "visualContainers": visuals_page_2,
            "width": 1280.0,
            "height": 720.0
        },
        {
            "name": "Section_Bottlenecks",
            "displayName": "Bottlenecks & Waiting Times",
            "filters": "[]",
            "ordinal": 2,
            "visualContainers": visuals_page_3,
            "width": 1280.0,
            "height": 720.0
        }
    ]

    return {
        "config": json.dumps(config_dict),
        "layoutOptimization": 0,
        "theme": theme,
        "sections": sections
    }

def main():
    print("=" * 70)
    print("   CAREFLOW: GENERATING POWER BI PROJECT (.PBIP) ARTIFACTS")
    print("=" * 70)

    # Ensure directories exist
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SEMANTIC_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Root .pbip file
    print(f"[1/5] Writing {PBIP_FILE.name}...")
    with open(PBIP_FILE, "w", encoding="utf-8") as f:
        json.dump(create_pbip_entry(), f, indent=2)

    # 2. Report definition.pbir
    pbir_file = REPORT_DIR / "definition.pbir"
    print(f"[2/5] Writing {pbir_file.name}...")
    with open(pbir_file, "w", encoding="utf-8") as f:
        json.dump(create_pbir_definition(), f, indent=2)

    # 3. Report report.json
    report_json_file = REPORT_DIR / "report.json"
    print(f"[3/5] Writing {report_json_file.name}...")
    with open(report_json_file, "w", encoding="utf-8") as f:
        json.dump(create_report_json(), f, indent=2)

    # 4. SemanticModel definition.pbism
    pbism_file = SEMANTIC_DIR / "definition.pbism"
    print(f"[4/5] Writing {pbism_file.name}...")
    with open(pbism_file, "w", encoding="utf-8") as f:
        json.dump(create_pbism_definition(), f, indent=2)

    # 5. SemanticModel model.bim
    model_bim_file = SEMANTIC_DIR / "model.bim"
    print(f"[5/5] Writing {model_bim_file.name}...")
    with open(model_bim_file, "w", encoding="utf-8") as f:
        json.dump(create_model_bim(), f, indent=2)

    print("\n" + "=" * 70)
    print("   POWER BI PROJECT GENERATED SUCCESSFULLY!")
    print(f"   Project File : {PBIP_FILE}")
    print(f"   Report Dir   : {REPORT_DIR}")
    print(f"   Semantic Dir : {SEMANTIC_DIR}")
    print("=" * 70)

if __name__ == "__main__":
    main()

