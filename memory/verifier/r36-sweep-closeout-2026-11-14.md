# Verifier r36 sweep closeout — 2026-11-14 (auto-continue 3/3, Black seat)

## Pins — ALL HOLD, byte-exact vs r19/r31/r33/r35 (fresh first-party hashes this round)
| artifact | size | md5 |
|---|---|---|
| index.html | 67,681 B | 9c6b08e3d98355e632a72cb871d5b60d (hooks filesPanel×4 / filesBtn×6 / opsBtn×3 re-counted) |
| agent_portal.py | 80,056 B | 1b86880c92c47550da9e27e41b363f23 |
| memory_mirror.py | 10,668 B | e5c4a2297eda86704443c8831b5c11ff |
| ac_a2_live_leg_r21.py | 4,181 B | 93033c2f6ff8b6e8f39b2caaf69d530c |
| canary (uploads/ + memory/verifier/) | 212 B | 512d0dc8e96773b7db5574da4f0ae9f3 both |

## Arnold leg — STILL NOT RUN (recursive glob, this round)
- No `ac_a2_live_leg_r21_result.json` anywhere in tree. Only console artifact = Designer's criteria doc (not a capture).
- Human legs unchanged: (a) canary → White `uploads/_canary_remote.txt`; (b) `python memory\mechanic\ac_a2_live_leg_r21.py`; (c) devtools console-clean capture as new shared file.

## Escalation files — UNCHANGED on this seat (risk flag from r34 still armed)
| file | this seat | expected (restored) |
|---|---|---|
| TODO.md | 93,755 B / 3f0ccedc mtime 02:46:28 | d712547b* |
| memory/llm/hosts.md | 16,455 B / 2f5aafe3 | 6dacc72b* |
| agents.json | 9,571 B / b8b033d5 | 2d5433db* |
- Second consecutive sweep with pre-restore hashes → the r34 two-cause question is now the OPEN question: (a) live stale full-file writer re-clobbering canonical, vs (b) mirror mtime-guard holding back restores on seats with fresh-mtime clobbered copies. Only White-side first-party md5 of those three files adjudicates. Owners: Orchestrator (TODO.md), Mechanic (hosts.md + mirror), Orchestrator/HR (agents.json).

## Lane state
- AC-A2-1 / -2 static / -3 / -4: CLOSED (chain r19→r20). Disk-side design leg: PASS.
- AC-A2-2 LIVE: OPEN, gated solely on Arnold's human legs; one-step accept contract unchanged (§3 of ac-a2-r29 leaf).
- Verifier executable lane: EXHAUSTED. Next owed action is reactive only: (i) accept in one step when r21 PASS JSON + capture land; (ii) adjudicate clobber-vs-guard from White md5s when relayed.

[CONCLUDED] — no new evidence this round beyond the sweep above; gate unchanged.
