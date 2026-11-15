# Public GitHub repo: agent-portal (2026-11-15)
Status: LIVE + reconciled 2026-11-15 ~13:2x. **Any tracked file in this workspace is now PUBLIC on the internet** - the post-turn auto-sync pushes every commit to origin/main.

## Facts
- Repo: https://github.com/ArnoldPieterse/agent-portal (public, main). Full history pushed 2026-11-15 ~13:0x; follow-up syncs through ~13:23 verified in sync (rev-list 0/0).
- Auth: Git Credential Manager browser sign-in as ArnoldPieterse (token in Windows Credential Manager - standard git behavior). Remote URL is plain https, no embedded creds. Temp token file deleted.
- Pre-push secret scan of all 446 tracked files: clean (real keys already `[redacted]` in agents.json/ops scripts).
- Unauthenticated reachability verified post-push: API 200 private=False, raw README 200, hosts.md 404.

## hosts.md handling (human deleted it on GitHub)
- Human removed `memory/llm/hosts.md` from the public repo (internal LAN host table: 192.168.x.x IPs + auth notes). Merge of their deletion landed locally (commit 21c2627).
- Local copy RESTORED but UNTRACKED: `.gitignore` line ~42 `/memory/llm/hosts.md` - auto-sync can never re-track it.
- `memory_mirror.py` got `INTERNAL_ONLY = ["memory/llm/hosts.md"]` appended to `_allowlist()` output (both git and fallback paths) so fleet remotes keep receiving it - the mirror allowlist is `git ls-files`-derived, so untracking alone would have silently stopped internal mirroring. Commit ef5e890.

## OPEN (human decision)
- ~50 OTHER tracked files still contain internal 192.168.x.x IPs (TODO.md, agents.json, memory/* notes). Human deleted only hosts.md - unclear if they want the rest scrubbed too. Repro scan: regex `\b(?:192\.168|10)\.\d{1,3}\.\d{1,3}\b` over `git ls-files`. Options: leave (LAN-only detail, low risk), redact in place (new commits, history keeps old copies), or purge history (rewrite + force push - disruptive). NOT done without human OK.

## Standing rule (all agents)
- No real secrets/tokens/keys into ANY tracked file. Redact as `[redacted]` before committing; the daily-git + post-turn syncs publish automatically.