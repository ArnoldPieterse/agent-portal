# Goal 1 (WCAG) accessible-name leg: settings-dialog labels fixed — 2026-11-21

**Closes:** the open item from `aria-audit-2026-11-21.md` ("Fixes pending index.html repin") and the HOT-NOTE known issue ("Settings dialog uses sibling labels… 23 flagged").

## What changed in index.html (21 edits, one pin cycle)
1. **14 settings-dialog sibling labels** got `for=` attributes matching their input ids:
   f_name, f_emoji, f_color, f_blurb, f_persona, f_studio, f_key, f_ragstudio, f_ragkey,
   f_model, f_temp, f_maxtok, f_reasoning, f_maxtools.
2. **3 group labels** (no single labelable target) converted to labelled groups:
   `role="group" aria-labelledby` on the container + `id` on the label —
   lbl-tools (Tools checkboxes), lbl-ragkb (RAG knowledge base), lbl-memcycle (Memory cycle).
3. **1 unlabelled select**: `#actSel` got `aria-label="Session"` (session picker in actPanel).
4. **3 remaining flagged elements** (previously classed "non-issues") given explicit names for a clean audit:
   `textarea#input` aria-label="Message"; hidden pickers `#filePick` aria-label="Attach files",
   `#dirPick` aria-label="Attach folder".

## Pin advance (same turn, per pin_guard rule)
- Round 1 (edits 1–3): sha12 `9eb4e3681bcc` → backup `index_html_CANONICAL_9eb4e3681bcc_2026-11-21y.html`, PIN_FILES updated.
- Round 2 (edit 4): sha12 `60fba65a2193` → backup `index_html_CANONICAL_60fba65a2193_2026-11-21z.html`, PIN_FILES updated. Live==pinned verified.

## Verification (static, sandbox — no browser per ops/browser-acceptance-workaround)
- `python memory/designer/aria_audit.py` → **interactive elements: 49 | missing accessible name: 0** (was 18 flagged / 17 fixable before this pass).
- Pin integrity: live index.html sha12 == PIN_FILES sha12 == backup sha12 (`60fba65a2193`).
- No layout impact: `for=`/`aria-*` attributes only; group wrappers reuse the existing `<div>` containers (no new elements, no CSS change).

## Status
Goal 1 acceptance leg "ARIA labels present on all buttons/inputs" now holds with **zero** audit findings. Goal 1 was already dashboard-verified for the icon-button leg; this leaf closes the last known accessible-name gap in the portal.
