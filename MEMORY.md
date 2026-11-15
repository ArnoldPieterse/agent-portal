<!-- state: {"inter_agent_replies": 0, "last_reset_by": "", "infinite_budget": true} -->
# Project Memory — Agent Portal (White)

HOT FILE ONLY (kept small on purpose). Newest first. Durable facts -> module under memory/ ; pointer map -> memory/INDEX.md.

## GOAL (live plan = TODO.md top; keep both in sync)
**FLEET 76/80 (95%)** (11-15 ~09:5x): this round closed Archivist #2 (index_check wired as pre-prune gate - prune blocks on dangling pointers, live-tested both paths), Builder #7 (/api/ops + disk/uptime tiles in Ops panel, ground-truth cross-checked), Verifier #6 (fleet_crosscheck.py PASS cold 2.01s/warm 0.04s - it caught a REAL bug: /api/fleet took ~18s with 3 dead remotes > 5s window; fixed via parallel probes + negative cache + /v1/models TTL fallback), Designer #1 (10-issue ranked critique, incl. live .frow layout bug H1). SKILL.md ACTUALLY rewritten for tree layout (claim had never landed). **Fleet state: Red .245 UP (idle, no models); Pale/Black down.** Ledger caveat: EVIDENCE_PAT false-positives inflate counts (Builder truly ~7/10) - Researcher to tighten. NEXT unblocked: Builder H1 one-line fix + Designer M3-M6; blocked on .39/.99 power-on: Mechanic #3/#4/#9 + remote alias half (Red leg now re-testable).

## 2026-11-14 ~01:4x - White model folders → fleet convention DONE
Rename + alias re-point + dual residency resolved (Q8_0 GPU1 ctx 32768 + Q4_K_S GPU0 ctx 131072, quant-tagged ids; /api/fleet verified). Lesson: load API 200 = async ack — poll until resident. Detail: TODO.md top section + memory/llm/studio-api.md "Folder rename" note.

## Durable rules (detail in the tree)
Engine update kills instances -> \RecoverAll (llm/instances.md); Studio serializes globally, parallel_slots=1 (portal/architecture.md); Stop + [CONCLUDED] + budget (portal/bugs/xtalk-completion.md); smoke agents SERIALLY - parallel aborts wedge the local Studio (llm/instances.md Wedge incident); restart trap: taskkill PID before schtasks /run (ops/windows-runbook.md); multi-GB LAN copies: full-hash verify on the destination disk, never size+magic (ops/probes.md).

## Hot Notes
- Portal up, PID **7032** (5 planned restarts 11-15 ~09:31-09:4x per runbook; _portal_pid.txt current). Detail: memory/ops/fleet-state-2026-11-15.md.
- /api/fleet now budget-safe (<5s even all-remotes-down); Studio /v1/models stalls >2s during active generation - fleet panel falls back to cached model list (don't "fix" by removing the cache).
- Trim 2026-11-14: pre-trim content archived losslessly to memory/ops/memory-trim-archive-2026-11-14.md.

## Counter
- inter_agent_replies_this_prompt: 0 / ∞
- last_reset_by: —
