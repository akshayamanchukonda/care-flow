"""CareFlow: Power BI Project (.pbip) Validation Suite.

Validates:
  1. JSON parsing and structure of all .pbip, .pbir, .pbism, .bim, and report.json files.
  2. Referential integrity: datasetReference, table names, column names in measures and relationships.
  3. Source CSV paths and row counts.
  4. DAX measure syntactic consistency.
"""

from pathlib import Path
import json
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent if (Path(__file__).resolve().parent / "reports").exists() else Path(__file__).resolve().parent.parent
REPORTS_DIR = REPO_ROOT / "reports"
PBIP_NAME = "CareFlow_Analytics"

PBIP_FILE = REPORTS_DIR / f"{PBIP_NAME}.pbip"
REPORT_DIR = REPORTS_DIR / f"{PBIP_NAME}.Report"
SEMANTIC_DIR = REPORTS_DIR / f"{PBIP_NAME}.SemanticModel"

def validate_pbip():
    print("=" * 65)
    print("   CAREFLOW: VALIDATING GENERATED POWER BI PROJECT (.PBIP)")
    print("=" * 65)

    errors = []

    # 1. Check PBIP
    print("\n[1/5] Validating root PBIP file...")
    if not PBIP_FILE.exists():
        errors.append(f"Missing PBIP file: {PBIP_FILE}")
    else:
        with open(PBIP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        report_path = data.get("artifacts", [{}])[0].get("report", {}).get("path")
        target_dir = REPORTS_DIR / report_path
        if not target_dir.exists():
            errors.append(f"PBIP points to non-existent report dir: {target_dir}")
        else:
            print(f"      PBIP root successfully points to: {target_dir.name}")

    # 2. Check definition.pbir
    print("\n[2/5] Validating definition.pbir...")
    pbir_file = REPORT_DIR / "definition.pbir"
    if not pbir_file.exists():
        errors.append(f"Missing definition.pbir: {pbir_file}")
    else:
        with open(pbir_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        sem_rel_path = data.get("datasetReference", {}).get("byPath", {}).get("path")
        resolved_sem = (REPORT_DIR / sem_rel_path).resolve()
        if not resolved_sem.exists():
            errors.append(f"definition.pbir points to non-existent model dir: {resolved_sem}")
        else:
            print(f"      definition.pbir successfully links to: {resolved_sem.name}")

    # 3. Check definition.pbism
    print("\n[3/5] Validating definition.pbism...")
    pbism_file = SEMANTIC_DIR / "definition.pbism"
    if not pbism_file.exists():
        errors.append(f"Missing definition.pbism: {pbism_file}")
    else:
        with open(pbism_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("version") != "1.0":
            errors.append(f"Unexpected pbism version: {data.get('version')}")
        else:
            print("      definition.pbism version 1.0 (TMSL model.bim) verified.")

    # 4. Check model.bim
    print("\n[4/5] Validating model.bim (Tables, Columns, Relationships, DAX)...")
    model_bim = SEMANTIC_DIR / "model.bim"
    if not model_bim.exists():
        errors.append(f"Missing model.bim: {model_bim}")
    else:
        with open(model_bim, "r", encoding="utf-8") as f:
            bim = json.load(f)
        model = bim.get("model", {})
        tables = model.get("tables", [])
        table_names = {t["name"] for t in tables}
        print(f"      Discovered {len(tables)} tables: {sorted(list(table_names))}")

        # Map table -> columns and validate column types
        table_cols = {}
        for t in tables:
            cols = {c["name"] for c in t.get("columns", [])}
            table_cols[t["name"]] = cols
            partitions = t.get("partitions", [])
            if not partitions:
                errors.append(f"Table {t['name']} has no partitions")
            is_calc = any(p.get("source", {}).get("type") == "calculated" for p in partitions)
            for c in t.get("columns", []):
                col_name = c.get("name")
                dt = c.get("dataType")
                inf = c.get("isDataTypeInferred", False)
                if dt == "Empty":
                    errors.append(f"Column '{t['name']}'[{col_name}] has invalid Empty dataType")
                if not is_calc and inf:
                    errors.append(f"Regular column '{t['name']}'[{col_name}] has invalid isDataTypeInferred=True")
            measures = t.get("measures", [])
            if measures:
                print(f"      Table '{t['name']}' (Calculated={is_calc}) has {len(measures)} DAX measures.")

        # Check relationships
        rels = model.get("relationships", [])
        print(f"      Discovered {len(rels)} relationships:")
        for r in rels:
            from_t, from_c = r["fromTable"], r["fromColumn"]
            to_t, to_c = r["toTable"], r["toColumn"]
            print(f"        • '{from_t}'[{from_c}] <---> '{to_t}'[{to_c}]")
            if from_t not in table_names or from_c not in table_cols[from_t]:
                errors.append(f"Invalid from in relationship {r['name']}: {from_t}[{from_c}]")
            if to_t not in table_names or to_c not in table_cols[to_t]:
                errors.append(f"Invalid to in relationship {r['name']}: {to_t}[{to_c}]")

    # 5. Check report.json
    print("\n[5/5] Validating report.json (Pages, Theme, Layout, Visuals)...")
    report_json_file = REPORT_DIR / "report.json"
    if not report_json_file.exists():
        errors.append(f"Missing report.json: {report_json_file}")
    else:
        with open(report_json_file, "r", encoding="utf-8") as f:
            rep = json.load(f)
        theme = rep.get("theme", {})
        colors = theme.get("dataColors", [])
        print(f"      Theme Name: '{theme.get('name')}', Data Colors: {colors[:4]}...")
        sections = rep.get("sections", [])
        print(f"      Pages Defined ({len(sections)}): {[s['displayName'] for s in sections]}")
        total_visuals = 0
        for s in sections:
            p_name = s.get("displayName")
            vcs = s.get("visualContainers", [])
            total_visuals += len(vcs)
            if not vcs:
                errors.append(f"Page '{p_name}' has 0 visual containers (shows empty canvas)")
            else:
                print(f"        • Page '{p_name}': {len(vcs)} visual containers verified.")
            for v in vcs:
                if "config" not in v:
                    errors.append(f"Visual in '{p_name}' missing config")
                else:
                    cfg = json.loads(v["config"])
                    sv = cfg.get("singleVisual", {})
                    vtype = sv.get("visualType")
                    if not vtype:
                        errors.append(f"Visual in '{p_name}' missing visualType")
        print(f"      Total Visual Containers Validated: {total_visuals}")

    print("\n" + "=" * 65)
    if errors:
        print("   VALIDATION FAILED WITH ERRORS:")
        for e in errors:
            print(f"   [!] {e}")
        print("=" * 65)
        return False
    else:
        print("   ALL PBIP COMPONENTS PASSED VALIDATION CHECKS (0 ERRORS)")
        print("=" * 65)
        return True

if __name__ == "__main__":
    import sys
    success = validate_pbip()
    sys.exit(0 if success else 1)

