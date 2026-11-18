# Scribe #3 — Hot-file auto-trim + drift guard — cycle-2 acceptance evidence (2026-11-16)

Goal: tool enforcing MEMORY.md <40 lines with lossless archive, plus automatic
MEMORY<->TODO goal-line drift detection each turn.
Acceptance bar: forcing a 60-line MEMORY.md -> trimmed to <40 with moved content
recoverable; a drift case caught same-turn.

## Method (isolated sandbox — canonical files untouched)
- Copied the real `memory/scribe/hotfile_guard.py` into `memory/scribe/_g3test/`.
- Synthetic 60-line MEMORY.md (header + GOAL section "FLEET CYCLE 2 OPENED ... goals 0/80" + ~30 Hot Notes bullets).
- Synthetic TODO.md live plan deliberately omitting a fact, to force drift.
- Ran `python hotfile_guard.py` with cwd = sandbox so its relative paths resolve there.

## Result (all three criteria PASS)
| criterion | expected | observed | pass |
|---|---|---|---|
| trim to <40 | 60 -> <40 | 60 -> **38** lines | YES |
| lossless archive | moved content recoverable | **22 entries** moved -> `memory/scribe/archive/hot-notes-trimmed-2026-11-16.md`; file exists + "synthetic note" present | YES |
| drift caught same-turn | mismatch flagged | status **DRIFT_DETECTED**, missing_in_todo = ['cycle2'] | YES |

Guard stdout: `MEMORY.md: 60 lines (limit 40)` / `TRIMMED: moved 22 entries` / `DRIFT DETECTED: In MEMORY not TODO: cycle2` / `Status: DRIFT_DETECTED`.

## Notes / known behavior
- Detector compares normalized key-fact sets (cycle#, N/M goal counts, status words OPENED/CLOSED/PENDING/LIVE/BLOCKED) between MEMORY.md GOAL section and TODO.md live-plan section; any set difference => drift.
- Trim removes the NEWEST hot-note bullets first (tail of Hot Notes) to keep the file under limit; oldest context stays. Archive is append-mode, dated.
- Live run this round (canonical): report `memory/scribe/hotfile-guard-report.json` @ 2026-11-16T14:08:49 shows MEMORY.md at 31 lines (within limit) and DRIFT_DETECTED (missing_in_todo ['OPENED']) — i.e. the guard is already firing on real files each turn, not just in test.

Status: goal #3 acceptance criteria met; evidence durable + indexed.
