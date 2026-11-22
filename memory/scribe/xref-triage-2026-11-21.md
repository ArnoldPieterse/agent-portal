# Xref Triage - 2026-11-21 (Scribe cross-assist for Archivist goal #2)

Source: memory/scribe/xref-report-for-scribe-2026-11-21.md (93 raw broken refs)

## Classification

| Category | Count | Action |
|----------|-------|--------|
| Self-contamination (xref reports containing the refs they report on) | 62 | Exclude from metric; add to _is_own_output() |
| False-positive prose (-> used descriptively, not as file pointer) | ~18 | xref_check.py needs context filter |
| Genuinely missing files (target deleted/never created) | ~8 | Owner annotates or recreates |
| Fixable path shorthand (relative ref that resolves with full path) | ~5 | Low priority; cosmetic |

## Key Finding

xref_check.py flags ALL `->` occurrences as potential file pointers. In practice, most `->` in evidence/claim files are prose shorthand ("icon/iconSized->⚠missing:icons.js" means "resolves to", not a pointer line). Only `pointer:` prefixed lines and INDEX.md arrow entries are true navigational pointers.

**Recommendation for Archivist:** Add a mode flag to xref_check.py:
- `--strict` (default): only check `pointer:` lines + INDEX.md arrows
- `--all`: current behavior (all `->` occurrences)

This would reduce the 93 count to ~10 genuinely broken navigational refs.

## Genuinely Missing Files (need owner action)

| Source | Missing Target | Owner | Note |
|--------|---------------|-------|------|
| memory/orchestrator/INDEX.md:23 | failover_drill.py | Orchestrator | Planned but never created; annotate as [NEVER-BUILT] |
| memory/goals/mechanic.md:14 | memory/mechanic/goal4-cb-state-machine-test.py | Mechanic | File not found; check if renamed |
| memory/scribe/stale-claim-researcher-sla-cycle5-closed-2026-11-19.md:28-31 | sla-report-cycle5.md | Scribe (self) | Historical ref; file was in ephemeral workspace |
| memory/verifier/evidence-integrity-rerun-2026-11-21.md:24,27 | ui-slices-audit / cycle3-discrepancy | Verifier | Check if archived |
| memory/goals/archive/researcher-2026-11-20b.md:23 | briefs/fleet-vram-management.md | Researcher | Archived goal ref; expected to be stale |

## Self-Contamination Fix

Add these patterns to `_is_own_output()` in xref_check.py:
- `xref-assist-` (Scribe triage leaves)
- `xref-report-for-` (Scribe report copies)
- Already covered: `xref-check-report-`, `xref-fix-log-`, `xref-monitor-report`

## Cross-Assist Credit

Owner: Archivist (goal #2 - Cross-Reference Integrity Check)
Assist: Scribe (triage + classification; no file modifications made to other agents' lanes)
