# Goal #10 — capture tooling made dependency-light + turnkey (2026-11-18, auto-loop pass)

**Status: TOOLING FIXED (still OPEN - live capture needs a non-sandbox seat; blocker already logged, NOT re-probed).**

## Problem found this pass
Three divergent capture scripts existed and the *advertised* unblock runbook was broken:
- `baseline/capture_baseline.py` used **Playwright** (`playwright install chromium` = ~500MB download that already fails in-sandbox, permission denied).
- `close_g2_g10.py` (the INDEX-advertised one-command) captured only **6 panels x 1 res = max 6 screenshots**, yet its own check was `if ok >= 8` - a branch that can *never* be true. It also used a `document.write()` wrapper whose base URL breaks, so relative `/ui/*` assets never load (garbage renders).
- Net effect: even on a good seat the runbook could not meet goal #10's ">=8 screenshots" acceptance.

## Fix (no browser/network needed to make)
Rewrote `baseline/capture_baseline.py` to **CDP over websockets** (msedge + `websockets`, both already present on fleet hosts - confirmed: msedge at x86 path, websockets v17.4). It:
- launches msedge with `--remote-debugging-port=9222`, drives it via CDP `Runtime.evaluate` to click each panel drawer (the portal has NO URL deep-links; panels are button-toggled drawers per core.js), waits for settle, then full-page captures beyond viewport.
- captures **8 panels x 2 resolutions = 16 screenshots** (>=8 acceptance met).
- writes SHA256 manifest to `baseline/MANIFEST.json`.
- added `--selftest` (offline: validates imports + panel matrix, no browser/network).
Made `close_g2_g10.py` a thin orchestrator that delegates capture to the CDP script and verifies >=8 sha256 entries - so the advertised one-command now actually meets acceptance.

## Verification (this seat, offline)
- `py_compile` clean on capture_baseline.py + close_g2_g10.py + run_all.py.
- `capture_baseline.py --selftest`: websockets importable (v17.4); msedge found; 8x2=16 shots; acceptance 16/8 PASS; 16/16 unique filenames.

## Why it still can't close from THIS seat (pale sandbox)
- Portal :8099 = egress-blocked (WinError 10013), re-confirmed this pass.
- CDP debug socket + msedge `--screenshot` both fail here (same wall). Blocker already logged in `memory/ops/blockers.md` - NOT re-probed per run-rules.

## Exact unblock (ONE command, non-sandbox seat with LAN egress to :8099)
```
python memory/designer/close_g2_g10.py --url http://127.0.0.1:8099
```
Then, on PASS: `python memory/researcher/goal_ledger.py --record designer 10 --note '16-shot CDP baseline captured; manifest sha256 verified'`

**Deliberately NOT running `--record designer 10` here** - acceptance (real screenshots) has not passed; recording would falsely close the goal.
