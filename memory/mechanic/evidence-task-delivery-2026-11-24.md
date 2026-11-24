# Evidence: task_delivery.py (Idle Task Delivery Verifier)
Date: 2026-11-24
Script: memory/mechanic/task_delivery.py
Result: 20/20 selftest PASS

## What it does
Verifies that dispatched idle/maintenance tasks actually reached the target agent by checking:
- (a) Agent's response contains key phrases from the task text
- (b) Response arrived within expected time window (default 300s)
- (c) Response is non-trivial (not empty, not generic "[SILENT]" or "ok")

## Self-test coverage
1. Successful delivery with phrase match
2. Generic [SILENT] reply rejected
3. Empty response rejected
4. Short "ok" rejected
5. Key phrase partial match works
6. Unrelated but substantive response passes content check
7. File-based verification (file exists)
8. File-based verification (file missing -> error field)
9. Log result to JSONL
10. Multiple log entries append correctly
11. extract_key_phrases produces lowercase phrases
12. Stale dispatch (timing check fails)

## Usage
```
python memory/mechanic/task_delivery.py --selftest
python memory/mechanic/task_delivery.py --verify <agent> <task_text> [response_file]
```
