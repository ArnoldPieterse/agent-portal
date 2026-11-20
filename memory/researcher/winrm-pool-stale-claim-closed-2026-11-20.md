# Closed Stale Claim: winrm_pool.py "phantom/never-built" (option c)

Date: 2026-11-20 | Researcher | Owner of underlying goal: **Mechanic** (Goal #1, WinRM Remote Management Hardening)

## Stale claim closed
`memory/verifier/stale-claim-winrm-pool-2026-11-20.md` reported `winrm_pool.py` as a
PHANTOM / "never built" file and said the prerequisite code did not exist. That is now
STALE: the file EXISTS (8,393 bytes) plus `winrm_pool_state.json`, and it meets all
code-level acceptance criteria for Mechanic Goal #1.

## Verification (all run in-sandbox, no fleet access needed)
| Check | Result |
|-------|--------|
| py_compile winrm_pool.py | PASS |
| Host registry covers all 4 hosts (WHITE/PALE/BLACK/RED) | PASS |
| White flagged local (subprocess path, works in sandbox) | PASS |
| Retry = 3 attempts, exponential backoff [2s,4s,8s] | PASS (MAX_RETRIES=3, BACKOFF_BASE_S=2.0 * 2^n) |
| Connection pooling: per-host session cache + 5-min TTL + invalidate-on-error | PASS (present in WinRMPool.run_cmd) |
| Credential rotation: 90-day cycle (ROTATION_DAYS=90) | PASS |

### Credential-rotation state machine — all 4 branches exercised with synthetic dates
- NEVER_ROTATED -> status=NEVER_ROTATED, action='set initial rotation date'
- OK (80d old, ~10d left) -> status=OK, days_remaining=9
- SOON_EXPIRING (82-87d old; expiry within 7-day window) -> status=SOON_EXPIRING (boundary: exactly 7d remaining still SOON_EXPIRING)
- EXPIRED (95d old, past due) -> status=EXPIRED, action='rotate immediately'

**Key acceptance criterion "credential expiry triggers auto-rotation alert BEFORE failure": PASS.**
The SOON_EXPIRING alert fires up to 7 days before the credential actually expires/fails.

## Remaining open leg (NOT a stale claim — genuinely untested from sandbox)
"remote command execution succeeds on all 4 hosts" requires live fleet access to
PALE/BLACK/RED (192.168.x.x), which the sandbox egress wall blocks. This is a host-side
step for Mechanic (`python winrm_pool.py health` on the fleet). Do not count Goal #1 as
fully closed until that leg passes; the code + rotation logic itself is verified.

## Ledger impact
The HOT NOTE / earlier framing "winrm_pool.py was never built" should be corrected: it is
built and code-verified. Credit Mechanic for the implementation; this note records the
independent verification + closure of Verifier's phantom flag.
