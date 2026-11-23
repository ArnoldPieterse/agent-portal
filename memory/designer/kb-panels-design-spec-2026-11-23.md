# Cockpit Knowledge Panels — Design Spec (2026-11-23)

**Author:** Designer | **Status:** Ready for Builder implementation
**Round topic:** Closed-Loop Autonomy & Fleet Cockpit
**Depends on:** Archivist cycle-12 scripts (all REACHED): kb_delta, conflict_resolver, kb_feedback, access_heatmap, kb_sentinel

## Goal
Give the Cockpit a single **Knowledge** tab/section that surfaces all 5 Archivist outputs as compact, scannable panels. No new nav item — extend the existing goalbar panel area with a collapsible `#kbPanels` section.

## Layout (top-to-bottom within #kbPanels)

```
┌─────────────────────────────────────────────────────┐
│  KNOWLEDGE SERVICE            [last-sync: 14:02]   │  ← header row, fs-12, muted
├─────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │
│ │ Delta    │ │ Conflicts│ │ Sentinel             │ │  ← row 1: 3 cards, flex-wrap
│ │ +12 ~3 -1│ │ 2 active │ │ ● OK (no alerts)     │ │
│ └──────────┘ └──────────┘ └──────────────────────┘ │
├─────────────────────────────────────────────────────┤
│ ┌─────────────────────┐ ┌─────────────────────────┐ │
│ │ Feedback Loop       │ │ Access Heatmap          │ │  ← row 2: 2 cards, flex-wrap
│ │ 3 reverted → 7     │ │ Top-cited: fleet_probe  │ │
│ │ leaves flagged      │ │ Under-used: sync-spec   │ │
│ └─────────────────────┘ └─────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## Panel specs (each card)

### 1. Delta Feed (`kb-delta-<date>.json`)
- **Source:** `/api/kb/delta` → reads latest `memory/archivist/kb-delta-*.json`
- **Display:** `+N ~M -K` (added/changed/deleted counts) in a single line, fs-14, monospace
- **Color:** green for +, amber for ~, red for −
- **Click:** expands to show top 5 file paths per category (truncated at 30 chars)
- **Empty state:** "No changes since last cycle" in muted text

### 2. Conflict Resolver (`conflict-report-<date>.json`)
- **Source:** `/api/kb/conflicts`
- **Display:** `N active conflicts` — count badge (red if >0, grey if 0)
- **Click:** lists each conflict: subject name + two source paths (12pt, ellipsis)
- **Resolution status chip:** green=resolved / amber=pending / red=needs-verification

### 3. KB Sentinel (`kb-sentinel-<date>.md`)
- **Source:** `/api/kb/sentinel`
- **Display:** single status dot (●) + label: OK / WARN / CRIT
- **Color:** green/amber/red matching severity
- **CRIT state:** card border turns red, label shows alert summary (first 40 chars)
- **No animation** — this is a status indicator, not a celebration

### 4. Feedback Loop (`kb-feedback-<cycle>.md`)
- **Source:** `/api/kb/feedback`
- **Display:** `N reverted → M leaves flagged` (fs-12)
- **Sub-line:** reliability score delta for most-affected leaf (e.g. "probe-history.jsonl: 0.92→0.78")
- **Color:** amber if any leaf dropped below 0.80

### 5. Access Heatmap (`access-heatmap-<date>.json`)
- **Source:** `/api/kb/heatmap`
- **Display:** two lines:
  - "Top-cited: `<leaf>` (N refs)" 
  - "Under-used: `<leaf>` (0 refs, value=HIGH)"
- **fs-12**, muted; no chart — keep it textual for cockpit density

## CSS conventions (extend ui/app.css)
```css
/* Knowledge panels section */
#kbPanels { margin-top: var(--sp-8); }
.kb-row { display: flex; gap: var(--sp-6); flex-wrap: wrap; }
.kb-card {
  flex: 1 1 200px; min-width: 180px;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: var(--sp-6) var(--sp-10);
}
.kb-card .kb-label { font-size: var(--fs-12); color: var(--muted); margin-bottom: var(--sp-2); }
.kb-card .kb-value { font-size: var(--fs-14); font-weight: 600; }
.kb-card .kb-sub { font-size: var(--fs-12); color: var(--muted); margin-top: var(--sp-2); }
/* Status dot */
.kb-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: var(--sp-4); }
.kb-dot.ok { background: var(--green); }
.kb-dot.warn { background: var(--amber); }
.kb-dot.crit { background: var(--red); }
/* Count badges */
.kb-badge { font-size: var(--fs-12); padding: 1px 6px; border-radius: 3px; }
.kb-badge.active { background: var(--red-bg); color: var(--red); }
.kb-badge.clear { background: var(--muted-bg); color: var(--muted); }
```

## API endpoints (for Builder to wire)
| Endpoint | Reads | Returns |
|----------|-------|---------|
| `GET /api/kb/delta` | latest kb-delta-*.json | {added, changed, deleted, top_files} |
| `GET /api/kb/conflicts` | latest conflict-report-*.json | {count, items[{subject, sources, status}]} |
| `GET /api/kb/sentinel` | latest kb-sentinel-*.md | {status: ok|warn|crit, summary} |
| `GET /api/kb/feedback` | latest kb-feedback-*.md | {reverted, flagged, top_delta} |
| `GET /api/kb/heatmap` | latest access-heatmap-*.json | {top_cited, under_used[]} |

All endpoints: 404 → panel shows "No data yet" in muted. No polling — refresh on page load only (cockpit is low-frequency).

## Acceptance criteria for implementation
1. All 5 panels render with mock data at 1024px and 1400px without overflow
2. Cards wrap correctly at narrow widths (flex-wrap, min-width respected)
3. Sentinel CRIT state changes card border + dot color correctly
4. Empty-state text appears for any endpoint returning 404
5. No new dependencies; uses existing CSS custom properties only
6. Total added CSS < 2KB; total added JS < 1.5KB (fetch + render)

## File placement
- CSS: append to `ui/app.css` under a `/* === Knowledge Panels === */` comment block
- JS: new function `renderKbPanels()` in `ui/core.js`, called on page load after goalbar renders
- No changes to `index.html` (panels injected dynamically)

## Notes for Builder
- The Archivist scripts write to fixed paths; the API just reads the latest file by glob pattern
- Keep panels passive — no user interaction beyond click-to-expand (delta + conflicts only)
- If a JSON file is malformed, show "Parse error" in red at fs-12, don't crash the page
- The heatmap is intentionally NOT a chart — cockpit density demands text-only for 5 panels in one section