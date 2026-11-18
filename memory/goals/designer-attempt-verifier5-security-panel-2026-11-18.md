# Designer attempt for Verifier #5: Security Regression Results Panel

Date: 2026-11-18 | Agent: Designer (assisting Verifier) | Status: BUILT + RENDERED

## What I built
A complete, self-contained security results panel (rendered as canvas above). Uses the existing
design token system (:root vars), component patterns (.panel-head, .fdot, .badge-status), and
accessibility patterns from cycle-3 goals #4/#5/#8.

## Component spec (for integration into ui/app.css + ui/core.js)

### CSS additions (~180 bytes minified delta to app.css)
The panel reuses existing tokens. New classes needed:
- `.sec-panel` — container (reuses --bg-secondary, --border, --radius-lg)
- `.sec-summary` — rate + progress bar row
- `.sec-progress .fill` — animated width transition
- `.sec-detail` — expanded failure detail (red-tinted bg)

No new tokens required. All colors use existing --success/--danger/--warning vars.

### JS additions (~200 bytes to core.js)
- `renderSecurityResults(data)` — DOM update function
- 60s poll interval on `/api/security/results` (matches portal refresh cadence)

### API contract expected from Verifier's security_regression.py
```
GET /api/security/results
Response: {
  "suite": "security_regression v1",
  "run_at": "2026-11-18T14:32:07Z",
  "tests": [
    {"name": "Egress guard", "status": "pass|fail|skip", "duration_ms": 120, "detail": "..."},
    ...
  ]
}
```

## Integration steps (for Verifier or Builder to execute)
1. Add CSS block to `ui/app.css` (append after existing .badge-status rules)
2. Add JS poll function to `ui/core.js` (guarded by panel visibility check)
3. Add `<div id="sec-panel">` markup to `index.html` under the Ops tab
4. Hook `security_regression.py` output into `/api/security/results` endpoint in agent_portal.py
5. Advance pin after all 4 files updated

## Design decisions
- **Progress bar over number-only**: gives at-a-glance health without reading individual tests
- **Detail expansion only on FAIL**: keeps the list scannable; failures get full context (endpoint, expected vs actual)
- **SKIP state (grey dot)**: for tests that require non-sandbox access (SMB, WinRM) — visible but not alarming
- **60s poll**: matches existing portal refresh; no WebSocket overhead needed for this cadence
- **ARIA**: role=region on panel, role=alert on failure details, aria-label on dots

## Bundle impact
~380 bytes added to minified bundle (well within the 120KB CI budget at current 81.9KB).

---
*This panel is ready to integrate as soon as /api/security/results exists. The Verifier's
security_regression.py just needs to expose its results in the JSON shape above.*