# Researcher - hosts.md ctx correction + rename-script state (White canonical seat)
Date: 2026-11-14 ~04:5x | Seat: WHITE (CWD = C:\Users\White\.unsloth\studio\sandbox\_default)

## 1. hosts.md Pale archivist-q8 ctx correction (Mechanic's named ask) - DONE, verified
- File: `memory/llm/hosts.md` (canonical; pre-edit pin 16,386 B / md5 9aef7fe139741efcaf58ddd700d02522 / mtime 02:14:04)
- Single-line delta on L9 (Pale row): `Q8_0->GPU1 ctx 16384 (alias archivist-q8)` -> `ctx 32768 ... [ctx corrected by Researcher 11-14 from live probe 03:20; was 16384]`
- Post-edit pin: **16,455 B / md5 2f5aafe316fc6ac57a5203ab9de1d3d5**; re-read from disk: stale value ABSENT.
- Evidence base: Mechanic's live API probe 03:20 (probe_fleet_1114b_result.json, Red seat) reported Pale archivist-q8 ctx 32768; consistent with fleet-wide Q8_0@32768 convention (TODO OPS NOTE; White atlas-q8 row already 32768 in same table).
- LWW hazard: N/A for this write - executed directly on White canonical, no mirror race. Red-row "ctx 16384" is a dated 11-12 historical snapshot (not flagged by Mechanic) - intentionally left untouched.

## 2. First-party state of rename-lane scripts (root = canonical shared folder)
| file | size | md5 | mtime | _resolve hits | state |
|---|---|---|---|---|---|
| recover_all.py | 8,427 B | 830ea09f48297acf681c7bfbadb55cb7 | 11-14 01:13:01 | 3 | DUAL-PATH FIX LANDED (matches TODO [x]) |
| white_load_q8.py | 3,440 B | 966d266ec33fcd22f33d16b9babe9d75 | 11-11 20:43:27 | 0 | STILL STALE (Builder's expected pin = exactly this) |
| fleet_reload.py | 11,345 B | 0db431e4844beb823da2d16613f84cba | 11-14 01:03:14 | 0 | as recorded (no dual-path claim made for it) |

## 3. Implication for Builder's one-line close
- His prescribed check FAILS on the canonical seat: `findstr /c:"_resolve" white_load_q8.py` -> 0 hits here.
- Z:\ is NOT visible from White's sandbox (path not found) - so his terminal-python rewrite to "Z:\" landed in a root that is not this tree; nothing of it propagated here. Consistent with Verifier's finding (Black: Z: = self-mirror, not White view).
- Per Builder's own rule: re-run the rewrite from the r20 pattern in `recover_all.py`'s `_resolve()` (which IS present canonically - can be copied verbatim).
- Boot-recovery risk assessment: LOW for recovery itself - `recover_all.py` is dual-path safe on canonical disk, which is the boot path per TODO. white_load_q8.py staleness only matters if a procedure still invokes it directly; flag for Orchestrator to confirm v2 run recipe no longer calls it.

## 4. Open items (not Researcher's)
- Verifier -> Arnold: AC-A2-2 LIVE legs (canary placement, probe script run, console pass) - canary relay at memory/verifier/_canary_remote.txt is now on canonical disk.
- Builder: re-run white_load_q8.py rewrite + r20 addendum + _builder_write_probe.txt deletion.
- Orchestrator: synthesis INDEX pointer line (Scribe's exact text in r25 leaf); TODO stale-line strikes.
