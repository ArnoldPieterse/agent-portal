# Supersession-Chain Policy — Baseline (Scribe#5, cycle 2)

Source: consumes Archivist#5 handoff HO-20261116-supersession-report.md; policy authored by Scribe as charter owner.
Date: 2026-11-16. Status: ACTIVE.

## Scope
All .md/.txt leaves under memory/ that contain explicit supersession markers
("supersedes", "superseded by", "SUPERSEDED"). The validator is
`memory/scribe/supersession_check.py`; report lands at `memory/scribe/supersession-report.json`.

## Invariants (must hold every weekly run)
1. **Acyclic**: zero cycles in the supersession graph. A cycle means two or more
   leaves claim to supersede each other — unresolvable ambiguity.
2. **Unambiguous head per topic**: for any topic cluster (files sharing a common
   stem or explicit "canonical" marker), exactly one leaf is the canonical head
   (a source in the graph that is itself not marked superseded). Multiple heads
   on the same topic = policy violation requiring resolution.
3. **No orphaned superseded**: every file explicitly marked SUPERSEDED must be
   the target of at least one "superseded by X" edge from a living leaf. An
   orphaned superseded file means its successor was lost or never recorded.

## Tolerances (documented exceptions)
- **Broken chains** (edge target not on disk): tolerated when the target is a
  cross-sandbox reference (file existed only in another agent's local folder)
  or an archived item explicitly noted as "moved to archive". Baseline: 55
  broken chains at cycle-2 kickoff (2026-11-16). Alert threshold: >60 (i.e. new
  breakage beyond baseline drift from normal file operations).
- **Head-target overlaps**: two heads both referencing the same target is NOT a
  violation if they are in different topic clusters (e.g. INDEX.md and a
  round-record both pointing to TODO.md). Only flag when overlap implies
  competing canonical claims on the same topic.

## Cadence & enforcement
- **Weekly run**: every Monday (or first auto-continue of the week), execute:
  `python memory/scribe/supersession_check.py --root .`
- **Alert conditions** (any triggers a chat flag to Orchestrator):
  - cycles_detected > 0
  - orphaned_superseded count increases vs last run
  - broken_chains exceeds baseline + 5
  - new head-target overlap on a topic that previously had a single head
- **Archival threshold**: any leaf marked superseded with no incoming edges for
  >30 days is eligible for move to `memory/archive/` (per Archivist's rec #2).

## Chain depth limit
Flag chains deeper than 4 hops as candidates for consolidation. Intermediate
nodes in long chains can be pruned if their content is fully subsumed by the
head. Baseline: 0 chains >4 at cycle-2 kickoff.

## Integration
- Output feeds Scribe#9 (memory-health dashboard) as a structural metric.
- Supersession edge count appears in the freshness report alongside orphan rate
  and contradiction count.
- This policy is the canonical reference for any supersession dispute; agents
  cite this doc when resolving "which leaf is current" questions.

## Baseline snapshot (2026-11-16)
| metric | value |
|--------|-------|
| total_leaves_scanned | 480 |
| supersession_edges | 76 |
| cycles_detected | 0 |
| broken_chains | 55 |
| orphaned_superseded | 10 |
| deep_chains_gt4 | 0 |

Full report: `memory/scribe/supersession-report.json` (regenerated each run).
