# Outlet - Platform Connection Runbook (goal #10) - EVIDENCE 2026-11-26

Deliverable: memory/outlet/platform-connection-runbook.md (concrete target = Bluesky, the
registered FLEET-TEMPLATE profile; generic shape for other platforms).

Executability discipline: EVERY numbered step is either a runnable command or an explicit
[HUMAN] action for Arnold. Companion tool memory/outlet/platform_connect.py enforces this:
  - audit-runbook: parses steps (STEP_NUM_RE), strips code backticks, classifies each as
    COMMAND (python/py/elev.py/schtasks/git/bsky/ls/test) or [HUMAN]; PASS only if >=1 step and 0 prose-only.

Verification (all run this pass):
  python memory/outlet/platform_connect.py audit-runbook -> '7 step(s), command-or-HUMAN 7, PROSE_ONLY 0 / PASS'
  python memory/outlet/platform_connect.py selftest     -> SELFTEST PASS:
    register_marks_live=True, register_idempotent=True, wired_missing_flagged=True,
    wired_present_ok=True, audit_runbook_pass=True (all in an isolated temp root).

Pre-wiring + safety:
  - register pre-wires the fleet-default profile row in profiles.md (idempotent; verified no-op on re-run).
  - Deliberately NOT run against the REAL registry: no account is actually connected yet, so marking it
    live would be a false claim. Confirmed real memory/outlet/profiles.md UNCHANGED (TEMPLATE row intact,
    no 'connected (pre-wired' marker present).
  - wired-check verifies a secret file exists WITHOUT printing its value; .secrets/ + .gitignore added so
    app passwords are never committed or shown.

Ship gate: step 7 is a [HUMAN] approval for Arnold to ship the first ready-for-human queue entry -
matches the 'nothing ships without human approval' hard line. Unblocks queue shipping on connection.
