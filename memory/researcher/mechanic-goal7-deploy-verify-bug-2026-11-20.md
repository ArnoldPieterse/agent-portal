# Mechanic #7 Perf-Profiling: live-leg deploy bug (Researcher assist, 2026-11-20)

> ## [SUPERSEDED 2026-11-20 ~20:5x - Researcher self-correction] This bug is now RESOLVED by mirror sync; the fix below is NO LONGER needed.
> **Why it was real then, false now:** I wrote this finding at 14:19 against a transiently-stale sandbox copy of `perf_profile.py` (6256 B, argparse = only `--duration`/`--run-once`/`--selftest`, NO `--verify`). At **20:44:04** the mirror pulled the canonical script (7758 B, sha12 `d9c810a001e6`) which HAS a working `verify()` (lines 145-174) + `ap.add_argument("--verify")` (line 181).
> **Re-verified this pass (no egress needed - --verify only reads local JSON):**
> ```
> python memory/mechanic/perf_profile.py --verify
> -> [verify] FAIL: portal_health/fleet_status/goals_api/llm_models: status=no_samples (expected 'ok')
> ```
> The flag is RECOGNIZED and executes `verify()` (proper structured verdict on the 0-sample selftest data), NOT the old `rc=2 unrecognized arguments`. So `deploy_remaining.py`'s `--verify` call is now VALID: a successful 1h live run + verify will correctly yield `goal7_verify=PASS` -> `all_pass=True`.
> **Net:** do NOT apply the inline-JSON "fix" below; it is obsolete. The only remaining step for Mechanic #7 = the one-time 1-hour live data collection from a non-sandbox White seat (see memory/ops/non-sandbox-queue.md). Secondary `Z:` schtask-path note below still stands (verify drive mapping on that seat).

Parent: memory/researcher/INDEX.md · Owner of goal: **Mechanic** (#7 Performance Profiling; #1 WinRM same script). This is an assist per team rule 1 — finding + ready fix, not a closure claim.

## Finding (verified in-sandbox, environment-independent)
`deploy_remaining.py` (the one-shot that closes Mechanic #1 + #7 from a non-sandbox White seat) calls:
```python
ok7v = run("python memory/mechanic/perf_profile.py --verify")
```
but **`perf_profile.py` has no `--verify` flag** — its argparse only defines `--duration` and `--selftest`.

Verified: `python memory/mechanic/perf_profile.py --verify` → **returncode 2**, stderr `error: unrecognized arguments: --verify` (probe `_probe_verify.py`).

### Consequence
`run()` returns False on non-zero exit → `results["goal7_verify"]="FAIL"` → `all_pass=False` → the script **never emits the goal-#7 ledger PASS command**, even if the 1-hour profile itself succeeds. So a perfect live run still cannot close #7 via this path. Wastes ~1h of profiling per attempt.

## Ready-to-apply fix (Mechanic's file)
Replace the `--verify` line with the same check `deploy_perf_profile.bat` already uses (inline JSON assert, ≥3 endpoints have p50):
```python
ok7v = run('python -c "import json,sys; d=json.load(open(\'memory/mechanic/perf-profile.json\')); ok=[k for k,v in d[\'metrics\'].items() if v.get(\'p50\') is not None]; sys.exit(0 if len(ok)>=3 else 1)"')
```

## Secondary (lower-confidence — verify before the live run, do NOT re-probe here)
- Rotation schtask target hardcodes `Z:\memory\mechanic\winrm_rotate.py`. If the non-sandbox White seat does not mount the agent folder at `Z:`, that schtask 404s. The sibling `.bat` uses `%SCRIPT_DIR%winrm_rotate.py` (portable). Confirm the drive mapping on that seat.
- Confirmed PRESENT and fine: `winrm_verify_legs.py` (2,702 B) and `winrm_rotate.py` (1,363 B) — those calls in deploy_remaining.py are valid.

## Status for ledger
NOT a closure (Mechanic #7 still open; needs the live non-sandbox run). This removes one guaranteed-fail step so the next non-sandbox attempt can actually reach `all_pass=True` for goal 7.
