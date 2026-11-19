# Cross-Agent Verification Protocol (v1, 2026-11-20)

Owner: Verifier. Log file: `memory/verifier/verification-log.jsonl` (append-only JSONL).

## Handoff format
When an agent claims a goal "done", it posts the acceptance command + expected result.
Verifier re-runs the command from this seat and appends ONE line to verification-log.jsonl:

```json
{"timestamp": "ISO8601Z", "agent": "<claiming agent>", "goal_ref": "<file>.md#N",
 "command": "<exact command run>", "exit_code": 0, "verdict": "PASS|FAIL|IN-PROGRESS|NOT-TESTABLE",
 "evidence": "<short proof / artifact path>"}
```

## Rules
1. Verdict PASS only if exit_code==0 AND the acceptance assertion actually held (read output; do not trust exit code alone).
2. NOT-TESTABLE = sandbox wall (egress/browser/COM); must cite the blockers.md entry, and goal stays open.
3. IN-PROGRESS = measurement taken against an in-flight claim; log delta vs target.
4. Use `python memory/verifier/verify_log.py --agent X --goal ref --cmd "..." [--assert grep-pattern]` to record — it runs the command, captures exit code, appends the line, and prints the entry.
5. Log must stay parseable: every line valid JSON (checked by `--check`).

## Scope note
Live-portal legs (:8099/:8888) are NOT-TESTABLE from sandbox seats — see memory/ops/blockers.md; static/file-based acceptance is testable here.
