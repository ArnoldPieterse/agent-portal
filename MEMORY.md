<!-- state: {"inter_agent_replies": 12, "last_reset_by": "", "infinite_budget": true} -->
# Project Memory — Agent Portal (White)

HOT FILE ONLY (kept small on purpose). Newest first. Durable facts -> module under memory/ ; pointer map -> memory/INDEX.md.

## GOAL (live plan = TODO.md top; keep both in sync)
**FLEET 77/80 (96%)** (11-15 ~11:0x): CRITICAL popup complaint FIXED - all 4 scheduled tasks now windowless (PortalRun via portal_hidden.vbs hidden-cmd pythonw; mirror/probe/daily-git run pythonw directly); verified live: mirror 10:57:31 + probe 11:01:01 fired with zero visible windows, fleet_probe's first-ever successful scheduled run. **Fleet FULLY UP**: human powered .39/.99 back on ~10:5x - all 4 hosts report (White busy Q8_0; Red/Pale/Black idle). Remote alias half PASS 6/6. Mechanic #4 + #9 CLOSED. SURFACED: remotes have NO model in VRAM -> DECISION NEEDED (human): load six bound models? Ledger caveat stands (EVIDENCE_PAT false-positives; Researcher to tighten). NEXT unblocked: Builder H1 .frow fix, Designer M3-M6, Mechanic #3 remote reboot dry-runs (pending human OK).

## 2026-11-14 ~01:4x - White model folders → fleet convention DONE
Rename + alias re-point + dual residency resolved (Q8_0 GPU1 ctx 32768 + Q4_K_S GPU0 ctx 131072, quant-tagged ids; /api/fleet verified). Lesson: load API 200 = async ack — poll until resident. Detail: TODO.md top section + memory/llm/studio-api.md "Folder rename" note.

## Durable rules (detail in the tree)
Engine update kills instances -> \RecoverAll (llm/instances.md); Studio serializes globally, parallel_slots=1 (portal/architecture.md); Stop + [CONCLUDED] + budget (portal/bugs/xtalk-completion.md); smoke agents SERIALLY - parallel aborts wedge the local Studio (llm/instances.md Wedge incident); restart trap: taskkill PID before schtasks /run (ops/windows-runbook.md); multi-GB LAN copies: full-hash verify on the destination disk, never size+magic (ops/probes.md).

## Hot Notes
- /api/fleet budget-safe (<5s even all-remotes-down); Studio /v1/models stalls >2s during generation - fleet panel falls back to cached model list (don't remove the cache).
- Trim 2026-11-14: pre-trim content archived losslessly to memory/ops/memory-trim-archive-2026-11-14.md.
- Fleet 77/80 (96%); popup fix verified
- Portal PID is now 19488 (was 54008); confirmed via `_portal_pid.txt`, stale ref fixed in MEMORY.md hot notes.
- Unapplied
- White :8099/:8888 time out from LAN — pre-existing firewall policy (
- Builder: last round's /api/goals + /api/provenance wiring and H1 .frow fix were lost; re
- Designer: Building Goals panel + /api/goals endpoint (both absent); confirmed 3 contrast failures; patch covers H2+M3–M6.
- Designer's CSS patch (goalsPanel, --faint, .phead, .toggles, motion) confirmed intact in 1032-line index.html
- Designer landed Goals first
## Counter
- inter_agent_replies_this_prompt: 12 / ∞
- last_reset_by: —
