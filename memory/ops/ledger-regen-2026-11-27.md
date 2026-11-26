## 2026-11-27 - Ledger Regeneration (Scribe)

**Problem**: goal_ledger.json showed 56/111 (50%) while next10.json showed 73/111 (65.8%).
Per-agent drift: forge +5, archivist +5, orchestrator +4, pixel +3, scribe +2, builder +1.
Also internal inconsistency: header said 56 but per-agent fields summed to 54.

**Root cause**: Ledger was not regenerated after the 11-25 fix (which wrote 101/110).
A subsequent partial/stale parse overwrote it with undercounted values.
The `evidence_gated: true` flag means only goals with explicit `(verified:` markers count;
agents that marked `[REACHED]` without the evidence marker were not counted by the stale parser.

**Fix applied**: Re-ran `python memory/researcher/goal_ledger.py --json goal_ledger.json`.
Result: 75/111 (68%), internally consistent, per-agent aligned with next10 except forge (+2,
timing: ledger regenerated 11-27 vs next10 generated 11-26 23:26).

**Prevention**: Add a staleness guard - if `goal_ledger.json` is >24h old at start of any
auto-loop batch, auto-regenerate before dispatch. The Researcher's script handles this;
it just needs to be invoked. Suggested hook: first agent in each batch pass runs it.

**Evidence**: This file + regenerated goal_ledger.json (101573 B, generated 2026-11-27).
