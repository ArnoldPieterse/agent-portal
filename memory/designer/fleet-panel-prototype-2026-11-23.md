# Fleet Status Panel — Design Prototype (Builder Goal #6 assist)
Date: 2026-11-23
Owner: Designer | Contributor to Builder goal 6

## What was done
Built a self-contained HTML prototype (`fleet-panel-prototype-2026-11-23.html`) showing the full Fleet Status Panel layout:

1. **Per-host VRAM bar** — green <70%, amber 70–85%, red >85% (matches spec exactly)
2. **Agent cards** — model alias + status dot (active=green, idle=grey, wedged=red+pulse animation)
3. **24h sparkline** — SVG polyline with gradient area fill, last-point dot
4. **Responsive grid** — auto-fill minmax(280px,1fr), collapses to 1-col at 640px
5. **Unknown host state** — blue card shows empty VRAM bar, "No agents assigned", "no data" sparkline

## Design decisions (for Builder)
- Uses existing design tokens from `ui/tokens.css` — zero hard-coded hex in new code
- Host state badge: pill shape with soft background tint (not solid fill) for hierarchy
- Wedged agent: 1.5s opacity pulse animation (subtle, not distracting)
- Sparkline: no library, raw SVG path — keeps bundle budget intact
- VRAM bar: 6px height (compact), rounded ends, CSS transition on width for smooth updates
- Agent cards: single-line with ellipsis overflow; model name right-aligned in dim color
- Panel header: "Fleet Status" title + relative timestamp, no action buttons (matches existing ops panel pattern)

## Data contract (from /api/fleet/status in agent_portal.py)
```json
{
  "hosts": {
    "<hostname>": {
      "state": "busy|idle|unknown",
      "vram_pct": 82,       // from /api/inference/status (may be null if host down)
      "latency_ms": 12,
      "agents": [{"name":"...", "model":"UD-Q4_K_M", "status":"active|idle|wedged"}],
      "spark_24h": [/* 24 hourly usage values or nulls */]
    }
  }
}
```
Note: `vram_pct` and `spark_24h` are NEW fields not yet in the API. Builder needs to add them to
`_fleet_probe()` / `_fleet_snapshot()` in agent_portal.py, OR I can scope the panel to use existing
fields (generations count as proxy for load) if VRAM isn't available from the Studio API.

## Files changed
- `memory/designer/fleet-panel-prototype-2026-11-23.html` — rendered prototype (open in browser)
- This spec file

## Acceptance status
- [x] Prototype renders all 4 hosts with correct state colors
- [x] VRAM thresholds match spec (green/amber/red at 70/85)
- [x] Agent cards show model + status correctly
- [x] Sparkline handles null data gracefully
- [x] Uses design tokens only (no hard-coded hex in component CSS)
- [ ] Integration into ui/fleet_status.js (Builder's step)
- [ ] API extension for vram_pct + spark_24h (Mechanic or Builder)

## Next steps for Builder
1. Add `vram_pct` field to `_fleet_probe()` — read from `/api/inference/status` response (the Studio already reports GPU memory)
2. Create `spark_24h` by sampling the existing load_trend.jsonl data (Mechanic's goal 1 data source)
3. Replace the compact strip in `ui/fleet_status.js` with the full card grid (CSS patterns in prototype)
4. Verify all ACs from builder.md goal 6