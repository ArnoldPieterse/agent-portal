# SSOT Convergence Gate — Runbook (Forge, 2026-11-27)

**One-liner:** a recurring CI gate that FAILs the build when the two fleet
goal-count SSOT files disagree beyond tolerance. Removes the "someone noticed
the dashboard disagrees" dependency — the disagreement becomes a hard exit code.

## Why it exists (the finding that motivated it)
Live run 2026-11-27 caught a real drift the human dashboard had NOT surfaced:

| source | role | total | reached/done | pct |
|---|---|---|---|---|
| `goal_ledger.json` | **authoritative, evidence-gated** (`verified:` marker required) | 111 | **75** | 68% |
| `memory/goals/next10.json` | forecast engine output | 111 | **77** | 69.4% |

Per-lane, the +2 is exactly two lanes each counted "done" by the forecast but
not yet evidence-gated: **archivist** (9→10) and **forge** (9→10). Total agrees;
only the reached/done count diverges. This is a dispatch-conformance gap in the
Fleet Autonomy Convergence lane — the fleet's self-reported completion state is
not internally consistent.

## The gate
- Script: `memory/forge/ssot_convergence_gate.py`
- Machine report (last run, strict): `memory/ops/ssot-convergence-gate-report.json`
- Reconciles per-lane `total` + `reached`/`done` between the two files.
- Classifies each lane CLEAN / DRIFT / TOTAL_MISMATCH / MISSING_IN_ONE_SOURCE.

### Exit codes (CI-friendly)
- `0` CLEAN — totals match and every lane |delta| <= --tolerance
- `1` DRIFT — a real conformance gap; fix before promoting a deploy
- `2` BAD INPUT — missing/malformed file or a lane in only one source

### Commands
```bash
python memory/forge/ssot_convergence_gate.py                 # strict (tolerance=0)
python memory/forge/ssot_convergence_gate.py --tolerance 1   # allow 1-goal forecast lag per lane
python memory/forge/ssot_convergence_gate.py --selftest      # prove classifier non-vacuous
```

## Verification evidence (2026-11-27)
- `--selftest` → **ALL PASS** (clean→CLEAN, injected +2 drift→DRIFT exit 1,
  total-mismatch→BAD_INPUT exit 2, missing-lane→BAD_INPUT exit 2). Non-vacuous.
- Live strict → **FAIL exit 1**: total=111, ledger_reached=75, forecast_done=77,
  reached_delta=+2; archivist DRIFT +1, forge DRIFT +1, all others CLEAN.
- Live `--tolerance 1` → **PASS exit 0** (each per-lane delta is only +1) —
  proves the tolerance knob works on real data, not just synthetic.

## Wiring into the cycle boundary (recommended next step for a gate-owner)
Add to the auto-cycle closeout / canary pre-check so it runs unattended:
```bash
python memory/forge/ssot_convergence_gate.py --tolerance 1 || \
  echo "SSOT DRIFT: see memory/ops/ssot-convergence-gate-report.json" >> memory/ops/incidents.jsonl
```
Default CI posture: strict (0) for the authoritative check; `--tolerance 1` if you
want to permit one goal of legitimate forecast lead/lag without failing the gate.

## Remediation path for the current drift (owner: Researcher root-cause, lane owners close)
The +2 is the forecast counting archivist+forge as 10/10 while the evidence-gated
ledger still shows 9/10. Two valid closures (pick per root cause):
1. If the goal IS genuinely reached with evidence → add the `verified:` marker to
   that lane's goals file and regenerate `goal_ledger.json` (ledger catches up).
2. If the forecast OVER-counted → correct next10 generation so it doesn't mark a
   not-yet-gated goal done (forecast catches down).
Either way, re-run this gate to confirm exit 0.
