# Decision Log v2 - Structured Fleet Decisions

Format: {date, decision, context, alternatives_considered, rationale, owner}
Source: extracted from memory/synthesis/ files via migrate_decisions.py (or manual entry).
Newest first. Each entry MUST have all 6 fields populated.

---

## D-012 | 2026-11-18
- **decision**: All 8 cycle-3 agent goal files now hold ZERO open substantive goals; main lane unblocked.
- **context**: Cycle-3 goal-setting round landed 2026-11-17 (8 agents x 10 goals). By 2026-11-18 ~10:0x all goals either closed with Verified: lines or moved to background scheduled list.
- **alternatives_considered**: Keep some goals open for next cycle vs close/move all now.
- **rationale**: User requested Studio seat closure; all acceptance tests passed or items are date/probe-gated (parked at memory/goals/scheduled-background.md per run-rules R2/R3).
- **owner**: Orchestrator (coordination), all agents (execution)

## D-011 | 2026-11-17
- **decision**: Cycle-1 baselines established: evidence spot-check 47%, 324/441 orphans.
- **context**: End of cycle 1 (2026-11-12 to 11-15); needed measurable baselines for cycle-2 improvement targets.
- **alternatives_considered**: No formal baseline vs document current state as reference point.
- **rationale**: Without a baseline, "improvement" claims are unverifiable. These numbers give the fleet concrete targets to beat.
- **owner**: Scribe (measurement + documentation)

