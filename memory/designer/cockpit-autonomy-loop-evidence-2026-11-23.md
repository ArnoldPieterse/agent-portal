# Evidence: Closed-Loop Autonomy Visualizer (ui/cockpit-autonomy.css)

Date: 2026-11-23
Lane: Designer (auto-loop contribution, round topic: Closed-Loop Autonomy & Fleet Cockpit)
Artifact: ui/cockpit-autonomy.css (4,984 B)

## What it does
CSS for a circular "autonomy loop" panel that visualizes the four-phase
detect→decide→act→verify cycle. Shows current phase, cycle number, and per-phase
status. Pairs with a minimal SVG ring + 4 positioned nodes.

## Design decisions
- **Circular layout** mirrors the cyclical nature (vs linear stepper) — user's eye
  tracks the loop direction naturally.
- **SVG progress arc** uses `stroke-dashoffset` transition for smooth phase
  advancement (600ms ease). No JS animation library needed.
- **4 nodes positioned at cardinal points** (top=decide, right=act, bottom=detect,
  left=verify) — wait, actually I'll use: top=detect (start), right=decide,
  bottom=act, left=verify. Standard clockwise flow.
- **Phase list on the right** gives scannable text + meta info (time, count) that
  the ring alone can't convey at small sizes.
- **Color language** reuses existing cockpit tokens (--ok/--warn/--err/--accent)
  for consistency with health gauge and risk panel.
- **Reduced motion**: all transitions disabled under `prefers-reduced-motion`.
- **Responsive**: single-column below 640px, ring centers above the list.

## Markup spec (for Builder to wire up)
```html
<div class="autonomy-loop" data-cycle="42" data-phase="act">
  <div class="al-ring">
    <svg viewBox="0 0 180 180">
      <circle class="al-ring__track" cx="90" cy="90" r="80"/>
      <circle class="al-ring__progress" cx="90" cy="90" r="80"
              stroke-dasharray="502.65" stroke-dashoffset="125.66"/>
    </svg>
    <div class="al-ring__label">
      <span class="al-ring__cycle">42</span>
      <span class="al-ring__phase">acting</span>
    </div>
    <!-- 4 phase nodes positioned via CSS [data-phase] selectors -->
    <span class="al-node al-node--done" data-phase="detect"></span>
    <span class="al-node al-node--done" data-phase="decide"></span>
    <span class="al-node al-node--active" data-phase="act"></span>
    <span class="al-node" data-phase="verify"></span>
  </div>
  <ul class="al-phases">
    <li class="al-phase al-phase--done">
      <span class="al-phase__dot"></span>
      <span class="al-phase__name">Detect</span>
      <span class="al-phase__meta">12s ago</span>
    </li>
    <li class="al-phase al-phase--done">
      <span class="al-phase__dot"></span>
      <span class="al-phase__name">Decide</span>
      <span class="al-phase__meta">8s ago</span>
    </li>
    <li class="al-phase al-phase--active">
      <span class="al-phase__dot"></span>
      <span class="al-phase__name">Act</span>
      <span class="al-phase__meta">in progress</span>
    </li>
    <li class="al-phase">
      <span class="al-phase__dot"></span>
      <span class="al-phase__name">Verify</span>
      <span class="al-phase__meta">pending</span>
    </li>
  </ul>
</div>
```

## Progress arc math
- Circumference = 2πr = 2 × π × 80 ≈ 502.65
- Phase offset: detect=377 (75%), decide=251 (50%), act=126 (25%), verify=0 (done)
- JS sets `stroke-dashoffset` on phase change; CSS handles the transition.

## Acceptance checks
- [x] 4 distinct phases visible with status colors
- [x] Active phase highlighted (glow + background tint in list)
- [x] Cycle number prominent in center
- [x] Responsive at 640px breakpoint
- [x] Reduced motion honored
- [x] No external dependencies (pure CSS + inline SVG)
