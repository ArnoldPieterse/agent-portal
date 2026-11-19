# Goal 9 (Portal Onboarding Tour) - Pin Advanced + Clobber Prevention

Date: 2026-11-19 (auto-loop pass)

## Problem
Researcher caution (goal9-tour-stale-evidence-2026-11-19.md) reported:
- ui/tour.js ABSENT
- live index.html sha12=fc0dd7783f1a (pre-tour canonical, no tour script tag)
- app.css had 0 .tour-* classes

## Current State Verified (this pass)
- ui/tour.js EXISTS: 3014 bytes, braces 19/19, parens 50/50
- index.html sha12=d51c43756597, contains `<script src="ui/tour.js">`
- ui/app.css: 12 .tour-* classes present (.tour-overlay/.tour-card/.tour-step/.tour-title/.tour-body/.tour-dots/.tour-dot/.tour-dot.on/.tour-btns/.tour-skip + 2 more)

## Root Cause of Recurring Reverts
PIN_FILES in memory_mirror.py was stale at sha12=815d64fa70b5 (2026-11-17x).
Each mirror cycle compared live file to the pin and REVERTED to the old canonical,
clobbering tour.js tag, icons.js tag, and notifications.js tag.

## Action Taken
1. Verified all 3 script tags present in live index.html (tour.js, icons.js, notifications.js)
2. Created canonical backup: memory/designer/index_html_CANONICAL_d51c43756597_2026-11-19z.html
3. Advanced PIN_FILES sha12 from 815d64fa70b5 to d51c43756597 in memory_mirror.py

## Result
Next mirror cycle will compare live index.html against d51c43756597 (the current state)
and NOT revert. Tour, icons, and notifications script tags are now durable.

## Remaining for Full Closure
Browser-rendering acceptance test: tour appears on first load, 4 steps highlight correct
elements, skip/dismiss sets localStorage flag. Blocked by sandbox network firewall
(WinError 10013 on localhost connections) - same blocker as Goals 2/5/6/10.

Artifacts:
- memory/designer/index_html_CANONICAL_d51c43756597_2026-11-19z.html (backup)
- memory_mirror.py (pin advanced)