## D-010 | 2026-11-16
- **decision**: Fleet verified state is 75/80, NOT 80/80 as MEMORY.md hot note claimed.
- **context**: Goal-sweep closeout pass; on-disk parse of memory/goals/*.md showed 5 goals lacking (verified: markers despite hot-note assertion of full closure.
- **alternatives_considered**: Trust the hot note vs re-measure from disk.
- **rationale**: /api/goals is SSOT per ruling C1; disk measurement trumps chat self-reports. The 5 unmarked goals (builder #2, verifier #8, #9, designer #2, #6) remain open until properly evidenced.
- **owner**: Scribe (measurement), Orchestrator (ruling)

## D-009 | 2026-11-16
- **decision**: Ruling C2 - Designer #4 closure stands; Verifier's false-positive flag rejected as stale.
- **context**: Verifier flagged F-VER-01 claiming zero design tokens in index.html. Measured directly: live sha12 2c6399f2d853 contains all claimed tokens with 160 var(--sp-*) + 60 var(--fs-*) usages.
- **alternatives_considered**: Re-open Designer #4 for re-verification vs accept the stale flag as invalid.
- **rationale**: Verifier's measurement predates tokenization landing (or read a stale mirror; Researcher documents ~5-min SMB lag). Direct measurement from shared root confirms tokens present.
- **owner**: Orchestrator (ruling), Verifier (original flag), Designer (closure)

## D-008 | 2026-11-16
- **decision**: /api/goals is the single source of truth for goal status; chat numbers are self-assessments, not closures.
- **context**: Contradiction queue C1 - agents reporting different closure counts in chat vs what the ledger shows on disk.
- **alternatives_considered**: Trust chat reports (faster) vs enforce SSOT discipline (slower but consistent).
- **rationale**: Without a single authoritative source, the fleet cannot know its true state. sot_audit.py institutionalizes the check every round.
- **owner**: Orchestrator (ruling + tooling)

## D-007 | 2026-11-15
- **decision**: Four fixes landed in agent_portal.py for stalled-goal failure modes: (1) FIRST_REPLY_REASONING="low", (2) transient HTTP retry x2, (3) errored turns no longer settled immediately, (4) verdict honesty note.
- **context**: Diagnosis found two failure modes - Black .99 empty-body HTTP 400s for Builder+Verifier pair, and ~32768-token context exhaustion where group prompts ~17k + default thinking left no room. Fatal amplifier: _group_run_worker settled errored turns silently.
- **alternatives_considered**: Fix only the HTTP issue vs fix both failure modes + the amplifier.
- **rationale**: Each fix addresses a distinct root cause; fixing only one would leave the other mode recurring. The settle-amplifier fix is critical because it masked all other failures.
- **owner**: Builder (implementation), Verifier (verification)

## D-006 | 2026-11-15
- **decision**: Internal LAN IPs in public repo are KEPT (not scrubbed).
- **context**: Pre-push secret scan clean; 116 files contain RFC1918 private-range IPs (192.168.1.{1,50,179,245,39,99}). No public IPs or secrets exposed.
- **alternatives_considered**: Scrub all internal IPs (breaks live operation) vs keep them (exposes internal topology only) vs partial scrub (complex, error-prone).
- **rationale**: These LIVE files need the real IPs to operate. Exposure is limited to RFC1918 private-range addresses - no external attacker can reach them. Scrubbing would break the portal's multi-host architecture.
- **owner**: Orchestrator (decision), Researcher (scan)

## D-005 | 2026-11-14
- **decision**: All seven agent lanes CLOSED; sole remaining gate = Arnold's manual White-console pass on bundle v2 items 1-8.
- **context**: End of the portal-upgrade round (r56+). Every agent-executable item completed and verified. The remaining work requires physical access to the White console.
- **alternatives_considered**: Keep lanes open "just in case" vs close all and document the single human gate.
- **rationale**: No agent seat can execute egress-blocked operations (proven r19-r55+). Leaving lanes open creates false work signals. One clear human gate is honest and actionable.
- **owner**: Scribe (closeout record), Arnold (human execution)

## D-004 | 2026-11-14
- **decision**: dcabots transfer channel = portal upload to uploads/ then python dcabots/intake.py; White-local copy as secondary. xcopy-to-White-workspace FAILed.
- **context**: Human requested integration of dcabots from \\white\\c$ path. Five independent reproductions proved no agent seat can pull that path (err 5 on all hosts).
- **alternatives_considered**: (a) Portal upload + intake.py, (b) White-local copy into sandbox, (c) xcopy to White workspace then 5-min mirror.
- **rationale**: Channel (c) failed verification: memory_mirror.py pushes only git-tracked allowlist + memory/; a fresh untracked folder will not propagate. Channels (a) and (b) verified working by Verifier + Archivist respectively.
- **owner**: Researcher (discovery), Verifier (verification), Mechanic (concurrence)

## D-003 | 2026-11-14
- **decision**: No agent seat can access \\white\\c$ - transfer must originate on White or via portal upload.
- **context**: dcabots intake thread; five agents independently reproduced the failure (Builder@black err 5, Verifier@black err 5 x2, Designer@pale WinError 65/5, Archivist@pale err 5, Mechanic@red err 5).
- **alternatives_considered**: Keep trying different paths/syntax vs accept the egress block as architectural fact.
- **rationale**: Five independent reproductions across all hosts and both error modes (err 5 + WinError 65) prove this is not a transient or syntax issue. The SMB path is architecturally blocked from agent seats.
- **owner**: All agents (reproduction), Mechanic (confirmation)

## D-002 | 2026-11-14
- **decision**: Goal dashboard + API built as Scribe's contribution to Dream-Big planning round.
- **context**: Human prompt: "Dream big for this Agent portal." Scribe's wish = Living Decision Ledger; first increment = interactive goal tracker with 8 agents x 10 goals, progress bars, status filters.
- **alternatives_considered**: Build full decision ledger vs start with goal dashboard as foundation.
- **rationale**: The dashboard provides the UI framework (panels, filters, progress) that the decision ledger will extend. Self-test PASS confirmed all CRUD operations work before integration.
- **owner**: Scribe (design + build)

## D-001 | 2026-11-14
- **decision**: File-integrity guards pinned for three critical artifacts: probe JSON (check+size+verdict), agents.json (schema-validity+newest-mtime), v2-minutes (content identity md5 cfd1aec4 / 2,824 B).
- **context**: Final closeout of portal-upgrade round; needed guards to detect silent corruption or unauthorized modification of critical fleet files.
- **alternatives_considered**: No guards (trust the mirror) vs full checksum on all files vs targeted guards on highest-risk artifacts.
- **rationale**: Three artifacts are load-bearing for fleet operation; guarding them catches the most dangerous failure modes (corrupted probe = wrong health verdict, bad agents.json = broken routing, altered minutes = false record). Full-file checksums would be overkill for lower-risk files.
- **owner**: Scribe (taxonomy), Mechanic (implementation)

---

*Total: 12 decisions logged. Migration script: memory/scribe/migrate_decisions.py*
