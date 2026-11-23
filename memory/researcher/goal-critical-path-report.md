# Goal Dependency & Critical-Path Analysis
Generated: 2026-11-23

**Open goals:** 49
**Cross-agent dependencies found:** 8
**Handoff edges parsed:** 4

## Critical Path (top 10 by dependency depth)
- **archivist#5** (depth 1): Decision-Knowledge Feedback Loop** - `python memory/archivist/kb_feedback.py`: for each cockpit deci
- **builder#10** (depth 1): Fleet State Snapshot Scheduler** - `python memory/builder/state_snapshot.py`: every 30 min (via scht
- **builder#10** (depth 1): Cockpit One-Click Runbook Trigger (pre-flight validated execution from UI)
- **designer#2** (depth 1): Decision Provenance Overlay** - Design the "where did this come from?" overlay: clicking any cockpit
- **designer#4** (depth 1): Predictive Risk Surface (Forward-Looking)** - Design the forward-looking risk panel: renders next10.
- **designer#7** (depth 1): Fleet Topology Live Graph** - Design the 4-host fleet as a live topology graph: nodes = hosts, edges
- **designer#9** (depth 1): Knowledge Impact Surface** - Design the "what knowledge did this decision use?" panel: when a goal c
- **researcher#6** (depth 1): Research-Instrument Health Feed** - `python memory/researcher/instrument_health.py`: emit a cockpit 
- **researcher#8** (depth 1): Cockpit Data Golden-Fixture Regression** - `python memory/researcher/cockpit_golden.py`: Playwright 
