# Mechanic r20 (2026-11-14 ~02:5x, Red seat) - seat change + fleet probe + AC-A2-2 live-leg handoff

## 1. SEAT CHANGE: White -> Red (durable until next rebind)
- This round my tool sandbox runs on **Red** (hostname `Red`, IPv4 Red, python under C:\Users\Red; cwd = shared _default sandbox). Previous rounds (01:1x-01:45 rename work) ran from a **White**-seated sandbox - that is why probe_white_1114.py / recover_all.py / white_load_q8.py target 127.0.0.1.
- Consequence: any 127.0.0.1-targeted script run FROM MY SEAT now addresses **RED's** Studio/portal, not White's. Loopback in this sandbox is blocked anyway (WinError 10013 on 127.0.0.1:8888/:8099), so they fail fast - but do NOT "fix" that by editing targets without re-checking which seat you are on. Check `hostname` first.
- Outbound LAN from my seat works (Black/Pale :8888 reachable); White :8888/:8099 remain firewalled from Red (re-verified 02:46, same as 11-13 19:39 - not a regression). SMB to White C$ = denied from sandbox context (no creds; mirror runs with its own).

## 2. Fleet probe 02:46 (lan_probe.py, Red seat)
- PASS tcp 179:445 + 179:3389 (SMB/RDP up); FAIL 179:8888/8099 (firewalled, known).
- PASS Black .99:8888 HTTP 200; PASS Pale .39:8888 HTTP 200. Red self :8888 not probeable from sandbox (loopback block) - no regression signal either way.
- Mirror fresh: TODO.md on my seat = White state through 01:46 RESOLVED tick; Scribe queue-4 leaf + Researcher farm-relpath diagnosis both landed via new-file propagation (transport healthy).

## 3. AC-A2-2 LIVE LEG - handoff (owner still Mechanic, executor must be White-side)
- Verifier sheet (ac-a2-closure-r19.md): sole open gate = one pass on PID 23704: /api/uploads N=1 row + raw fetch 200 + exactly 212 B + console clean. I cannot reach 179:8099 from Red (documented dead end, re-verified today).
- One-shot staged in shared folder: **ac_a2_live_leg_r20.py** (py_compile OK; two read-only GETs; writes ac_a2_live_leg_r20_result.json). Run ON WHITE: `python ac_a2_live_leg_r20.py`. Expected verdict PASS = [1] N=1 ('uploads/_canary_remote.txt', 212) + [2] 200/212 B (md5 recorded for Verifier's full-pin compare).
- Console-clean leg (no JS errors, no /api/uploads background timer) = browser/devtools, Arnold or a White-seated agent; static side already CLOSED by Verifier.
- Cross-seat canary byte-check from seats is IMPOSSIBLE until P1 uploads-mirror ships: uploads/ is not in memory_mirror.py SYNC set (my seat sees only stale AgentPortal_V1/ dir from 11-12). Verifier's Black reading (N=1, 212 B, pin prefix 512d0dc8) stands as the inventory evidence of record.

## Runbook one-liners
- What broke: nothing new this round - seat rebind White->Red made my 127.0.0.1 probes hit the wrong host (10013/timeout, no side effects; all probes read-only).
- What fixed it: `hostname` check before any local-port probe; White-targeted work now goes through staged one-shots run from a White seat (ac_a2_live_leg_r20.py) or Arnold's console.
