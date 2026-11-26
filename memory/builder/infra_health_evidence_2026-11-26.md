# Builder Goal #4 — Autonomy-Infra Self-Health Probe (REACHED 2026-11-26)

**Artifact:** `memory/builder/infra_health.py` (209 lines) -> appends `memory/builder/infra-health.jsonl`.

## What it does
Liveness probe over Builder's own 5 autonomy scripts, each checked for: exists, compiles
(py_compile into a temp dir — no stray .pyc), and a fresh last-run marker. A script's
"last run" is the mtime of its real output artifact (honest liveness):
- fleet_mode_writer -> ops/fleet-mode.json
- convergence_fsm   -> ops/fsm-events.jsonl
- dispatch_filter   -> ops/dispatch-cache.json
- status_propagator -> ops/mode-freshness.json
- cycle_closeout    -> ops/cycle-closeout.jsonl

Per-record schema (stable for a Pixel widget + Forge gate):
`{ts, script, ok, exists, compiles, last_run, age_hours, latency_ms, error, flag, marker_source}`
plus a trailing `{type:summary, all_healthy, flagged[], max_age_hours}` line the watchdog reads.
Watchdog flags: `missing` (no source/marker), `compile-error`, `stale` (age > --max-age-hours, default 48h ~= 2 cycles).

## Verification (selftest, `--selftest`)
- (a) clean state (fresh stamps for all 5) -> all ok; REQUIRED_KEYS present on every record.
- (b) clear one marker (convergence_fsm) -> that exact script flagged `flag=missing`, no collateral flags on the other 4.
- (c) age a marker 72h (> 48h threshold) -> flagged `flag=stale`.
- (d) live probe (real artifacts, no stamps dir) serializes to valid JSONL.

Result: **SELFTEST PASS** (all four criteria asserted).

## Live run (2026-11-26T10:58Z)
All 5 scripts ok=true on real artifacts; summary `all_healthy:true, flagged:[]`. Ages:
mode_writer 0.07h, fsm 0.06h, dispatch_filter 47.95h (just under threshold), status_propagator 0.07h, closeout 39.5h.

## Notes for downstream
- Pixel: render the per-script `flag`/`age_hours` from infra-health.jsonl last line per script.
- Forge: gate can block a deploy if `summary.all_healthy=false` (any autonomy script degraded).
- Distinct from convergence_health.py / drift_detector.py: those watch fleet state; this watches Builder's own automation liveness (meta-self-healing).
