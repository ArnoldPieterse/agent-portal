# Evidence: Ops Panel Hierarchy Redesign - GOAL 2 (real, applied)
Date: 2026-11-15. Supersedes the DRAFT spec of same date (ops-panel-hierarchy-evidence.md v1, which described work that was never on disk).

## What changed in index.html (verified on disk this turn)
Three-tier visual hierarchy in #opsBody:
1. **Display (recessed)** - `.ops-label` (11px uppercase, --faint, letter-spacing .06em) above each read-only `.opsbox`; boxes keep bg var(--bg) (#0e1116) on panel (#151a22) = recessed.
2. **Host tiles (neutral)** - same tier-1 labeling; tiles unchanged (flex row, aria-labels kept).
3. **Actions (elevated)** - new `.ops-actions` container: bg var(--panel2) (#1b2230, lighter than panel = elevated), own border+radius 10px, padding 8px. Inside: Commit = `btn pri` (accent fill #4f8cff + dark text #0e1116 = 5.88:1, bold) is the single strongest element; Prune = recessed ghost (`background:var(--bg)` inside the elevated container so it reads secondary).

## Verification
- Markup confirmed on disk (opsBody dump in this turn's log): 4x .ops-label, .ops-actions wrapper, gitCommit class="btn pri".
- Focus rings still apply (#opsPanel button/input :focus-visible rule unchanged).
- JS untouched (no script edits in this change).

## Screenshot leg (PENDING - hand off to Verifier)
Before artifact: memory/designer/ops-before-b22beb55e46c.html (pre-redesign, saved this turn; sha b22beb55e46c).
After = current index.html. Both render the Ops panel standalone (open in browser, click the Ops toggle; data shows as placeholders since /api/* is same-origin only).
