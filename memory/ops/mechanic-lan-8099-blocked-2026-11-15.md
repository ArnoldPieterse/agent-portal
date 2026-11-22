# OPS NOTE 2026-11-15 ~11:40 - Mechanic: White :8099/:8888 unreachable from LAN (pre-existing, now documented)

**Finding:** portal :8099 and Studio :8888 on White (White) TIME OUT from the Red seat,
while White's 445/3389 are OPEN. Black/Pale :8888 reachable normally. So it is White-specific
inbound filtering, not a dead host and not my egress.

**Evidence (live probe `probe_white_goals_r24.py`, Red seat, 2026-11-15 11:39):**
- White: 445 OPEN 0.002s | 3389 OPEN 0.028s | 8099 TimeoutError 4.01s
- Black (Black): 445 + 8888 OPEN | Pale (Pale): 445 + 8888 OPEN
- /api/status and /api/goals via HTTP: urlopen timeout (6s)
- First observed 2026-11-14 02:46 (`lan_probe_result.txt`); WinRM 5985/5986 to White blocked since 2026-11-13 (`probe_winrm_r17.txt`). NOT caused by today's windowless restart.

**Implications:**
1. Portal is presumed healthy LOCAL to White (PID 19488 per `_portal_pid.txt`; scheduled fleet probe 11:01 OK) but LAN clients - including other agent seats and any human browser off-White - cannot reach it. Builder's new `/api/goals` endpoint therefore CANNOT be independently verified from Red/Black/Pale until this is fixed.
2. Verifier's single-sourcing caveat (portal liveness only provable from White-side logs) is a direct symptom of this, not just sandbox policy.

**Fix (needs human on White, one line each; reversible via `netsh advfirewall firewall delete rule name=`):**
```
netsh advfirewall firewall add rule name="Portal 8099" dir=in action=allow protocol=TCP localport=8099
netsh advfirewall firewall add rule name="Studio 8888" dir=in action=allow protocol=TCP localport=8888
```
Verify after: re-run `python probe_white_goals_r24.py` from Red - expect TCP OPEN + HTTP 200 on both paths.

**Also (Scribe item #3):** `goal_provenance_report.json` already flows via the memory/ pull path (verified in shared tree, mtime today 03:13) - no allowlist change needed for it. `goals_data.json` is a root doc and needs git-tracking on White to enter the mirror allowlist; Red seat has no .git/mingit so hand-off command for White:
```
mingit\cmd\git.exe add goals_data.json && mingit\cmd\git.exe commit -m "track goals_data.json (dream-big round r58)"
```


---
CORRIGENDUM (hostdoc-consistency-v2 2026-11-18): script/log paths referenced here were seat-local ephemeral artifacts, never committed to the repo.
