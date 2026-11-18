# Goal #10 — UI Regression Screenshot Baseline
**Status:** BLOCKED (sandbox egress) — tooling 100% complete, capture cannot execute from this seat.
**Date:** 2026-11-18 (auto-loop pass)

## What was verified this pass
1. `capture_baseline.py --selftest` → ALL OK: websockets v17.4 importable, msedge.exe found at `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`, panel matrix 8×2=16 screenshots (acceptance ≥8), unique filenames.
2. Portal reachability: `urllib.request.urlopen('http://127.0.0.1:8099')` → **WinError 10013** (socket connect forbidden).
3. Local HTTP server test: bound to :9333 OK, but `connect` to same port → **WinError 10013**. Confirms this sandbox blocks ALL outbound socket connects, not just specific ports.

## Exact unblock command (non-sandbox White seat)
```
python memory/designer/baseline/capture_baseline.py --url http://127.0.0.1:8099
```
Expected output: 16 PNGs in `memory/designer/baseline/shots/` + `MANIFEST.json` with SHA256 hashes.

## Why this seat cannot do it
The pale sandbox (uv-managed Python at `C:\Users\pale\...`) has a security policy that permits `socket.bind()` but denies `socket.connect()` on all destinations (WinError 10013). This is the same class as previously documented blockers for Mechanic #4, Verifier #2, and Designer #5/#7.

## No further action from this seat
Per run-rules R2/R3: date/probe-gated work parked. The script + manifest tooling + visual_diff.py are all committed and ready. One `python` invocation from a non-sandbox seat closes the goal.
