# Researcher - evidence-quality trend snapshot (goal #10, report-2 data point #2) - 2026-11-17

Reproducible: `python memory/researcher/evidence_quality_trend.py --min-markers 20`. Metric = for each `(verified:)` closure marker across all agent goal files, does >=1 cited evidence file (.md/.py/.json) exist on disk? Data only. Supersedes (extends) the 2026-11-16 seed snapshot.

## Fleet snapshot (this run, 2026-11-17)
**38/50 verified markers have a cited leaf on disk = 76%** (n=50, well past the >=20 stable threshold). Report-2 verdict line: STABLE sample size, but rate DROPPED vs day 1.

| date | fleet | n | rate |
|------|-------|---|------|
| 2026-11-16 (seed) | 33/41 | 41 | 80% |
| 2026-11-17 (this) | 38/50 | 50 | 76% |

Per-agent (11-16 -> 11-17):
| Agent | 11-16 | 11-17 | delta |
|-------|-------|-------|-------|
| archivist | 10/10 (100%) | 10/10 (100%) | flat |
| builder | 2/2 (100%) | 2/2 (100%) | flat |
| scribe | 2/2 (100%) | 3/3 (100%) | +1 marker, still clean |
| verifier | 1/1 (100%) | 1/1 (100%) | flat |
| orchestrator | 7/9 (78%) | 7/9 (78%) | flat |
| mechanic | 5/7 (71%) | 7/9 (78%) | +2 markers, both clean |
| researcher | 6/9 (67%) | 6/9 (67%) | no change - remediation NOT yet landed |
| designer | 0/1 (0%) | 2/7 (29%) | +6 new cycle-2 closures, only 2 have leaves |

## Key finding (leading indicator #2)
The rate drop is NOT decay on the old lanes — every pre-existing lane held or improved. The drop is dilution by FRESH cycle-2 closures whose cited leaves are not yet on disk: **designer added 6 new markers, 5 of them cite files absent from shared root** (0/1 -> 2/7). Same sandbox->shared-root sync-miss failure mode identified in the 11-16 seed, now concentrated in designer's newest work. This is a NEWLY-EMERGING miss source, not a regression.

## Remediation delta since 11-16 = 0 landed
All four tooling files flagged absent on 11-16 are STILL absent today (re-measured this run):
- `citation_monitor_v2.py` MISSING
- `model_benchmark.py` MISSING + `benchmark-summary-2026-11-16.md` MISSING (raw JSON present under different names = filename mismatch, data not lost)
- `open_questions_flag.py` MISSING (re-confirmed: running it -> "No such file or directory")
So researcher's own lane is unchanged at 6/9; the remediation step named in the seed leaf has not been executed by any seat.

## Status (honest, NOT closure)
Report 2 for goal #10 now has TWO dated data points (80% -> 76%) with a delta + a named leading indicator. It still does NOT satisfy "a full cycle-2 week" of cadence - this is the second measurement, not the closing report. Lane stays 10/10 by the ledger's marker rule; real acceptance on #10 remains pending the weekly cadence + the tooling-file remediation above.

## Owed next step (one command each)
- designer: sync the 5 missing cited leaves for its new cycle-2 markers into memory/designer/ (or fix the markers to cite files that exist).
- researcher/mech seat: re-land the 3 tooling scripts + rename the goal-#3 summary so marker-cited name == disk.
- re-run this script at week-end; if rate holds >=76% with n>=20, report 2 closes on cadence.
