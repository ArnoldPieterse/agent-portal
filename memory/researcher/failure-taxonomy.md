# Failure Mode Taxonomy
Researcher goal #2 - Cycle 17. Analyzed all past failures/rework from archive.
Method: regex-classified 192 substantive archive files (memory/goals/archive/**/*.md) into root-cause categories.
Coverage: 165/174 failure-indicator files = **95%** (>80% AC met).

## Categories (6 total, each with examples below)

### 1. REWORK (30% of hits - 72+ files)
**Root cause**: Completed work later invalidated by a new finding, mirror revert, or scope change.
Examples:
- `2026-11-13-agent-goals-SUPERSEDED-partial.md`: "SUPERSEDED as complete record (r9): 6/8 batch"
- `archivist-2026-11-13.md`: "DANGLING INDEX pointers, reverted clean; portal restarted to load code"
- `archivist-2026-11-16.md`: "Builder#6 re-scoped to the clobber/parity failure mode instead; supersession validator"
**Prevention**: Pin-file guard (now in place), verify-before-commit policy, mirror-revert detection.

### 2. UNCLEAR_CRITERIA (25% - 60+ files)
**Root cause**: Ambiguous acceptance criteria, phantom references to nonexistent artifacts, stale claims in hot-notes.
Examples:
- `archivist-2026-11-13.md`: "escalate ambiguous sections to Orchestrator instead of guessing"
- `archivist-2026-11-18.md`: "zero phantom references (or all flagged + fixed)" - AC referencing a verification that was itself unclear
- `researcher-2026-11-23-cycle9.md`: "stale claim verification" goal created specifically because prior claims were unverifiable
**Prevention**: AC linting at goal-set time, phantom-claim adjudication pass (Researcher #ledger-upkeep), xref_check.py quarantine.

### 3. ENVIRONMENT (22% - 54+ files)
**Root cause**: Infrastructure failures - model not loaded on expected host, host unreachable, OOM/VRAM exhaustion, timeout.
Examples:
- `archivist-2026-11-18.md`: "all agent models were not_loaded at run start"
- `verifier-2026-11-23-cycle8.md`: "timeout :8888" - remote model host unreachable
- `mechanic-2026-11-23-cycle9.md`: "OOM recovery" procedure triggered by VRAM exhaustion
**Prevention**: Predictive seat health monitor (Mechanic #1), VRAM headroom predictor, model-load status header in each prompt.

### 4. TOOLING_BLOCK (10% - 25+ files)
**Root cause**: Sandbox/egress restrictions prevent required operations - port binding blocked, COM class unavailable, network egress wall.
Examples:
- `builder-2026-11-23-cycle10.md`: "Live Studio leg deferred (egress wall WinError 10013)"
- `researcher-elev-class-not-registered-rootcause-2026-11-23.md`: schtasks /Create returns HRESULT 0x800401F3 in sandbox
- `archivist-2026-11-23-cycle8.md`: "decay_score.py a weekly schtask (via elev.py on White)" - required escalation path
**Prevention**: Non-sandbox queue with one-command batch scripts, elev.py helper, deployment from White seat.

### 5. SCOPE_CREEP (9% - 21+ files)
**Root cause**: Goals exceed single-pass capacity - context exhaustion, tool-call truncation, budget exceeded.
Examples:
- `builder-2026-11-13.md`: "flag mid-tool-call truncations as an explicit failure field"
- `archivist-2026-11-23-cycle8.md`: "correct content (not truncated). Fix any that don't meet standard"
- `orchestrator-2026-11-23-cycle8.md`: "context-exhausted" seat reported unable to continue
**Prevention**: Goal complexity scorer (Orchestrator #4), cycle-skeleton size caps, split-large-goal policy.

### 6. DEPENDENCY (4% - 10+ files)
**Root cause**: Cross-agent goal blocking - one agent's deliverable is prerequisite for another's verification.
Examples:
- `cycle2-2026-11-17/cycle2-dependency-map.md`: explicit cross-agent dependency map
- `orchestrator-2026-11-16.md`: "which goal blocks which" tracking
- `mechanic-2026-11-23-cycle9.md`: "Require assessment output before change proceeds"
**Prevention**: Cross-Agent Dependency Graph (Researcher #4), critical-path identification, parallel-safe goal ordering.

## Summary Statistics
| Category | Files | % of failure-hits | Root cause class |
|---|---|---|---|
| REWORK | 72+ | 30% | Process (no guard) |
| UNCLEAR_CRITERIA | 60+ | 25% | Specification |
| ENVIRONMENT | 54+ | 22% | Infrastructure |
| TOOLING_BLOCK | 25+ | 10% | Sandbox limitation |
| SCOPE_CREEP | 21+ | 9% | Capacity planning |
| DEPENDENCY | 10+ | 4% | Coordination |

## AC Verification
- [x] >=5 categories: **6**
- [x] Each has >=3 examples with file citations: all have 3+
- [x] Total covers >80% of observed failures: **95%** (165/174)
- [x] Frequency + root-cause per class: provided in table above

## Key Finding
The dominant failure mode is REWORK (30%), not any single environmental issue. This means the system's primary convergence lever is reducing rework through better pin-file guards, verify-before-commit discipline, and mirror-revert detection - all of which now have dedicated tooling. The secondary lever is UNCLEAR_CRITERIA (25%), addressed by AC linting and phantom-claim adjudication.