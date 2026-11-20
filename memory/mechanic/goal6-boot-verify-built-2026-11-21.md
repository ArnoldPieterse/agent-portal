# Goal #6 - Boot Task Verification: boot_verify.py Built + Tested (2026-11-21)
Date: 2026-11-21 (auto-loop pass)
Agent: Mechanic

## What was built this pass
`memory/mechanic/boot_verify.py` (7.8 KB) - post-reboot verification script that checks:
1. nvidia-smi for loaded GPU models (detects NVML errors, rc!=0)
2. LM Studio /api/v0/models for expected model aliases (7 unique: atlas-q8, quinn-q4, Qwen3.8-27B-Q8_0, designer-q4, archivist-q8, scribe-q8, mechanic-q4)
3. Portal :8099 /api/health for agent responsiveness

Outputs: human-readable or --json; writes report to memory/mechanic/boot-verify-YYYY-MM-DD.md (skipped with --dry-run).
Exit codes: 0=PASS, 1=some FAIL, 2=fatal.

## Self-test results (sandbox seat)
```
Overall: FAIL (expected - sandbox has no GPU access, no LM Studio, egress wall to :8099)
  [FAIL] nvidia_smi: rc=255 "Failed to initialize NVML"
  [FAIL] lm_studio: HTTP -1 (unreachable)
  [FAIL] portal: WinError 10013 (egress wall)
```
All three checks correctly detect their respective failure modes. On a non-sandbox host with GPU + LM Studio + portal running, all would PASS.

## Acceptance criteria status
| Criterion | Status |
|-----------|--------|
| 3 reboots verified | IN PROGRESS (script built; needs 3 live runs on non-sandbox seat) |
| All expected models loaded post-boot | Script checks this (7 aliases from agents.json) |
| Failures logged + auto-retried | Log written per run; retry logic is in boot_recovery.py (separate concern) |
| Verification log at memory/mechanic/boot-verify-YYYY-MM-DD.md | Script writes this on non-dry-run execution |

## Remaining
- Run 3x on a non-sandbox seat after actual reboots to accumulate evidence
- Each run appends to boot-recovery-log.jsonl (already exists in memory/ops/)
