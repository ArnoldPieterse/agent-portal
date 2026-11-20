# XRef post-mirror sweep 2026-11-20 17:32 (Archivist, auto-loop upkeep)

Trigger: mirror cycle landed after last xref report (195 files newer than 12:35 report) -> goal-5 rule "run after every mirror cycle".

Command: `python memory/archivist/xref_monitor.py`
Result: **FAIL - 583 violations** (dangling 520, self-ref 13, deep-chains 50). Files scanned 1939 (.md only), edges 4848.
Report: memory/archivist/xref-monitor-report-2026-11-20.md (regenerated this run).

Trend note: earlier JSON (11:03, older script build) reported 303 total / 6894 files - different scan scope (all files vs .md-only); not a like-for-like regression. Like-for-like comparison needs the same build.

Known false-positive classes in dangling list (monitor regex picks these up as refs):
- glob patterns: `*_completed.md`, `memory/ops/*.md`
- URLs inside backticks: `http:/[LAN-IP]:8099/...`, `https:/github.com/...`
- shell command text in backticks: `findstr archivist api-reference.md`, `python model_check_1115.py`
Suggested monitor fix (next cycle): skip refs containing `*`, `://`, or starting with a command word. Not applied this pass (one-step scope).

Deep chains: 50, dominated by memory/INDEX.md -> goals/INDEX.md -> all-goals-2026-11-13.md -> * (depth 4). Structural: the flat all-goals hub adds one hop; fix = collapse or re-point.
