#!/usr/bin/env python3
"""
owl_to_json.py
==============
Converts the DOM OWL ontology + dom_sections.json into the data files
used by the DOM Taxonomy Browser (index.html).

Usage
-----
  python owl_to_json.py <owl_file> <dom_sections_json> [output_dir]

Arguments
---------
  owl_file          Path to the OWL/XML ontology (e.g. dom-v2_1-complete.owl)
  dom_sections_json Path to the dom_sections.json content file
  output_dir        Folder containing index.html (default: same folder as this script)

What it does
------------
  1. Parses the OWL file with rdflib
  2. Extracts L0 MacroProcess, L2 Capability, L3 SubCapability nodes
  3. Writes taxonomy.json  (node graph)
  4. Copies dom_sections.json → sections.json
  5. Re-injects both JSON blobs into index.html (replaces the embedded data)

Requirements
------------
  pip install rdflib

After running, simply reload the browser — no server restart needed.
"""

import sys
import json
import os
import re

try:
    from rdflib import Graph, Namespace, RDF, RDFS, SKOS
except ImportError:
    print("ERROR: rdflib not installed. Run:  pip install rdflib")
    sys.exit(1)

DOM = Namespace("http://strategic-advisory.com/ontology/dom/2.0#")
MACRO_ORDER = {"L0.GOVERN": 1, "L0.MANAGE": 2, "L0.BUILD": 3, "L0.RUN": 4}


# ── RDF helpers ─────────────────────────────────────────────────────────────

def get_label(g, subj, lang="en"):
    for o in g.objects(subj, RDFS.label):
        if hasattr(o, "language") and o.language == lang:
            return str(o)
    for o in g.objects(subj, RDFS.label):
        return str(o)
    return str(subj).split("#")[-1]


def get_def(g, subj, lang="en"):
    for o in g.objects(subj, SKOS.definition):
        if hasattr(o, "language") and o.language == lang:
            return str(o)
    for o in g.objects(subj, SKOS.definition):
        return str(o)
    return None


def get_prop(g, subj, prop):
    v = g.value(subj, prop)
    return str(v) if v else None


# ── OWL → taxonomy dict ──────────────────────────────────────────────────────

def owl_to_taxonomy(owl_path):
    print(f"  Parsing OWL: {owl_path}")
    g = Graph()
    g.parse(owl_path, format="xml")
    nodes = {}

    # L0 — MacroProcess
    for s in g.subjects(RDF.type, DOM.MacroProcess):
        cap_id = get_prop(g, s, DOM.capabilityId)
        if not cap_id:
            continue
        nodes[cap_id] = {
            "id": cap_id, "level": "L0",
            "label": get_label(g, s), "definition": get_def(g, s),
            "parent": None, "children": []
        }

    # L2 — Capabilities
    l2_list = []
    for s in g.subjects(RDF.type, DOM.L2Capability):
        cap_id = get_prop(g, s, DOM.capabilityId)
        if not cap_id:
            continue
        parent_uri = g.value(s, DOM.belongsToMacroProcess)
        parent_id  = get_prop(g, parent_uri, DOM.capabilityId) if parent_uri else None
        l2_list.append({
            "id": cap_id, "level": "L2",
            "label": get_label(g, s), "definition": get_def(g, s),
            "parent": parent_id, "children": []
        })
    for n in sorted(l2_list, key=lambda x: (MACRO_ORDER.get(x["parent"], 99), x["id"])):
        nodes[n["id"]] = n

    # L3 — SubCapabilities
    l3_list = []
    for s in g.subjects(RDF.type, DOM.L3SubCapability):
        cap_id = get_prop(g, s, DOM.capabilityId)
        if not cap_id:
            continue
        parent_uri = g.value(s, DOM.belongsToL2)
        parent_id  = get_prop(g, parent_uri, DOM.capabilityId) if parent_uri else None
        l3_list.append({
            "id": cap_id, "level": "L3",
            "label": get_label(g, s), "definition": get_def(g, s),
            "parent": parent_id, "children": []
        })
    for n in sorted(l3_list, key=lambda x: x["id"]):
        nodes[n["id"]] = n

    # Wire children
    for nid, node in nodes.items():
        if node["parent"] and node["parent"] in nodes:
            nodes[node["parent"]]["children"].append(nid)

    return nodes


