"""CareFlow: Enterprise Power BI Project (.pbip) Generator.

Constructs an evaluator-ready, submission-standard Power BI Project containing:
  - CareFlow_Analytics.pbip (root pointer)
  - CareFlow_Analytics.Report/ (definition.pbir, report.json with 6 pages, 62 visuals, .platform, theme)
  - CareFlow_Analytics.SemanticModel/ (definition.pbism, model.bim with 6 tables, 24 DAX measures, relationships, .platform)
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent if Path(__file__).resolve().parent.name == "scratch" else Path(__file__).resolve().parent
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
CSV_VARIANTS = (DATA_DIR / "conformance_summary.csv").as_posix()


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


def create_report_platform() -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {
            "type": "Report",
            "displayName": PBIP_NAME
        },
        "config": {
            "version": "2.0",
            "logicalId": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d"
        }
    }


def create_semantic_platform() -> dict:
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {
            "type": "SemanticModel",
            "displayName": PBIP_NAME
        },
        "config": {
            "version": "2.0",
            "logicalId": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e"
        }
    }


def create_theme_file_dict() -> dict:
    return {
        "name": "CareFlowTheme",
        "dataColors": [
            "#1E3A8A",  # Deep Navy (Primary brand)
            "#0D9488",  # Teal Accent (Positive / Conformance)
            "#0284C7",  # Sky Blue (Secondary / Outpatient)
            "#D97706",  # Amber Bottleneck (Warning / Delay)
            "#E11D48",  # Coral / Rework (Critical loop-backs)
            "#10B981",  # Emerald (Ideal pathway)
            "#6366F1",  # Indigo (Diagnostics)
            "#F59E0B"   # Warm Gold (Quartiles)
        ],
        "background": "#FFFFFF",
        "foreground": "#1E293B",
        "tableAccent": "#1E3A8A"
    }


def create_model_bim() -> dict:
    """Builds Tabular Model Scripting Language (TMSL) model.bim with 6 tables and 24 measures."""
    m_events = f"""let
    Source = Csv.Document(File.Contents("{CSV_EVENTS}"), [Delimiter=",", Columns=10, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{{{ "case_id", type text }}, {{ "activity_name", type text }}, {{ "event_timestamp", type datetime }}, {{ "activity_sequence", Int64.Type }}, {{ "is_loopback", Int64.Type }}, {{ "patient_id", type text }}, {{ "event_id", type text }}, {{ "department", type text }}, {{ "status", type text }}, {{ "waiting_time_minutes", Int64.Type }}}})
