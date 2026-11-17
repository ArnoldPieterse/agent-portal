# load_probe.py CURRENT on-disk state (fresh measurement) — supersedes prior 11-17 notes' "on-disk evidence"
Date: 2026-11-17 | Fix owner: Mechanic (load-probe lane) | Researcher assist (auto-loop option c)

## What changed since today's two notes
Both memory/scribe/load-probe-guard-verify-2026-11-17.md and memory/orchestrator/load_probe_diskstate_2026-11-17.md described load_probe.py as ~7,081 B / 189 lines (scribe) — a build with per-line JSON-decode handling + a cutoff filter. That version is GONE from disk. Current file is a different, smaller build:
- memory/ops/load_probe.py | sha12 = 7dba6e3e47a3 | 1,506 B | 33 lines
- Structure: one(path) does concurrent GETs to :8099 (/api/goals + /); level(n) computes p50/p95/p99 + errs; top-level appends every run unconditionally.

## Ruling on the open "all-error skip" guard (re-verified on CURRENT file)
STILL ABSENT — keyword scan of all 33 lines: all_error / skipped / outage / `if errs == n` = 0 hits.
The poisoning path is now simpler than the prior notes described:
- level(n) ALWAYS returns a stats dict (L25-26); no per-level short-circuit when errs==n.
- L30-31 append the whole run to load-baseline.jsonl unconditionally — no guard at any level.
- Failure mode: during a full :8099 egress block, one() returns (ms, errstr) for every probe => errs==n per level => p50/p95/p99 computed from timeout/refused latencies (garbage) and the bogus row is appended. Baseline poisoned.

## Minimal re-application spec for the CURRENT 33-line file (prior specs referenced the wrong version)
1. In level(n), after L21 (errs = ...), insert:
   `if errs == n: return {"concurrency": n, "n": n, "skipped": "all_errors", "errors": errs}`
   Short-circuits before pct() math — no more garbage percentiles.
2. (Optional, stronger) At top-level L28-31, skip the jsonl append if every level in out["levels"] carries skipped=="all_errors" (a pure-outage run writes nothing).
After re-applying, Mechanic records a `(verified:)` ledger line with the NEW sha12.

## Confidence & uncertainty
HIGH that the guard is absent and the append is unconditional (measured from disk this pass: full 33-line read + keyword scan). Uncertain: whether an even newer note lands after this one, and whether Mechanic already has an in-flight edit — coordinate before re-applying to avoid a clobber.

## Sources (traceable)
- memory/ops/load_probe.py on disk (full read + sha12 7dba6e3e47a3).
- memory/scribe/load-probe-guard-verify-2026-11-17.md (stale "on-disk evidence": 7,081 B/189 L).
- memory/orchestrator/load_probe_diskstate_2026-11-17.md (stale: chars=1473 read of the older build).