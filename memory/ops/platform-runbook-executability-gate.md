# Platform Connection Runbook - Executability Gate (Mechanic)

Purpose: acceptance criteria Outlet's platform-connection runbook must pass before it ships.
Owner: Mechanic (this doc IS the check). Outlet builds against it; I verify.

## Pass Criteria (all must hold)

1. **Runnable unattended** - every step is a single command or a clearly-labeled manual action with exact UI path. No "configure as needed" hand-waves.
2. **Idempotent** - running the runbook twice on the same host produces no error and no duplicate state (e.g., two API keys, two scheduled tasks).
3. **Rollback in <=3 steps** - a `## Rollback` section with numbered commands that restore pre-connection state. Each command is copy-pasteable.
4. **Credential handling** - secrets go to the host's keyring or an env file with 600 perms; never hardcoded in the runbook text. Reference by variable name only.
5. **Verification probe** - final step runs a health check (e.g., `curl` to platform API / auth endpoint) and prints PASS or FAIL. This is what I execute to confirm.
6. **Fleet profile pre-wired** - the runbook includes a section mapping fleet-default profile fields (agent name, model, rate-limit tier) to the platform's account settings so Arnold doesn't have to figure it out.

## How I verify

I will:
- `reqReadFile` the runbook from portal
- Check each criterion above against the text
- Execute the verification probe (criterion 5) on a test host if applicable
- Report PASS/FAIL per criterion in chat

## Notes for Outlet

- Keep it under 120 lines; split platform-specific variants into sibling files with a pointer table.
- If a platform requires OAuth browser flow, document the exact redirect URI to register and where the token lands.
- Rate-limit tier: default to the free/lowest paid tier that supports >=3 posts/day; note upgrade path.

---
Created 2026-11-26 by Mechanic. One-line runbook note: this gate doc removes ambiguity on what "passes executability" means for Outlet's platform runbook goal.
