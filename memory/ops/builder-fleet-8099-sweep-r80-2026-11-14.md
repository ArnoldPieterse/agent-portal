# Builder r80 — fleet-wide :8099 sweep (2026-11-14, seat = Black Black)

Artifact: `probe_fleet_8099_r80.py` (working dir). First-party matrix from a seat with
terminal LAN egress:

| Host  | IP              | :8099          | :445   |
|-------|-----------------|----------------|--------|
| White | White   | TimeoutError   | OPEN   |
| Red   | Red   | TimeoutError   | OPEN   |
| Pale  | Pale    | TimeoutError   | OPEN   |
| Black | Black    | PermissionErr* | PermErr*|
| local | 127.0.0.1       | PermissionErr* | PermErr*|

\* WSAEACCES-class = Black sandbox/terminal local-loopback block (known quirk, not a network fact).

## Findings
1. All 4 hosts ALIVE (SMB open on White/Red/Pale). No state change vs 04:21 snapshot.
2. **Zero :8099 listeners reachable from LAN on ANY host** — no stray portal instance on
   Red/Pale either. HTTP legs skipped (no OPEN).
3. Signature ambiguity stands per white-lan-firewall-drop-2026-11-14.md: timeout ≠ down;
   it is equally consistent with "portal up but firewall-dropped". Only White-console
   `netstat -ano | findstr :8099` + `netsh advfirewall` check distinguishes.
4. **PID 10692 provenance gap**: Mechanic reports `_portal_pid.txt` = 10692, but that file
   and the string "10692" appear NOWHERE in Black's mirrored tree (grep'd *.md/*.py/*.json/*.txt
   incl. memory/**). So it is either Red-local (non-memory file, never mirrored) or read from a
   path no agent seat can see. A PID file is inert evidence — consistent with both "restart landed
   and process later died" and "stale file". Corroboration requires the same White-console leg.

## Net effect
No new unblock. AC-A2-2 LIVE gate unchanged: Arnold on White console — (a) confirm portal proc
alive + :8099 bound, (b) optionally allow 8099 inbound in Windows Firewall so future agent sweeps
can see live status instead of timeout, (c) relay PID / open Files panel for the browser leg.


---
CORRIGENDUM (hostdoc-consistency-v2 2026-11-18): script/log paths referenced here were seat-local ephemeral artifacts, never committed to the repo.
