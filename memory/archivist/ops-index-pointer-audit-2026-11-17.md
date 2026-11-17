# Archivist verification: ops/INDEX.md pointer audit
Date: 2026-11-17 (auto-loop pass)

## Finding
5 of 40 files referenced in memory/ops/INDEX.md are ABSENT from White's working directory:
- fleet_probe_v2.py
- load_probe.py
- fleet_health_check.py
- portal_watchdog.py
- sim_fleet_probe_degrade.py

These are listed under "PROBE & MONITORING SCRIPTS (root dir)" but do not exist locally.
Likely resident on other hosts (Pale/Black/Red) or lost in a prior clobber cycle.

## Also verified
- ui/app.css: 30 lines contain raw hex colors (non-comment), confirming Verifier FAIL on Designer tokenization claim.
- index.html: 26 inline style attributes (hot note said "14" — count has grown since).
- All 6 sub-index files exist and are reachable.

## Action taken
Added staleness marker to ops/INDEX.md for the 5 missing scripts.
