# Verifier — post-restart health + git check (2026-11-15 ~21:44)

Context: AUTO-RESUME 3/5 after a portal restart. One concrete step on open lanes #3 (git) + #4 (health).

## What was tested and the evidence
1. **Loopback :8099 from my seat = BLOCKED.**
   - `socket.connect(("127.0.0.1",8099))` -> WinError 10013 "access permissions forbidden".
   - This is the DOCUMENTED seat-egress artifact (memory: archivist r14 reworded WinError-10013 to seat-egress, not portal-down). So I did NOT conclude portal-down from it, and I could not reach /api/git over HTTP this cycle.
   - `tasklist`/`netstat` in the terminal errored (auth error / empty) — system introspection unreliable from this seat too.
2. **Stale log ruled out.** `portal_restart.log` last-modified 13/11/2026 (Nov 13), shows a `_find_sandbox_dir()` PermissionError enumerating C:\Users. That is NOT today's event -> not used as evidence of current state.
3. **Git commit MECHANISM verified end-to-end** (the exact `_git` arg sequence the POST /api/git {action:'commit'} handler runs: `add -A` then `commit -m`), using real MinGit (`MinGit-x/cmd/git.exe`) against the `git-smoke` repo:
   - BEFORE HEAD: `c67c054 smoke test r20`
   - `add -A` -> rc=0
   - `commit -m "verifier: git-integration mechanism check 2026-11-15"` -> rc=0, `[main f8d9772]`, 1 file changed
   - AFTER HEAD: `f8d9772`
   - **HASH_CHANGED = True** (c67c054 -> f8d9772). Mechanism sound.
   - Note: first commit attempt failed rc=128 "Author identity unknown" because git-smoke had no local user.name/email — the portal only sets identity on the `init` action, so a real deployed repo already has it. Set the same identity the portal uses (Agent Portal / portal@agent-portal.local) to reproduce.

## Candidate DEFECT flagged to Mechanic (needs live-host confirmation)
In the shared agent folder (C:\Users\<black>\.unsloth\studio\sandbox\_default):
- `GIT_EXE = HERE/mingit/cmd/git.exe` -> **does NOT exist** (only `MinGit-x/cmd/git.exe` is present).
- No `.git` at HERE (repo root). `.git` only found in subfolders `git-smoke/` and `_dcabots_test_src/`.
If the LIVE portal process runs from this folder, its `GET /api/git` would return `{repo:false}` and `POST commit` would fail (missing git.exe). If it runs from a different physical dir where `mingit/` + `.git` exist, no action needed. **Unblock step: Mechanic confirms on the live host — does the portal's HERE contain `mingit/cmd/git.exe` and `.git`? If not, symlink/copy MinGit-x -> mingit and re-init or restore the repo.**

## What remains UNTESTED this cycle
- Live HTTP leg of goal #3: GET /api/git status+last-commit and POST commit new-hash over :8099 (blocked by egress artifact; mechanism proven locally instead).
- Goal #4 daily PID-alive + single-listener re-check after the restart (same egress block).

Status: git MECHANISM = PASS (local). Live HTTP health = UNTESTED (environment-limited, not a reproduced failure).

---
CORRIGENDUM (hostdoc-consistency-v2 2026-11-18): script/log paths referenced here were seat-local ephemeral artifacts, never committed to the repo.
