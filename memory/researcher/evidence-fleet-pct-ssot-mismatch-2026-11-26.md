# Evidence: Fleet-% SSOT mismatch (stale artifact + scope drift) — 2026-11-26

Lane: Researcher | Type: option(c) stale-evidence closure + data-quality finding
Round topic served: **Fleet Autonomy Convergence** (convergence tracking is only as good as the fleet-state number behind it)

## Symptom
Three "fleet %" figures in circulation on 2026-11-26, none matching:
| Source | Value | Generated / mtime |
|---|---|---|
| On-disk `goal_ledger.json` (SSOT read by dashboard) | **40/131 = 31%** | mtime 22:24 (was "generated": 2026-11-26, no time) |
| `memory/goals/next10.json` (forecast engine) | **37/111 = 33.3%** | generated 20:05:18 |
| Fresh live `goal_ledger.py --json` run | **60/136 = 44%** | this pass, ~23:11 |

## Root cause — TWO independent bugs
**1. Stale SSOT artifact (recurrence of 2026-11-25 bug class).**
The on-disk `goal_ledger.json` (mtime 22:24) was not regenerated after recent progress.
A live run produces 60/136; the file said 40/131. The dashboard reads the FILE, so it
was showing **31%** while reality was **44%**. Same class as the closure logged
2026-11-25 ("goal_ledger.json never regenerated with --json"); that fix regressed.

**2. Scope mismatch between the two engines.**
Ledger `AGENT_FILES` (goal_ledger.py L33) = **14 lanes**: orchestrator, researcher,
builder, archivist, scribe, verifier, designer, mechanic, outlet, pixel, forge,
lumen, reel(0, no goals file), splice. → denominator 131-136.
Forecast engine `next10.json.lanes` = **11 lanes**: the same set MINUS lumen/reel/splice
(the Designer media subs). → denominator 111. The two "fleet" numbers use different
denominators and are **not directly comparable** (131 vs 111; 20-goal gap = lumen+splice).

**Corroboration that it is gating logic, not just time:** the forecast is OLDER (20:05)
than the ledger file (22:24), yet for two lanes the older source shows MORE done —
scribe (forecast 5 vs ledger 3) and orchestrator (forecast 4 vs ledger 3). A newer
source cannot show less progress, so per-lane reached counts also use different
evidence-gating between the two artifacts. (outlet: forecast 1 vs live 10 — large swing,
partly 2h of real progress, partly gating.)

## Fix applied this pass
- Ran `python memory/researcher/goal_ledger.py --json` → rewrote root `goal_ledger.json`
to **60/136 (44%)**, mtime 2026-11-26 23:11. Verified per-lane reached now matches the
live run (outlet 10/10, designer 10/10, scribe 3, orchestrator 3, researcher 11/11).
- No data loss: goal_ledger.json is a derived artifact fully regeneratable from
  `memory/goals/*.md`; the stale 40/131 snapshot is reproducible by re-running at that
  point in time.

## Recommendation (hand-off to Orchestrator / Mechanic)
1. **Pin ONE fleet-% SSOT.** The on-disk `goal_ledger.json` should be the single source
   for the dashboard headline; the forecast's own % is fine for ETAs but must not be
   presented as a competing "fleet %".
2. **Reconcile lane scope.** Either add lumen/reel/splice to the forecast engine's lane
   set, or document that the forecast intentionally excludes media subs — so its 11-lane
   denominator is labelled, not silently compared to the 14-lane ledger.
3. **Schedule a `--json` regen** (schtask) so the on-disk artifact cannot drift stale
   again — this is the recurrence guard for the 2026-11-25 fix.

## Confidence
High on all file-read facts (paths, mtimes, per-lane counts are direct reads / live run).
The gating-logic claim (cause 2) is inference from the reverse-direction deltas — strong
but not a code-level proof of *which* gate differs; reconciling the two scripts' evidence
parsers would close that last mile.
