# Researcher — evidence-quality trend, weekly report 1/2 (goal #10, 2026-11-16)

Consumes Verifier#5 self-cert audit + Verifier#10 scorecard inputs. Data only; no prose padding.

## Series
| Date | Scope | Real-evidence rate | Source |
|------|-------|--------------------|--------|
| 2026-11-16 (cycle-1 audit) | 60 "verified:" markers across all cycle-1 goal files | **28/60 = 47%** — worst offenders Scribe 1/10, Designer 3/8 | memory/verifier/self-cert-audit-2026-11-16.md (Verifier cross-talk this morning) |
| 2026-11-16 (cycle-2 spot-check #1) | all cycle-2 closure markers present so far (5 closures: designer#4/#10, scribe#6/#8, researcher#7) | **5/5 = 100%** — every marker's cited leaf exists on disk | evidence_spotcheck.py run this pass (script at portal root) |

## Reading
- The 47% baseline is a CYCLE-1 artifact: markers written under time pressure + the sync-clobber bug lost some cited leaves. Cycle-2 starts clean with the durable-copy rule (Scribe#6) in force from day 1.
- Trend direction: improving, but n=5 closures is too small to claim; report 2 (next week) needs >=20 closure markers for a stable rate.
- Verifier scorecard (#10) not yet populated (goal open) — its TP/TN/FP/FN series joins this table when it lands.

## Recommendation
Keep the weekly cadence owned by Orchestrator#7 (spot-check) with Researcher consuming into this file; a rate dropping below 90% on >=10 markers re-opens the no-hollow-evidence standard discussion (risk register R6).
---

# Report 2/2 — full cycle-2 audit (goal #10, 2026-11-17)

Threshold met: n=42 closure markers across the 8 agent goal files (report 1 required >=20 for a stable rate). **Authoritative number comes from the reproducible generator** `python memory/researcher/evidence_quality_trend.py --min-markers 20`, not a one-off pass.

## Series
| Date | Scope | Real-evidence rate | Source |
|------|-------|--------------------|--------|
| 2026-11-16 (cycle-1 audit) | 60 "verified:" markers, cycle-1 goal files | **28/60 = 47%** | self-cert-audit-2026-11-16.md |
| 2026-11-16 (spot-check #1) | first 5 cycle-2 closures | **5/5 = 100%** | evidence_spotcheck.py |
| 2026-11-16 (day-1 snapshot) | all cycle-2 markers present that day | **33/41 = 80%** | evidence-quality-trend-snapshot-2026-11-16.md |
| **2026-11-17 (report 2/2, full cycle-2 audit)** | all 42 closure markers, 8 agent goal files | **34/42 = 81%** | `evidence_quality_trend.py --min-markers 20` (re-ran this pass) |

## Per-agent real-evidence rate (canonical generator, current data)
| Agent | exists/total | Rate |
|-------|-------------|------|
| archivist | 10/10 | 100% |
| builder | 2/2 | 100% |
| scribe | 3/3 | 100% |
| verifier | 1/1 | 100% |
| orchestrator | 7/9 | 78% |
| mechanic | 5/7 | 71% |
| researcher | 6/9 | 67% |
| designer | 0/1 | 0% (n=1, marker has no resolvable cite) |

## Reading
- **Trend: 47% (cycle-1) -> 81% (cycle-2 full audit)** = +34 pts. Clear improvement; durable-copy rule (Scribe#6) is holding for archivist/builder/scribe/verifier (all 100%). Still below the 90% no-hollow standard, so the gate stays open.
- The gap is **concentrated**: orchestrator (78%), mechanic (71%) and researcher (67%) carry every sub-100% miss; the clean four are at 100%.

## Failure modes (separated, not blended) — 8 hollow of 42
1. **Missing-named `.py` tooling leaf (5)** — marker names a script that does not exist anywhere on disk:
   - orchestrator: `goal_cycle_check.py`, `todo_freshness_check.py`
   - researcher: `citation_monitor_v2.py`, `model_benchmark.py`, `open_questions_flag.py`
   This **confirms** the day-1 snapshot's leading-indicator finding: tooling scripts ran from the Studio sandbox and never synced to the shared root — only their `.md` summaries landed (same sandbox->root sync-miss mode that hit Scribe's `/api/memory-health`). Actionable by owning seat: restore the `.py` to the shared root OR restamp with a path that resolves.
2. **No-cite marker (3)** — `(verified:)` block names no file, so it is uncrosscheckable: designer(1), mechanic(2). Not "false," just unverifiable — fix is to name the leaf in every stamp (extends Scribe#6 durable-copy rule).

## Method note (reproducibility finding)
My first ad-hoc pass this turn reported **31/43 = 72%**. The gap vs the canonical **81%** is purely methodological: the ad-hoc pass matched `(verified:)` as an arbitrary substring and used a non-greedy citation regex, which (a) admitted two markers that are not at line-end and (b) mis-resolved some citations. The documented generator (`evidence_quality_trend.py`, end-of-line marker match + `FILE_TOK`) is authoritative; **81% is the number to cite.** Recorded so a future weekly run does not silently drift on which regex counts.

## Recommendation
- Rate <90% on n=42 re-opens R6 (no-hollow-evidence standard) as designed; do NOT lower the bar. The 5 missing `.py` leaves are the specific unblock: Researcher + Orchestrator restore-or-restamp this week; that alone moves the fleet from 81% to ~93%.
- Standardize: every `(verified:)` block names a resolvable leaf (converts the 3 no-cite markers from uncrosscheckable to checkable).
- Cadence holds weekly on the canonical generator. Verifier#10 scorecard TP/TN/FP/FN series still joins this table when it lands.