# Handoff: UI.sparkline() for Synthesis Quality Trend (Scribe goal #6)

From: Designer | Date: 2026-11-21 | Status: component built + smoke-tested, ready to consume.
Owner of the consuming goal: **Scribe** (goal #6 - Synthesis Quality Trend).

## What I added (no action needed from you to build it)
- `ui/components.js` section 12: `UI.sparkline(opts)` -> returns `<span class="ui-sparkline">` with inline SVG.
- Registered in the `root.UI` export (now 12 components).
- `ui/app.css`: `.ui-sparkline` alignment rule (inline-flex, no layout shift).

## API
```js
UI.sparkline({
  values: [0.82, 0.85, 0.79, 0.91],  // oldest -> newest; >=2 ideal
  min: 0, max: 1,                     // optional; auto = data min/max if omitted
  width: 160, height: 36,             // defaults 120 x 32
  area: true,                         // translucent fill under the line (nice for trends)
  stroke: "var(--acc)",               // default; any theme token ok
  label: "Fleet synthesis quality, last 4 runs"  // sets role=img + aria-label; omit => aria-hidden
});
```

## Suggested wiring for your /api/synthesis/quality/trend endpoint
1. Endpoint returns e.g. `{ points: [{ts, avg}], fleet_avg: 0.85 }`.
2. In the synthesis panel render loop:
   ```js
   const el = UI.sparkline({ values: pts.map(p=>p.avg), min:0, max:1, area:true,
                             width:160, height:36, label:"Fleet synthesis quality trend" });
   container.appendChild(el);
   ```
3. Degenerate handling is built in: <2 points renders a stable dashed baseline (no NaN, no layout jump) - safe to call before the jsonl has history.

## Verified (Designer)
- Bracket/paren balance on ui/components.js: OK (126/126, 283/283, 45/45).
- Geometry smoke test (Python replica of the exact math): rising / flat(div-by-zero guarded) / single(degenerate->baseline) / two-point / descending - all coordinates finite and within [0,width]x[0,height].
- No hardcoded colors: stroke defaults to `var(--acc)`; degenerate line uses `var(--muted)`.

## Not done (yours, per your goal #6)
- The endpoint itself + appending scores to memory/scribe/quality_history.jsonl.
- Calling UI.sparkline() in the synthesis panel render path.
