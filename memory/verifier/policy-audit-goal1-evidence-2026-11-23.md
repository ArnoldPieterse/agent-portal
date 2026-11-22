# Decision Policy Compliance Audit - Evidence (Goal #1)

**Date:** 2026-11-23
**Script:** `memory/verifier/policy_audit.py`
**Self-test:** 12/12 PASS
**Real audit:** FAIL (by design - found real violation)

## What was tested:
- Scanned 16 entries across `decision-log.jsonl` (root) and `memory/ops/decision-log.jsonl`
- Classified: 3 remediation actions, 13 exempt (playbook/cycle/selftest)
- Rules checked: R001 (model_swap)

## Findings:
| Check | Severity | Entry | Detail |
|-------|----------|-------|--------|
| P3 (preconditions) | advisory | agent=nonexistent-agent-xyz, ts=22:03:31 | No precondition evidence in log |
| P4 (rollback) | advisory | same entry | No rollback reference |
| **P5 (failure w/o rollback)** | **hard** | same entry | Failed model_swap (`agent_not_found`) with no rollback triggered or waiver documented |

## Verdict:
Audit mechanism is functional and correct. The hard violation is a genuine finding in the decision log: an agent named "nonexistent-agent-xyz" attempted a model swap that failed without triggering the policy-mandated rollback (R001.rollback = restore_original_model). This was likely a test entry but should have been logged with `dry_run` type or had a waiver note.

## Artifacts:
- `memory/verifier/policy_audit.py` (audit script, 14KB)
- `memory/verifier/policy_audit_report.json` (machine-readable report)
- Self-test: 12/12 green (T1 exempt, T2 P5 catch, T3 dry-run pass, T4 P2 bounds, T5 compliant entry)