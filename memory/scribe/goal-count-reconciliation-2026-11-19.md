# Goal-Count Reconciliation (2026-11-19, Scribe)

Why: the auto-loop nudges reported open-goal counts that matched NEITHER counting
method in the repo. This snapshot pins the authoritative state so passes stop chasing
phantom goals. SSOT = strict ledger parser (memory/researcher/goal_ledger.py::parse_agent_file),
the same one the dashboard nudge (_agent_goals_block) uses.

| agent | total | reached | open(strict) | open(regex scan) | note |
|---|---|---|---|---|---|
| archivist | 10 | 1 | 9 | 9 |  |
| builder | 10 | 10 | 0 | 1 | regex over-counts (pointer:/recorded markers missed) |
| designer | 10 | 2 | 8 | 10 | methods disagree |
| mechanic | 10 | 10 | 0 | 0 |  |
| orchestrator | 20 | 20 | 0 | 0 |  |
| researcher | 12 | 12 | 0 | 0 |  |
| scribe | 10 | 10 | 0 | 0 |  |
| verifier | 11 | 11 | 0 | 0 |  |

## Findings
- **scribe = 10/10 reached, 0 open.** The '3 open' nudge this pass is STALE (predates the
  2026-11-19 verification sweep). No scribe goal needs work.
- **Genuinely open fleet-wide: archivist 9/10, designer 8/10.** Everyone else is 100% reached.
- **Method discrepancy:** regex scan_goals() flags builder#6 + 2 designer lines that the strict
  ledger counts as reached (they carry (pointer:)/(recorded) markers, not literal '(verified:').
  Consequence: open_items_scan.py over-reports. Recommend it delegate per-goal status to
  parse_agent_file() instead of its own regex so the tracker and dashboard agree.

## Routing for next pass (assist targets, oldest-first)
- Archivist unreachable this round -> its 9 open are seat-drafted; do NOT cross-talk.
- Designer + Mechanic ARE in-batch: Designer owns the real open work (8). Mechanic is 10/10
  reached, so its '4 open' nudge is also stale - it should assist, not self-verify.
