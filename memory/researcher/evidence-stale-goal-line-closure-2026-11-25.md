# Evidence: Stale fleet-goal-line closure (2026-11-25)

Lane: Researcher | Type: stale-evidence verification + remediation | Round topic: Fleet Autonomy Convergence

## Claim under test
Three conflicting figures for the same fleet goal total were in circulation on 2026-11-25:
- MEMORY.md GOAL line (L14): **69/80 (86%)**, "designer 9/10, scribe 0/10"
- Hot-note (MEMORY.md L21): claimed ledger = **75/80 (94%)**, "builder actually 5/10"
- On-disk SSOT `goal_ledger.json` at time of inspection: **77/80 (96%)**

## Method
1. Read on-disk `goal_ledger.json` header + per-agent sums -> internally consistent but only **8 agents / 80 total**.
2. Inspected generator `memory/researcher/goal_ledger.py`: `AGENT_FILES` was updated 2026-11-25 to include
   `outlet`, `pixel`, `forge` (-> 11 agents). The on-disk JSON predated that change.
3. Called `build_ledger()` in-memory -> **11 agents / 110 total / 104 reached (95%)**.
4. Discovered the CLI writes the JSON only when invoked with `--json` (bare run prints text summary, does NOT overwrite).
   The stale artifact had never been regenerated after the AGENT_FILES change.

## Remediation (concrete, reproducible)
- Backed up stale artifact -> `memory/researcher/backup_goal_ledger_STALE_2026-11-25.json`.
- Ran `python memory/researcher/goal_ledger.py --json goal_ledger.json` (RC 0).
- Re-read on-disk: header now **110 / 104 / 95**, 11 agents -> matches `build_ledger()` exactly.
- Corrected MEMORY.md GOAL line (L14) to the verified figure with a `(verified:)` marker.

## Verified ground truth (2026-11-25)
Fleet = **104/110 (95%)**. Open lanes: archivist 9/10 (Knowledge SPOF Audit), outlet 8/10
(Milestone Auto-Draft Trigger, Platform Connection Runbook), forge 7/10 (Runbook Executability Audit,
Cross-Host Consistency Test, Gate Pipeline Drift Detector). All other 8 lanes 10/10.

## Confidence & caveats
- HIGH on the numbers: build_ledger() and the regenerated on-disk JSON agree byte-for-byte on totals.
- The "96/110" figure in MEMORY.md's DREAM SYNC comment (L2) is also now superseded by 104/110; that comment
  predates the outlet/pixel/forge evidence closures that brought reached from ~96 to 104.
- Residual uncertainty: /api/goals endpoint behaviour was not live-probed this pass (no running portal in sandbox);
  it is expected to read this same goal_ledger.json per MEMORY.md L14 SSOT note. If the API caches, a reload may be needed.

## Cross-checks
- Per-agent sum of reached == header fleet_reached (77->104 both consistent with their respective agent sets).
- No fabricated evidence: all figures derived from goal .md sources via the existing generator, not hand-entered.
