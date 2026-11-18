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
Status (as of 2026-11-18): BUILT + unit-tested (Mechanic Phase 1-4 on Red sandbox) but NOT promoted to canonical memory_mirror.py at this root. The live mirror still executes mtime-LWW. See: memory/researcher/mirror-revert-fix1-promotion-gap-2026-11-18.md
Effort: Low for deployment (code exists + tested); Medium if integration gaps found during promotion

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
- Promotion-gap finding: memory/researcher/mirror-revert-fix1-promotion-gap-2026-11-18.md

## PRE-POPULATED HYPOTHESIS (from local pin-file forensics, 2026-11-18)

### Observed Pin-Burst Pattern (local memory/designer/, NOT from live mirror log)

| Date | index_html pins | ui file pins | Total | Notes |
|------|----------------|--------------|-------|-------|
| 2026-11-16 | 24 | 0 | 24 | UI split day: sizes 91KB to 10KB (monolithic to modular transition) |
| 2026-11-17 | 21 | 3 | 24 | Post-split stabilization; ui/app.css, ui/core.js, ui/uploads.js first pinned |
| 2026-11-18 | 1 | 0 | 1 | Quiet (window day 2) |
| **Total** | **46** | **3** | **49** | index.html = 94% of all pin events |

### Hypothesis for Frequency Table (to be CONFIRMED by live mirror log at closure)

1. **index.html will dominate the revert frequency table** - 94% local pin share predicts it will be the top-1 path in the live log's "most-reverted files" ranking, UNLESS other file types (ui/*.css, ui/*.js, memory/*.md) accumulate reverts from non-designer agents.

2. **Pin-burst events cluster on edit-heavy days** - 45 pins in 2 days (11-16 to 11-17) vs 1 pin on 11-18. The frequency table should separate these "burst" windows from organic steady-state reverts.

3. **Size discontinuity at the split boundary** - pre-split pins are ~91KB, post-split ~10KB. Any live-log events spanning this boundary will show a hash_mismatch trigger that is actually a STRUCTURAL change (UI split), not a sync bug. Recommend flagging these as "intentional structural change" in the final analysis to avoid miscounting them as failures.

### Methodology Note
This hypothesis is derived from LOCAL pin-file accumulation (each CANONICAL file = one successful pin-advance, which implies at least one prior revert cycle). It is a LOWER BOUND on actual reverts (some reverts may not produce a new pin if the content was restored to a previous version). The live mirror log will give the true count; this table provides the expected SHAPE for cross-checking.
