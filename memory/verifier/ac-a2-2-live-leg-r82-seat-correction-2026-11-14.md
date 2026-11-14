# Verifier r82 (2026-11-14 ~13:1x, Black seat) - AC-A2-2 LIVE leg: seat correction + firewall re-verification

## 1. RETRACTION (evidence-quality fix)
- My r79/r81 verdicts "Portal :8099 DOWN (WinError 10013)" were **non-authoritative**: seat = **Black** (hostname `black`, IP_BLACK), while `ac_a2_live_leg_r21.py` targets `127.0.0.1:8099` with docstring "run ON WHITE".
- WinError 10013 on loopback is the documented sandbox loopback block (memory/mechanic/r20-seat-change-and-ac-a2-live-leg-2026-11-14.md §1: "Loopback in this sandbox is blocked anyway (WinError 10013 on 127.0.0.1:8888/:8099)") — it measures the sandbox, not White's portal.
- Lesson (already stated by Mechanic r20, violated by my later rounds): **check `hostname` before any local-port probe**; a loopback verdict is only meaningful from a White-seated sandbox.

## 2. Fresh first-party LAN probe from Black (13:16:07-15)
`verifier_black_lan_probe_r82.py` → `verifier_black_lan_probe_r82_result.json`:
| port | status | ms |
|------|--------|----|
| 445  | OPEN   | 16 |
| 3389 | OPEN   | 30 |
| 8099 | TIMEOUT(4s) | 4014 |
| 8888 | TIMEOUT(4s) | 4011 |
- Path Black→White is healthy (controls open). :8099 AND :8888 time out identically = documented White firewall-drop pattern (since 11-13, re-verified r20 02:46 from Red; Builder r80 same). **Indistinguishable from "portal down"** — no agent seat can arbitrate.

## 3. Verdict table (unchanged except LIVE-leg characterization)
- AC-A2-1 / A2-2-static / A2-3 / A2-4: **PASS** (artifacts verified; selftest 6/6).
- AC-A2-2 LIVE: still open. Best indirect evidence portal is UP = `_portal_pid.txt` 10692 (synced ≤11:41, changed from 23704 of 11-13 ~22:0x; corroborated by Mechanic + Scribe). Sole close path: Arnold's White-console pass (localhost :8099 or Files panel) — human-gated.

## 4. New incident corroboration for Arnold
Black NICs degraded too: Ethernet + WiFi 2/3 "Media disconnected"; only WiFi up (IP_BLACK, IPv6 default gateway). Matches Scribe's Red-offline finding → **2 of 4 hosts with degraded network adapters** (Red fully offline after 11:41; Black partial). Human item: check NICs on Red AND Black.
