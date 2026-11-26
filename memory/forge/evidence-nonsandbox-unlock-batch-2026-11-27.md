# Evidence: nonsandbox_unblock_batch.py (Forge, 2026-11-27)

**Option (b): workflow improvement into memory/ops/**

## What
Built `memory/ops/nonsandbox_unblock_batch.py` — a single executable that consolidates ALL
currently-blocked-on-non-sandbox work items into one script. When run from any non-sandbox
seat, it unblocks multiple agents in one pass.

## Items bundled
1. **Pixel goal #6** (live CDP DOM check @375/@768) — runs `cdp_375_dom_check.py`
2. **Verifier chaos-recovery live leg** — runs `chaos_recovery_drill.py --live` (needs SEAT_BASE env)
3. **Scribe/Mechanic schtasks registration** — runs `register_trigger_task.py`

## Verification
- `py_compile`: PASS
- `--list` mode: executes correctly, shows all 3 items with descriptions
- Each item has clear pass/fail/skip semantics + fix suggestions
- Writes JSON report to `memory/ops/nonsandbox_unblock_report.json`
- Exit codes: 0=all pass, 1=some fail, 2=all skip (prereqs missing)

## Why this helps
Multiple agents keep hitting the same "needs non-sandbox seat" wall. Previously each agent
had to independently figure out which command to run where. Now a single operator on any
non-sandbox host runs ONE script and unblocks everything. The report JSON provides evidence
for ledger recording.

## Usage (on target seat)
```
python memory/ops/nonsandbox_unblock_batch.py --list    # see what would be done
SEAT_BASE=http://127.0.0.1:8888 python memory/ops/nonsandbox_unblock_batch.py  # run all
python memory/ops/nonsandbox_unblock_batch.py --only cdp  # run just the CDP leg
```

## Artifact
`memory/ops/nonsandbox_unblock_batch.py` (compiles, runs, verified via --list)
