# DOM Taxonomy Browser

**Standalone browser for the Data Operating Model (DOM) — Anchor Data Capabilities.**  
Built with the STRADA design system. No framework, no backend, no build step.

![DOM v2.1](https://img.shields.io/badge/DOM-v2.1-4f8cff?style=flat-square) ![License: MIT](https://img.shields.io/badge/License-MIT-success?style=flat-square) ![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square)

---

## Features

- **Matrix view** — full L0 / L2 / L3 capability map (landing page)
- **Hierarchy view** — collapsible tree with full-text search
- **Detail modal** — 15-section DOM card per capability (Definition, Activities, Tools, KPIs…)
- **Print** — clean print stylesheet for both views and modal cards
- **Light / Dark theme** — toggle in the topnav
- **OWL-driven** — all content generated from the source ontology; update in Protégé and regenerate in one command

---

## Quick start — Windows

Double-click **`start.bat`** — it starts a local HTTP server and opens the browser automatically.

> A local HTTP server is required because the app loads its data via `fetch()`.  
> `start.bat` handles this automatically.

## Quick start — macOS / Linux

```bash
cd dom-taxonomy/
python3 -m http.server 8080
# Open http://localhost:8080
```

---

## File structure

```
dom-taxonomy/
├── index.html          ← Single-file application (Matrix + Hierarchy views)
├── taxonomy.json       ← Node graph: L0 / L2 / L3 (generated from OWL)
├── sections.json       ← 15-section content per capability (generated from OWL)
├── owl_to_json.py      ← Regeneration script — run after editing in Protégé
├── start.bat           ← One-click launcher (Windows)
├── .gitignore
├── LICENSE
└── README.md
```

---

## Updating after a Protégé edit

1. Open the OWL file in **Protégé**, make your changes, save as OWL/XML
2. Run:

```bash
python owl_to_json.py path/to/dom.owl path/to/dom_sections.json ./
```

This script:
- Parses the OWL with `rdflib`
- Writes `taxonomy.json` and `sections.json`
- Re-injects both data blobs directly into `index.html`

3. Reload the browser — done.

### Install the only dependency

```bash
pip install rdflib
```

---

## DOM ontology structure

| Level | OWL class | Example |
|-------|-----------|---------|
| L0 | `MacroProcess` | GOVERN, MANAGE, BUILD, RUN |
| L2 | `L2Capability` | Data Governance & Oversight |
| L3 | `L3SubCapability` | ML/AI Model Governance |

Each node carries `rdfs:label`, `skos:definition`, `dom:capabilityId`, and parent links.

---

## Design

Built on the **STRADA** design system — Inter font, CSS custom properties, liquid-glass topnav, light/dark themes. Zero external JS framework or CSS library.

---

## License

MIT — see [LICENSE](LICENSE).
