<!-- state: {"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": true} -->
# Project Memory — Agent Portal (White)

HOT FILE ONLY (kept small on purpose). Newest first. Durable facts -> module under memory/ ; pointer map -> memory/INDEX.md.

## GOAL (live plan = TODO.md top; keep both in sync)
**FLEET GOAL SWEEP LANDED** (11-15 ~01:5x): fleet ledger 37 -> **70/80 (88%)**; Scribe 10/10, all others 6-9/10. Test suites shipped (prune regression, upload path-safety, /api/git probe - all PASS); live prune e2e + post-prune audit ritual; index sweep 0 dangling; junk untracked (baseline 417); daily 18:00 git task + 10-min fleet probe tasks live. NEXT: confirm SwapDrill1114b verdict -> close orchestrator goal 4; remote-dependent goals (Verifier #6, Mechanic #3/#4/#9, alias half) blocked on human power-on of .245/.39/.99; then Verifier AC V-09.

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
