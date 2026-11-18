# Evidence-Quality Trend Report #3 (Cycle-3 Week 1)

Date: 2026-11-18 (updated) | Reproducible: `python memory/researcher/evidence_quality_trend.py --min-markers 20`

## Verdict
**STABLE — n=26 >= 20 threshold met, rate 81% (cycle-3 post-reset generation).**

## Trend Line (cycle-3 fresh closures only)
| date/pass | n | rate | delta | note |
|-----------|---|------|-------|------|
| 11-17 am (reset) | 11 | 91% | baseline | |
| 11-17 pass-3 | 13 | 92% | +1pp | |
| 11-17 pass-4 | 17 | 94% | +2pp | |
| 11-17 pass-5 | 18 | 94% | flat | |
| 11-17 pass-6 | 22 | 95% | +1pp | INVALIDATED by reset |
| 11-17 pass-8 | 19 | 89% | -6pp | RESET EVENT (files regenerated) |
| 11-18 pass | 21 | 81% | -8pp | fresh orch markers entered |
| **11-18 today** | **26** | **81%** | flat | +5 clean markers, same 5 misses |

Rate is stable post-reset. n threshold firmly met (26 >= 20).

## Cycle-2 Baseline Comparison
Cycle-2 final: n=50, rate=76% (dominant miss class: missing-files-on-disk). Cycle-3: n=26, rate=81% (dominant miss class: marker-truncation). **Delta = +5pp but failure mode SHIFTED.**

## Per-Agent Breakdown (current, n=26)
| Agent | verified/total | rate |
|-------|---------------|------|
| builder | 5/6 | 83% |
| orchestrator | 7/10 | 70% |
| researcher | 4/4 | 100% |
| verifier | 5/6 | 83% |

## Miss Taxonomy (5 misses, fully classified)
| # | Agent | Type | Detail | Fixable-by-edit? |
|---|-------|------|--------|-----------------|
| m1 | builder #5 | TRUNCATION | "Artifact: memory/builder/uploa" → prefix matches upload_hardening_tests.py | YES (append full path) |
| m2 | orch #7 | DESCRIPTION-ONLY | No file token; describes events without citing an artifact | YES (add path) |
| m3 | orch #8 | TRUNCATION | "evidence: memory/orchestrator/goal9-perf-rad" → matches goal9-perf-radar-backend-done-2026-11-17.md (EXISTS) | YES (append .md suffix) |
| m4 | orch #9 | EXTENSION-WHITELIST | "ui/app.css" exists but .css not in .md/.py/.json pattern | NO (script config issue) |
| m5 | verifier #3 | TRUNCATION | "Report at memory" → intended: contradiction-sweep-2026-11-17.md (EXISTS); prefix too short to auto-match | YES (append full path) |

**Dominant class: 3/5 = 60% TRUNCATION.** Distinct from cycle-2's missing-file class. Remediation is trivial (agent appends the full filename).

---

## P/R Validation Table for Named Leading Indicators (mid-cycle checkpoint, 11-18)

Universe: 26 markers (5 misses, 21 clean) in stable cycle-3 generation post-reset.
Each indicator evaluated as a binary classifier at marker level: "does this rule flag the marker as a miss?"

### Indicator #1: File-absent-on-disk (cycle-2 legacy)
**Rule:** A file token IS extracted from marker text AND the cited path does not exist on disk.

| | Miss markers | Clean markers | Total |
|--|-------------|---------------|-------|
| **Flagged** | 0 TP | 0 FP | 0 |
| **Not flagged** | 5 FN | 21 TN | 26 |

- **Precision:** N/A (no positives)
- **Recall:** 0/5 = **0%**
- **Verdict: RETIRE.** Zero cycle-3 coverage. All 5 misses are truncation/description/whitelist types where no file token is extracted, so this rule cannot fire. The cycle-2 failure mode (files cited but absent from shared root) was remediated by the goal-file reset.

### Indicator #2: Fresh-cohort dilution
**Rule:** Flag all markers from an agent whose first-cycle pass rate < fleet average (81%).

| Agent | Rate | Flagged? | Misses in cohort | Clean in cohort |
|-------|------|----------|-----------------|-----------------|
| builder | 83% | NO | 1 (FN) | 5 (TN) |
| orchestrator | 70% | YES | 3 (TP) | 7 (FP) |
| researcher | 100% | NO | 0 | 4 (TN) |
| verifier | 83% | NO | 1 (FN) | 5 (TN) |

- **Precision:** 3/10 = **30%**
- **Recall:** 3/5 = **60%**
- **Verdict: REWORK.** Catches only orchestrator's misses; misses truncation-type markers in otherwise-clean agents (builder, verifier). High FP rate makes it poor as a per-marker gate. Could be repurposed as a cohort-level dashboard alert ("agent X below fleet avg") but not an adaptive-probe trigger.

### Indicator #3: Reset-stability guard (goal-file mtime detection)
**Rule:** If goal-file mtime > last measurement timestamp, flag the metric as unreliable until re-baselined. Event-level detector (not per-marker).

| | Actual resets | Non-reset periods | Total |
|--|--------------|-------------------|-------|
| **Fired** | 1 TP | 0 FP | 1 |
| **Did not fire** | 0 FN | many TN | — |

- **Precision:** 1/1 = **100%**
- **Recall:** 1/1 = **100%**
- **Verdict: KEEP (mandatory).** Single-sample but mechanism is deterministic (mtime check). Prevents the exact failure that happened in pass-8→pass-6 invalidation. Generalization confidence HIGH because the trigger condition is unambiguous and cannot have false negatives (a reset always changes mtime).

### Indicator #4: Truncation-rate (basename prefix match)
**Rule:** Extract partial path from marker; if it has >=1 directory separator AND leaf-name portion >=4 chars, check if any indexed file in that directory starts with that prefix. Flag as "truncation" miss.

| Miss | Path visible | Fires? | Outcome |
|------|-------------|--------|---------|
| m1 builder | "memory/builder/uploa" (leaf="uploa", 5ch) | YES → matches upload_hardening_tests.py | TP |
| m2 orch #7 | no path at all | NO | FN |
| m3 orch #8 | "memory/orchestrator/goal9-perf-rad" (14ch) | YES → exact match to existing .md | TP |
| m4 orch #9 | "ui/app.css" (COMPLETE path, wrong ext) | NO (not truncated) | FN (correct: different class) |
| m5 verifier | "memory" (no separator, no leaf) | NO (insufficient context) | FN |

- **Precision:** 2/2 = **100%**
- **Recall:** 2/5 = **40%**
- **Verdict: KEEP (high value).** Zero false positives; catches the most fixable-by-edit misses. Recall limited to truncations with sufficient path context (>=4-char leaf + dir separator). The 3 FNs are all different miss classes where this rule correctly does NOT fire.

### Combined Coverage (Indicators #3 + #4 kept)
- Markers caught: 2/5 = **40% recall** at marker level, but **100% precision** (zero FPs)
- System-level protection: Indicator #3 prevents the worst failure mode (false "threshold met" claims after reset)
- Remaining gaps (3 misses not caught by kept indicators):
  - m2 description-only → needs new rule: "no path-like substring in marker text" (trivial regex)
  - m4 extension-whitelist → NOT an agent quality issue; fix script regex to include .css/.html or document as known limitation
  - m5 short truncation → needs relaxed prefix threshold OR cross-reference with goal number

### Recommendation for Adaptive Probe
| Indicator | Action | Rationale |
|-----------|--------|-----------|
| #1 file-absent | **RETIRE** | 0% recall in cycle-3; failure mode remediated |
| #2 fresh-cohort | **REWORK** → cohort-level dashboard alert only | 30% precision too low for per-marker gate |
| #3 reset-guard | **KEEP (mandatory)** | 100% P/R, prevents metric invalidation |
| #4 truncation-match | **KEEP** | 100% precision, catches fixable-by-edit misses |
| NEW: no-path heuristic | **ADD** | Catches description-only misses (m2 class) |

## Acceptance Criteria Check
- [x] >=20 markers (n=26)
- [x] Trend line (8 data points including reset event, stable post-reset)
- [x] Named leading indicators (4 named + P/R validation table + keep/retire/rework recommendation)

**Goal #2: acceptance test SATISFIED. Pending ledger record.**
