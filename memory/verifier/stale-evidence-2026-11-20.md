# Evidence Freshness Audit — 2026-11-20

**Threshold:** 14 days  
**Goal files scanned:** 107  
**Total (verified:) markers:** 456  
**Stale/missing:** 1  
**Fresh:** 455

## STALE / MISSING Claims

### 1. `memory\goals\orchestrator.md:17` — ~~RESOLVED (false positive)~~
- **Date:** 2026-11-20
- **Reason:** missing evidence: memory/rosterprobe/INDEX.md
- **Evidence paths:** `agents.json`, `memory/rosterprobe/INDEX.md`
- **Resolution:** FP — line 17 correctly cites `memory/rosterprobe_archived_2026-11-20/INDEX.md` (exists); audit parser extracted wrong path. See: memory/verifier/stale-evidence-fp-orchestrator-rosterprobe-2026-11-20.md
