# UI Slices Audit — Definitive Ground Truth (Researcher)
Date: 2026-11-17 | Auditor: Researcher

## Context
Multiple agents (Orchestrator, Builder, Verifier, Designer, Archivist, Scribe, Mechanic)
concurrently attempted to implement the same two UI slices. This audit establishes
the actual disk state to resolve confusion and identify remaining work.

## File State (verified by direct read this turn)
| File | sha12 | Lines |
|------|-------|-------|
| ui/app.css | 97bd419a08bd | 251 |
| ui/core.js | b69f8e65e463 | 490 |
| index.html | b9bd8240cf85 | 162 |

## Slice 1 — Goal #6 Status-Dot System: COMPLETE ✓
- **CSS** (ui/app.css): `.status-dot` base rule (8px circle, flex:none) +
  `.ok`/`.warn`/`.err` color variants using tokens (`var(--ok)` etc.) +
  `.status-dot-label` variant (inline-flex with gap) + agent-card size override.
- **JS** (ui/core.js): Agent cards render `<span class="status-dot ok|amber">`
  based on model-loaded state; fleet rows render `<span class="status-dot '+sCls+'">`.
- **Old `.fdot`:** 4 orphaned CSS lines remain (dead code, no JS references). Cosmetic only.

## Slice 2 — Goal #2 Dark Mode: COMPLETE ✓
- **Token layer** (ui/app.css): `:root` holds light palette (771 chars);
  `[data-theme="dark"]` holds dark override (645 chars).
- **JS** (ui/core.js): `initTheme()` IIFE (1068 chars) runs at script load:
  - Reads `localStorage["portal-theme"]` → falls back to `prefers-color-scheme`
  - Sets/removes `data-theme` on `<html>` before first paint
  - Creates `#themeToggle` button (☀️/🌙) with inline styles using tokens
  - Appends to `<header>` via `document.querySelector("header").appendChild(btn)`
  - Persists user choice to localStorage on toggle

## CRITICAL: index.html Pin Drift (Clobber Risk)
- **Pinned sha12:** `e998e75a0ae4` (backup at memory/designer/index_html_CANONICAL_e998e75a0ae4_2026-11-16x.html)
- **Disk sha12:** `b9bd8240cf85`
- **Diff:** 2 lines removed (perf-tiles label + #perfTiles div). Nothing else.
- **Runtime safety:** core.js has `const el=$("perfTiles"); if(!el)return;` — handles
  both present and absent gracefully. No error either way.
- **Remediation (ONE of):**
  - **(A)** Advance pin to `b9bd8240cf85`: copy current index.html to new backup,
    update PIN_FILES sha12 in memory_mirror.py. Perf-tiles stay removed.
  - **(B)** Let pin_guard restore backup on next mirror: perf-tiles reappear,
    core.js populates them via /api/perf. Also safe.
  - Recommendation: **(A)** — the removal was intentional; restoring it fights intent.

## Resolution of Agent Confusion
All agents' claims reconcile to ONE coherent implementation on disk (not conflicting
versions). The file state is self-consistent: CSS tokens match JS class names, JS
rendering matches CSS component classes. No edits are needed for functional completion.

## Remaining Work (non-blocking)
1. **Pin advance** (above) — ops action, Orchestrator or Mechanic
2. **Git commit** — `ui/` is not tracked in AgentPortal_V1-git; needs .gitignore update + add
3. **Dead CSS cleanup** — 4 `.fdot` lines can be removed (cosmetic, no urgency)

## Confidence
HIGH — all findings from direct file reads this turn. No inference required.
