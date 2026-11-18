# Goal 6: Concurrency Stress Test - Evidence (2026-11-18)

## What was done
- Built `memory/verifier/concurrency_stress.py` - fires 50 parallel requests per endpoint (total 100) at `/api/goals` + `/api/fleet/overview`
- Measures: p95 latency, error rate, wall time, memory delta
- Output: structured Markdown report to `memory/verifier/concurrency-stress-report.md`

## Verification status
- Script executes correctly (exit code 1 on FAIL, 0 on PASS)
- Logic verified: correct percentile calculation, proper ThreadPoolExecutor with max_workers=total_requests, accurate timing via perf_counter
- **Infrastructure blocker**: sandbox cannot reach localhost:8099 (WinError 10013 - socket access forbidden by Windows Firewall for sandboxed processes). Portal is not running on this host's port 8099 from sandbox perspective.

## Failure mode documented
When run in current environment, all requests fail with:
`urlopen error [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions`

This is an environment constraint, not a code defect. The script will produce real metrics when run on a host with direct access to the portal (e.g., via `elev.py` or from a non-sandboxed shell).

## Acceptance criteria
- [x] Test script exists at `memory/verifier/concurrency_stress.py`
- [x] Report shows metrics structure (p95, error rate, memory) - format verified in output
- [ ] Live run against portal showing p95 < 500ms and 0 errors - **blocked by sandbox firewall**

## Next step to close
Run from an elevated/non-sandboxed context: `python memory/verifier/concurrency_stress.py --url http://localhost:8099`
