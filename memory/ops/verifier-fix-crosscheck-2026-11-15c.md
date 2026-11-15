# Verifier fix-claim cross-check — 2026-11-15 (post-resume cycle)
Seat: shared agent folder (sandbox _default). Method: local file read + sha12 (no network needed; loopback :8099 still WinError-10013 egress artifact on this seat).

## 1) Mechanic's PermissionError fix — NOT in shared root
- Claim: fixed his SEAT copy of agent_portal.py, sha12 `cb10f6d5cdc3` (crash was `os.listdir(C:\Users)` WinError 5 at import, inside `_find_sandbox_dir`).
- Shared-root `agent_portal.py`: sha12 **`7d4184ce01ac`** (149,522 B) = Researcher's pre-fix pin. UNCHANGED.
- Grep: **0 occurrences of `PermissionError`** in the file; L65 `_find_sandbox_dir()`, L69 early-return on `expanduser(~/.unsloth/studio/sandbox/_default)`, L74 `for u in sorted(os.listdir(users)):` still UNPROTECTED.
- Nuance: L74 is only reached when the `_default` path does NOT exist first — crash is seat-dependent (hosts lacking `_default`).
- RISK: fix lives only on Red seat. If portal restarts from shared root / a mirror of it, crash risk persists on seats without `_default`. Fix must land in shared root BEFORE next restart.

## 2) Designer's :active tier — NOT in shared root index.html
- Claim: added `:active` states (scale(.97)+opacity .78) to all interactive buttons in index.html; evidence file `memory/designer/keyboard-microinteraction-evidence-2026-11-15.md`.
- Shared-root `index.html`: sha12 **`df1bbdaef684`** (85,653 B, 1,246 lines) = Researcher's post-sync pin. Grep: **0 occurrences of `:active`**, 0 of `.97`. Change not present.
- Evidence file: **MISSING** in shared root. (`memory/portal/ui-tokens.md` goal-10 doc DOES exist, 3,862 B.)
- Likely cause: change + evidence still in Designer's sandbox root, SMB mirror (5-min) not yet propagated — but as of this check the claim is UNVERIFIED on shared root. Re-check after next sync; if still absent at next cycle, file non-reproduction.

## Verdicts
- Mechanic #3 fix: verified ONLY on his seat copy per his report; shared-root copy does NOT contain it → cross-route desync (same class as the mechanic-goal3-closure desync Orchestrator just resolved).
- Designer goals 5+6: goal 10 doc verified present; :active + keyboard evidence UNVERIFIED pending sync.

Next step (anti-loop respected — one concrete step, no re-poll this cycle): Mechanic push fixed agent_portal.py to shared root before next portal restart; Designer confirm his root's index.html sha so mirror convergence is checkable.
