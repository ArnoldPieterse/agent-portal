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