in
    #"Changed Type" """

    m_transitions = f"""let
    Source = Csv.Document(File.Contents("{CSV_TRANSITIONS}"), [Delimiter=",", Columns=8, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{{{ "case_id", type text }}, {{ "patient_id", type text }}, {{ "from_activity", type text }}, {{ "to_activity", type text }}, {{ "from_timestamp", type datetime }}, {{ "to_timestamp", type datetime }}, {{ "transition_time_minutes", type number }}, {{ "is_rework_loop", Int64.Type }}}}),
    #"Added Pathway Column" = Table.AddColumn(#"Changed Type", "pathway", each [from_activity] & " -> " & [to_activity], type text)
in
    #"Added Pathway Column" """

    m_conformance = f"""let
    Source = Csv.Document(File.Contents("{CSV_CONFORMANCE}"), [Delimiter=",", Columns=14, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{{{ "case_id", type text }}, {{ "patient_id", type text }}, {{ "department", type text }}, {{ "is_conformant", Int64.Type }}, {{ "conformance_status", type text }}, {{ "conformance_category", type text }}, {{ "trace_pattern", type text }}, {{ "event_count", Int64.Type }}, {{ "transition_count", Int64.Type }}, {{ "rework_loop_count", Int64.Type }}, {{ "primary_deviation", type text }}, {{ "trace_fitness", type number }}, {{ "journey_duration_minutes", type number }}, {{ "total_waiting_minutes", Int64.Type }}}})
in
    #"Changed Type" """

    m_benchmark = f"""let
    Source = Csv.Document(File.Contents("{CSV_BENCHMARK}"), [Delimiter=",", Columns=13, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{{{ "from_activity", type text }}, {{ "to_activity", type text }}, {{ "transition_count", Int64.Type }}, {{ "is_loopback", Int64.Type }}, {{ "pct_of_total_transitions", type number }}, {{ "avg_transition_time_minutes", type number }}, {{ "median_transition_time_minutes", type number }}, {{ "std_dev_minutes", type number }}, {{ "min_transition_time_minutes", type number }}, {{ "max_transition_time_minutes", type number }}, {{ "p25_minutes", type number }}, {{ "p75_minutes", type number }}, {{ "iqr_minutes", type number }}}}),
    #"Added Pathway" = Table.AddColumn(#"Changed Type", "pathway", each [from_activity] & " -> " & [to_activity], type text)
in
    #"Added Pathway" """

    m_variants = f"""let
    Source = Csv.Document(File.Contents("{CSV_VARIANTS}"), [Delimiter=",", Columns=11, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers", {{{{ "variant_id", type text }}, {{ "trace_pattern", type text }}, {{ "is_conformant", Int64.Type }}, {{ "conformance_category", type text }}, {{ "case_count", Int64.Type }}, {{ "pct_of_total_cases", type number }}, {{ "rework_loops_per_case", Int64.Type }}, {{ "primary_deviation", type text }}, {{ "avg_journey_minutes", type number }}, {{ "median_journey_minutes", type number }}, {{ "avg_waiting_minutes", type number }}}})
in
    #"Changed Type" """

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
            "name": "Variants_Summary",
            "columns": [
                {"name": "variant_id", "dataType": "string", "sourceColumn": "variant_id"},
                {"name": "trace_pattern", "dataType": "string", "sourceColumn": "trace_pattern"},
                {"name": "is_conformant", "dataType": "int64", "sourceColumn": "is_conformant"},
                {"name": "conformance_category", "dataType": "string", "sourceColumn": "conformance_category"},
                {"name": "case_count", "dataType": "int64", "sourceColumn": "case_count"},
                {"name": "pct_of_total_cases", "dataType": "double", "sourceColumn": "pct_of_total_cases"},
                {"name": "rework_loops_per_case", "dataType": "int64", "sourceColumn": "rework_loops_per_case"},
                {"name": "primary_deviation", "dataType": "string", "sourceColumn": "primary_deviation"},
                {"name": "avg_journey_minutes", "dataType": "double", "sourceColumn": "avg_journey_minutes"},
                {"name": "median_journey_minutes", "dataType": "double", "sourceColumn": "median_journey_minutes"},
                {"name": "avg_waiting_minutes", "dataType": "double", "sourceColumn": "avg_waiting_minutes"},
            ],
            "partitions": [
                {
                    "name": "Variants_Summary_Partition",
                    "mode": "import",
                    "source": {
                        "type": "m",
                        "expression": [line for line in m_variants.split("\n")]
                    }
                }
            ]
        },
        {
            "name": "CareFlow_Measures",
            "columns": [
                {
                    "name": "Measure_Group",
                    "dataType": "string",
                    "type": "calculatedTableColumn",
                    "sourceColumn": "[Value]",
                    "isHidden": True
                }
            ],
            "partitions": [
                {
                    "name": "CareFlow_Measures_Partition",
                    "mode": "import",
                    "source": {
                        "type": "calculated",
                        "expression": 'ROW("Measure_Group", "CareFlow Operational Metrics")'
                    }
                }
            ],
            "measures": [
                {"name": "Total Events", "expression": "COUNTROWS('Events')", "formatString": "#,0"},
                {"name": "Total Visits", "expression": "DISTINCTCOUNT('Events'[case_id])", "formatString": "#,0"},
                {"name": "Unique Patients", "expression": "DISTINCTCOUNT('Events'[patient_id])", "formatString": "#,0"},
                {"name": "Conformant Visits", "expression": "CALCULATE(COUNTROWS('Visits_Conformance'), 'Visits_Conformance'[is_conformant] = 1)", "formatString": "#,0"},
                {"name": "Conformance Rate", "expression": "DIVIDE([Conformant Visits], [Total Visits], 0)", "formatString": "0.0%"},
                {"name": "Rework Visits", "expression": "CALCULATE(COUNTROWS('Visits_Conformance'), 'Visits_Conformance'[is_conformant] = 0)", "formatString": "#,0"},
                {"name": "Rework Rate", "expression": "DIVIDE([Rework Visits], [Total Visits], 0)", "formatString": "0.0%"},
                {"name": "Total Transitions", "expression": "COUNTROWS('Transitions')", "formatString": "#,0"},
                {"name": "Rework Loop Transitions", "expression": "CALCULATE(COUNTROWS('Transitions'), 'Transitions'[is_rework_loop] = 1)", "formatString": "#,0"},
                {"name": "Rework Transition Pct", "expression": "DIVIDE([Rework Loop Transitions], [Total Transitions], 0)", "formatString": "0.0%"},
                {"name": "Avg Journey Duration Mins", "expression": "AVERAGE('Visits_Conformance'[journey_duration_minutes])", "formatString": "0.0"},
                {"name": "Median Journey Duration Mins", "expression": "MEDIAN('Visits_Conformance'[journey_duration_minutes])", "formatString": "0.0"},
                {"name": "Avg Waiting Time Mins", "expression": "AVERAGE('Events'[waiting_time_minutes])", "formatString": "0.0"},
                {"name": "Median Waiting Time Mins", "expression": "MEDIAN('Events'[waiting_time_minutes])", "formatString": "0.0"},
                {"name": "Conformant Avg Journey Mins", "expression": "CALCULATE(AVERAGE('Visits_Conformance'[journey_duration_minutes]), 'Visits_Conformance'[is_conformant] = 1)", "formatString": "0.0"},
                {"name": "Non-Conformant Avg Journey Mins", "expression": "CALCULATE(AVERAGE('Visits_Conformance'[journey_duration_minutes]), 'Visits_Conformance'[is_conformant] = 0)", "formatString": "0.0"},
                {"name": "Delay Penalty Mins", "expression": "[Non-Conformant Avg Journey Mins] - [Conformant Avg Journey Mins]", "formatString": "+0.0;-0.0;0.0"},
                {"name": "Delay Penalty Pct", "expression": "DIVIDE([Delay Penalty Mins], [Conformant Avg Journey Mins], 0)", "formatString": "0.0%"},
                {"name": "Avg Length of Stay Hours", "expression": "DIVIDE([Avg Journey Duration Mins], 60, 0)", "formatString": "0.00"},
                {"name": "Median Length of Stay Hours", "expression": "DIVIDE([Median Journey Duration Mins], 60, 0)", "formatString": "0.00"},
                {"name": "Conformant ALOS Hours", "expression": "DIVIDE([Conformant Avg Journey Mins], 60, 0)", "formatString": "0.00"},
                {"name": "Non-Conformant ALOS Hours", "expression": "DIVIDE([Non-Conformant Avg Journey Mins], 60, 0)", "formatString": "0.00"},
                {"name": "Total Loopback Events", "expression": "CALCULATE(COUNTROWS('Events'), 'Events'[is_loopback] = 1)", "formatString": "#,0"},
                {"name": "Loopback Event Rate", "expression": "DIVIDE([Total Loopback Events], [Total Events], 0)", "formatString": "0.0%"}
            ]
        }
    ]

    relationships = [
        {
            "name": "Events_Visits_Rel",
            "fromTable": "Events",
            "fromColumn": "case_id",
            "toTable": "Visits_Conformance",
            "toColumn": "case_id",
            "crossFilteringBehavior": "bothDirections"
        },
        {
            "name": "Transitions_Visits_Rel",
            "fromTable": "Transitions",
            "fromColumn": "case_id",
            "toTable": "Visits_Conformance",
            "toColumn": "case_id",
            "crossFilteringBehavior": "bothDirections"
        }
    ]

    return {
        "name": "CareFlow_Analytics",
        "compatibilityLevel": 1606,
        "model": {
            "culture": "en-US",
            "dataAccessOptions": {
                "legacyRedirects": True,
                "fastCombine": False
            },
            "relationships": relationships,
            "tables": tables
        }
    }


