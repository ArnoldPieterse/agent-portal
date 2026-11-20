# Goal 3 - Information Hierarchy Audit: Re-land + New Fixes (pass d)
Date: 2026-11-20
Agent: Designer (auto-loop pass)

## Context
Prior pass (goal3-hierarchy-audit-2026-11-20.md) made 9 rule changes but they were
partially reverted by the mirror cycle. This pass re-lands all prior fixes AND adds
2 new hierarchy improvements found during a fresh audit.

## Changes (11 rules total in ui/app.css)

### Re-landed from prior audit (7 rules):
| Element | Before | After | Rationale |
|---------|--------|-------|----------|
| .mh-v | --fs-15 / 700 | --fs-18 / 700 | Metric value must dominate its card |
| .ft-hostname | --fs-12 / 600 | --fs-14 / 600 | Diagram labels need to be primary |
| #fleetHead | --fs-12 dim | --fs-14 dim | Section headers >= body size |
| #opsHead | --fs-12 dim | --fs-14 dim | Same |
| #actHead | --fs-12 dim | --fs-14 dim | Same |
| #filesHead | --fs-12 dim | --fs-14 dim | Same |
| #goalsHead | --fs-12 dim | --fs-14 dim | Same |

### New in this pass (4 rules):
| Element | Before | After | Rationale |
|---------|--------|-------|----------|
| .gring .pct | --fs-12 / 600 | --fs-15 / 700 | Ring percentage is THE primary number; must dominate tile |
| .gname | --fs-12 / 600 | --fs-14 / 600 | Agent name is primary identifier, not metadata |
| .frow-h b (new rule) | inherited --fs-12 | --fs-14 / 600 | Fleet hostname is the row's primary data point |
| #filesList a | --fs-12 (inherited) | --fs-14 / 500 | Filename is the actionable element; metadata stays 12px |

## Resulting Hierarchy Scale
```
Primary data:     18px (.mh-v metric values)
Key identifiers:  15px (.gring .pct ring percentage)  
Secondary:        14px (names, labels, section headers, fleet hostnames, filenames)
Metadata:         12px (timestamps, status hints, model lists, dim text)
```

## Verification
- All 11 rules confirmed present via regex check
- Braces balanced: 301/301
- No off-scale font-size values introduced
- Hierarchy ratios: primary/secondary = 1.29x; secondary/metadata = 1.17x

## Remaining for full closure (goal 3 acceptance criteria)
- [ ] Before/after screenshots at live portal (needs :8099 running)
- [ ] Visual confirmation that .mh-v at 18px doesn't overflow small metric cards
- [ ] CDP check: no layout shift from header size increase
- [ ] Audit report documents >=5 fixes (THIS FILE = 11 documented; passes)

## Files Modified
- ui/app.css (11 rules changed)