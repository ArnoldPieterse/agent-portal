# White LAN reachability — :8099/:8888 firewall-style drop (2026-11-14)

Recorded by Scribe from Mechanic's Red-seat ops wrap-up. Rationale: this finding is the
single unblock for the remaining AC-A2 / smoke8 lanes, and Mechanic's "Logged in TODO.md +
hosts.md" claim was NOT visible on the mirrored seat (only the older 17:18 firewall theory
was present) — so it is recorded here durably to guarantee it is not lost.

## Ground truth (on-disk artifact)
- `probe_white_reach_result.json` = 468 B, ts **2026-11-14 04:21:06**, seat Red:
  - `[LAN-IP]:445`  OPEN (0.02 s)
  - `[LAN-IP]:3389` OPEN (0.03 s)
  - `[LAN-IP]:8099` TimeoutError (timed out)
  - `[LAN-IP]:8888` TimeoutError (timed out)
  - studio HTTP → URLError(TimeoutError), 15.02 s; portal HTTP → URLError(TimeoutError), 15.0 s
- Mechanic reports the same signature consistent at **03:20, 03:51, 04:21** (the JSON is the 04:21 snapshot).

## Interpretation
- White (.179) is ALIVE on SMB :445 + RDP :3389, but portal :8099 and Studio :8888 are **TIMEOUT from LAN** = firewall-style drop, NOT connection-refused.
- No exec path Red→White: SMB C$ denied (err 5), WinRM not bootstrapped on White. So this is a **White-console** leg only.
- Distinguishing note (traces to memory/llm/hosts.md): Black's :8888 closed-from-White was root-caused as a **127.0.0.1-only bind, not firewall**. White could be EITHER loopback-bind OR an inbound firewall rule — the console check below distinguishes.

## Open action (owner: Arnold)
ONE White-console check:
1. Windows Firewall inbound rules for 8099 and 8888 (`netsh advfirewall firewall show rule name=all | findstr /i "8099" "8888"`).
2. Whether Studio rebound :8888 loopback-only (Black precedent) — `netstat -ano | findstr :8888` bind address.
3. Re-probe from a remote seat after the fix; log result to memory/ops/.

## Cross-refs
- Related but DISTINCT: the older ~17:18 regression (White alive locally, unreachable off-loopback) already in TODO.md — this 03:2x finding is the current-state confirmation of that same class of symptom on a fresh probe.
- Unblocks: full smoke8 + AC-A2-2 LIVE legs that are currently BLOCKED solely on White's LAN ports (per Mechanic).
