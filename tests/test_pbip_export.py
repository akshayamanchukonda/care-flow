"""CareFlow: Unit Tests for Power BI Project (.pbip) Export.

Validates:
  1. PBIP root, report, and semantic model files exist.
  2. JSON syntax and version compliance for .pbip, .pbir, .pbism, model.bim, and report.json.
  3. Model consistency: tables ('Events', 'Transitions', 'Visits_Conformance', 'Pathway_Benchmark', 'CareFlow_Measures'),
     relationships, and explicit DAX measures.
  4. Theme palette contains required Navy (#1E3A8A), Teal (#0D9488), and Amber (#D97706) colors.
"""

from pathlib import Path
import json
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = REPO_ROOT / "reports"
PBIP_NAME = "CareFlow_Analytics"
PBIP_FILE = REPORTS_DIR / f"{PBIP_NAME}.pbip"
REPORT_DIR = REPORTS_DIR / f"{PBIP_NAME}.Report"
SEMANTIC_DIR = REPORTS_DIR / f"{PBIP_NAME}.SemanticModel"


class TestPowerBIProjectExport(unittest.TestCase):
    """Test suite for CareFlow Power BI Project (.pbip) export."""

    def test_pbip_files_exist(self):
        """Verify all essential PBIP project files exist on disk."""
        self.assertTrue(PBIP_FILE.exists(), f"Missing {PBIP_FILE}")
        self.assertTrue((REPORT_DIR / "definition.pbir").exists())
        self.assertTrue((REPORT_DIR / "report.json").exists())
        self.assertTrue((SEMANTIC_DIR / "definition.pbism").exists())
        self.assertTrue((SEMANTIC_DIR / "model.bim").exists())

    def test_pbip_root_structure(self):
        """Verify PBIP root points to the valid report directory."""
        with open(PBIP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("version"), "1.0")
        report_path = data["artifacts"][0]["report"]["path"]
        self.assertEqual(report_path, f"{PBIP_NAME}.Report")
        self.assertTrue((REPORTS_DIR / report_path).is_dir())

    def test_pbir_and_pbism_references(self):
        """Verify report links to semantic model and model format is version 1.0."""
        with open(REPORT_DIR / "definition.pbir", "r", encoding="utf-8") as f:
            pbir = json.load(f)
        self.assertEqual(pbir.get("version"), "1.0")
        sem_path = pbir["datasetReference"]["byPath"]["path"]
        resolved = (REPORT_DIR / sem_path).resolve()
        self.assertEqual(resolved, SEMANTIC_DIR.resolve())

        with open(SEMANTIC_DIR / "definition.pbism", "r", encoding="utf-8") as f:
            pbism = json.load(f)
        self.assertEqual(pbism.get("version"), "1.0")

    def test_model_bim_tables_and_measures(self):
        """Verify tables, columns, and DAX measures in model.bim."""
        with open(SEMANTIC_DIR / "model.bim", "r", encoding="utf-8") as f:
            bim = json.load(f)
        model = bim["model"]
        tables = {t["name"]: t for t in model["tables"]}
        expected_tables = {
            "Events",
            "Transitions",
            "Visits_Conformance",
            "Pathway_Benchmark",
            "CareFlow_Measures",
        }
        self.assertTrue(expected_tables.issubset(set(tables.keys())))

        # Verify all 18 measures are present
        measures_table = tables["CareFlow_Measures"]
        measures = measures_table.get("measures", [])
        self.assertEqual(len(measures), 18)
        measure_names = {m["name"] for m in measures}
        expected_measures = {
            "Total Events",
            "Total Visits",
            "Unique Patients",
            "Conformant Visits",
            "Conformance Rate",
            "Rework Visits",
            "Rework Rate",
            "Total Transitions",
            "Rework Loop Transitions",
            "Rework Transition Pct",
            "Avg Journey Duration Mins",
            "Median Journey Duration Mins",
            "Avg Waiting Time Mins",
            "Median Waiting Time Mins",
            "Conformant Avg Journey Mins",
            "Non-Conformant Avg Journey Mins",
            "Delay Penalty Mins",
            "Delay Penalty Pct",
        }
        self.assertEqual(measure_names, expected_measures)

        # Verify CareFlow_Measures is a valid calculated table
        partitions = measures_table.get("partitions", [])
        self.assertTrue(any(p.get("source", {}).get("type") == "calculated" for p in partitions))
        cols = measures_table.get("columns", [])
        self.assertEqual(len(cols), 1)
        self.assertEqual(cols[0]["name"], "Measure_Group")
        self.assertEqual(cols[0]["type"], "calculatedTableColumn")
        self.assertEqual(cols[0]["dataType"], "string")

        # Verify no column in any table has dataType Empty
        for t in model["tables"]:
            is_calc = any(p.get("source", {}).get("type") == "calculated" for p in t.get("partitions", []))
            for c in t.get("columns", []):
                self.assertNotEqual(c.get("dataType"), "Empty")
                if not is_calc:
                    self.assertFalse(c.get("isDataTypeInferred", False))

        # Verify relationships
        rels = model.get("relationships", [])
        self.assertGreaterEqual(len(rels), 2)
        rel_froms = {r["fromTable"] for r in rels}
        self.assertIn("Events", rel_froms)
        self.assertIn("Transitions", rel_froms)

    def test_report_json_theme_and_sections(self):
        """Verify navy/teal theme and multi-page configuration in report.json."""
        with open(REPORT_DIR / "report.json", "r", encoding="utf-8") as f:
            rep = json.load(f)
        theme = rep.get("theme", {})
        colors = theme.get("dataColors", [])
        self.assertIn("#1E3A8A", colors)  # Navy
        self.assertIn("#0D9488", colors)  # Teal
        self.assertIn("#D97706", colors)  # Amber

        sections = rep.get("sections", [])
        self.assertEqual(len(sections), 3)
        section_titles = [s["displayName"] for s in sections]
        self.assertIn("Executive Overview & KPIs", section_titles)
        self.assertIn("Process Flow & Rework Analysis", section_titles)
        self.assertIn("Bottlenecks & Waiting Times", section_titles)

    def test_report_json_visual_containers_and_referential_integrity(self):
        """Verify real, schema-valid visual objects exist on every page and map to model.bim."""
        with open(REPORT_DIR / "report.json", "r", encoding="utf-8") as f:
            rep = json.load(f)
        with open(SEMANTIC_DIR / "model.bim", "r", encoding="utf-8") as f:
            bim = json.load(f)

        tables = {t["name"]: t for t in bim["model"]["tables"]}
        table_cols = {tname: {c["name"] for c in tdata.get("columns", [])} for tname, tdata in tables.items()}
        table_meas = {tname: {m["name"] for m in tdata.get("measures", [])} for tname, tdata in tables.items()}

        sections = rep.get("sections", [])
        self.assertEqual(len(sections), 3)

        # Expected visual counts per page
        page_visual_counts = {
            "Executive Overview & KPIs": 9,
            "Process Flow & Rework Analysis": 6,
            "Bottlenecks & Waiting Times": 6,
        }

        total_visuals = 0
        for s in sections:
            p_name = s["displayName"]
            vcs = s.get("visualContainers", [])
            self.assertEqual(len(vcs), page_visual_counts[p_name], f"Page {p_name} visual count mismatch")
            total_visuals += len(vcs)

            for v in vcs:
                # Check dimensions fit on canvas
                self.assertLessEqual(v["x"] + v["width"], s["width"])
                self.assertLessEqual(v["y"] + v["height"], s["height"])

                cfg = json.loads(v["config"])
                sv = cfg.get("singleVisual", {})
                vtype = sv.get("visualType")
                self.assertIn(vtype, {"card", "clusteredBarChart", "clusteredColumnChart", "tableEx", "slicer"})

                pq = sv.get("prototypeQuery", {})
                from_entities = {f["Name"]: f["Entity"] for f in pq.get("From", [])}
                for f_alias, entity in from_entities.items():
                    self.assertIn(entity, tables, f"Visual references unknown table {entity}")

                for sel in pq.get("Select", []):
                    if "Column" in sel:
                        src_alias = sel["Column"]["Expression"]["SourceRef"]["Source"]
                        prop = sel["Column"]["Property"]
                        entity = from_entities[src_alias]
                        self.assertIn(prop, table_cols[entity], f"Column {entity}[{prop}] not in model")
                    elif "Measure" in sel:
                        src_alias = sel["Measure"]["Expression"]["SourceRef"]["Source"]
                        prop = sel["Measure"]["Property"]
                        entity = from_entities[src_alias]
                        self.assertIn(prop, table_meas[entity], f"Measure {entity}[{prop}] not in model")

        self.assertEqual(total_visuals, 21)


if __name__ == "__main__":
    unittest.main()

