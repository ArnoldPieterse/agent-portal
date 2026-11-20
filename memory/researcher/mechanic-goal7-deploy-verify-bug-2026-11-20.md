# Mechanic #7 Perf-Profiling: live-leg deploy bug (Researcher assist, 2026-11-20)

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
