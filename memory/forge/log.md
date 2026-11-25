# Forge run log

| date | event | result | evidence |
|------|-------|--------|----------|
| 2026-11-25 | Red host powered on (human broadcast) | ACK - red reachable; unblocks Scribe+Mechanic home seats, restores 4-host probe coverage for smoke suite | user message um-20261125-125759 |
| 2026-11-25 13:08 | smoke_suite: smoke_suite: PROBE FAILED (elev.py or network error) |
| 2026-11-25 13:12:18 | smoke_suite: FAILURES (4 hosts, 4 issues) |
| 2026-11-25 14:16:00 | smoke_suite: FAILURES (4 hosts, 4 issues) |
| 2026-11-25 14:18:23 | canary_deploy: START canary=White file=_canary_test.txt sha=1c7de0d250b63b2c |
| 2026-11-25 14:18:25 | canary_deploy: SUCCESS: _canary_test.txt deployed to all 4 hosts (canary=White) |
| 2026-11-25 14:32:52 | smoke_suite: FAILURES (4 hosts, 4 issues) |
| 2026-11-25 14:36:15 | canary_deploy: START canary=White file=_perf_test_file.txt sha=2bb644d7127d0892 |
| 2026-11-25 14:36:17 | canary_deploy: SUCCESS: _perf_test_file.txt deployed to all 4 hosts (canary=White) |
| 2026-11-25 14:37:49 | gate_health: ALL GATES HEALTHY |
| 2026-11-25 14:45:56 | smoke_suite: REMEDIATING White - TCP: PermissionError: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions |
