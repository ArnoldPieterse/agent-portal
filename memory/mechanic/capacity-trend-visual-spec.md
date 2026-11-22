# Capacity & Trend Strip — Visual Spec (Designer assist, 2026-11-21)

Owner: Mechanic (data pipeline already built). This spec defines how to present it in the portal fleet tab. No host access required to implement — pure frontend over existing data.

## Goal
Surface per-host trend + breach prediction so a human sees "host X will be >90% in ~N days" at a glance, not after opening a report file.

## Data sources (already exist)
- `memory/mechanic/capacity_data.jsonl` — points: `{ts, host, metric, value}` where metric ∈ {`disk_pct`, `mem_pct`}.
- `/api/fleet/status` — snapshot: `{overall, hosts:{name:{reachable, latency_ms, disk_pct, mem_pct}}}`.
- Suggested new read endpoint (Mechanic): `GET /api/capacity/trend?host=&metric=&days=7` → `{points:[{ts,value}], prediction:{pct_now, growth_per_day, days_to_90, breach_ts}, n_points}`. Reuse `capacity_trend.py` logic.

## Placement
New horizontal strip directly under the existing per-host status strip in `ui/fleet_status.js` (which already renders `disk_pct`/`mem_pct`). One compact row per host: `[dot] white · disk 44% ▁▂▃ 7d · ⚠ full ~18d`. Max height 2 lines; no new scroll.

## Threshold bands (reuse existing tokens)
- <70% → `var(--ok)` fill
- 70–90% → `var(--warn)` fill
- ≥90% → `var(--err)` fill + breach chip
These match the dot thresholds already in `fleet_status.js` (`disk>=85`/`mem>=90` = amber), so extend: bump to red at 90 and add a dashed 90% reference line on the sparkline.

## Sparkline
- Inline SVG, width ~72px height 16px, `vector-effect:non-scaling-stroke`, stroke `currentColor` (inherits band color). No external deps — consistent with the icon-set rule (currentColor-only).
- Draw a dashed horizontal line at the 90% position.
- Hover tooltip (reuse `UI.tooltip`) shows `metric value @ ts` per point; on insufficient history show "—" not an empty chart.

## States (reuse existing components — do NOT invent new ones)
- No points yet → `UI.emptyState({icon:"gauge", title:"No trend data", msg:"Capacity probe hasn't recorded 3+ samples for this host."})` scoped to that host row, not the whole panel.
- <3 points (current reality per `capacity-report-2026-11-20.md`: "insufficient history") → render dots + current % only, suppress sparkline and prediction; show muted `"need 3+ samples"` label. This is the LIVE state today — must look intentional, not broken.
- Endpoint error / host unreachable → `UI.errorState({message:"Capacity data unavailable", detail})`, matches existing diskTile error handling in `core.js:440`.

## Breach chip (the one new element)
- Only when `days_to_90 >= 0` and `n_points >= 3`. Format: `⚠ <metric> full ~Nd` (e.g. `⚠ disk full ~18d`).
- Color by urgency: >7d → `var(--warn)`; ≤7d → `var(--err)` + subtle pulse (`@keyframes`, respect `prefers-reduced-motion` per animations.css).
- 48h-before-breach alert (Mechanic's goal) should light this chip, not a separate toast.

## Accessibility
- Each host row: `<li>` with `aria-label="white: disk 44 percent, predicted full in about 18 days"` (screen-reader text spells the prediction; sparkline is `role=img aria-hidden` decorative).
- Keep heading order intact (this strip is content under the fleet h2 — no new headings).

## Acceptance (Mechanic closes against this)
1. At 768px the strip wraps without horizontal scroll on the panel.
2. Insufficient-history hosts render the muted state, not an error.
3. A test point set pushed to 92% shows red band + breach chip; sparkline 90% line visible.
4. `prefers-reduced-motion` disables the chip pulse.
5. All colors via var() — 0 hardcoded hex in the new markup.
