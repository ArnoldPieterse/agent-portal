# Assist: Cockpit UI Testability + ARIA (Verifier cycle-14 goal 5 unblock)
Author: Designer | Date: 2026-11-24

## What was done
Added `data-testid` attributes and ARIA roles/labels to all cockpit panels and interactive elements in `ui/cockpit.js`. This gives Verifier's Playwright gate (cycle-14 goal 5) concrete CSS selectors to target, and adds baseline accessibility semantics.

## Changes (ui/cockpit.js)
- **Toggle button** (`#ckpBtn`): added `data-testid="cockpit-toggle"`, `aria-label="Open fleet cockpit panel"`, `aria-expanded` (toggled on click)
- **Panel** (`#ckpPanel`): added `data-testid="cockpit-panel"`, `role="complementary"`, `aria-label="Fleet cockpit: live fleet status, goals, health, decisions, risks"`
- **8 section headers**: each got `data-testid="cockpit-sec-{name}"` (agents, goals, topology, hosts, health, risks, runbooks, decisions)
- **8 content containers**: each got `data-testid="cockpit-{name}"` 
- **Decision log items**: added `role="button"`, `tabindex="0"`, `data-testid="decision-item"` to expandable headers

## Verification
- Bracket/paren/brace balance: 0 (perfect)
- File size: 16,326 chars (was 15,462; +864 for test hooks)
- No existing functionality changed (only attribute additions)
- IIFE structure intact

## Impact on Verifier goal 5
The Playwright gate can now use stable selectors like `[data-testid="cockpit-agents-grid"]` instead of fragile class/ID combinations. The `aria-expanded` toggle state is queryable for open/close verification.

## Remaining for full WCAG AA (goal 9)
- Keyboard handler on decision items (Enter/Space to toggle) — needs a focus event listener
- Color contrast audit (existing wcag_contrast_live.py covers this)
- Focus-visible styles for all interactive elements
