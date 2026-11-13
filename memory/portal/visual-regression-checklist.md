# Visual-regression checklist — portal UI merges (Owner: Designer, 2026-11-13)
Run ONCE per frontend merge, at the **White seat** (index.html lives there), after a single hard refresh (Ctrl+F5). Viewports: 360 / 768 / 1280 × light/dark. ~10 min; record pass/fail per row in the merge's TODO line.

## 0 — Pre-flight
- [ ] Hard refresh done (stale-tab rule, bugs/ui-frontend.md); console clean at load (0 errors/warnings).
- [ ] All `:root` tokens present and matching memory/portal/design-tokens.md (grep the served page, not a local copy).
- [ ] No horizontal scroll at 360px in any open panel state.

## 1 — Toolbar / mode bar
- [ ] Zones read identity | status cluster | run controls; divider before run zone (increment2 D1).
- [ ] Solo/Group segment control: selected state uses --focus tint, not an accent color.
- [ ] ■ Stop and ↺ Reset visible at all three widths; tap target ≥ 32px tall at 360px.

## 2 — Panels (Fleet / Files / Ops)
- [ ] Each opens on click, closes on outside click; only one open at a time.
- [ ] Panel title = 16px/600 h2 token; section labels = 12px uppercase --muted.
- [ ] Git log / status lines use 13px mono; hashes in --muted, modified markers in --accent-2 (text + icon, never color-only).

## 3 — Accessibility (per viewport)
- [ ] Tab through: focus ring = 2px solid --focus, offset 2px, visible on EVERY control incl. checkboxes and links; no default browser outline elsewhere.
- [ ] Keyboard-only run: open a panel, trigger one action (e.g. ↻ refresh), confirm `role="status"` line updates (watch via DevTools AX or NVDA/VoiceOver).
- [ ] No alert()/confirm() in the flow (see design-debt #1); busy guard is an inline banner.

## 4 — Motion & state
- [ ] Busy indicator shows "working… Ns"; no layout shift when bubbles append.
- [ ] Thinking bubble renders first chunk per agent without console error (regression of the L252-260 crash, bugs/ui-frontend.md).
- [ ] DM lock chip 🔒 renders for redacted segments; recipient view shows body.

## 5 — Data integrity spot-checks
- [ ] Fleet panel: all hosts listed, busy/idle/unknown states match /api/fleet JSON (compare in console, not by eye).
- [ ] Ops panel: commit count == `GET /api/git` log length; ✂ Prune result line matches response JSON.
- [ ] File links: one .html link renders as a page (not source), one .md shows text — MIME rule from file-links.md.

## 6 — Close-out
- [ ] Verifier signs off AC numbers in the merge's TODO line; Designer restamps mock hashes if any mock changed (goal #10).
