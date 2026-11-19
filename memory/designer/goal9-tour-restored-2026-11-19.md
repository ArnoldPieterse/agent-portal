# Designer Goal #9 - Onboarding Tour Restored (2026-11-19)

## What was done this pass
1. **ui/tour.js** confirmed present and complete (4,591 bytes) - 4-step coach-mark tour: Fleet tab -> Goals panel -> Ops tab -> Uploads. Uses localStorage flag `portal.tour.v1`; dismissible + skippable; `window.runTour()` for manual re-trigger.

2. **ui/app.css** += 13 new `.tour-*` CSS rules (tokenized):
   - `.tour-scrim` fixed overlay z=9000, fade-in animation
   - `.tour-card` floating card z=9001, pop-in animation, max-width 300px
   - `.tour-step` / `.tour-title` / `.tour-desc` typography (fs-12/fs-18/fs-13, tokenized)
   - `.tour-bar` flex row; `.tour-skip` ghost button
   - `.tour-target` outline 2px var(--acc) + glow box-shadow
   - `body.tour-on` cursor:default
   Braces verified: 295/295 balanced.

3. **index.html** += `<script src="ui/tour.js"></script>` after notifications.js (L165). Pin advanced to sha12=eae59c3676ef; backup at memory/designer/index_html_CANONICAL_eae59c3676ef_2026-11-19x.html.

## Acceptance status
- Code complete: tour.js + CSS + script tag all in place
- Remaining: browser rendering acceptance test (first-visit shows 4 steps, skip sets flag, does not reappear) - shared blocker with #2/#5/#6/#10
