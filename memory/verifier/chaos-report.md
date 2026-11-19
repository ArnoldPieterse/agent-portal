# Chaos Engineering Lite Report

Run: 2026-11-19 17:58:10Z
Duration: 2.03s
Result: 4/4 scenarios passed

| # | Scenario | Passed | Detail |
|---|---|---|---|
| 1 | A: kill-portal-mid-request | YES | clean URLError caught (no unhandled exception) |
| 2 | B: corrupt-agents-restore | YES | corrupt caught (JSONDecodeError), restore+reparse OK |
| 3 | C: disk-full-path | YES | clean PermissionError caught when writing to bad path (no crash) |
| 4 | D: tcp-timeout | YES | clean timeout caught (TimeoutError), no unhandled exception |

## Summary: ALL PASS
