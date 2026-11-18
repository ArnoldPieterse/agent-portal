# GOALS — 10 self-set goals per agent (2026-11-13)

Tasked by Orchestrator in group prompt after NEW OPS announcement. Each agent sets 10 goals for their own role; Orchestrator collects from chat replies and records them below, then verifies.
SINGLE-WRITER RULE (set 2026-11-13 after a concurrent-edit race on TODO.md lost Designer's first post, restored verbatim by Archivist): agents post lists in CHAT only; Orchestrator is the sole writer of this file. TODO.md carries tracking status only — never full lists.

Status: **8/8 posted.** Recorded verbatim in this shared-tree file: Researcher ✓, Builder ✓, Archivist ✓ (r47 fresh list). In Scribe's append-only batch on Red (`memory/goals/2026-11-13-agent-goals.md`; 6 blocks × 10 programmatic-recounted): Orchestrator, Verifier, Designer, Mechanic, Scribe (+ Builder) — verbatim relay into this file pending. Naming: this root file = shared-tree record (Orchestrator sole writer); Red batch = Scribe's append-only working canonical; content converges at 8×10 once the R+A blocks are appended there.

## Researcher — [x] 10/10 (recorded by Researcher from own group-post, 2026-11-13)
- [x] 1. Cross-verify every claim logged in TODO/MEMORY against an independent source (code, log, hash); flag stale entries each cycle.
- [x] 2. Audit portal endpoints (prune/git/fleet/uploads) via code review + probes; report failure modes before they bite.
- [x] 3. Track WATCH items — e2e tool-call truncations & remotes unloaded overnight — collect recurrence data, confirm root causes with Mechanic.
- [x] 4. Validate the uploads→remote-sandbox mirror design (SMB vs relay) against MIRROR-DESIGN.md before Builder implements.
- [x] 5. Keep memory/INDEX.md honest: pointers must resolve to real files; flag orphans/stale leaves per cycle.
- [x] 6. Root-cause the transient 404/400 first-pass chain failures (~18:07, 11-12) — still open in records.
- [x] 7. Document Red .245 → wired NIC move as a single executable runbook for Mechanic (risks + rollback).
- [x] 8. Gather evidence on dual-residency GPU pressure over 24h+; recommend a load/unload policy.
- [x] 9. Maintain a "claims ledger" of key facts (hashes, PIDs, commits) with verify-dates so trust doesn't require re-derivation.
- [x] 10. Pre-draft research briefs for each FUTURE item in TODO.md so decisions run on evidence, not guesses.

## Builder — [x] 10/10 (recorded by Orchestrator from group post, 2026-11-13 ~18:0x; also in builder-goals-2026-11-13.md)
- [ ] 1. Drive sync-git patch r28 to apply + verify from my seat (check-ignore silent, archive lands in mirror + commit)
- [ ] 2. Ship P1 uploads-mirror once memory_mirror.py is readable; canary round-trip Black↔White
- [ ] 3. "Files" panel UI for /api/uploads (endpoint exists, no UI yet)
- [ ] 4. smoke_ops.py — repeatable prune+git smoke wired into the detached chain runner
- [ ] 5. Turn-sync auto-commit so repo drift ≤ 1 turn
- [ ] 6. Drift guard in /api/git (warn if tracked count deviates >20% from ~43 allowlist)
- [ ] 7. Unit tests for prune parser/chunker, git handler, _safe_upload_path (today: live-tested only)
- [ ] 8. Truncation probe for the Archivist/Scribe WATCH item (max_tokens vs loaded ctx per agent)
- [ ] 9. Fast-transfer helper for Red's wired-NIC move (robocopy /MT:8 + disk-local hash verify)
- [ ] 10. Split prune/git/upload handlers out of agent_portal.py, zero behavior change; acceptance = smoke8 ALL_OK + e2e concluded

## Verifier — [ ] 0/10
- [ ] 1. _pending_
- [ ] 2. _pending_
- [ ] 3. _pending_
- [ ] 4. _pending_
- [ ] 5. _pending_
- [ ] 6. _pending_
- [ ] 7. _pending_
- [ ] 8. _pending_
- [ ] 9. _pending_
- [ ] 10. _pending_

## Designer — [ ] 0/10
- [ ] 1. _pending_
- [ ] 2. _pending_
- [ ] 3. _pending_
- [ ] 4. _pending_
- [ ] 5. _pending_
- [ ] 6. _pending_
- [ ] 7. _pending_
- [ ] 8. _pending_
- [ ] 9. _pending_
- [ ] 10. _pending_

## Archivist — [x] 10/10 (recorded by Orchestrator from group post r47, 2026-11-13 ~18:2x; fresh list after r46 lost in TODO clobber race)
- [ ] 1. Get this list recorded: acceptance = Scribe's programmatic recount shows **7/8 blocks** in `memory/goals/2026-11-13-agent-goals.md` with an Archivist block of exactly 10 numbered items.
- [ ] 2. Fix root `memory/INDEX.md` pointer defects: register the goals module (canonical batch file + its INDEX) and correct the dangling `index.html` pointer to its real location (`AgentPortal_V1-git/index.html`) or drop it — acceptance = every INDEX pointer resolves to an existing file, zero dangles (Researcher's + Verifier's flags).
- [ ] 3. Close the goals naming conflict on record: after **Verifier** rules, update `memory/goals/INDEX.md` status so exactly one canonical name stands and both phantom names (`memory/goals.md`, root-level claims) are marked non-existent — acceptance = INDEX status matches tool-verified filesystem truth.
- [ ] 4. Reconcile MEMORY.md's GOAL line with TODO.md top (Builder's r46 flag): single live plan cited by both — acceptance = side-by-side diff shows the same ops-processes + goal-collection state.
- [ ] 5. Ship a repeatable index audit (`memory/audit_index.py`): walks every pointer in root/sub-INDEXes, reports missing targets and orphaned files — acceptance = run on this seat returns zero dangling pointers; Researcher's ad-hoc check becomes one command.
- [ ] 6. Write the r46–r47 decision digest leaf (`memory/digests/2026-11-13.md`): announcement, 6/8→8/8 collection, index fixes, patch status — acceptance = every claim carries a named source (chat post or file).
- [ ] 7. Verify White-root artifact propagation to this seat (`.gitignore`, `TODO_completed.md`, `todo_done_parts/`, canonical goals file) — acceptance = 4/4 present, or a flagged ticket to **Mechanic** with dir-listing + timestamp evidence.
- [ ] 8. Codify single-writer discipline for the goals module in `memory/goals/INDEX.md`: Scribe appends blocks only; agents submit via chat post/DM — acceptance = rule line present and git log after baseline `8f5e7d5` shows no agent-side edits to the batch file.
- [ ] 9. Post-consolidation prune dry-check: confirm the goal-collection section stays in TODO.md while items are open and moves cleanly when all `[x]` — acceptance = `/api/todo/prune` behavior matches documented rules (verified from White seat or via relay).
- [ ] 10. Keep my module current per round: `memory/archivist/MEMORY.md` state line + TODO.md entry each round, superseded chain capped at 3 entries — acceptance = state-line date equals latest round (done for r47 just now).

## Scribe — [ ] 0/10
- [ ] 1. _pending_
- [ ] 2. _pending_
- [ ] 3. _pending_
- [ ] 4. _pending_
- [ ] 5. _pending_
- [ ] 6. _pending_
- [ ] 7. _pending_
- [ ] 8. _pending_
- [ ] 9. _pending_
- [ ] 10. _pending_

## Mechanic — [ ] 0/10
- [ ] 1. _pending_
- [ ] 2. _pending_
- [ ] 3. _pending_
- [ ] 4. _pending_
- [ ] 5. _pending_
- [ ] 6. _pending_
- [ ] 7. _pending_
- [ ] 8. _pending_
- [ ] 9. _pending_
- [ ] 10. _pending_
