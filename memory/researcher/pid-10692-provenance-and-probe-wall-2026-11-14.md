# Researcher — PID 10692 provenance + probe-wall characterization (2026-11-14 ~13:2x)

## Finding 1: PID 10692 has NO on-disk provenance in any shared/mirrored tree (RESOLVES Builder vs Mechanic/Scribe contradiction)
- First-party source check of `memory/builder/arnold-restart-r19.ps1` (the r19 script that produced PID 23704): it writes the PID file via **relative path** — `"$new" | Set-Content _portal_pid.txt` — i.e. into Arnold's console CWD on White, NOT into Z:\ shared folder.
- Confirmed `_portal_pid.txt` ABSENT from: my tree (root + parent), Builder's Black tree-wide grep, and `Z:\` dir listing taken directly on White via terminal.
- Only on-disk occurrence of "10692" in the shared tree = Scribe's own hot-note in MEMORY.md (mtime 12:15). Conclusion: Mechanic/Scribe reads came from unmirrored local seat copies; **no mirrored artifact corroborates PID 10692**.

## Finding 2: r19 script semantics change the operational read
- Script has hard fail-fast gates: asserts old listener == 27268 BEFORE kill; AFTER `schtasks /run /tn PortalRun` it REQUIRES a new :8099 listener to appear, else `Write-Error "no listener after restart - check portal_run_err.log"` and exits WITHOUT writing the PID file.
- So "fresh PID in file + port unconfirmed" ⇒ either (a) process died AFTER script completed, or (b) 10692 is spurious. Actionable for Arnold: if the restart ran, check White console output + `portal_run_err.log` (in portal CWD).

## Finding 3: NO agent-executable path to an authoritative :8099 verdict — fully characterized wall
- My terminal seat = **White itself** ([LAN-IP] via ipconfig). From the portal host, every local introspection path is blocked:
  - netstat → "Access is denied"; tasklist → credential error (SMB-cwd artifact); powershell → safety-blocked; schtasks → "Class not registered"; python sockets → sandbox allowlist blocks even loopback/127.0.0.1.
- Other seats: Verifier 10013 = WSAEACCES (LOCAL firewall block, not proof of portal down); Builder timeouts on 8099 AND known-open 8888 = whole-path/firewall ambiguity; Scribe's seat Red offline (NIC media-disconnected after 11:41);
- ⇒ Only a human interactive console on White (or a browser on White) can settle AC-A2-2 LIVE. No agent lane is blocked on any AGENT action.

## My standing lane items (unchanged)
- `probe_fleet_1114b_result.json` still ABSENT tree-wide (re-grepped this round) — awaits 5-min White sync or Arnold's pass.
- dcabots re-prompt support / atlas-q8 pre-check: rides with the same human gate; unreachable from agent seats.
