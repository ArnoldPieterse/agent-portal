# Mirror-Revert Day-7 Closure De-Risk — E2E Contract Test + Filler Hardening
Date: 2026-11-18 (auto-loop pass, goal #3)
Status: PROGRESS (goal still OPEN — gated on live window 11-17->11-24). This pass produced two
new artifacts that reduce day-7 closure risk WITHOUT touching the logged NEEDS-HUMAN seed wall.

## What was done (ONE concrete step, no re-probe of seed wall)
Goal #3's acceptance is a single command at ~11-24: `python memory/researcher/fill_analysis.py <live-log>`.
That chain = memory_mirror.log_event() [writer] -> parse_mirror_events.py + fill_analysis.py [consumers].
Prior passes validated each piece in ISOLATION (parse vs synthetic; filler vs a hand-built 7-day
synthetic) — but never the REAL writer's byte output routed through BOTH consumers together, and the
filler's confidence line had an unguarded timestamp parse. Both gaps closed this pass.

### 1. New: memory/researcher/mirror-e2e-contract-test.py (E2E contract test)
- Redirects the real memory_mirror.EVENT_LOG to a temp JSONL, drives the ACTUAL log_event() with the
  exact kwarg dicts from all 4 call sites (write push_root/push_mem/pull_mem, revert pin_drift),
  spanning a 3-day window (165 events).
- Feeds that SAME file through BOTH consumers via subprocess.
- Asserts: parse rc=0 + all 4 sections present; filler rc=0 + confidence line + by-kind table +
  top-3 reverting populated + trigger distribution + targeted fixes present.
- RESULT: **PASS** (rc=0, every assertion OK). Proves the writer's byte schema flows through both
  consumers with all sections + confidence intact.

### 2. New: fill_analysis.py hardened (tolerant timestamp parse)
- The confidence line did an UNGUARDED `strptime(t,'%Y-%m-%d %H:%M:%S')` — if a future mirror edit
  changed the timestamp format, day-7 one-command closure would raise ValueError at the exact moment
  of closure. (Hourly bucketing was already guarded; this line was not — asymmetric robustness.)
- Fix: added `_parse_ts()` trying 4 formats ('%Y-%m-%d %H:%M:%S', ISO-T, both +.%f); on any
  unparseable value it DEGRADES (confidence->LOW + WARN line) instead of crashing.
- NEGATIVE CASE PROVEN: fed a genuinely unparseable timestamp -> rc=0 (no crash), confidence=LOW,
  WARN 'timestamp format unrecognised' emitted. Pre-fix the same input crashed with unhandled ValueError.

## Net effect on day-7 closure risk
The single-command closure is now crash-proof to BOTH failure classes that could bite at 11-24:
(a) writer/consumer schema drift (proven by E2E test) and (b) timestamp-format drift (proven by
negative case). The only remaining gate is the live dataset itself, which is still gated on the
NEEDS-HUMAN seed (logged once in memory/ops/blockers.md, owner = non-sandbox White seat; NOT re-probed).

## Artifacts
- memory/researcher/mirror-e2e-contract-test.py  (E2E contract test, PASS)
- memory/researcher/fill_analysis.py             (hardened _parse_ts + degrade branch)
- runbook daily-sampling row updated: mirror-revert-closure-runbook-2026-11-17.md
