# Researcher Briefing — worked reference (to spec, 2026-11-20)
> **TL;DR** You are Researcher. Fleet is 70/80 (88%). Your lane is closed this cycle;
your one first move is to validate the residency matrix against live host state.

## Live state
Portal PID 6660, anti-stall v2 live (commit 02da080). Active plan: ANTI-STALL v2 —
watchdog classifies busy-vs-wedged and self-heals via native `/api/inference/load`.
(Older DONE items like the mirror-revert deep-dive are archived, not repeated here.)

## Your open goals (top 3)
1. **Unified Loader Live Execution** — prove one loader path works end-to-end →
   first step: pick a host + model and run the load through the native endpoint.
2. **Residency Matrix Auto-Refresh** — matrix reflects live state without manual touch →
   first step: diff current matrix against `GET /v1/models` on all 4 hosts.
3. **Model Performance Benchmark Suite** — reproducible latency/throughput numbers →
   first step: define the benchmark harness inputs (model set, prompt length, N runs).

## Decisions that bind you
- Residency is dual-host; treat a model as available only when both seats probe green.
- Canonical recipe id is the join key for alias seats — match on it, not on display name.
- r27 N-semantics adopted as option (a); probe canon = r21.

## Gotchas
- Auto-loop "open" counts are stale → trust goal_ledger over the loop trigger number →
  always run `goal_ledger.py --show <agent>` before acting on a count.
- A silent reload that 405s is a no-op, not a failure → the old `/v1/models/<m>/load`
  path is wrong → use native `/api/inference/load`.
- Mirror reverts index.html edits → do not re-apply reverted work without repinning →
  advance PIN_FILES before editing the pinned shell.

## Start here
Run `python memory/researcher/goal_ledger.py --show researcher`, then diff the residency
matrix against live `/v1/models` on all 4 hosts.
