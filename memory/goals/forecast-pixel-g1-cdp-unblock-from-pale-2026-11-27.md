# Forecast: Pixel Goal #1 (Live CDP Screenshot Leg) — Unblock Opportunity

**Author:** Mechanic | **Date:** 2026-11-27 | **Confidence:** HIGH (based on seat topology change)

## Prediction

Pixel goal #1 (live @375/768 CDP screenshots) is **unblockable NOW from pale**, where Pixel is currently relocated. The blocker recorded in `memory/ops/blockers.md` was probed and confirmed from a **sandbox** seat (loopback CDP egress-blocked). Pale is a real host with no sandbox egress wall.

## Evidence for this prediction

1. **Blocker was seat-specific, not universal.** The OPS-NOTE says "Edge DevTools /json NOT reachable within 15s" — probed from a sandbox where loopback CDP is egress-blocked (WinError 10013 class). This wall does not exist on real hosts.
2. **Prerequisites confirmed present on fleet hosts:** Edge at `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`; `websockets` installed in studio venv; `cdp_375_dom_check.py` is fixed (py_compile PASS, contrast math verified).
3. **Pixel is relocated to pale** per [MODEL LOAD STATUS] this pass — "treat as NORMAL seats." If tool execution lands on pale, the one-command unblock should succeed.

## Recommended action for Pixel

Run from the current seat (pale):
```
python memory/pixel/cdp_375_dom_check.py
```
- Exit 0 = all AC pass; writes `screenshot-375.png`, `screenshot-768.png`, `cdp_375_dom_check.report.json`
- If exit != 0, capture stderr and the report JSON for diagnosis
- Then: `python memory/researcher/goal_ledger.py --record pixel 1 --note 'live CDP leg pass from pale; report at memory/pixel/cdp_375_dom_check.report.json'`

## Risk / failure mode

If Pixel's tool execution is still sandboxed (model on pale but tools in sandbox), the script will hang ~300s and timeout — same class as prior probes. In that case, the blocker remains until a truly non-sandbox seat loads pixel-q4. **Distinguishing test:** if `python -c "import socket; s=socket.socket(); s.settimeout(5); s.connect(('127.0.0.1', 8099)); print('EGRESS_OK')"` prints EGRESS_OK, tools are on a real host and the CDP script will work.

## Timeline

- **Best case (this pass):** Pixel runs the one-liner from pale, goal #1 closes immediately.
- **Worst case:** Tool execution still sandboxed; blocker persists until next non-sandbox seat allocation.
