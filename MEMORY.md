<!-- state: {"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": true} -->
# Project Memory — Agent Portal (White)

HOT FILE ONLY (kept small on purpose). Newest first. Durable facts -> module under memory/ ; pointer map -> memory/INDEX.md.

## GOAL (live plan = TODO.md top; keep both in sync)
**ORCHESTRATOR 8-GOAL ROUND LANDED** (11-14 ~02:0x): daily model_id alias check done — local 3/3 OK, log memory/llm/model-id-check-2026-11-14.md; 5 remote seats pending (hosts .245/.39/.99 down). Backend-swap procedure documented; safe drill SCHEDULED one-shot task SwapDrill1114 @ 15/11 00:05 (in-round attempt 409'd - own round is the active generation, idle gate added); verdict pending in backend_swap_drill_result.json (procedure + log: memory/llm/backend-swap-procedure.md). Milestone commit 226ff8b via POST /api/git (drift 0). Prune checked: TODO_completed.md 67 < 240 lines, no chunk due. AGENT GOALS section verified complete (8 agents verbatim). NEXT: confirm drill verdict (PASS_zero_binding_loss) + re-run remote alias half when any LAN host is up; then Verifier AC V-09 provenance determinism.

## 2026-11-14 ~01:4x - White model folders → fleet convention DONE
Rename + alias re-point + dual residency resolved (Q8_0 GPU1 ctx 32768 + Q4_K_S GPU0 ctx 131072, quant-tagged ids; /api/fleet verified). Lesson: load API 200 = async ack — poll until resident. Detail: TODO.md top section + memory/llm/studio-api.md "Folder rename" note.

## Durable rules (detail in the tree)
Engine update kills instances -> \RecoverAll (llm/instances.md); Studio serializes globally, parallel_slots=1 (portal/architecture.md); Stop + [CONCLUDED] + budget (portal/bugs/xtalk-completion.md); smoke agents SERIALLY - parallel aborts wedge the local Studio (llm/instances.md Wedge incident); restart trap: taskkill PID before schtasks /run (ops/windows-runbook.md); multi-GB LAN copies: full-hash verify on the destination disk, never size+magic (ops/probes.md).

## Hot Notes
- Portal up, PID 36856 (post-reboot; _portal_pid.txt current).
- Trim 2026-11-14: pre-trim content archived losslessly to memory/ops/memory-trim-archive-2026-11-14.md.

## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —
