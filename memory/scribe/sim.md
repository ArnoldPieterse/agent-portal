# SIM — Self-Improvement Memory (Scribe lane)
# Source: arxiv 2611.18856v1 (Yu et al., Google Cloud AI, 2026)
# Groups recurring synthesis/compression problems; each entry records rationale → prediction → observation → provenance.
# Consult before any compression or synthesis decision: retain / revise / replace / remove based on history below.

## Problem: compression-fidelity-loss
- a1 (2026-11-14): Synthesis index canonical chain (r61→r72→r73) with supersession pointers
  - rationale: repeated full rewrites lost context; need stable "current" pointer + audit trail of prior versions
  - predicted: agents can always find the latest synthesis without reading all prior versions
  - observed: PASS — chain works; but 4 stale files accumulated before cleanup (index grew to 5 entries)
  - provenance: memory/scribe/synthesis-index-canonical-r73-8e194239-2026-11-14.md
- a2 (2026-11-26): Convergence memory compression (goal #5) — 5 cycles → 547 tokens, 3 decisions preserved verbatim
  - rationale: fleet-history.md was growing linearly; needed fixed-size rolling summary with lossless decision preservation
  - predicted: compression stays under 600 tokens for any window of ≤8 cycles while preserving all "decision" lines verbatim
  - observed: PASS — 547 tokens, archive created at memory/scribe/archive/fleet-history/
  - provenance: memory/scribe/fleet-history.md
- **Decision rule**: When compressing, NEVER paraphrase a decision line (one-line rationale + owner). Preserve verbatim. Compress only narrative/context. Archive the pre-compression version before overwriting.

## Problem: stale-evidence-detection
- a1 (2026-11-17): Memory-integrity reconciliation — 256 issues found, 128 genuine / 128 false-positive
  - rationale: automated integrity check flagged files as "missing" when they were renamed or moved
  - predicted: separating genuine from false-positive reduces noise; genuine set is actionable
  - observed: PASS — resolve_target bug identified (checked old path without following supersession pointer); 128 true issues catalogued
  - provenance: memory/scribe/memory-integrity-reconciliation-2026-11-22.md
- a2 (2026-11-27): Ledger regeneration discrepancy flag — forecast said 94/111 but only 69 had dated evidence
  - rationale: goal_ledger.json was regenerated from stale source; numbers didn't match what agents actually recorded
  - predicted: cross-checking ledger against actual evidence files catches drift before it propagates to dashboard
  - observed: PASS — discrepancy flagged, Archivist regenerated root goal_ledger.json (evidence-stale-goal-ledger-regen-057.md)
  - provenance: memory/scribe/ledger-regen-discrepancy-flag-057.md
- **Decision rule**: Before citing any fleet-wide number (X/Y goals), verify it against the source evidence files, not just the ledger JSON. If discrepancy > 5%, flag and regenerate.

## Problem: contradiction-between-agents
- a1 (2026-11-16): Contradiction detector (cycle-2 goal) — automated scan for conflicting claims
  - rationale: two agents reported different states for the same artifact; needed systematic detection
  - predicted: detector catches ≥90% of true contradictions with <5% false positives
  - observed: PARTIAL — detector built and tested on synthetic data; real-world FP rate higher due to temporal ordering (agent A was right at time T1, agent B was right at T2)
  - provenance: memory/scribe/contradiction-detector-evidence-2026-11-16.json
- a2 (2026-11-27): Convergence status brief — fixed I3 false-negative where incidents.jsonl was missing recovery fields
  - rationale: convergence_contract.py reported NOT CONVERGED because it checked for a field that wasn't being written
  - predicted: adding the missing field + re-running contract flips I3 to PASS
  - observed: PASS — cycle 18 now reports CONVERGED; root cause was schema drift (field added to spec but not to writer)
  - provenance: memory/scribe/convergence-status-2026-11-27.md
- **Decision rule**: When two agents contradict, check TEMPORAL ORDER first (who was right when?). If both are time-correct, it's drift not contradiction. Only flag as true contradiction if same-timeframe claims conflict.

## Problem: index-staleness-orphan-files
- a1 (2026-11-16): Orphan sweep + self-healing index (cycle-2 goal)
  - rationale: INDEX.md accumulated pointers to files that were renamed/deleted; agents following stale pointers wasted context
  - predicted: automated sweep catches orphans within one cycle of the rename/delete
  - observed: PASS — orphan-sweep-2026-11-16.json shows 0 dangling after sweep; but recurrence requires running sweep after every file operation
  - provenance: memory/scribe/orphan-sweep-2026-11-16.json
- a2 (2026-11-27): Archivist size_guard_report — memory tree at 96.71 MB, FAIL over 5 MB limit
  - rationale: files accumulate without pruning; need hard size guard that triggers automatic archiving
  - predicted: with prune_memory_tree.py in ops/, tree stays under 100 MB after each run
  - observed: IN PROGRESS — dry-run reclaims 352 MB (1.3GB→966MB); not yet scheduled as recurring task
  - provenance: memory/ops/prune_memory_tree.py (Builder), Archivist size_guard_report.md
- **Decision rule**: After ANY file create/rename/delete in memory/, update the relevant INDEX.md in the same pass. If a sweep finds >3 orphans, investigate why the writing agent didn't update its index.

## Problem: goal-drift-across-cycles
- a1 (2026-11-26): Goal-set drift detector (goal #6) — 6 cycles compared, 22 drift events detected
  - rationale: goals subtly change meaning as context shifts; without detection, agents optimize for the wrong target
  - predicted: detector flags semantic drift when a goal's acceptance criteria text changes >20% between cycles
  - observed: PASS — synthetic tests pass; real data shows 22 events (mostly benign rewording, 3 substantive)
  - provenance: memory/scribe/goalset_drift.py
- **Decision rule**: When a goal's wording changes between cycles, check if the ACCEPTANCE CRITERIA changed. If only description changed, it's cosmetic. If AC changed, flag as drift and require owner confirmation before continuing work.

## Problem: context-budget-management
- a1 (2026-11-25): Memory modularity rule — pointer map + on-demand leaf loading
  - rationale: full memory dumps exceeded context window; agents needed to load only relevant modules
  - predicted: with INDEX.md as pointer map, each agent loads <2 KB of pointers + only the specific leaves it needs
  - observed: PASS — system works; but some agents still paste whole modules into chat (violating the rule)
  - provenance: memory/portal/file-modularity.md
- a2 (2026-11-27): SIM adoption (this file) — structured problem-grouped memory replaces chronological log
  - rationale: chronological evidence files are hard to consult for "what worked last time I tried X"; SIM groups by problem so the answer is one section read
  - predicted: next time a recurring problem arises, I can check SIM in <500 tokens and decide retain/revise/replace/remove without re-reading all prior evidence
  - observed: PENDING (first entry; will validate on second occurrence of any listed problem)
  - provenance: memory/scribe/sim.md (this file)
- **Decision rule**: Before starting work on a known problem type, read the relevant SIM section first. If the decision rule says "retain", do the same thing. If it says "revise", note what changed and why. Record the new attempt in SIM after completion.
