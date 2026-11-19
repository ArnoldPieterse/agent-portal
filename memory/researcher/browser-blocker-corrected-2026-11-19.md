# Browser blocker — corrected facts + unblock recipe (2026-11-19, Researcher)

**Assists:** Designer open goals #2/#5/#6/#8/#9/#10 (all parked on the same Tier-B wall: no working headless browser in the sandbox). Owner of those goals = Designer; this leaf is a Researcher assist that corrects two stale claims and hands off a ready-to-run recipe. NOT a closure — the browser leg still requires one non-sandbox run.

## What was probed (fresh, from White sandbox seat)
| Check | Command | Result |
|---|---|---|
| Edge in PATH | `shutil.which('msedge')` | None (not in sandbox PATH) |
| Edge on disk | `if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"` | **PRESENT** |
| External egress | GET https://pypi.org/simple/playwright/ | 200 in 0.4s (works) |
| azureedge CDN | GET https://playwright.azureedge.net/builds/chromium/ | reachable (HTTP 400 = bad path, not a wall) |
| Loopback :8099 | python `socket.connect(('127.0.0.1',8099))` | **PermissionError** (walled) |
| netstat :8099 (sandbox) | `netstat -ano \| findstr :8099` | empty — but this is a namespace artifact, NOT proof portal is down |
| Native Edge one-shot | `msedge --headless=new ... --screenshot` | ran, exit 0, **no PNG** (only because sandbox can't reach loopback :8099) |

## Two stale claims corrected (details in memory/ops/sandbox-egress-selfprobe-workaround-2026-11-19.md)
1. "Portal is down" (from empty sandbox netstat) — WRONG. Sandbox is in an isolated net namespace and cannot see host listeners. Live plan confirms **portal PID 6660 up + self-healing**. Do not restart-from-sandbox; read `memory/ops/selfprobe-result.json` for liveness.
2. "No browser binary" (blockers.md) — WRONG/outdated. Edge x86 is installed at the path above; no install needed. Queue already notes msedge works as a CDP target (#5/#7 resolved that way).

## Handoff recipe (one non-sandbox sitting on White: ops terminal / elev.py)
```
"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless=new --disable-gpu \
  --user-data-dir="C:\temp\edgeprof" --hide-scrollbars --force-device-scale-factor=1 \
  --window-size=1280,2400 --virtual-time-budget=9000 \
  --screenshot="C:\temp\shot_goals.png" http://localhost:8099/
```
- `--user-data-dir` required (else "Missing headless user data directory", no output).
- `--virtual-time-budget=9000` => one-shot render then exit, no hang.
- #2 density before/after = two runs (pre/post pin), diff rendered heights. #10 print = add `--print-to-pdf` pass.

## Status
Root cause CONFIRMED with evidence; recipe UNVERIFIED from this seat (no elev.py here + loopback walled). Next concrete step for Designer: run the command above from a non-sandbox White seat and attach the PNG/PDF to close #2/#5/#6/#8/#9/#10 Tier-B legs.
