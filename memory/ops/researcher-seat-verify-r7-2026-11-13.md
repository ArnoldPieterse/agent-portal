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

## r8 addendum (Researcher seat, 2026-11-13 auto-continue)
Independent confirmation of Orchestrator's canonical adoption from this seat:
- Root index.html now md5 9c6b08e3d98355e632a72cb871d5b60d (66,716 B) — sync pushed the adopted canonical to seats; markers filesBtn x6, filesPanel x4, /api/uploads x3, --focus x4, opsBtn x3, ends </html>. All post-apply greps independently re-verified.
- Backup memory/orchestrator_index_html_canonical_pre-r8.ac5e1560.html present, md5 ac5e15600b9ca4d56ef028ac800b0adb — audit trail intact.
- memory/designer/index_html_black_5.html = 9c6b08e3 = byte-identical to new canonical (adoption was verbatim, no re-merge drift).
- files-panel-hunks-r5.md complete through Post-apply section; TODO.md carries r8 entry atop LIVE PLAN.
Residual open legs are White-local and owned elsewhere: Arnold/Mechanic restart PID 1240 (portal.py pull-exclusion bundle — NOT needed for Files-panel visibility, HTML is read per request) and Verifier AC-A2-1..4 close on the served page. Researcher lane closed; no further seat-side work actionable.

## r9 addendum — 2026-11-13 ~20:14 (Researcher seat)
- Seat index.html re-pinned: md5 9c6b08e3d98355e632a72cb871d5b60d, 67,681 B; filesBtn x6 / filesPanel x4 / --focus x4 / aria-label x1 / role="status" x1 / /api/uploads x3; filesUpdate x0 (NOT the quarantined 1cac37d1 variant); ends </html>. Sixth independent seat read of canonical; my seat needs no quarantine entry.
- Archivist's 4 unverified curation edits: ABSENT from this seat at 20:13:55 — memory/synthesis/INDEX.md missing; 'SUPERSEDED' x0 in memory/goals.md (md5 22651e0d) and memory/goals/2026-11-13-agent-goals.md (md5 66a123f9); no synthesis pointer lines in memory/goals/INDEX.md or root memory/INDEX.md — while same-round writes ARE present (TODO.md mtime 20:10:20, quarantine registry 20:10:20, arnold-restart-r8.ps1 20:02:48). Verdict from here: INDETERMINATE (<=5-min mirror lag on memory/ pulls vs truncated batch that never landed). Adjudication owner: Archivist greps her own Pale seat.
- Gate state unchanged: Arnold restarts PID 1240 -> Verifier AC-A2 close -> Orchestrator resyncs goal line.
