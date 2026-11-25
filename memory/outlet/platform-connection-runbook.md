# Platform Connection Runbook - connect a platform account to the fleet default profile
Date: 2026-11-26. Owner: Outlet. Target example: Bluesky (the registered FLEET-TEMPLATE profile). Other platforms follow the same shape.

Purpose: connect one platform account so Outlet can ship approved queue entries with the fleet-default profile pre-wired. Every step below is either a runnable command or an explicit [HUMAN] action for Arnold - that discipline is what makes this pass the executability audit (every step = a command or a named human action).

## Steps
1. `python memory/outlet/platform_connect.py register --platform bluesky --handle @fleet.example`
2. [HUMAN] Arnold - open https://bsky.app and log in to the target account.
3. [HUMAN] Arnold - go to Settings -> Apps and passwords -> create an app-specific password (label it "outlet-fleet").
4. [HUMAN] Arnold - place that app password at memory/outlet/.secrets/bluesky.txt with owner-only permissions; do NOT paste the value into chat.
5. `python memory/outlet/platform_connect.py wired-check --platform bluesky`
6. `python memory/outlet/queue_check.py`
7. [HUMAN] Arnold - approve the first ready-for-human queue entry to ship (human approval gate; nothing ships before this).

## Verify
Run `python memory/outlet/platform_connect.py audit-runbook` - PASS means every step is a command or a [HUMAN] action (no prose-only steps). Run `python memory/outlet/platform_connect.py wired-check --platform bluesky` after step 4 to confirm the account is wired before shipping.

## Rollback
To disconnect, delete memory/outlet/.secrets/bluesky.txt and set the platform row's Status back to "awaiting connection" in memory/outlet/profiles.md. No fleet state changes on disconnect - only the secret file and one registry cell.
