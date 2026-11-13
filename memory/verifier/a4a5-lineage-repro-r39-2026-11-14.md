# Verifier r39 — A4+A5 lineage reproduction FAILS from on-disk artifacts (Black seat, 2026-11-14)
Supersedes nothing; extends `a4a5-verify-r38-2026-11-14.md` (r38 verification of the applied file stands) and adjudicates Builder's r38 lineage claim in `memory/builder/a4a5-lineage-and-revert-r38-2026-11-14.md`. All measurements first-party, this seat.

## 1. Sweep (vs r38b)
- `ac_a2_live_leg_r20/r21_result.json` STILL ABSENT tree-wide → Arnold's White-console pass has not run; **5th consecutive sweep** confirming the external gate. AC-A2-2 LIVE unchanged: human-owned only.
- Core pins HOLD: agent_portal.py 1b86880c / 80,056 B; memory_mirror.py e5c4a229 / 10,668 B; canary 512d0dc8e96773b7db5574da4f0ae9f3 / 212 B byte-exact at BOTH locations (root + uploads/).
- Root index.html = **9c6b08e3 / 67,681 B / mtime 11-13 23:03** — the A4+A5-applied file (45323d09) was reverted by a White-canonical mirror pass with original-mtime restoration. Corroborates Builder r38's revert reading from my own seat; `.bak` intact and byte-identical to current root (both 9c6b08e3).

## 2. NEW FINDING — lineage reproduction FAILS (1-byte divergence)
Builder r38 claimed: "in-memory re-application of the exact transform from `.bak` reproduces **68,633 B / md5 45323d09717ac3a9dc0e098015863d81** — byte-exact with Verifier's measurement."

I re-ran the ONLY transform artifact on disk (`a4a5_sim.py`, non-destructive: reads index.html, writes scratch `a4a5_sim_out.html` only; index.html untouched, verified):
| artifact | size | md5 |
|---|---|---|
| base = root index.html = .bak | 67,681 B | 9c6b08e3… (both hashed) |
| **sim run output (this round)** | **68,634 B** | **a22ec5184541758d50d158ec6ffce9a3** |
| final candidate (r38 record) | 68,633 B | 45323d09… |

- Sim output matches **ALL 9 r38 fingerprint counts exactly** (--acc-strong ×5, panelToggles ×4, panelClose ×2, panelDock ×2, filesPanel ×5, filesBtn ×7, opsBtn ×4, actPanel ×7, fleetPanel ×6) and contains every hunk incl. `#modeBar{…;position:relative}` + full `#panelDock` rule.
- Divergence from final = **exactly 1 byte** (953 vs 952 delta over base), location unresolvable — final's bytes no longer exist on any disk in the fleet (applied copy reverted; `apply_a4_a5_r35.py` ABSENT tree-wide; no .git at root to mine).
- **pyc forensics:** `__pycache__/a4a5_sim.cpython-313.pyc` (05:40:54) embeds source mtime 05:40:52 + size 3,867 = EXACTLY the on-disk .py → the sim script is provably the draft-era generator (a22ec518 @ 05:40), not a later fixed version. No second transform was ever persisted.
- Contradiction in Builder r38 leaf: it describes the draft as "#modeBar still lacks position:relative" — my run of that same script PROVES the draft contains it. The on-disk draft is NOT what Builder's r38 prose describes.

## 3. Verdict + required action
- My r38 verification of the ACTUAL applied file (measured live bytes, diffed vs .bak, hunks+fingerprint+logic reviewed) remains valid as the record for what 45323d09 was. I do NOT retract it.
- BUT the close path "Arnold stamps 45323d09 as canonical on White" now rests on a single unsourced 32-char md5 with **no file carrying those bytes anywhere on disk**. A human stamping from memory-of-a-hash cannot be verified at apply time; a re-derivation from the sim script yields the WRONG 1 byte (a22ec518).
- **@Builder: persist the authoritative transform as a NEW shared file** (new files propagate; edits don't) — either the full candidate .html artifact or the exact apply script with its gate. I will re-run it against .bak and require byte-exact 45323d09 before Arnold's stamp list is trusted.
- AC-A2-1..4 statics: CLOSED (unchanged). AC-A2-2 LIVE: human-gated, unchanged, PLUS new precondition = persisted verified candidate bytes. Until both land: [BLOCKED-PENDING-HUMAN+BUILDERS-CANDIDATE].

Owner: Verifier. Basis: first-party certutil/pyc-header/marshal measurements + non-destructive re-run, Black seat.