def make_card(name: str, x: float, y: float, width: float, height: float, table: str, measure: str, title: str, subtitle: str = None, tab_order: int = 0) -> dict:
    """Builds an enterprise-styled Power BI Card visualContainer."""
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
        },
        "objects": {
            "title": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "10D"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1E3A8A'"}}}}}
                }
            }],
            "labels": [{
                "properties": {
                    "fontSize": {"expr": {"Literal": {"Value": "22D"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Bold'"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#0F172A'"}}}}}
                }
            }],
            "categoryLabels": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "false"}}}
                }
            }],
            "border": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E2E8F0'"}}}}}
                }
            }],
            "background": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}
                }
            }]
        }
    }
    if subtitle:
        sv["objects"]["subTitle"] = [{
            "properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "text": {"expr": {"Literal": {"Value": f"'{subtitle}'"}}},
                "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}},
                "fontSize": {"expr": {"Literal": {"Value": "8.5D"}}},
                "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#64748B'"}}}}}
            }
        }]

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


def make_header_banner(name: str, x: float, y: float, width: float, height: float, title: str, subtitle: str, tab_order: int = 0) -> dict:
    """Builds a crisp, professional top navigation/header card visual container."""
    qref = "CareFlow_Measures.Total Visits"
    sv = {
        "visualType": "card",
        "projections": {"Values": [{"queryRef": qref}]},
        "prototypeQuery": {
            "Version": 2,
            "From": [{"Name": "t", "Entity": "CareFlow_Measures", "Type": 0}],
            "Select": [{
                "Measure": {
                    "Expression": {"SourceRef": {"Source": "t"}},
                    "Property": "Total Visits"
                },
                "Name": qref,
                "NativeReferenceName": "Total Visits"
            }]
        },
        "objects": {
            "title": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Bold'"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "13D"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1E3A8A'"}}}}}
                }
            }],
            "subTitle": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{subtitle}'"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "9.5D"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#475569'"}}}}}
                }
            }],
            "labels": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "false"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "1D"}}}
                }
            }],
            "categoryLabels": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "false"}}}
                }
            }],
            "border": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#CBD5E1'"}}}}}
                }
            }],
            "background": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#F8FAFC'"}}}}}
                }
            }]
        }
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


def make_chart(name: str, x: float, y: float, width: float, height: float, vtype: str, cat_tbl: str, cat_col: str, val_tbl: str, val_meas: str, title: str, subtitle: str = None, tab_order: int = 0) -> dict:
    """Builds a schema-valid clusteredBarChart, clusteredColumnChart, donutChart, or lineChart."""
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
        },
        "objects": {
            "title": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "11D"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1E3A8A'"}}}}}
                }
            }],
            "border": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E2E8F0'"}}}}}
                }
            }],
            "background": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}
                }
            }]
        }
    }
    if subtitle:
        sv["objects"]["subTitle"] = [{
            "properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "text": {"expr": {"Literal": {"Value": f"'{subtitle}'"}}},
                "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}},
                "fontSize": {"expr": {"Literal": {"Value": "9D"}}},
                "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#64748B'"}}}}}
            }
        }]

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


