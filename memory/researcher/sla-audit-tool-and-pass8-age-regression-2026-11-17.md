# SLA audit tooling + pass-8 age-regression finding (goal #8, 2026-11-17 pass-9)

**Purpose:** one concrete forward step on open goal #8 (open-questions cycle-3 reset + SLA enforcement). Two outcomes: (1) a REPRODUCIBLE one-command audit tool that removes the manual-computation error class, and (2) a FINDING that pass-8's hand-computed ages overstated by ~24h.

## FINDING — pass-8 age recalc is wrong (overstated ~24h / off-by-one-day)
Pass-8 (23:37) reported: Black .99 "~56h BREACH ×1.17", Designer patch "~58h BREACH ×1.2", White Q4 ctx "~108h BREACH ×2.25" — all three in breach.

Recomputed from the entries' STATED first-open dates (the OPEN section of open-questions-log.md + the OPEN-line provenance notes), at host-now 2026-11-17 23:48:

| Entry | Stated open | Correct age @ 23:48 | Pass-8 reported | Verdict |
|---|---|---|---|---|
| Black .99 unreachable | 11-16 ~15:40 ("new since 11-15 3/3 up") | **~32h — PROACTIVE, NOT breach** (breach-by 11-18 15:40) | ~56h BREACH ×1.17 | OVERSTATED +24h |
| Designer patch apply | 11-16 (~15:4x cluster est.) | **~32h — PROACTIVE, NOT breach** (breach-by 11-18 15:40) | ~58h BREACH ×1.2 | OVERSTATED +26h |
| White Q4 ctx mismatch | 11-14 (~12:00 est., pre-existing) | **~84h — genuine BREACH ×1.75** (breach-by was 11-16 12:00) | ~108h BREACH ×2.25 | breach is real; multiplier slightly overstated |

Corroboration that the smaller figures are right: earlier passes were internally consistent with the stated dates — pass-4 called Black/Designer "~36–48h SLA boundary TONIGHT", pass-5 "~50h". Only pass-8 jumped to 56/58h and declared all three in breach. Back-solving pass-8's numbers implies open dates ~1 day EARLIER than the log states (11-15 instead of 11-16), with no supporting provenance — i.e., an off-by-one-day regression, not new evidence.

**Net corrected picture @ 2026-11-17 23:48:** 2 RESOLVED (Red portal, orphan logs) | **1 genuine BREACH (White Q4 ctx only)** | 2 PROACTIVE (Black .99, Designer patch — both cross 48h on ~11-18 15:40). Passes 6/7/8's "2–3 full breaches persist" should read **1 full breach + 2 approaching**.

## Residual uncertainty (stated honestly)
Exact open hour:minute is ESTIMATED — the log gives only "~15:4x" for Black, just "11-16" for Designer, and "11-14" (described as pre-existing) for White Q4. If any true open was earlier on its day, age is larger and breach-by is earlier — so the corrected figures are a LOWER bound on breach risk, not an upper one. The direction of the pass-8 error (overstatement) is robust regardless of the ±hours uncertainty: even +6h on Black/Designer keeps them under 48h until ~11-18.

## DELIVERABLE — reproducible audit tool (removes the error class)
- `memory/researcher/sla_registry.json` — authoritative SLA clock. Each entry carries an EXPLICIT `sla_started` timestamp SEPARATE from any re-list date, plus status/owner/unblock_cmd + a note on the open-time estimate. This is the single source of truth for age math; the markdown log stays the human record.
- `memory/researcher/sla_audit.py` — one-command audit: `python memory/researcher/sla_audit.py` (vs host now) or `--ref YYYY-MM-DDTHH:MM` (fixed reference, e.g. the ~11-20 mid-cycle re-audit) or `--json`. Prints per-entry class (OK/PROACTIVE/BREACH/RESOLVED), age, breach-by deadline, owner + unblock command; exit 0 = zero-breaches, 1 = ≥1 breach, 2 = bad input. Graceful error on malformed --ref.

**Mid-cycle forecast (`--ref 2026-11-20T09:00`):** all 3 active entries in breach (Black ×1.86, Designer ×1.86, White Q4 ×2.94). Zero-breaches acceptance target is met ONLY if Black .99 + Designer patch close before ~11-18 15:40 AND White Q4 ctx closes before the mid-cycle check. All three still need NON-SANDBOX dispositions (Mechanic apply/probe, host power-on, doc sign-off) — none available from this seat.

## Closure status
NOT closed. Acceptance test = "zero entries >48h at mid-cycle check" (~11-20). Now runnable as ONE command: `python memory/researcher/sla_audit.py --ref 2026-11-20T09:00` (or live `--now`). The tool + this finding are the concrete step; the breach outcomes still depend on non-sandbox dispositions landing. No false close recorded.
