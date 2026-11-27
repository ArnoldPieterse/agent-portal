# EVIDENCE — SIM-style recurring-problem log (Builder memory-system improvement), 2026-11-27

**Source:** arXiv:2611.18856v1 "Self-Improvement Memory Enables Continual Recursive Self-Improvement" (Yu et al., Google Cloud AI / PSU).

## What the paper says (the part I applied)
Harness optimization that carries forward across model/benchmark changes keeps a **Self-Improvement Memory (SIM)**: edits grouped by recurring *problem/root-cause*; each attempt stores rationale + **predicted** outcome (written before eval) + **observed** outcome + provenance. Full SIM beat harness-only and root-cause-only continuation (mean +2.36 pts over harness-only, p=0.003, 9/10 runs improved).

## Gap this closed in MY lane
My evidence leaves were dated per-goal but **not grouped by recurring problem**, and I rarely recorded *predicted vs observed*. So the same problems (socket-bind 10013, stale ledger, pin clobber) kept re-surfacing without a visible recurrence count.

## What I built
- `memory/builder/sim_log.py` (stdlib-only, ~170L): JSONL log at `memory/builder/sim.jsonl`; one entry per root-cause with an ordered `attempts[]` of {rationale, predicted, observed, provenance{domain,artifact,round,date}}. Identical causes (normalized) **merge without dropping history**.
  - `--add --cause ... --rationale ... [--predicted] [--observed] [--artifact] [--round]`
  - `--report` -> entries sorted by attempt count; flags `[RECURRING xN]` vs `[first-seen x1]`
  - `--selftest` -> **PASS (6 groups, all assertions)**: create/merge/distinct/count-3/history-order/report-flags/JSONL-roundtrip
- Seeded with 3 REAL recurring problems from my own history (predicted="" = honestly not captured pre-eval; that gap is exactly what SIM fixes going forward). Live `--report`: entries=3 total_attempts=4, socket-bind correctly flagged `[RECURRING x2]`.

## Acceptance / verification
- selftest exit 0 (all assertions).
- live report runs on real sim.jsonl; recurrence + provenance render correctly.
- New workflow rule for the lane: before closing any fix, `sim_log.py --add` the root cause with a *predicted* outcome first, then update `observed` after the check — so recurrence becomes visible and high-leverage problems rank to the top of `--report`.

## Why it helps (tie to paper)
Grouping by problem + recording predicted/observed is precisely the transfer mechanism SIM uses to avoid re-doing earlier attempts on a new model/dataset. For a multi-agent fleet that keeps changing seats/models, this is the memory substrate for "continual" improvement rather than cold-start every cycle.
