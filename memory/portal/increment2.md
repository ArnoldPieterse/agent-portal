# increment2 — Designer UI spec, round 5 (planning meeting 2026-11-13, file-sharing era)
Status: DESIGN DECISIONS + ACCEPTANCE CRITERIA. Scope = `index.html` only; hard-refresh-safe; NO new endpoints (AC-5 discipline carries over). Queue position: **behind Increment 1** (ws-b-increment1/index.html still unported into live tree) — D2/D5 build on the committed IDENTITY table and monograms, so merge order is strict. File sharing now lets Builder fetch my reference files by relative path (`/api/file?raw&p=designer/increment2-portal-mock.html`, `ws-b-increment1/index.html`) — no more White-drop gate for DESIGN artifacts; the live-tree edit still lands via Builder's row-5 MERGE (diff-reconcile, never blind-overwrite).

## Context: what the file-sharing change unblocks
- My reference implementations travel as files: increment 1 ref = `ws-b-increment1/index.html`; increment 2 interactive mock = `designer/increment2-portal-mock.html` (clickable: arm/confirm, simulated run with typing indicators, jump-pill behavior). Builder can port from the shared folder directly.
- Still gated elsewhere: loopback :8099 is policy-blocked from sandboxes (WinError 10013), so before/after live captures remain a White-side/human step (AC-4 baseline unchanged).

## The five upgrades (increment 2)
All decisions below are scoped to the EXISTING DOM vocabulary (header.bar, modeBar buttons, thread, composer) — additive classes/containers, no layout rewrite.

1. **D1 — Toolbar zoning** — Current mode bar puts Solo/Group tabs + 🛰 Fleet + ⏱ Activity + ■ Stop + ↺ Reset in one equal-weight row: nothing tells the eye which items are navigation vs status surfaces vs destructive run controls. Split into three zones with a 1px divider between zone 2 and 3: left = title + Solo/Group segmented control; center-right = status cluster (Fleet, Activity — quiet, icon+label); right = run controls (Stop, Reset — the only ones that act on the conversation). Hierarchy by grouping + spacing, not font size. Reference pattern: Material 3 top app bar action grouping; VS Code's separation of title/status/command surfaces.
2. **D2 — Per-agent live typing indicator** — With up to 8 agents streaming in parallel, the user cannot tell who is still working when bubbles interleave. While a stream for agent X is active: pulsing ring on X's monogram in a roster strip under the toolbar + one hint line above the composer ("Name is thinking…", max TYPING_HINT_MAX=3 names shown, then "+N more"). Driven by the EXISTING busyNames set (setBusyHint/clearBusyHint already track it) — zero new endpoints. Cleared within one frame of stream end. Reference: Slack typing indicator.
3. **D3 — System events as first-class components** — ✓ Concluded verdicts, ↻ AUTO-CONTINUE n/3, ⚠ auto-continue-limit lines are currently inline text bubbles visually identical to agent speech. Render them centered, 12px, letter-spaced small-caps, muted ink, hairline rules above/below; no monogram, no bubble surface. Separates "what agents said" from "what the engine did" — the user must never re-read a verdict as if an agent wrote it. Reference: Discord system messages / GitHub status lines.
4. **D4 — Smart auto-scroll + jump-to-new pill** — Long group runs yank the reader away from their position every time a bubble lands. Auto-follow only while pinned to bottom (within AUTO_SCROLL_PX=80 of thread end); otherwise accumulate a count and show a floating "↓ N new" pill above the composer; click = scroll to bottom, clear counter, resume auto-follow. Pill is a real <button> (keyboard-reachable, aria-label). Reference: Slack/Teams/Discord standard.
5. **D5 — Bubble metadata + human distinction** — Every agent bubble carries .bmeta: name + HH:MM timestamp (+ round tag in group view); max-width 72ch; ALL bubbles left-aligned with identity carried by monogram (a two-column L/R layout is worse here — 8 speakers make Slack-style "left=them, right=me" ambiguous). Human messages keep the single column but get a 2px accent border (var(--focus)) + explicit "You" text label — distinction by border+label, not color alone (WCAG 1.4.1).

## Shared constants (no magic numbers)
- `AUTO_SCROLL_PX = 80` (pin threshold), `TYPING_HINT_MAX = 3` (names shown in hint line). Join Increment 1's `NAMED_ARM_MS = 3000` as the app's only timing constants.

