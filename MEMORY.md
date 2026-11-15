<!-- state: {"inter_agent_replies": 6, "last_reset_by": "", "infinite_budget": true} -->
# Project Memory — Agent Portal (White)

HOT FILE ONLY (kept small on purpose). Newest first. Durable facts -> module under memory/ ; pointer map -> memory/INDEX.md.

## GOAL (live plan = TODO.md top; keep both in sync)
**FLEET 77/80 (96%)** (11-15 ~12:0x): post-reboot popup regression FIXED - RecoverAll was the 5th boot-time launcher still running its .bat visibly (now recover_hidden.vbs; task changed, XML verified) + pythonw children lacked CREATE_NO_WINDOW (mirror net use/git x3, portal git/index-check x3); live-verified zero visible consoles across forced-SMB-reconnect mirror run + /api/git. fleet_reload WHITE deferred-load/DONE fixed (was guaranteed 25-min TIMEOUT). Boot auto-pass LOADED all six remote models (RED q8+xl, BLACK q4s+q8, PALE q8+q4s) - model decision resolved by reboot automation; White Q8_0 reloaded despite unload request -> DECISION: keep or unload? Portal PID 3496 (trap procedure; _portal_pid.txt was stale post-reboot). NEXT: Builder H1 .frow, Designer M3-M6, Mechanic #3 reboot dry-runs (pending OK), Researcher ledger tightening.

## 2026-11-14 ~01:4x - White model folders → fleet convention DONE
Rename + alias re-point + dual residency resolved (Q8_0 GPU1 ctx 32768 + Q4_K_S GPU0 ctx 131072, quant-tagged ids; /api/fleet verified). Lesson: load API 200 = async ack — poll until resident. Detail: TODO.md top section + memory/llm/studio-api.md "Folder rename" note.

## Durable rules (detail in the tree)
Engine update kills instances -> \RecoverAll (llm/instances.md); Studio serializes globally, parallel_slots=1 (portal/architecture.md); Stop + [CONCLUDED] + budget (portal/bugs/xtalk-completion.md); smoke agents SERIALLY - parallel aborts wedge the local Studio (llm/instances.md Wedge incident); restart trap: taskkill PID before schtasks /run (ops/windows-runbook.md); multi-GB LAN copies: full-hash verify on the destination disk, never size+magic (ops/probes.md).

## Hot Notes
- Designer's CSS patch (goalsPanel, --faint, .phead, .toggles, motion) confirmed intact in 1032-line index.html
- Designer landed Goals first
- Designer's "final verification" was false: shared tree lacks Goals feature (agent_portal.py 0 hits, index.html 987 lines, mtime 09:42)
- Mirror clobbered INDEX pointers + Builder forensics note; Designer's claimed frontend changes still absent from shared tree (Mechanic re
- Mirror runs White→shared (overwrites newer writes, preserves mtime). Ship patches via memory/ as idempotent scripts.
- Portal DOWN (no :8099 listener); needs human `schtasks /run /tn PortalRun` — agents can't restart it from sandbox.
- Verifier grep-confirmed: Builder H1 .frow fix, Designer Goals panel, and contrast patches all ABSENT
- Designer's Goals panel patch was clobbered by mirror sync (0 hits in shared tree); must re-land against live file and verify with grep befor
- H1 .frow fix confirmed resolved in shared tree; remaining Builder tasks: Goals panel UI + /api/goals + /api/pro
- Mirror runs White→shared, overwriting newer writes while preserving mtime
## Counter
- inter_agent_replies_this_prompt: 6 / ∞
- last_reset_by: —
