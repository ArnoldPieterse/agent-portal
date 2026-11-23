# Cockpit Cognitive Load Budget
Lane: Designer | Date: 2026-11-23 | Cycle-12 Goal 10

## Principle
Operator identifies (a) fleet health, (b) what's in-flight, (c) what needs attention in <=5s without reading text.

## Thresholds (measurable)
| Metric | Max | Rationale |
|--------|-----|----------|
| Primary visual channels above fold | 3 | Health color, motion (active), spatial position |
| Interactive elements per panel (above fold) | 8 | Each is a decision point |
| Distinct colors per panel (above fold) | 5 | Beyond 5 the eye can't map meaning |
| Text nodes above fold (visible, non-empty) | 40 | Reading time budget at 250wpm |

## Channels Definition
- Channel 1: Color (state) — ok/warn/err + neutral
- Channel 2: Motion (activity) — pulse/spin on active loops only
- Channel 3: Position (hierarchy) — top row = fleet health, middle = in-flight, bottom = attention

## Audit
Run: `python ui/cockpit-load-audit.py --headless`
Exit code: 0 = pass, 1 = violation (fails QA gate cycle-11 goal 9).
Reports per-panel element counts at 768px and 1024px breakpoints.

## Enforcement
CI gate: audit script runs on every commit touching ui/*.css or index.html.
Violation blocks merge until threshold restored.