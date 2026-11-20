# Cycle 8 Quality Report

Generated: 2026-11-20 23:14 by `memory/verifier/cycle_quality.py` (local artifacts only; no :8099 egress).

## 1. Goals Completed + Verification Pass Rate

| Agent | Closed | Total | % |
|-------|-------|-------|---|
| archivist | 0 | 10 | 0% |
| builder | 3 | 10 | 30% |
| designer | 0 | 10 | 0% |
| mechanic | 0 | 10 | 0% |
| orchestrator | 3 | 10 | 30% |
| researcher | 2 | 10 | 20% |
| scribe | 2 | 10 | 20% |
| verifier | 2 | 10 | 20% |
| **Fleet** | **12** | **80** | **15%** |

## 2. Evidence Quality Scores

Source: `evidence-quality-2026-11-20.md` (rubric: specificity/reproducibility/currency, 1-5).

- Leaves scored: **1998** | flagged (<3 any axis): 1016 (50%)
- High (>=4.0): 829 | Low (<2.5): 8
- Averages: spec=3.80 repro=2.60 curr=4.97

## 3. SLO Compliance

Latest report: `slo-report-2026-11-16.md` | Verdict: **PASS** | endpoints OK 11/11 | alerts logged: 1

## 4. Security Findings

Source: `security-audit-2026-11-20.md`.

| Severity | Count |
|----------|-------|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 0 |

## 5. Performance Trends

**DEGRADED** (captured 2026-11-20 13:09:44Z): all endpoints null (egress-wall capture, no live samples). No live samples available from this seat (:8099 egress wall) - reported as NOT PASS, not a regression.

## 6. Evidence Integrity (cross-reference)

Source: `evidence-xref-report-2026-11-20.md` | dangling refs: **None**

## 7. Git Activity (last 14 days)

git unavailable: [WinError 2] The system cannot find the file specified

## 8. Cycle Summary / Verdict

goals 12/80 (15%) SLO=PASS security findings=0 perf=DEGRADED dangling refs=None

