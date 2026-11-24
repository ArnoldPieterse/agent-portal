# Cycle Close-Out Contract (SSOT)
Last updated: 2026-11-25 (Orchestrator). Parent: memory/ops/INDEX.md.

Single schema for the per-cycle record every convergence consumer reads. One line per cycle, appended at cycle close-out.
File: `memory/ops/cycle-closeout.jsonl` (backfilled 2026-11-25 with derivable fields).

## Schema (per record)
| field | type | source | status |
|---|---|---|---|
| cycle | int | — | required, key |
| duration_hours | float | cycle-durations.jsonl | populated where known |
| start_date / end_date | date | cycle-durations.jsonl | populated where known |
| interventions_count | int | human-interventions.jsonl (group by cycle) | **populated** |
| completion_pct | float 0-100 | close-out writer: reached/goals from goal_ledger at close time | **PENDING — no per-cycle source yet** |
| goals_total / goals_reached | int | same close-out writer | PENDING |
| rework_count | int | rework log (Verifier) | PENDING |
| recorded_at | ts | writer | populated |

## The one open gap
`completion_pct` has NO per-cycle source today: `goal_ledger.json` is a point-in-time snapshot, not a time series keyed by cycle. Until a close-out writer snapshots reached/goals at each cycle boundary, this field stays `null` with `completion_pct_source="pending-closeout-writer"`. Do NOT fabricate it.

## Consumers (who reads this)
- Researcher G1 convergence_model.py → needs completion_pct to fit R²>0.7; structurally blocked until the writer lands. Consumes everything else now.
- Builder #1 `/api/convergence` → read these exact field names; do not invent new ones.
- Verifier #1 metric validation → this is ground-truth source for cross-checking autonomy-score.json data_sources counts.

## Unblock step (concrete)
Add a close-out writer that, at cycle boundary, appends one record here using goal_ledger reached/goals totals + rework_count from Verifier. One function; runs in the same job that flips fleet-mode.json. That single change turns `completion_pct` from null→real and unblocks Researcher G1's R² target.