## Acceptance criteria — increment 2 (pre-change, per Verifier's gate rule)
- **AC-6 Toolbar zoning** — DOM contains three containers `.tb-identity`, `.tb-status`, `.tb-run`; run controls are the LAST zone; one divider element between status and run zones. Pass = static snapshot shows order + divider; regression: Stop/Reset arm-confirm flow (AC-2/AC-3) unchanged.
- **AC-7 Typing indicator** — mid-stream for agent X: X's roster monogram has `.typing` class AND the composer hint line contains X's name; both clear within one frame after stream end. Concurrent streams: ≤ TYPING_HINT_MAX names + "+N more" text. Pass = scripted solo run (present mid / absent post) + group run with 4 concurrent streams asserting the cap.
- **AC-8 System events** — verdict/auto-continue/limit lines render inside `.sysline` elements (centered, no monogram sibling); zero agent-styled wrapper around them. Pass = DOM snapshot of a concluded run: 100% of system strings inside `.sysline`.
- **AC-9 Jump pill** — scrolled to top + ≥2 appended messages → pill visible with exact count; click → `scrollHeight - scrollTop < 4px` and pill hidden; auto-follow resumes while pinned. Pass = scripted scroll/append/click sequence asserts count, position, hide.
- **AC-10 Bubble metadata** — every agent bubble has `.bmeta` (name + HH:MM); human bubbles have `.human` class + 2px var(--focus) border + "You" text label. Pass = snapshot of a thread mixing ≥3 agents + human shows all metadata present; removing color still distinguishes human via label+border.

## Port kit — mock → live hook map (added r56, so the merge is mechanical)
Single source of truth for all CSS/JS = `designer/increment2-portal-mock.html` (copy the `<style>` blocks + functions verbatim; do NOT re-implement from this doc). Mapping onto live `index.html` — **Builder: confirm each anchor against live markup from your seat before touching anything** (live file is not mirrored into the shared folder; names below come from docs, not a live read):
- **D1** — inside existing `header.bar`: wrap current children in `.tb-identity` (title + Solo/Group tabs), `.tb-status` (🛰 Fleet button, keep its current id), insert ONE `.tb-divider`, then `.tb-run` (Stop, Reset — keep current ids). No new buttons; pure re-wrapping.
- **D2** — live already tracks busy agents via `setBusyHint/clearBusyHint` (busyNames set): extend those two functions with (a) roster strip (build once from the increment-1 IDENTITY table; one `.mono` per alias, id `ro-<alias>`) + `.typing` class toggle, (b) replace hint text with mock's `refreshHint()` (TYPING_HINT_MAX cap). No new state.
- **D3** — in the live bubble-render path for engine messages (verdict / `↻ AUTO-CONTINUE n/3` / ⚠ limit lines currently rendered as kind="prompt" bubbles): emit mock's `sysline(text)` div instead of an agent card; skip linkifyFiles for those.
- **D4** — wrap the live thread element in `.thread-wrap{position:relative}` + append mock's `#jumpPill` button; call mock's `pinned()`/`bumpNew()` from whichever function appends bubbles to the thread (Builder: confirm name), plus the scroll listener.
- **D5** — in the live agent-bubble builder: add `.bmeta` row (name + HH:MM, round tag in group view) and 72ch cap; human bubbles get `.human` class + "(You)" label. Chips (increment-1 contract) render inside bubble text unchanged.
Mock JS re-verified r56 (delimiters balanced, all 12 fns defined; esprima unavailable on this seat — Verifier's browser run is the real gate).

## Hand-off
- Builder: port order = Increment 1 (ws-b-increment1/index.html) THEN increment 2, both as row-5 MERGE diff-reconcile on live index.html; my mock is the visual reference for D1–D5 (`designer/increment2-portal-mock.html`).
- Verifier: AC-6…AC-10 are the gate; before/after capture still needs a :8099-reachable seat (White/human) — loopback blocked from sandboxes.
- Orchestrator: ratify queue order + confirm Builder's port window; Scribe: fold into UPGRADES log when ACs land.

## Cross-refs
- -> ui-upgrades-r4.md   increment 1 decisions + AC-1…AC-5 (identity, arm-confirm Stop/Reset, chips)
- -> fleet-status.md     panel UI already built; D1 keeps 🛰 Fleet in its current status zone (no rework)
- -> file-links.md       chip contract consumed by D5 bubble text
- -> v1-inventory.md     row 5 MERGE posture + hard-refresh rule