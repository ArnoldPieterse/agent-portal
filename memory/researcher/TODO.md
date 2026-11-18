# Researcher — TODO

## LIVE (2026-11-14 auto-continue 3/3, ~r45 sweep)
- [x] First-party sweep: ac_a2_live_leg r20/r21 result JSON still ABSENT tree-wide; canary intact 212 B / 512d0dc8; root index.html 67,681 B / 8ef4e222 = matches r45 pin (zero drift). No new ground truth.
- [x] Truncation check on my seat: r41 E14 re-verify leaf complete (probe :1235 BLOCKED WinError 10013, cache 89 entries intact, entrypoint present); probe script retained. Nothing truncated or empty owed from this seat.
- [ ] PASSIVE: await Arnold's White-console leg (bundle v2, stamp ffa77423). Until it lands, NO agent-executable work on my seat.
- [ ] On Arnold's pass landing -> relay/confirm for Verifier's one-step AC-A2-1..4 + LIVE acceptance; do NOT re-write root index.html from this seat (7:5x ruling holds, White canonical 9c6b08e3).
- [ ] Relay my seat's pre-restore hashes to Orchestrator/Mechanic for the escalated-files clobber-vs-mtime-guard adjudication (White-side md5s are their leg): TODO.md 3f0ccedc / hosts.md 2f5aafe3 / agents.json b8b033d5.

## DONE this round
- [x] Closed the house-convention sub-gap Archivist flagged: created memory/researcher/MEMORY.md + TODO.md (was INDEX.md-only).
- [x] hosts.md White model-rename line corrected + cross-checked vs studio-api.md / instances.md (confirmed by Mechanic on Red).
- [x] r27 N-semantics -> option (a) adopted; amended bracket ratified by Verifier. Probe canon = r21 93033c2f.

## NOT mine (owned elsewhere — tracked only)
- A4 apply -> Builder. AC-A2/AC-A4 process acceptance + escalation adjudication -> Verifier. dcabots re-prompt / full smoke8 -> human (Arnold). builder-q8 alias drift -> Orchestrator/Builder.

## r47 first-party cross-verify (2026-11-14, Researcher seat)
- Result JSON hunt: ac_a2_live_leg_r20/r21_result.json + smoke8 artifacts = NONE tree-wide (13th consecutive absent). No new ground truth.
- Mechanic staging cross-check: uploads/_canary_remote.txt CONFIRMED byte-exact 212 B / 512d0dc8e96773b7db5574da4f0ae9f3 on my seat (critical artifact for the live leg). ac_a2_live_leg_r21.py: root copy NOT visible from my seat, but memory/mechanic/ac_a2_live_leg_r21.py = 4,181 B / 93033c2f6ff8b6e8f39b2caaf69d530c (byte-identical to his pin) -> Arnold should pull from memory/mechanic/ or Verifier re-verifies on White itself; likely inter-seat mirror lag, not a missing artifact.
- Verifier r20-drift flag CONFIRMED first-party: memory/mechanic/ac_a2_live_leg_r20.py = 2,344 B / e0327c726d5f83816972bb566a2b9a20 (hash prefix matches his measurement).
- FLAG (for Orchestrator adjudication, non-blocking): root index.html on my seat = 67,681 B / 8ef4e2227a7afd506ed2b55dc9dd170d (matches r45 pin), but Verifier's current sweep reports the same file as 9c6b08e3d98355e632a72cb871d5b60d at identical size; NO file matching 9c6b08e3 exists anywhere in my tree -> possible inter-seat mirror skew or a different measured path. My lane unchanged: sole remaining work = Arnold's human White-console pass.

## r47b (auto-continue) — pin contradiction re-measured first-party, NOT resolvable from this seat
- Re-measure after Scribe's ruling: root index.html on MY seat = 67,681 B / md5 8ef4e2227a7afd506ed2b55dc9dd170d (unchanged); NO copy of 9c6b08e3 exists anywhere in my tree.
- agents.json on MY seat = 9,559 B / md5 2d5433dbdf70d22da44cc9725f2e1ef8 — matches Orchestrator's pin; Scribe measured b8b033d5/9,571 B (delta +12 B).
- So it is now 2 seats vs 2 seats (Researcher+Orchestrator: 8ef4e222 / Verifier+Scribe: 9c6b08e3 for index.html; Researcher+Orchestrator: 2d5433db / Scribe: b8b033d5 for agents.json). Same-size-different-hash on index.html = genuine content divergence, not a stale-read of a different file.
- I cannot reach White (loopback WinError 10013, LAN timeout — established this thread), so adjudication requires one measurement ON White.
- ASK: add to Arnold's human pass — `md5sum index.html agents.json` on the White console alongside his existing stamps; that pins canonical values and lets every seat reconcile in one shot. Non-blocking for the r21 leg itself (it only GETs canary + uploads list).
