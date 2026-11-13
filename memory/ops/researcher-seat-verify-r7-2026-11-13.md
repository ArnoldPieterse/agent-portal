# Researcher seat verification — OPS r7 (2026-11-13)
Independent spot-check from Researcher seat (not White/Orchestrator). All hashes = md5 first 8, tool-verified this round.

## Seat ground truth
- `./agent_portal.py` = **b2a299ef** (original r5 variant — matches LIVE PLAN) ; `./memory_mirror.py` = **c1f4699c** (original). py/AST parse OK.
- `./index.html` = **ac5e1560** = ops-polish only: opsBtn x3, actPanel x6, filesPanel/filesBtn x0 → NO Files panel on this seat; matches canonical White per Orchestrator r7.
- 5 legacy copies (AgentPortal_V1-git/, gapfix-test/, uploads/AgentPortal_V1/, _boot2/, _bootstrap_test/) all **e6958ac6** = pre-A3-B base WITH Files panel (filesPanel x5/filesBtn x6, opsBtn x0). Consistent with r7 quarantine; fallback merge source only.
- Builder staged copies at memory/builder/ match LIVE PLAN hashes exactly: agent_portal_ops-r5_staged.py = 563cd9b3, memory_mirror_ops-r5_staged.py = 2774436c. AST-parse OK both.
- `designer/files-panel-hunks-r5.md`: NOT present anywhere in my tree (full walk) — consistent with r7 "undelivered or lost"; re-issue to Designer stands.
- MEMORY.md goal line on my seat still old ~14:0x text — EXPECTED (PID 1240 pre-fix LWW); deliberately untouched (Orchestrator owns resync post-restart; avoid rollback cycle #6).

## Function-equivalence spot-check (goal #6, Verifier AC-A2 PASS claim)
Diffed section-3 `_sync_workspace_to_sandbox()` between b2a299ef (mine) and 563cd9b3 (Builder): 23 changed lines, same function only.
- Mine: LWW loop over SYNC_LWW with explicit skip `if rel in ("TODO.md","MEMORY.md"): continue`.
- Builder: pull walks memory/ leaves ONLY; root docs structurally unreachable (PUSH-ONLY per comment block).
- Both close the clobber path at source level; difference is implementation style, not behavior. **Confidence: HIGH** that "two behavior-equivalent variants" holds for the clobber fix. NOT independently re-run as live A/B (needs portal restart — Arnold's gate).

## Gate state from this seat (unchanged)
Single gate remains 3 legs: (1) Designer delivers files-panel-hunks-r5.md verbatim; (2) Mechanic/Arnold White-local bundle = restart PID 1240 + one-shot #5 fetch Black index.html + hard-refresh; (3) Verifier AC-A2 process-level close post-reload. Nothing further actionable from an agent seat without Arnold/Designer input.
