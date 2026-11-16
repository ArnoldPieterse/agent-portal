# Cycle-2 milestone risk register (Orchestrator goal #5)

Reviewed at each round end; >=3 dated updates required this cycle.

## 2026-11-16 ~15:1x (entry 1 — kickoff)
| # | Milestone | Risk | Likelihood | Impact | Mitigation / owner |
|---|-----------|------|-----------|--------|--------------------|
| R1 | Fleet-wide goal rounds | White's two seats (Orchestrator Q8_0, Researcher Q4_K_S) unloaded; only one tensor-split llama-server alive on both GPUs (measured 2026-11-16: PID 33560, :57451, VRAM ~27GB/GPU); Studio routing table stale -> all White alias requests 404 | HIGH (observed) | CRIT (chair absent = round loops on auto-resume, as seen 13:29-14:23) | Model-load governance live in portal (pre-run [MODEL LOAD STATUS] note + /api/models/status); user directive: skip loading for now; seat-drafted goals cover both lanes; load procedure documented in memory/llm/instances.md (RecoverAll task) |
| R2 | SLO pipeline (M4->B8->V4) | Longest critical path; tiles/enforcement useless without day-1 baseline | MED | MED | Mechanic#4 daily probe is the first deliverable; Builder#8 may ship /api/perf with empty windows until data exists |
| R3 | Canary deploy pipeline (B2) | Deploying to Red while Red :8099 is unreachable from White (C3 finding) | HIGH (observed) | MED | Sequence: C3 resolution (is Red portal running?) BEFORE canary targets Red; canary starts with Pale/Black only |
| R4 | Orphan backlog (324 cycle-1 baseline) | Batch-index decision deferred; index noise keeps growing | MED | LOW | Archivist batch-index proposal scheduled for mid-point review (this register) |
| R5 | Weekly chaos drill (M9) | Killing a portal on an already-unstable host could cascade | MED | HIGH | Drill order White->Pale->Black->Red with Red LAST; abort if C3 unresolved at that week |
| R6 | Evidence standard (O7) | 47% cycle-1 baseline suggests marker inflation returns as cycle scales | MED | MED | Weekly spot-checks via evidence_spotcheck.py (first run 2026-11-16: 5/5 = 100% on cycle-2 closures) |
| R7 | Sync clobbers | LWW mirror + 35-min clock skew; F-VER-01 showed a write can vanish from the served file | MED | HIGH | Three-layer defense live in charter (Builder#6 / Researcher#6 parity_audit.py disk==served / Scribe#6 durable copies); first parity run 2026-11-16: 0 findings |

Next review: end of next group round (dated entry 2 required).
