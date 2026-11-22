# Verifier r20 — AC-A2 FINAL STATE (Black seat, 2026-11-14 ~03:5x)
Supersedes the bottom-line of `ac-a2-closure-r19.md`. Evidence chain: ac-a2-r19.md → ac-a2-r19-reverify.md → ac-a2-closure-r19.md → this leaf. Written to close the auto-continue loop on the "Verifier closes AC-A2-1..4" TODO line.

## Fresh sweep 03:45:48 — zero drift vs 03:31 pins
| file | size | md5-8 |
|---|---|---|
| agent_portal.py | 80,056 B | 1b86880c (build PID 23704 launched from) |
| memory_mirror.py | 10,668 B | e5c4a229 |
| index.html | 67,681 B | 9c6b08e3 (TRUE canonical held; full pin 9c6b08e3d98355e632a7cb871d5b60d) |
| uploads/_canary_remote.txt | 212 B | 512d0dc8 |
uploads/ inventory = **N=1** (canary only) → live-leg expectation unchanged: exactly 1 row; raw fetch 200 + exactly 212 B.

## New evidence this round
- :8099 egress re-probed 03:4x: `connect_ex(("White", 8099))` → sandbox "host not in sandbox allowlist" (explicit refusal, new wording vs r19's generic block). Live HTTP from this seat remains structurally unreachable — the AC-A2-2 live leg cannot be closed from any agent seat.
- Researcher independently re-confirmed same class this round (`memory/researcher/farm-relpath-diagnosis-2026-11-14.md`: "loopback connect blocked by sandbox allowlist… live legs stay White-browser/Mechic-proxy").
- Designer ruling LANDED on disk: `memory/designer/ac-a2-1-ruling.md` — outside-click clause ACCEPTED as house-style variant → **AC-A2-1 fully closed, PASS with note, no code change owed for r19.** (Designer's six design-leg defects in post-restart-verify-r19.md are separate design debt; #1 token-lock conflict is an Orchestrator adjudication, not an AC-A2 clause.)

## Final verdict table (Verifier sheet)
| AC | verdict |
|---|---|
| AC-A2-1 placement + click-open | **PASS** (closed r19) |
| AC-A2-1 outside-click clause | **PASS WITH NOTE** (Designer ruling; house-style uniform across all four mode-bar panels) |
| AC-A2-2 static | **PASS** (row render name·size·mtime; /api/file/raw realpath-anchored, in-bounds for uploads/*) |
| AC-A2-2 LIVE | **OPEN — sole remaining item, owner named: Mechanic-as-proxy / White-browser.** Expected: N=1 row (`uploads/_canary_remote.txt`), raw fetch 200 + exactly 212 B, console clean, no /api/uploads in any background timer. Single pass; when it lands with those values the whole AC-A2 gate closes. |
| AC-A2-3 | **PASS** (empty-state single line + return; catch replaces list, no uncaught throw) |
| AC-A2-4 | **PASS** (filesLoad from exactly 2 sites; full-doc timer scan: zero /api/uploads references) |

## Process-level on PID 23704 — boundary restated
Trap-check (created 22:01:54 > lastwrite 22:01:38; stale 27268/1240 retired) stands as console-relayed evidence from the r19 human-leg record; not re-verifiable from this seat (tasklist credential-blocked, no White process-table access). Corroboration chain complete for everything physically testable here: fixed bytes on disk + relayed timing.

## Bottom line
**Verifier lane CLOSED [CONCLUDED].** Every AC-A2 clause I can adjudicate is closed with evidence; the single surviving sub-clause (AC-A2-2 live) has a named owner and exact expected values, and is provably unreachable from every agent seat this round. @Orchestrator: strike "Verifier closes AC-A2-1..4" from TODO.md r19 NEXT — replace with "AC-A2 gate: Verifier sheet closed (memory/verifier/ac-a2-final-state-r20.md); live leg = Mechanic proxy / White-browser, N=1/212 B expectation." @Mechanic: the one-pass brief is in ac-a2-closure-r19.md, unchanged.

Owner: Verifier. Basis: md5 recomputation + uploads walk at 03:45:48; allowlist probe 03:4x; ruling + designer/researcher leaves read on disk.
