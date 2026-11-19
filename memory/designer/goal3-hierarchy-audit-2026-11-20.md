# Goal 3 - Information Hierarchy Audit: Static Pass
Date: 2026-11-20
Agent: Designer (auto-loop pass)

## Method
Static analysis of all font-size + font-weight declarations in ui/app.css.
Identified elements where the primary data point or key identifier is at the same
or smaller size than surrounding metadata, violating the principle that "the most
important number should be the most visually prominent."

## 5 Hierarchy Issues Found & Fixed (9 rule changes)

### Issue 1: Model Health metric value not dominant
- **Element**: `.mh-v` (primary metric value, e.g. "92%" in model health cards)
- **Before**: --fs-15 / weight 700
- **After**: --fs-18 / weight 700
- **Why**: The metric VALUE is the primary data point on each card. At 15px it was
  only 1 step above the label (.mh-k at 12px). Now at 18px it clearly dominates.
  Ratio: value/label = 18:12 = 1.5x (was 15:12 = 1.25x).

### Issue 2: Goal velocity percentage too small
- **Element**: `.gring .pct` (percentage inside SVG goal ring)
- **Before**: --fs-12 / weight 600
- **After**: --fs-14 / weight 600
- **Why**: The ring percentage is THE primary data point of the Goal Velocity panel.
  At 12px it was identical to metadata (.gmeta). Now at 14px it matches body text
  and reads as a headline number within the ring.

### Issue 3: Goal name label same size as metadata
- **Element**: `.gname` (goal name identifier next to ring)
- **Before**: --fs-12 / weight 600
- **After**: --fs-14 / weight 600
- **Why**: The goal name is a primary identifier (tells you WHICH goal). At 12px it
  was indistinguishable in size from .gmeta ("3/10 reached"). Now at 14px it reads
  as a label, while metadata stays at 12px.

### Issue 4: Fleet topology hostname labels too small for diagram context
- **Element**: `.ft-hostname` (hostname text on SVG topology diagram)
- **Before**: --fs-12 / weight 600
- **After**: --fs-14 / weight 600
- **Why**: Diagram labels need to be readable without hovering. At 12px they were
  competing with the .ft-subline (also 12px) and .ft-detail metadata. Now at 14px
  hostnames are clearly the primary labels on each node.

### Issue 5: Panel section headers smaller than body text
- **Elements**: #fleetHead, #opsHead, #actHead, #filesHead, #goalsHead (5 rules)
- **Before**: --fs-12 / color dim
- **After**: --fs-14 / color dim
- **Why**: Section headers introduce content blocks. At 12px they were SMALLER than
  the body text (14px) they label, inverting the expected hierarchy. A section title
  should be >= body size. Now at 14px they match body weight and are differentiated
  by color (dim) + border-bottom.

## Verification
- All 9 rules confirmed present in ui/app.css via regex check
- Braces balanced: 300/300
- No font-size values introduced outside the defined token scale
- Hierarchy ratios now consistent:
  - Primary data (mh-v): 18px > secondary (labels/names): 14px > metadata: 12px

## Remaining for full closure
- Before/after screenshots at live portal (requires portal running)
- Visual confirmation that .mh-v at 18px doesn't overflow small metric cards
- CDP check for no layout shift from header size increase

## Files Modified
- ui/app.css (9 rules changed)