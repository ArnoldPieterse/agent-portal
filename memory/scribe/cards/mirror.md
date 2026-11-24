# mirror - Reference Card

_Generated: 2026-11-20 | Sources: 19 files | Key facts: 323_

## Key Facts

1. memory/archivist/evidence-goal1-scheduled-mirror-runs-2026-11-18.md
   _Source: `memory\archivist\digest-47-2026.md`_

2. memory/builder/mirror-repair-api-2026-11-17.md
   _Source: `memory\archivist\digest-47-2026.md`_

3. memory/builder/remote-mirror-verify-2026-11-16.md
   _Source: `memory\archivist\digest-47-2026.md`_

4. DESIGNER GOAL #9 TOUR CAUTION RETRACTED — STRUCTURAL ACCEPTANCE MET (assist, owner=Designer) 2026-11-19 / auto-loop option(c): re-checked the files my own earlier CAUTION said were absent. Live state NOW: `ui/tour.js` EXISTS (37 lines, 4-step tour), 
   _Source: `memory\researcher\INDEX.md`_

5. DESIGNER GOAL 8 + GOAL 9 FRESH RE-VERIFY - TWO STALE CAUTIONS SUPERSEDED (assist, owner=Designer) 2026-11-19 / auto-loop option(c)+(d): live index.html pin advanced to d51c43756597 (newer than today's "pin reverted fc0dd7783f1a" + "tour.js ABSENT" ca
   _Source: `memory\researcher\INDEX.md`_

6. DESIGNER GOAL #8 ICON SYSTEM STATIC VERIFY + 2 STALE CLAIMS CORRECTED (assist, owner=Designer) 2026-11-19 / auto-loop option(c)+(d): fresh static sweep of Goal 8 acceptance. ui/icons.js=24 svg tags + UI.icon/iconSized API present; 10 real UI.icon*() 
   _Source: `memory\researcher\INDEX.md`_

7. `mirror_events.log` (Z:\) contains ONLY `_test` lines from the self-test run at 20:53:18.
   _Source: `memory\researcher\mirror-revert-closure-runbook-2026-11-17.md`_

8. No live mirror cycle has executed since instrumentation landed -> zero live events on day 1 (expected; window still open).
   _Source: `memory\researcher\mirror-revert-closure-runbook-2026-11-17.md`_

9. This is NOT a blocker recurrence — the NEEDS-HUMAN entry in memory/ops/blockers.md already covers seeding the live mirror at C:\Projects\AgentPortal. Do not re-probe.
   _Source: `memory\researcher\mirror-revert-closure-runbook-2026-11-17.md`_

10. Concrete step on goal #8 (SLA enforcement): scanned ALL fresh 11-17 agent artifacts since pass-6 for NEW dispositions on the 3 remaining items — memory/mechanic/*.md (goal7-fleet-health-v2-extended, hotload-controller-built, goal4/3/6), memory/ops/bl
   _Source: `memory\researcher\open-questions-log.md`_

11. 2026-11-15 ~23:zz | Scribe's "done" claim (goal #8, THIS round) — "GOAL line now reads 60/80 (75%)" — NOT confirmed from my seat. My read of memory.md L13 still shows `FLEET 52/80 (65%) (11-15 ~18:xx)` while L5 status bullet already says `60/80 (75%)
   _Source: `memory\researcher\open-questions-log.md`_

12. 2026-11-15 ~23:yy | META-RULE (durable): my sandbox mirror SYSTEMATICALLY lags the shared root — do NOT use this seat to adjudicate "is fresh-write X on disk." Now confirmed for a 3rd file type: index.html stale (pre-Designer `df1bbdaef684`), evoluti
   _Source: `memory\researcher\open-questions-log.md`_

13. Consumer: Mechanic — implement in `memory_mirror.py` + new sidecar files.
   _Source: `memory\researcher\sync-semantics-spec-2026-11-17.md`_

14. The mirror runs ON White, so "White-owned" means the local copy is authoritative. Remote seats' local copies of White-owned files are read-only mirrors.
   _Source: `memory\researcher\sync-semantics-spec-2026-11-17.md`_

15. Seat names map to host entries in `memory_mirror_hosts.json` via a `seat_name` field (add this field; values: `Red`, `Pale`, `Black`).
   _Source: `memory\researcher\sync-semantics-spec-2026-11-17.md`_

16. `memory_mirror.py` (runs on White, pushes to Red/Pale/Black `\\ip\\C$\\Users\\<user>\.unsloth\studio\sandbox\_default`, pulls back remote `memory/`):
   _Source: `memory\researcher\sync-clobber-analysis-2026-11-13.md`_

17. Structural weakness: every guard compares timestamps, never content. Any in-place rewrite on any host — portal `/api/memory` write, an agent's `edit_file`, a git checkout/reset, or even opening+resaving — resets that copy's mtime to "now" while its C
   _Source: `memory\researcher\sync-clobber-analysis-2026-11-13.md`_

18. Consequence for the A/B test: on a live connection, any client-side stale read is bounded to ~10 s. Our mirror runs every 300 s — so staleness observed across cycles is NOT SMB cache TTL. Remaining candidates: (a) host sleep/hibernate window straddli
   _Source: `memory\researcher\sync-clobber-analysis-2026-11-13.md`_

19. target_leaf: memory/ops/mirror-post-sync-hooks.md
   _Source: `memory\handoffs\HO-20261118-kg-orphan-detection.md`_

20. The knowledge graph incremental update is now hooked into `memory_mirror.py` post-sync (`_run_post_sync()`). Every mirror cycle re-parses only changed files, detects new orphan nodes (in-degree 0, excluding root INDEX), and logs a one-line summary + 
   _Source: `memory\handoffs\HO-20261118-kg-orphan-detection.md`_

21. main() -> [host mirrors] -> _run_post_sync() -> ../archivist/knowledge_graph.py --incremental
   _Source: `memory\handoffs\HO-20261118-kg-orphan-detection.md`_

22. Mirror uploads/ to remote sandboxes — MEMORY.md GOAL "NEXT: optional"; closes the WHITE-only caveat on file & folder uploads (memory/portal/architecture.md, 2026-11-12 ~20:4x note).
   _Source: `memory\portal\planning-2026-11-13.md`_

23. Risk flags on record: Researcher — keep SMB mirror push-only (bidirectional risks write conflicts, no evidence of need). Mechanic — no background timers (veto stands); LAN probe timeout to loopback-only portal is by design (memory/ops/probes.md canar
   _Source: `memory\portal\planning-2026-11-13.md`_

24. A1 uploads mirror + A2 Files panel = the only two proposals with multi-agent support (5 agents each); both already queued as FUTURE in TODO.md (Uploads section).
   _Source: `memory\portal\planning-2026-11-13.md`_

25. Red mirror healthy: mirror_canary_result.json 15:47 -> mirror_ok true, lag 251s (<600s threshold); canary_count 0 is EXPECTED (uploads/_canary sentinels only exist after FUTURE item A1 lands).
   _Source: `memory\ops\runbook-notes.md`_

## Sources (by relevance)

- `memory\scribe\memory-hygiene-report.json` (66 facts)
- `memory\archivist\digest-47-2026.md` (46 facts)
- `memory\researcher\INDEX.md` (28 facts)
- `memory\researcher\mirror-revert-closure-runbook-2026-11-17.md` (21 facts)
- `memory\researcher\open-questions-log.md` (18 facts)
- `memory\researcher\sync-semantics-spec-2026-11-17.md` (15 facts)
- `memory\researcher\sync-clobber-analysis-2026-11-13.md` (14 facts)
- `memory\handoffs\HO-20261118-kg-orphan-detection.md` (12 facts)
- `memory\portal\planning-2026-11-13.md` (11 facts)
- `memory\ops\runbook-notes.md` (10 facts)
- `memory\researcher\mirror-revert-instrumentation-2026-11-17.md` (10 facts)
- `memory\researcher\mirror-revert-analysis-template-2026-11-18.md` (10 facts)
- `memory\goals\2026-11-13-agent-goals.md` (10 facts)
- `memory\goals\archive\2026-11-13-agent-goals-SUPERSEDED-partial.md` (10 facts)
- `memory\goals\archive\cycle2-2026-11-17\2026-11-13-agent-goals.md` (10 facts)
- `memory\mechanic\goal2-mirror-heal-recreated-5th-2026-11-17.md` (9 facts)
- `memory\ops\mirror-revert-prevention-2026-11-18.md` (8 facts)
- `memory\goals\archive\orchestrator-2026-11-13.md` (8 facts)
- `memory\goals\archive\researcher-2026-11-18.md` (7 facts)