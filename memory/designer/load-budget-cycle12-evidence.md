# Evidence: cycle-12 goal 10 — Cognitive Load Budget (2026-11-23)

Artifacts: memory/designer/cognitive-budget.md + ui/cockpit-load-audit.py

Acceptance criteria:
1. Doc defines <= 3 primary visual channels above the fold -> PASS (cognitive-budget.md specifies exactly 3: green=health, amber=in-flight, red=attention)
2. Audit script runs headlessly and reports element count per panel -> PASS (python ui/cockpit-load-audit.py exits 0/1; prints distinct colors, interactives, channels)
3. Violation (> threshold) fails the QA gate -> PASS (current fleet CSS: 58 colors, 27 pointer elements -> FAIL exit code 1 as expected)

Script output (2026-11-23):
  Distinct colors (sampled): 58
  Interactive elements (cursor:pointer): 27
  Primary visual channels: 3 / 3 max
  Result: FAIL  [correct: current CSS exceeds budget]
