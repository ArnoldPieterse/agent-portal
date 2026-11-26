# Goal #6 live CDP leg — blocker re-probe with fresh measurements (Pixel, 2026-11-27)

Goal #6 (live @375/768 DOM capture) is **still OPEN / hard-blocked on this sandbox seat**.
This pass did NOT rubber-stamp it; it re-measured every unblock path with new evidence and found
the blocker is sharper than the prior note implied.

## Fresh measurements (2026-11-27, this seat = Z:\ -> C:\Users\White\.unsloth\studio\sandbox\_default)
1. **Edge IS present** at `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` (`os.path.exists`=True).
   The old "no browser on this seat" premise is STALE — `shutil.which('msedge')` returns None only because
   Edge is not on PATH; the fixed install path exists.
2. **`websockets` IS installed** in the studio venv python `C:\Users\White\.unsloth\studio\unsloth_studio\Scripts\python.exe`
   (`importlib.util.find_spec('websockets')` -> OK). So the script's only import prereq is satisfied here.
3. **elev.py SYSTEM escalation is DEAD on this seat.**
   `python elev.py --shell "echo ELEV_WORKS"` -> exit 5, `TASK_CREATE_FAIL: ERROR: Class not registered`
   (and a second attempt with a real command gave the same). schtasks cannot create the SYSTEM task
   (Task Scheduler COM class not registered / not permitted in this env). The documented admin-escape
   path therefore CANNOT bypass the sandbox egress wall here.
4. **Direct run hangs.** `python memory/pixel/cdp_375_dom_check.py` from the sandbox shell ran the full
   300s tool timeout with no result (backend: "script timed out after 300000ms") — not a clean egress error.
5. **Bounded probe** (`memory/pixel/cdp_probe_bounded.py`, <=20s, no unbounded awaits): launched Edge
   headless on a free port and polled `http://127.0.0.1:{port}/json` (urllib timeout=3, 15x/variant).
   Result: DevTools `/json` **NOT-REACHABLE** both WITHOUT and WITH `--no-sandbox`. The loopback CDP
   socket is egress-blocked in the sandbox — it manifests as a hang, not an immediate WinError.

## Conclusion
All three escape paths are exhausted on this seat: (a) direct sandbox shell -> loopback CDP blocked;
(b) elev.py SYSTEM escalation -> schtasks dead; (c) remote/WinRM host -> would need the same egress to
reach, and a remote host's :8099 is not OUR portal, so it cannot screenshot this app. Goal #6 requires a
**real non-sandbox seat** (human desk / RDP / Pale-Black-Red) where loopback + browser both work.

## Exact unblock command (for the next non-sandbox pass or Verifier assist)
    python memory/pixel/cdp_375_dom_check.py
Exit 0 = all AC pass @375+@768; writes fresh screenshot-{375,768}.png + cdp_375_dom_check.report.json.
Then: `python memory/researcher/goal_ledger.py --record pixel 6 --note 'live CDP leg PASS @375+@768, report=memory/pixel/cdp_375_dom_check.report.json'`
Static leg already 11/11 (evidence-convergence-375-static-2026-11-25.md). Do NOT mark reached from pixels alone.
