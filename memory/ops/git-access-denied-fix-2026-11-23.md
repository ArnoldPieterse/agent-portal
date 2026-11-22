# Git "Access is denied" — root cause, fix, popup fallback (2026-11-23)

## Symptom
Every non-elevated launch of the only full git on this box failed:
`error launching git: Access is denied.` (rc 1 out of `cmd\git.exe`). The fleet-throughput
commit was left pending because of this; it eventually landed via the portal's auto
post-turn sync / 15-min safety-net commits.

## Diagnosis chain
1. `cmd\git.exe` in hermes' git tree is a 46 KB **launcher stub**; the real binary is
   `mingw64\bin\git.exe` (4.3 MB). The stub's own CreateProcess on it failed — hence the
   message comes from *inside* the stub, and other exes launched fine.
2. That file's DACL was locked down: only `SYSTEM:(F)`, `Administrators:(F)`,
   `OWNER RIGHTS:(F)` — no entry for White, while every parent directory grants White F.
3. Elevated `icacls /T /grant WHITE\White:(OI)(CI)F` reported "10123 files, 0 failed",
   but the grant was **absent from that file's DACL minutes later** — something
   re-locks (or strips the ACE from) this one file. Setting the integrity label to Medium
   did not help either. Root cause = the locked-down DACL on `mingw64\bin\git.exe` itself.

## Fix (deployed, verified)
- One elevated `robocopy` of the whole tree → **`C:\Users\White\git-portable`**
  (384 MB, normal ACLs: White has F). Verified non-elevated:
  `git version 2.53.0.windows.3`; status/log/add/commit all work from it.
- All git ops should use this copy. Grep verified no code hardcoded the old hermes path.

## Popup fallback (the "so we don't get access denied" mechanism)
`git_run.py` (repo root, allowlisted in .gitignore): runs git normally via the portable
copy; if any launch hits access-denied it **automatically retries elevated** — Windows
shows a UAC consent popup, click Yes, and output + exit code come back to the caller.
Usage: `python git_run.py <git args...>` (cwd is inherited). Exit code = git's exit code.

## Housekeeping in the same pass
- Root `goal_ledger.py` EVIDENCE_PAT tightened: the old pattern matched the words
  "verified"/"acceptance"/"evidence"/"recorded" **anywhere** in a line, so
  acceptance-criteria text inside an open goal counted as proof (phantom 78/80 reached).
  Now only explicit closure markers count — inline `(verified: ...)` or a
  `— recorded <date>` stamp — the same strict pattern memory/researcher/goal_ledger.py
  uses. True state after tightening: **11/78 (14%)** per the root module.
  (Note: the researcher module still reports 25/78 — the two parsers differ in scope;
  the portal uses the researcher one, so fleet numbers are unaffected.)
- `goal_ledger.py` and `git_run.py` added to the .gitignore allowlist.
