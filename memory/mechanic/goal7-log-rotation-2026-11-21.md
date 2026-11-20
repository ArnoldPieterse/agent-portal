# Goal #7 Log Rotation + Retention - Progress 2026-11-21

## What was done this pass
- Rewrote `memory/mechanic/log_rotate.py` to match full goal spec:
  - MAX_SIZE: 10MB -> **50MB**
  - Scope: memory/mechanic/ only -> **entire fleet (memory/** + root)**
  - File types: .log only -> **.log + .jsonl**
  - Retention: 5 rotations -> **7-day time-based pruning**
  - Compression: oldest rotation only -> **immediate gzip on every rotation**
  - Naming: sequential (.1, .2...) -> **timestamped (.YYYYMMDD_HHMMSS.gz)**
- Ran `--once` live: scanned 401 files, all under 50MB (correct no-op)
- Self-test: 7/7 assertions pass (rotate >50MB, empty original, .gz valid+
decompresses correctly, small file not rotated, 8-day-old pruned, fresh preserved)

## Remaining for full closure
- Register as daily schtask on White: `python elev.py --shell "schtasks /create /tn LogRotate /tr \"python Z:\\memory\\mechanic\\log_rotate.py --once\" /sc daily /st 03:00"`
- (Same COM/elev wall as other goals - needs non-sandbox seat)
- Acceptance criteria met in sandbox: test file >50MB rotated, 8-day-old pruned,
  disk bounded, no data loss.

## Runbook note
log_rotate.py was underspec'd (10MB/.log-only/mechanic-dir); now matches goal spec
(50MB/fleet-wide/.jsonl+.log/7-day retention). Self-test proves rotation+compression+
pruning logic. Schtask registration is the only remaining live step.
