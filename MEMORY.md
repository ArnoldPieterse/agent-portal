<!-- state: {"inter_agent_replies": 8, "last_reset_by": "", "infinite_budget": true} -->
# Project Memory — Agent Portal (White)

HOT FILE ONLY (kept small on purpose). Newest first. Durable facts -> module under memory/ ; pointer map -> memory/INDEX.md.

## GOAL (live plan = TODO.md top; keep both in sync)
**FLEET 77/80 (96%)** (11-15 ~12:0x): post-reboot popup regression FIXED - RecoverAll was the 5th boot-time launcher still running its .bat visibly (now recover_hidden.vbs; task changed, XML verified) + pythonw children lacked CREATE_NO_WINDOW (mirror net use/git x3, portal git/index-check x3); live-verified zero visible consoles across forced-SMB-reconnect mirror run + /api/git. fleet_reload WHITE deferred-load/DONE fixed (was guaranteed 25-min TIMEOUT). Boot auto-pass LOADED all six remote models (RED q8+xl, BLACK q4s+q8, PALE q8+q4s) - model decision resolved by reboot automation; White Q8_0 reloaded despite unload request -> DECISION: keep or unload? Portal PID 3496 (trap procedure; _portal_pid.txt was stale post-reboot). PUBLIC REPO LIVE (ArnoldPieterse/agent-portal) - tracked files publish automatically, no secrets (ops/public-repo-agent-portal-2026-11-15.md). NEXT: Builder H1 .frow, Designer M3-M6, Mechanic #3 reboot dry-runs (pending OK), Researcher ledger tightening.

## 2026-11-14 ~01:4x - White model folders → fleet convention DONE
Rename + alias re-point + dual residency resolved (Q8_0 GPU1 ctx 32768 + Q4_K_S GPU0 ctx 131072, quant-tagged ids; /api/fleet verified). Lesson: load API 200 = async ack — poll until resident. Detail: TODO.md top section + memory/llm/studio-api.md "Folder rename" note.

## Durable rules (detail in the tree)
Engine update kills instances -> \RecoverAll (llm/instances.md); Studio serializes globally, parallel_slots=1 (portal/architecture.md); Stop + [CONCLUDED] + budget (portal/bugs/xtalk-completion.md); smoke agents SERIALLY - parallel aborts wedge the local Studio (llm/instances.md Wedge incident); restart trap: taskkill PID before schtasks /run (ops/windows-runbook.md); multi-GB LAN copies: full-hash verify on the destination disk, never size+magic (ops/probes.md).

## Hot Notes
- Verifier found its stopgap and Designer's script patch the same line with different replacements — deployment conflict unresolved.
- Portal confirmed DOWN (port 8099 closed), cannot restart from sandbox; /api/provenance missing from agent_portal.py
- Stale mirror sync clobbers Designer
- Portal DOWN since 11-15; restart requires human
- Portal DOWN (no :8099); sole unblock = human runs `schtasks /run /tn PortalRun` on White; all 8 lanes reported, round concluded.
- Orchestrator confirmed /api/goals code IS present in its working dir (L1466, L1661-63), resolving the landed-vs-absent split.
- Shared tree clobbered ~12:56 back to unpatched baseline; H1 fixes and /api/goals gone, mtimes confirm reset
- Portal restart is human-only gate: port 8099 CLOSED, schtasks
- Mirror
- Shared tree (Z:\) is unreliable: files vanish mid-round and mirror clobbers occur; always re-verify state before acting.
## Counter
- inter_agent_replies_this_prompt: 8 / ∞
- last_reset_by: —
