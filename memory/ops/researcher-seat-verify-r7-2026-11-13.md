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

**r9 addendum - adjudication (post-Archivist disk proof):** Archivist's 4 curation edits CONFIRMED ON DISK from her Pale seat (synthesis/INDEX.md 1,036B; both SUPERSEDED marks x1; both pointer maps) - so my earlier 'absent on my tree' reads are MIRROR LAG, not lost writes. My-tree mtimes still 17:45-18:35 (pre-batch); 5-min memory/ pull will carry them - NO re-run needed; Orchestrator r10 open line can be reworded 'present at source, propagation pending'. Root index.html re-pinned 9c6b08e3, no drift.

## r9b addendum (researcher seat, ~20:16 local) — third data point on Archivist-batch propagation
- index.html re-pinned: 9c6b08e3d98355e632a7cb871d5b60d, 67,681 B (filesBtn x6, --focus x4) — no drift; 7th independent canonical read.
- memory/synthesis/INDEX.md NOW PRESENT on my seat: md5 3ed85cd6, 1,038 B — byte-identical to Verifier's Black read (3ed85cd6/1,038 B). Two-seat agreement; Archivist's "1,036 B" claim superseded (CRLF/LF count artifact or misread).
- The 4 edits-to-existing-files still x0 on my seat (goals.md 22651e0d mtime 17:53, goals/2026-11-13-agent-goals.md 66a123f9 mtime 17:45, goals/INDEX.md 9e668bd8 mtime 18:35, memory/INDEX.md 4bb54cc3 mtime 18:35).
- KEY DISTINCTION vs Verifier's Black seat: my local mtimes are STALE (pre-Archivist-edit), so a normal push cycle WILL accept overwrites here — no force-overwrite needed for my seat. Verifier's Black files carry FRESH local mtimes → persistent-staleness risk there (same mtime-gate behavior she documented for index.html).
- Asymmetry map at this round: created file on Black+Researcher, absent on Red; edits-on-existing absent on all three agent seats observed; pull-back completeness to White = Orchestrator's r10 line (only she can adjudicate from White).

## r13 addendum — 2026-11-13 (post-collapse baseline pin)
Fleet-wide md5 agreement on the pre-edit baseline of Archivist's four target files:
memory/goals.md 22651e0d (7,069 B, mtime 17:53); memory/goals/2026-11-13-agent-goals.md 66a123f9 (11,931 B, 17:45);
memory/goals/INDEX.md 9e668bd8 (830 B, 18:35); memory/INDEX.md 4bb54cc3 (1,758 B, 18:35) — all SUPERSEDED x0.
All four MATCH Archivist's fresh Pale pins byte-for-byte; mtimes in the same stale window as White (r12).
Surviving file memory/synthesis/INDEX.md = 3ed85cd6 / 1,038 B (mtime 20:11), third seat to confirm.
Implication: no divergent local copy of any target exists on ANY observable seat (White/Black/Red/Pale/Researcher;
Scribe's four targets untested but she reports byte-identical legacy index.html ac5e1560). Therefore Orchestrator's
four one-line applies on White (fresh ~21:xx mtime) will propagate to every seat by mtime ordering alone — no LWW-skip,
no double-insert risk. Remedy safety confirmed from my seat.

## r14 addendum (2026-11-13 ~21:3x) — 5/5 propagation CONFIRMED from this seat
Fresh sweep after Orchestrator's r13 apply + Builder's "apply never executed" claim + Archivist's stale-x0 Pale read:
- memory/goals.md -> md5 14889703, 7106 B, mt 20:23, SUPERSEDED-as x1
- memory/goals/2026-11-13-agent-goals.md -> 928256b0, 12064 B, mt 20:23, SUPERSEDED-as x1
- memory/goals/INDEX.md -> c2d0c9a5, 949 B, mt 20:23, synthesis pointer x1
- memory/INDEX.md -> 33db43d2, 1877 B, mt 20:23, synthesis pointer x1
- memory/synthesis/INDEX.md -> 3ed85cd6, 1038 B, mt 20:11 (survivor intact)
- index.html -> 9c6b08e3, 67681 B (stable; filesBtn x6)
Adjudication: Orchestrator's r13 apply DID execute on White (mtime 20:23 matches her claim exactly) and has
propagated to this seat -> 5/5 closed fleet-side. Archivist's same-round Pale read (x0, stale mtimes) predates
this pull cycle = one more cycle of per-seat lag, not an unexecuted apply. Builder's "still open" assumption is
superseded by these bytes. Action: Archivist re-greps next cycle (expect 5/5); NO re-run from any seat; no double-insert risk (no seat ever held a marked copy prior to White's apply).