def make_table(name: str, x: float, y: float, width: float, height: float, items: list, title: str, subtitle: str = None, tab_order: int = 0) -> dict:
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
        },
        "objects": {
            "title": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "11D"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1E3A8A'"}}}}}
                }
            }],
            "border": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E2E8F0'"}}}}}
                }
            }],
            "background": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}
                }
            }]
        }
    }
    if subtitle:
        sv["objects"]["subTitle"] = [{
            "properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "text": {"expr": {"Literal": {"Value": f"'{subtitle}'"}}},
                "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}},
                "fontSize": {"expr": {"Literal": {"Value": "9D"}}},
                "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#64748B'"}}}}}
            }
        }]

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


def make_slicer(name: str, x: float, y: float, width: float, height: float, table: str, column: str, title: str, subtitle: str = None, tab_order: int = 0) -> dict:
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
        },
        "objects": {
            "title": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "text": {"expr": {"Literal": {"Value": f"'{title}'"}}},
                    "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI Semibold'"}}},
                    "fontSize": {"expr": {"Literal": {"Value": "10.5D"}}},
                    "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#1E3A8A'"}}}}}
                }
            }],
            "border": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#E2E8F0'"}}}}}
                }
            }],
            "background": [{
                "properties": {
                    "show": {"expr": {"Literal": {"Value": "true"}}},
                    "color": {"solid": {"color": {"expr": {"Literal": {"Value": "'#FFFFFF'"}}}}}
                }
            }]
        }
    }
    if subtitle:
        sv["objects"]["subTitle"] = [{
            "properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "text": {"expr": {"Literal": {"Value": f"'{subtitle}'"}}},
                "fontFamily": {"expr": {"Literal": {"Value": "'Segoe UI'"}}},
                "fontSize": {"expr": {"Literal": {"Value": "8.5D"}}},
                "fontColor": {"solid": {"color": {"expr": {"Literal": {"Value": "'#64748B'"}}}}}
            }
        }]

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
    """Builds report.json with 6 enterprise pages, header banners, styled cards, and varied charts."""
    theme = {
        "name": "CareFlowTheme",
        "dataColors": [
            "#1E3A8A",  # Deep Navy
            "#0D9488",  # Teal Accent
            "#0284C7",  # Sky Blue
            "#D97706",  # Amber Bottleneck
            "#E11D48",  # Coral / Rework
            "#10B981",  # Emerald Conformant
            "#6366F1",  # Indigo Secondary
            "#F59E0B"   # Warm Gold
        ],
        "background": "#FFFFFF",
        "foreground": "#1E293B",
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

    # =========================================================================
    # Page 1: Executive Overview & Operational KPIs (13 visuals)
    # =========================================================================
    visuals_page_1 = [
        # Top Header Banner
        make_header_banner(
            "p1_header", 16, 12, 1248, 48,
            "CAREFLOW CLINICAL INTELLIGENCE | EXECUTIVE OVERVIEW & OPERATIONAL KPIS",
            "Hospital-wide operational performance monitoring across 500 patient journeys, 3,030 events, and 6 departments", 1
        ),
        # KPI Ribbon (6 Cards)
        make_card("p1_c1_patients", 16, 66, 200, 92, "CareFlow_Measures", "Unique Patients", "UNIQUE PATIENTS", "420 Distinct Patients", 2),
        make_card("p1_c2_visits", 226, 66, 200, 92, "CareFlow_Measures", "Total Visits", "TOTAL PATIENT VISITS", "500 Completed Cases", 3),
        make_card("p1_c3_events", 436, 66, 200, 92, "CareFlow_Measures", "Total Events", "CLINICAL EVENTS", "3,030 Activity Steps", 4),
        make_card("p1_c4_conformance", 646, 66, 200, 92, "CareFlow_Measures", "Conformance Rate", "PATHWAY CONFORMANCE", "346 Standard Journeys (69.2%)", 5),
        make_card("p1_c5_rework", 856, 66, 200, 92, "CareFlow_Measures", "Rework Visits", "REWORK CASES (VISITS)", "154 Deviating Cases (30.8%)", 6),
        make_card("p1_c6_alos", 1066, 66, 198, 92, "CareFlow_Measures", "Avg Length of Stay Hours", "AVG LENGTH OF STAY", "4.22h Mean (253.5 mins)", 7),
        
        # Content Row 1 (y = 166, h = 265)
        make_chart("p1_chart_activities", 16, 166, 460, 265, "clusteredBarChart", "Events", "activity_name", "CareFlow_Measures", "Total Events", "Clinical Activity Volumes", "Activity step frequencies from Registration to Discharge", 8),
        make_chart("p1_chart_cohorts", 488, 166, 390, 265, "donutChart", "Visits_Conformance", "conformance_category", "CareFlow_Measures", "Total Visits", "Conformance Cohort Distribution", "Ideal Standard (175), Diagnostic (171), Rework (154)", 9),
        make_slicer("p1_slicer_dept", 890, 166, 374, 265, "Visits_Conformance", "department", "Filter by Department", "Interactive multi-select department filter", 10),
        
        # Content Row 2 (y = 441, h = 265)
        make_chart("p1_chart_depts", 16, 441, 460, 265, "clusteredColumnChart", "Visits_Conformance", "department", "CareFlow_Measures", "Total Visits", "Patient Volume by Department", "Distribution across General Emergency, Acute, Observation & Outpatient", 11),
        make_chart("p1_chart_alos_comp", 488, 441, 390, 265, "clusteredColumnChart", "Visits_Conformance", "conformance_status", "CareFlow_Measures", "Avg Journey Duration Mins", "Length of Stay by Status (Mins)", "Conformant (220.1m) vs Non-Conformant (328.5m)", 12),
        make_slicer("p1_slicer_status", 890, 441, 374, 265, "Visits_Conformance", "conformance_status", "Filter by Conformance Status", "CONFORMANT_IDEAL, CONFORMANT_DIAGNOSTIC, NON_CONFORMANT_REWORK", 13)
    ]

    # =========================================================================
    # Page 2: Patient Journey & Clinical Progression (10 visuals)
    # =========================================================================
    visuals_page_2 = [
        make_header_banner(
            "p2_header", 16, 12, 1248, 48,
            "PATIENT JOURNEY & CLINICAL PROGRESSION INTELLIGENCE",
            "End-to-end clinical workflow tracking from Registration to Discharge across 2,530 handovers", 1
        ),
        make_card("p2_c1_transitions", 16, 66, 304, 92, "CareFlow_Measures", "Total Transitions", "TOTAL HANDOVERS", "2,530 Inter-stage Transitions", 2),
        make_card("p2_c2_events", 330, 66, 304, 92, "CareFlow_Measures", "Total Events", "CLINICAL ACTIVITY STEPS", "3,030 Sequential Event Steps", 3),
        make_card("p2_c3_alos", 644, 66, 304, 92, "CareFlow_Measures", "Avg Length of Stay Hours", "AVERAGE LENGTH OF STAY", "4.22 Hours (Mean Total Journey)", 4),
        make_card("p2_c4_med_alos", 958, 66, 306, 92, "CareFlow_Measures", "Median Length of Stay Hours", "MEDIAN LENGTH OF STAY", "4.12 Hours (50th Percentile Journey)", 5),
        
        make_chart("p2_chart_progression", 16, 166, 370, 540, "clusteredBarChart", "Events", "activity_name", "CareFlow_Measures", "Total Events", "Stage Progression Volume", "Volume at each stage: Reg, Triage, Consult, Diag, Treat, Disch", 6),
        make_table("p2_table_benchmark", 398, 166, 530, 540, [
            ("Pathway_Benchmark", "pathway", False),
            ("Pathway_Benchmark", "transition_count", False),
            ("Pathway_Benchmark", "avg_transition_time_minutes", False),
            ("Pathway_Benchmark", "median_transition_time_minutes", False),
            ("Pathway_Benchmark", "iqr_minutes", False)
        ], "Pathway Handover Latency Benchmark (min)", "Observed transitions, sample counts, mean, median and IQR dispersion", 7),
        make_chart("p2_chart_pathways", 940, 166, 324, 265, "clusteredBarChart", "Transitions", "pathway", "CareFlow_Measures", "Total Transitions", "Handover Pathway Volumes", "All 9 clinical handover pathways ranked by volume", 8),
        make_slicer("p2_slicer_from", 940, 441, 156, 265, "Transitions", "from_activity", "From Stage", "Originating clinical stage", 9),
        make_slicer("p2_slicer_to", 1108, 441, 156, 265, "Transitions", "to_activity", "To Stage", "Destination clinical stage", 10)
    ]

    # =========================================================================
    # Page 3: Waiting Time Intelligence & Bottleneck Analysis (9 visuals)
    # =========================================================================
    visuals_page_3 = [
        make_header_banner(
            "p3_header", 16, 12, 1248, 48,
            "WAITING TIME INTELLIGENCE & CLINICAL BOTTLENECK ANALYSIS",
            "Operational dwell time benchmarks, queue delays, and non-conformance penalties across 6 stages", 1
        ),
        make_card("p3_c1_avg_wait", 16, 66, 304, 92, "CareFlow_Measures", "Avg Waiting Time Mins", "AVERAGE QUEUE WAIT", "15.9 min Mean Dwell Time", 2),
        make_card("p3_c2_med_wait", 330, 66, 304, 92, "CareFlow_Measures", "Median Waiting Time Mins", "MEDIAN QUEUE WAIT", "14.0 min (50th Percentile)", 3),
        make_card("p3_c3_delay_pen", 644, 66, 304, 92, "CareFlow_Measures", "Delay Penalty Mins", "NON-CONFORMANCE DELAY", "+108.4 min Delay Penalty", 4),
        make_card("p3_c4_delay_pct", 958, 66, 306, 92, "CareFlow_Measures", "Delay Penalty Pct", "RELATIVE DELAY PENALTY", "+49.3% Duration Surge", 5),
        
        make_chart("p3_chart_stage_wait", 16, 166, 480, 540, "clusteredColumnChart", "Events", "activity_name", "CareFlow_Measures", "Avg Waiting Time Mins", "Queue Bottlenecks by Clinical Stage (min)", "Diagnostics (39.5m) and Consultation (33.6m) are the primary queue bottlenecks", 6),
        make_chart("p3_chart_cohort_dur", 508, 166, 470, 265, "clusteredColumnChart", "Visits_Conformance", "conformance_category", "CareFlow_Measures", "Avg Journey Duration Mins", "Total Length of Stay by Conformance Cohort", "Conformant Ideal (219.7m) vs Diagnostic (220.5m) vs Rework (328.5m)", 7),
        make_chart("p3_chart_dept_wait", 508, 441, 470, 265, "clusteredBarChart", "Visits_Conformance", "department", "CareFlow_Measures", "Avg Waiting Time Mins", "Departmental Queue Dwell Benchmarks", "Average waiting time across 6 hospital departments", 8),
        make_slicer("p3_slicer_stage", 990, 166, 274, 540, "Events", "activity_name", "Filter by Clinical Stage", "Filter all queue metrics by clinical activity", 9)
    ]

    # =========================================================================
    # Page 4: Operational Rework & Loop-Back Analysis (10 visuals)
    # =========================================================================
    visuals_page_4 = [
        make_header_banner(
            "p4_header", 16, 12, 1248, 48,
            "OPERATIONAL REWORK & CLINICAL LOOP-BACK ANALYSIS",
            "Detailed audit of 172 rework loop transitions, 214 loopback events, and 154 affected patient cases", 1
        ),
        make_card("p4_c1_rework_cases", 16, 66, 240, 92, "CareFlow_Measures", "Rework Visits", "REWORK CASES (VISITS)", "154 of 500 Cases (30.8%)", 2),
        make_card("p4_c2_rework_trans", 268, 66, 240, 92, "CareFlow_Measures", "Rework Loop Transitions", "REWORK LOOP TRANSITIONS", "172 of 2,530 Handovers (6.8%)", 3),
        make_card("p4_c3_loopback_evts", 520, 66, 240, 92, "CareFlow_Measures", "Total Loopback Events", "TOTAL LOOPBACK EVENTS", "214 of 3,030 Events (7.1%)", 4),
        make_card("p4_c4_nonconf_alos", 772, 66, 240, 92, "CareFlow_Measures", "Non-Conformant ALOS Hours", "NON-CONFORMANT ALOS", "5.48 Hours (328.5 mins)", 5),
        make_card("p4_c5_conf_alos", 1024, 66, 240, 92, "CareFlow_Measures", "Conformant ALOS Hours", "CONFORMANT BASELINE ALOS", "3.67 Hours (220.1 mins)", 6),
        
        make_chart("p4_chart_rework_paths", 16, 166, 420, 540, "clusteredBarChart", "Transitions", "pathway", "CareFlow_Measures", "Rework Loop Transitions", "Rework Loop Pathway Frequency", "Diagnostics->Consultation (116), Treatment->Diagnostics (29), Triage->Reg (27)", 7),
        make_chart("p4_chart_rework_dept", 448, 166, 410, 265, "clusteredColumnChart", "Visits_Conformance", "department", "CareFlow_Measures", "Rework Visits", "Rework Patient Volume by Department", "Count of patient cases experiencing rework loops by department", 8),
        make_table("p4_table_patterns", 448, 441, 410, 265, [
            ("Variants_Summary", "trace_pattern", False),
            ("Variants_Summary", "conformance_category", False),
            ("Variants_Summary", "case_count", False),
            ("Variants_Summary", "rework_loops_per_case", False),
            ("Variants_Summary", "primary_deviation", False)
        ], "Rework Pattern Deviation Registry", "Trace patterns, case counts, and clinical root-cause deviations", 9),
        make_slicer("p4_slicer_cohort", 870, 166, 394, 540, "Visits_Conformance", "conformance_category", "Filter by Conformance Cohort", "Select Ideal Standard, Permitted Diagnostic, or Rework Loops", 10)
    ]

    # =========================================================================
    # Page 5: Process Mining & Conformance Alignment (10 visuals)
    # =========================================================================
    visuals_page_5 = [
        make_header_banner(
            "p5_header", 16, 12, 1248, 48,
            "PROCESS MINING & NORMATIVE PATHWAY CONFORMANCE",
            "Token replay & variant discovery across 11 distinct clinical process variants", 1
        ),
        make_card("p5_c1_conf_visits", 16, 66, 304, 92, "CareFlow_Measures", "Conformant Visits", "CONFORMANT PATIENT CASES", "346 Cases (69.2% Rate)", 2),
        make_card("p5_c2_rework_cases", 330, 66, 304, 92, "CareFlow_Measures", "Rework Visits", "NON-CONFORMANT CASES", "154 Cases (30.8% Rate)", 3),
        make_card("p5_c3_conf_dur", 644, 66, 304, 92, "CareFlow_Measures", "Conformant Avg Journey Mins", "CONFORMANT MEAN ALOS", "220.1 min Baseline Duration", 4),
        make_card("p5_c4_nonconf_dur", 958, 66, 306, 92, "CareFlow_Measures", "Non-Conformant Avg Journey Mins", "NON-CONFORMANT MEAN ALOS", "328.5 min (+108.4m Penalty)", 5),
        
        make_chart("p5_chart_variants", 16, 166, 390, 540, "clusteredBarChart", "Visits_Conformance", "trace_pattern", "CareFlow_Measures", "Total Visits", "Process Mining Variant Distribution", "Variant 1 (175), Variant 2 (171), Variants 3-11 (154 rework cases)", 6),
        make_chart("p5_chart_dur_status", 418, 166, 360, 265, "clusteredColumnChart", "Visits_Conformance", "conformance_status", "CareFlow_Measures", "Avg Journey Duration Mins", "Journey Duration by Status (min)", "CONFORMANT_IDEAL (219.7m) vs DIAGNOSTIC (220.5m) vs REWORK (328.5m)", 7),
        make_chart("p5_chart_status_donut", 418, 441, 360, 265, "donutChart", "Visits_Conformance", "conformance_status", "CareFlow_Measures", "Total Visits", "Conformance Proportion", "346 Conformant (69.2%) vs 154 Non-Conformant (30.8%)", 8),
        make_table("p5_table_variants", 790, 166, 474, 360, [
            ("Variants_Summary", "variant_id", False),
            ("Variants_Summary", "trace_pattern", False),
            ("Variants_Summary", "conformance_category", False),
            ("Variants_Summary", "case_count", False),
            ("Variants_Summary", "pct_of_total_cases", False),
            ("Variants_Summary", "avg_journey_minutes", False)
        ], "Process Mining Variant Registry", "Full catalog of 11 discovered process variants with case counts & times", 9),
        make_slicer("p5_slicer_variant", 790, 538, 474, 168, "Variants_Summary", "variant_id", "Filter by Variant ID", "Filter specific process variant (VAR01 - VAR11)", 10)
    ]

    # =========================================================================
    # Page 6: Detailed Patient & Case Explorer (10 visuals)
    # =========================================================================
    visuals_page_6 = [
        make_header_banner(
            "p6_header", 16, 12, 1248, 48,
            "DETAILED PATIENT JOURNEY & CLINICAL CASE EXPLORER",
            "Case-level audit trail, chronological event history, and dynamic multi-criteria filtering", 1
        ),
        make_card("p6_c1_visits", 16, 66, 304, 92, "CareFlow_Measures", "Total Visits", "FILTERED PATIENT VISITS", "Active Cases in View", 2),
        make_card("p6_c2_events", 330, 66, 304, 92, "CareFlow_Measures", "Total Events", "FILTERED CLINICAL EVENTS", "Audit Log Records", 3),
        make_card("p6_c3_patients", 644, 66, 304, 92, "CareFlow_Measures", "Unique Patients", "FILTERED UNIQUE PATIENTS", "Distinct Patients in View", 4),
        make_card("p6_c4_journey", 958, 66, 306, 92, "CareFlow_Measures", "Avg Journey Duration Mins", "FILTERED MEAN DURATION", "Average Case Duration (min)", 5),
        
        make_table("p6_table_cases", 16, 166, 550, 540, [
            ("Visits_Conformance", "case_id", False),
            ("Visits_Conformance", "patient_id", False),
            ("Visits_Conformance", "department", False),
            ("Visits_Conformance", "conformance_status", False),
            ("Visits_Conformance", "rework_loop_count", False),
            ("Visits_Conformance", "journey_duration_minutes", False),
            ("Visits_Conformance", "total_waiting_minutes", False)
        ], "Patient Case Conformance Explorer", "Master patient visit table. Click any Case ID to drill down into its event trail", 6),
        make_table("p6_table_trail", 578, 166, 430, 540, [
            ("Events", "case_id", False),
            ("Events", "activity_sequence", False),
            ("Events", "activity_name", False),
            ("Events", "event_timestamp", False),
            ("Events", "department", False),
            ("Events", "waiting_time_minutes", False),
            ("Events", "is_loopback", False)
        ], "Chronological Event Audit Trail", "Sequential activity log with timestamps, dwell times, and loopback flags", 7),
        make_chart("p6_chart_case_dur", 1020, 166, 244, 215, "clusteredColumnChart", "Visits_Conformance", "conformance_status", "CareFlow_Measures", "Avg Journey Duration Mins", "Duration by Status", "Cohort mean journey duration", 8),
        make_slicer("p6_slicer_dept", 1020, 393, 244, 150, "Visits_Conformance", "department", "Filter by Department", "Select hospital department", 9),
        make_slicer("p6_slicer_case", 1020, 555, 244, 151, "Visits_Conformance", "case_id", "Filter by Case ID", "Search & select single case", 10)
    ]

    sections = [
        {
            "name": "Section_Overview",
            "displayName": "Executive Overview & Operational KPIs",
            "filters": "[]",
            "ordinal": 0,
            "visualContainers": visuals_page_1,
            "width": 1280.0,
            "height": 720.0
        },
        {
            "name": "Section_Workflow",
            "displayName": "Patient Workflow & Clinical Progression",
            "filters": "[]",
            "ordinal": 1,
            "visualContainers": visuals_page_2,
            "width": 1280.0,
            "height": 720.0
        },
        {
            "name": "Section_Bottlenecks",
            "displayName": "Waiting Time & Stage Bottleneck Analysis",
            "filters": "[]",
            "ordinal": 2,
            "visualContainers": visuals_page_3,
            "width": 1280.0,
            "height": 720.0
        },
        {
            "name": "Section_Rework",
            "displayName": "Operational Rework & Loop-Back Analysis",
            "filters": "[]",
            "ordinal": 3,
            "visualContainers": visuals_page_4,
            "width": 1280.0,
            "height": 720.0
        },
        {
            "name": "Section_Conformance",
            "displayName": "Process Mining & Conformance Alignment",
            "filters": "[]",
            "ordinal": 4,
            "visualContainers": visuals_page_5,
            "width": 1280.0,
            "height": 720.0
        },
        {
            "name": "Section_Explorer",
            "displayName": "Detailed Patient & Case Explorer",
            "filters": "[]",
            "ordinal": 5,
            "visualContainers": visuals_page_6,
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
    print("=" * 75)
    print("   CAREFLOW: GENERATING ENTERPRISE 6-PAGE POWER BI PROJECT (.PBIP)")
    print("=" * 75)

    # Ensure directories exist
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    SEMANTIC_DIR.mkdir(parents=True, exist_ok=True)
    theme_dir = REPORT_DIR / "StaticResources" / "SharedResources" / "BaseThemes"
    theme_dir.mkdir(parents=True, exist_ok=True)

    # 1. Root .pbip file
    print(f"[1/8] Writing {PBIP_FILE.name}...")
    with open(PBIP_FILE, "w", encoding="utf-8") as f:
        json.dump(create_pbip_entry(), f, indent=2)

    # 2. Report definition.pbir
    pbir_file = REPORT_DIR / "definition.pbir"
    print(f"[2/8] Writing {pbir_file.name}...")
    with open(pbir_file, "w", encoding="utf-8") as f:
        json.dump(create_pbir_definition(), f, indent=2)

    # 3. Report .platform
    report_platform_file = REPORT_DIR / ".platform"
    print(f"[3/8] Writing Report {report_platform_file.name}...")
    with open(report_platform_file, "w", encoding="utf-8") as f:
        json.dump(create_report_platform(), f, indent=2)

    # 4. Report BaseTheme CareFlowTheme.json
    theme_file = theme_dir / "CareFlowTheme.json"
    print(f"[4/8] Writing Theme {theme_file.name}...")
    with open(theme_file, "w", encoding="utf-8") as f:
        json.dump(create_theme_file_dict(), f, indent=2)

    # 5. Report report.json
    report_json_file = REPORT_DIR / "report.json"
    print(f"[5/8] Writing {report_json_file.name} (6 pages, 62 visual containers)...")
    with open(report_json_file, "w", encoding="utf-8") as f:
        json.dump(create_report_json(), f, indent=2)

    # 6. SemanticModel definition.pbism
    pbism_file = SEMANTIC_DIR / "definition.pbism"
    print(f"[6/8] Writing {pbism_file.name}...")
    with open(pbism_file, "w", encoding="utf-8") as f:
        json.dump(create_pbism_definition(), f, indent=2)

    # 7. SemanticModel .platform
    semantic_platform_file = SEMANTIC_DIR / ".platform"
    print(f"[7/8] Writing SemanticModel {semantic_platform_file.name}...")
    with open(semantic_platform_file, "w", encoding="utf-8") as f:
        json.dump(create_semantic_platform(), f, indent=2)

    # 8. SemanticModel model.bim
    model_bim_file = SEMANTIC_DIR / "model.bim"
    print(f"[8/8] Writing {model_bim_file.name} (6 tables, 24 DAX measures)...")
    with open(model_bim_file, "w", encoding="utf-8") as f:
        json.dump(create_model_bim(), f, indent=2)

    print("\n" + "=" * 75)
    print("   CAREFLOW ENTERPRISE POWER BI PROJECT GENERATED SUCCESSFULLY!")
    print(f"   Project File : {PBIP_FILE}")
    print(f"   Report Dir   : {REPORT_DIR}")
    print(f"   Semantic Dir : {SEMANTIC_DIR}")
    print("=" * 75)


if __name__ == "__main__":
    main()
