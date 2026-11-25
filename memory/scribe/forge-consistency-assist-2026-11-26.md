# Scribe Assist: Forge Goal #9 (Cross-Host Consistency Test)

Date: 2026-11-26
What: Added --simulate-mismatch HOST and --test-mismatch flags to memory/forge/consistency_check.py

## Verification performed (sandbox, no live fleet):
- `--test-mismatch`: synthetic 2-host scenario (White=gpt-4o, Red=claude-sonnet) -> verdict MISMATCH + fix command, exit code 1 (confirmed via subprocess.returncode)
- `--local-only --simulate-mismatch White`: single-host PASS with simulated model, exit code 0
- Normal mode: probes real hosts; in sandbox all UNREACHABLE (expected)

## Remaining for Forge to verify on live fleet:
- All-green state (4 hosts same model) -> verdict should be PASS/CONSISTENT
- Real mismatch scenario (one host with different model after a bad deploy)
- Note: script uses "PASS" not "CONSISTENT" as the all-green label (minor naming; Forge may want to align)

## Bug fixed:
Original comparison `h["name"] == args.simulate_mismatch.upper()` failed because h["name"] is title-case ("White") vs upper ("WHITE"). Fixed to `.upper()` on both sides.
