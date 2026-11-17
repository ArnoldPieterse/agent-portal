# Mirror-Revert Frequency Analysis (goal #3) - TEMPLATE

Pre-drafted 2026-11-18. Fill with live data at 11-24 (or per contingency table).
This file IS the analysis leaf; the date in filename updates to actual analysis date.

## Data Source
- Log: Z:\mirror_events.log
- Live event window: [FILL: first-to-last timestamp]
- Total live events: [FILL]
- Parse command used: `python memory/researcher/parse_mirror_events.py Z:\mirror_events.log`

## Frequency Table

### By kind
| kind | count | pct |
|------|-------|-----|
| write (push_root) | [FILL] | |
| write (push_mem) | [FILL] | |
| write (pull_mem) | [FILL] | |
| revert | [FILL] | |

### By path (top-3 reverting)
| path | revert count | trigger | notes |
|------|-------------|---------|-------|
| [FILL] | | | |
| [FILL] | | | |
| [FILL] | | | |

### By hour (distribution check)
[INSERT hourly histogram from parse output]

## Mechanism Assessment
- Are observed reverts consistent with known pin_drift mechanism? [Y/N + evidence]
- Any NEW trigger not seen in cycle 2? [FILL]
- Correlation with agent activity? [FILL if applicable]

## Targeted Fixes (beyond auto-repair daemon)

### Fix 1: Pin-stability guard
Mechanism: [FILL based on data. Expected: files pinned by PIN_FILES in memory_mirror.py revert when a non-canonical copy is pushed. A pre-write hash check would catch drift before it propagates.]
Implementation hint: Add sha256 comparison at push_root/push_mem: if incoming file hash differs from current AND file is in PIN_FILES list, skip write + log warning instead of silent overwrite.
Effort: Low (one conditional in memory_mirror.py)

### Fix 2: Per-file epoch stamping (from goal #1 spec)
Mechanism: [FILL. Expected: LWW conflict resolution causes legitimate edits to be reverted by a stale pull. Epoch stamps per file would make the mirror reject stale writes.]
Implementation hint: See memory/researcher/sync-semantics-spec-2026-11-17.md, Data Model section (epoch field in .meta.json per file). Migration path: 4-phase, non-breaking.
Effort: Medium (requires spec implementation by Mechanic)

### Fix 3: [FILL if data reveals a third mechanism]
Mechanism: [FILL]
Implementation hint: [FILL]
Effort: [FILL]

## Confidence + Residual Uncertainty
- Dataset size: [N events / M days] -> confidence level: [HIGH/MEDIUM/LOW per contingency table]
- Known limitations: [FILL - e.g., "shorter than 7-day window; absolute frequency undercounted"]
- What would change this analysis: [FILL]

## Cross-references
- Instrumentation: memory/researcher/mirror-revert-instrumentation-2026-11-17.md
- Pipeline validation: memory/researcher/mirror-revert-pipeline-validation-2026-11-17.md
- Closure runbook + contingency: memory/researcher/mirror-revert-closure-runbook-2026-11-17.md
- Sync semantics spec (goal #1): memory/researcher/sync-semantics-spec-2026-11-17.md
