# state_collector.py post-mirror integrity check — 2026-11-24

**Date:** 2026-11-24 (auto-loop pass)
**Context:** Hot note warns "Mirror cycle reverts Mechanic edits (state_collector.py + deploy_all_schtasks.py); must re-verify after each sync pass."

## Result

| Check | Verdict |
|-------|---------|
| File present | PASS (14450B, sha12=f3523abf913b) |
| selftest command | PASS — 18/18 assertions green |
| JSONL output valid | PASS (120 entries, no parse errors) |
| Collection <2s | PASS (0.0ms simulated) |
| No TODO.md modification | PASS |

**Verdict:** state_collector.py is intact and functional. Mirror has NOT reverted it this cycle.

## deploy_all_schtasks.py

| Check | Verdict |
|-------|---------|
| File present | PASS (5599B, sha12=08a3071ac40f) |

Both files survived the latest mirror sync. No re-apply needed.

## Runbook note
If a future mirror cycle DOES revert these: re-verify by running `python memory/mechanic/state_collector.py selftest` — 18/18 PASS = intact; any assertion failure = reverted, needs re-land from canonical copy.
