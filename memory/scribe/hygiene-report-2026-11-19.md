# Memory Hygiene Report — 2026-11-19

Generated: 2026-11-19 00:45 by Scribe (memory/scribe/hygiene_report.py)

## Summary Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Total files | 1751 | — | — |
| Total size | 10677.0 KB | — | — |
| Files >5KB | 274 | 0 | ⚠️ |
| Orphaned files | 1461 | 0 | ⚠️ |
| Stale files (>30d) | 0 | <10% | ✅ |

## Files >5KB (should be split)

- `memory/archivist/kg_state.json` — 928.8 KB
- `memory/scribe/memory-hygiene-report.json` — 849.1 KB
- `memory/archivist/decay-report.md` — 519.4 KB
- `memory/archivist/manifest-20261118.json` — 514.3 KB
- `memory/mechanic/agent_portal_pre-decisions-v2-reland-2026-11-18.py` — 220.1 KB
- `memory/builder/canary/black/agent_portal.py` — 215.5 KB
- `memory/builder/canary/pale/agent_portal.py` — 215.5 KB
- `memory/builder/canary/red/agent_portal.py` — 215.5 KB
- `memory/scribe/agent_portal_CANONICAL_5b65f15bb4b5_2026-11-17x.py` — 211.4 KB
- `memory/builder/canary/agent_portal_slo_patched.py` — 210.8 KB
- `memory/archivist/knowledge_graph_manifest.json` — 210.2 KB
- `memory/archivist/hostdoc-consistency-v2-2026-11-18.json` — 171.3 KB
- `memory/designer/ledger_snapshot.json` — 85.3 KB
- `memory/verifier/visual_baseline.json` — 78.7 KB
- `memory/builder/agent_portal_r16_staged.py` — 78.2 KB
- `memory/builder/agent_portal_ops-r5_staged.py` — 77.0 KB
- `memory/archivist/knowledge_graph.json` — 63.3 KB
- `memory/archivist/manifest-20261117.json` — 59.7 KB
- `memory/scribe/durable_baseline.json` — 56.2 KB
- `memory/mechanic/goal-ledger-current.json` — 53.6 KB
- ... and 254 more

## Orphaned Files (not referenced by any INDEX.md)

- `memory/archivist/_patch2.py`
- `memory/archivist/_patch_hostdoc.py`
- `memory/archivist/api-ref-autogen-progress-2026-11-18.md`
- `memory/archivist/api-ref-diff-2026-11-18.md`
- `memory/archivist/api-ref-e2e-2026-11-18.md`
- `memory/archivist/api-ref-evidence.md`
- `memory/archivist/api_snapshot.json`
- `memory/archivist/apply_staged_patches.py`
- `memory/archivist/bundle-v2-item1-staleness-r73-2026-11-14.md`
- `memory/archivist/bundle-v2-item9-queue4-reword-gap-r74-2026-11-14.md`
- `memory/archivist/check_doc_file_refs.py`
- `memory/archivist/cycle3-goals-drafted-2026-11-17.md`
- `memory/archivist/dcabots-intake-2026-11-14.md`
- `memory/archivist/decay-report.md`
- `memory/archivist/doc-file-refs-report.json`
- `memory/archivist/doc-ref-scanner-progress-2026-11-18.md`
- `memory/archivist/dream-big-wishes-2026-11-14.md`
- `memory/archivist/evidence-goal1-delta-reporting-2026-11-18.md`
- `memory/archivist/evidence-goal1-kg-autoupdate-2026-11-18.md`
- `memory/archivist/evidence-goal1-kg-autoupdate-real-2026-11-18.md`
- `memory/archivist/evidence-goal1-kg-delta-confirmed-2026-11-18.md`
- `memory/archivist/evidence-goal1-knowledge-graph-hook-2026-11-18.md`
- `memory/archivist/evidence-goal1-scheduled-mirror-runs-2026-11-18.md`
- `memory/archivist/evidence-goal1-stale-verification-2026-11-18.md`
- `memory/archivist/evidence-goal2-handoff-protocol-v2-2026-11-18.md`
- `memory/archivist/evidence-goal3-api-ref-complete-2026-11-18.md`
- `memory/archivist/evidence-goal3-api-ref-diff-2026-11-18.md`
- `memory/archivist/evidence-goal3-api-ref-progress-2026-11-18.md`
- `memory/archivist/evidence-goal3-api-ref-restored-2026-11-18.md`
- `memory/archivist/evidence-misattribution-goal4-vs-goal7-2026-11-17.md`
- ... and 1431 more

## Remediation List

1. Split 274 files >5KB into modules
2. Add INDEX.md references or archive 1461 orphaned files
