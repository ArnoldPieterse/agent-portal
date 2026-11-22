# Evidence-to-Decision Traceability Report
Generated: 2026-11-22T23:45:28Z

## Summary
- Decisions traced: **20**
- Total evidence links: **36**
- Resolved links: **31**
- Unresolvable links: **5**
- **Resolution rate: 86.1%**

## Per-Decision Trace

### [0] builder / cycle_trigger (OK)
- Timestamp: 2026-11-22T21:35:52.410186Z
- Evidence links: 1 (resolved: 1)
  - [OK] `decision-log.jsonl` -> decision-log.jsonl

### [1] builder / runbook_exec (OK)
- Timestamp: 2026-11-22T21:38:01.302963+00:00
- Evidence links: 2 (resolved: 2)
  - [OK] `memory/ops/runbooks/safe_test.md` -> memory/ops/runbooks/safe_test.md
  - [OK] `decision-log.jsonl` -> decision-log.jsonl

### [2] Builder / runbook_execution (PARTIAL)
- Timestamp: 2026-11-23T08:45:35.351199
- Evidence links: 2 (resolved: 1)
  - [MISSING] `Safe Test` -> NOT FOUND
  - [OK] `memory/decision-log.jsonl` -> memory/decision-log.jsonl

### [3] Builder / runbook_execution (PARTIAL)
- Timestamp: 2026-11-23T08:45:37.895668
- Evidence links: 2 (resolved: 1)
  - [MISSING] `Safe Test` -> NOT FOUND
  - [OK] `memory/decision-log.jsonl` -> memory/decision-log.jsonl

### [4] Builder / runbook_execution (PARTIAL)
- Timestamp: 2026-11-23T08:18:29.133450
- Evidence links: 2 (resolved: 1)
  - [MISSING] `Safe Test` -> NOT FOUND
  - [OK] `memory/decision-log.jsonl` -> memory/decision-log.jsonl

### [5] Builder / runbook_execution (PARTIAL)
- Timestamp: 2026-11-23T08:18:34.537904
- Evidence links: 2 (resolved: 1)
  - [MISSING] `Safe Test` -> NOT FOUND
  - [OK] `memory/decision-log.jsonl` -> memory/decision-log.jsonl

### [6] Builder / runbook_execution (PARTIAL)
- Timestamp: 2026-11-23T09:20:49.523299
- Evidence links: 2 (resolved: 1)
  - [MISSING] `Safe Test` -> NOT FOUND
  - [OK] `memory/decision-log.jsonl` -> memory/decision-log.jsonl

### [7] Builder / playbook_dry_run (OK)
- Timestamp: 2026-11-22T20:26:33.080010+00:00
- Evidence links: 2 (resolved: 2)
  - [OK] `memory\ops\runbooks\safe_test.md` -> memory\ops\runbooks\safe_test.md
  - [OK] `memory/ops/decision-log.jsonl` -> memory/ops/decision-log.jsonl

### [8] Builder / playbook_step (OK)
- Timestamp: 2026-11-22T20:26:34.965977+00:00
- Evidence links: 2 (resolved: 2)
  - [OK] `memory\ops\runbooks\safe_test.md` -> memory\ops\runbooks\safe_test.md
  - [OK] `memory/ops/decision-log.jsonl` -> memory/ops/decision-log.jsonl

### [9] Builder / playbook_step (OK)
- Timestamp: 2026-11-22T20:26:35.071888+00:00
- Evidence links: 2 (resolved: 2)
  - [OK] `memory\ops\runbooks\safe_test.md` -> memory\ops\runbooks\safe_test.md
  - [OK] `memory/ops/decision-log.jsonl` -> memory/ops/decision-log.jsonl

### [10] Builder / playbook_step (OK)
- Timestamp: 2026-11-22T20:26:35.086069+00:00
- Evidence links: 2 (resolved: 2)
  - [OK] `memory\ops\runbooks\safe_test.md` -> memory\ops\runbooks\safe_test.md
  - [OK] `memory/ops/decision-log.jsonl` -> memory/ops/decision-log.jsonl

### [11] Builder / playbook_complete (OK)
- Timestamp: 2026-11-22T20:26:35.086530+00:00
- Evidence links: 2 (resolved: 2)
  - [OK] `memory\ops\runbooks\safe_test.md` -> memory\ops\runbooks\safe_test.md
  - [OK] `memory/ops/decision-log.jsonl` -> memory/ops/decision-log.jsonl

### [12] Builder / playbook_step (OK)
- Timestamp: 2026-11-22T20:26:38.480837+00:00
- Evidence links: 2 (resolved: 2)
  - [OK] `memory\ops\runbooks\safe_test.md` -> memory\ops\runbooks\safe_test.md
  - [OK] `memory/ops/decision-log.jsonl` -> memory/ops/decision-log.jsonl

### [13] Builder / playbook_step (OK)
- Timestamp: 2026-11-22T20:26:38.586244+00:00
- Evidence links: 2 (resolved: 2)
  - [OK] `memory\ops\runbooks\safe_test.md` -> memory\ops\runbooks\safe_test.md
  - [OK] `memory/ops/decision-log.jsonl` -> memory/ops/decision-log.jsonl

### [14] Builder / playbook_step (OK)
- Timestamp: 2026-11-22T20:26:38.586742+00:00
- Evidence links: 2 (resolved: 2)
  - [OK] `memory\ops\runbooks\safe_test.md` -> memory\ops\runbooks\safe_test.md
  - [OK] `memory/ops/decision-log.jsonl` -> memory/ops/decision-log.jsonl

### [15] Builder / playbook_rollback (OK)
- Timestamp: 2026-11-22T20:26:38.693352+00:00
- Evidence links: 2 (resolved: 2)
  - [OK] `memory\ops\runbooks\safe_test.md` -> memory\ops\runbooks\safe_test.md
  - [OK] `memory/ops/decision-log.jsonl` -> memory/ops/decision-log.jsonl

### [16] Builder / playbook_complete (OK)
- Timestamp: 2026-11-22T20:26:38.693832+00:00
- Evidence links: 2 (resolved: 2)
  - [OK] `memory\ops\runbooks\safe_test.md` -> memory\ops\runbooks\safe_test.md
  - [OK] `memory/ops/decision-log.jsonl` -> memory/ops/decision-log.jsonl

### [17] mechanic / SELFTEST (OK)
- Timestamp: 2026-11-22T20:39:46.129680+00:00
- Evidence links: 1 (resolved: 1)
  - [OK] `memory/ops/decision-log.jsonl` -> memory/ops/decision-log.jsonl

### [18] test_agent / oom_recovery (OK)
- Timestamp: 2026-11-22T22:17:58.698011+00:00
- Evidence links: 1 (resolved: 1)
  - [OK] `memory/ops/decision-log.jsonl` -> memory/ops/decision-log.jsonl

### [19] test_agent / oom_recovery (OK)
- Timestamp: 2026-11-22T23:10:36.112747+00:00
- Evidence links: 1 (resolved: 1)
  - [OK] `memory/ops/decision-log.jsonl` -> memory/ops/decision-log.jsonl

## Interpretation
Traceability is MODERATE. Some references point to missing or moved files.
