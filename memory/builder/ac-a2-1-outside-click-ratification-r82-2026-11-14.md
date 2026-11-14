# Builder r82 — AC-A2-1 outside-click (A4) ratification, 2026-11-14

**Trigger:** Scribe r81 routed "AC-A2-1 outside-click ratification → Designer/Builder".

## Verdict: RATIFIED (static, artifact f18b24c4 / 71,096 B — the file Arnold will stamp)

### A4 block location & review (`index_html_v22_f18b24c4d5cce206bf85fc41ca550bc5.html`, lines 1009–1024)
- `panelToggles` map covers all four panels: act / fleet / ops / files (btn + panel refs).
- `panelClose(k)` delegates via `t.btn.click()` — re-enters the OWNING handler, so each panel's own cleanup (`actTimer`/`fleetTimer`) runs. No duplicated state management. Correct pattern.
- Idempotency guard: only clicks when `classList.contains("open")` → double-close safe.
- Hit-test: skips when `e.target` is inside btn OR panel (`contains()` on both). Correct — button and panel are separate elements.
- Event ordering: document-level bubble listener (no capture), same shape as existing attachWrap handler (line 757). Toggle button's own onclick fires first (target phase); the A4 loop then sees `btn.contains(e.target)` → skips. No double-toggle bug.
- Files panel: closing via btn.click() only toggles classes off — no fetch triggered, consistent with AC-A2-4 (no polling; filesLoad is open-only).

### Syntax sanity (Black seat; node unavailable on host)
String/comment/regex-aware bracket balance on both `<script>` blocks of f18b24c4:
- script 0: {} 160/160, () 614/614, [] 40/40 — OK
- script 1: {} 120/120, () 530/530, [] 27/27 — OK
(First pass showed 2 "mismatches"; both traced to my checker not handling regex literals, e.g. `/[\^\]\n]/gi` in renderDms — artifacts of the tool, not the code.)
Complements Verifier's static sweep (script balance 2/2, zero console-error source patterns).

### Non-blocking note (of record)
A4 comment says "one-open-at-a-time + outside-click-close". Code implements **outside-click-close-all** (any click outside every open panel closes them all; clicking inside one panel also closes the others). True mutual-exclusion-at-open is NOT enforced — two panels can be momentarily open together. Comment slightly overstates; behavior is safe and arguably better for this UI. No change owed for an internal ops tool.

### Seat-state observation (not a defect)
Black-seat root `index.html` = 8fc29f19 / 68,549 B — pre-A4 (only the attachWrap outside-click at line 721). Matches Verifier r81's Black read. A4 exists only in the v2.2 artifact pending Arnold's stamp on White → consistent with AC-A2-2 LIVE still being the sole open gate.

**Builder lane: [CONCLUDED].** No further agent-executable work owed; remaining gates are Arnold's human-only White-console pass (stamp f18b24c4 + portal restart + PID/CreationDate relay).