def build_matrix_data(taxonomy):
    """Build the ordered macro→L2→L3 structure used by the Matrix view."""
    macros = {k: v for k, v in taxonomy.items() if v["level"] == "L0"}
    result = []
    for macro_id in sorted(macros, key=lambda x: MACRO_ORDER.get(x, 99)):
        macro = macros[macro_id]
        l2s = sorted(
            [taxonomy[c] for c in macro["children"] if taxonomy.get(c, {}).get("level") == "L2"],
            key=lambda x: x["id"]
        )
        for l2 in l2s:
            l2["l3s"] = sorted(
                [taxonomy[c] for c in l2["children"] if taxonomy.get(c, {}).get("level") == "L3"],
                key=lambda x: x["id"]
            )
        macro_entry = {
            "id": macro["id"],
            "label": macro["label"],
            "definition": macro["definition"],
            "l2s": [{"id": l2["id"], "label": l2["label"], "definition": l2["definition"],
                     "l3s": [{"id": l3["id"], "label": l3["label"], "definition": l3["definition"]}
                              for l3 in l2["l3s"]]}
                    for l2 in l2s]
        }
        result.append(macro_entry)
    return result


# ── Re-inject data into index.html ───────────────────────────────────────────

INJECT_MARKERS = {
    "MATRIX_DATA":  (r"const MATRIX_DATA\s*=\s*", r";"),
    "TAXONOMY":     (r"const TAXONOMY\s*=\s*",     r";"),
    "SECTIONS":     (r"const SECTIONS\s*=\s*",     r";"),
}

def inject_into_html(html_path, taxonomy, matrix_data, sections):
    with open(html_path, encoding="utf-8") as f:
        html = f.read()

    replacements = {
        "MATRIX_DATA": json.dumps(matrix_data, separators=(",", ":"), ensure_ascii=False),
        "TAXONOMY":    json.dumps(taxonomy,     separators=(",", ":"), ensure_ascii=False),
        "SECTIONS":    json.dumps(sections,     separators=(",", ":"), ensure_ascii=False),
    }

    # Use line-based replacement to avoid regex stopping at first semicolon inside JSON.
    lines = html.split("\n")
    for var, new_value in replacements.items():
        replaced = False
        for i, line in enumerate(lines):
            if re.match(rf"\s*const {re.escape(var)}\s*=", line):
                indent = re.match(r"(\s*)", line).group(1)
                lines[i] = f"{indent}const {var} = {new_value};"
                replaced = True
                print(f"  \u2713 {var} injected ({len(new_value):,} chars)")
                break
        if not replaced:
            print(f"  WARNING: could not find marker for {var} in index.html — skipped.")

    with open(html_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    owl_path      = sys.argv[1]
    sections_path = sys.argv[2]
    out_dir       = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(os.path.abspath(__file__))
    html_path     = os.path.join(out_dir, "index.html")

    print("\nDOM Taxonomy — OWL → JSON regeneration")
    print("=" * 42)

    taxonomy    = owl_to_taxonomy(owl_path)
    matrix_data = build_matrix_data(taxonomy)

    with open(sections_path, encoding="utf-8") as f:
        sections = json.load(f)

    # Write standalone JSON files
    tax_out = os.path.join(out_dir, "taxonomy.json")
    sec_out = os.path.join(out_dir, "sections.json")
    with open(tax_out, "w", encoding="utf-8") as f:
        json.dump(taxonomy, f, indent=2, ensure_ascii=False)
    with open(sec_out, "w", encoding="utf-8") as f:
        json.dump(sections, f, indent=2, ensure_ascii=False)
    print(f"  ✓ taxonomy.json — {len(taxonomy)} nodes")
    print(f"  ✓ sections.json — {len(sections)} capability sections")

    # Re-inject into index.html
    if os.path.exists(html_path):
        print(f"\n  Re-injecting data into {html_path} ...")
        inject_into_html(html_path, taxonomy, matrix_data, sections)
    else:
        print(f"\n  NOTE: {html_path} not found — JSON files written but index.html not updated.")

    print(f"\n✅ Done. Reload your browser to see changes.")
    print(f"   Output: {out_dir}\n")


if __name__ == "__main__":
    main()
