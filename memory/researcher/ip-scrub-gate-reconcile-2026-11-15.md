# Researcher — IP-scrub human gate: count reconciliation + functional-IP evidence (2026-11-15)

Scope: resolve the 85/96/~50 discrepancy on "tracked files with internal IPs" and verify the functional-IP caveat before the human decides scrub vs leave.

## Measured (White host, full shared tree scan, all file types)
- **146 files / 429 occurrences** of `192.168.x.x` in the local shared tree.
- Breakdown: .md=85, .html=24, .py=14, .json=13, .bak/.txt/.cnf/.dist/none=7.
- By top dir: memory/=66, root=18, uploads=11, AgentPortal_V1-git=10, gapfix-test=10, _boot2=10, _bootstrap_test=10, truncation-probe=7, Mingit=4.

## Why the team's numbers differ (all correct, different scopes)
- Archivist **85** = .md files only.
- Mechanic **96** = .md/.py/.json/.txt across whole tree.
- Verifier **86/201** = top+memory subset only (Black host).
- My **146** includes per-host local junk (test dirs, Mingit install) that is NOT in the repo.

## Repo-scope estimate
- GitHub API root listing of `ArnoldPieterse/agent-portal` main confirms tracked root = portal core files + memory/ only; local junk dirs are not tracked.
- Excluding non-repo dirs: **≈84 tracked files** in scope (146 − 62 in local-only dirs).
- Exact `git grep` count vs live HEAD could NOT be run from this sandbox: local clone `AgentPortal_V1-git` is stale (last commit ec37a1fa, 2026-11-12; broken main ref) and network fetch fails (`getaddrinfo() thread failed to start` — sandbox libcurl limit). Needs Orchestrator's live repo or the human's machine for a definitive count.

## Functional-IP caveat (evidence, not hearsay)
- **agents.json** (TRACKED, confirmed in API): 6 IPs = studio URLs (`http://192.168.1.{99,39,245}:8888`) for Black/Pale/Red. Redacting in place would break agent→studio routing → needs placeholder + gitignored local override (same pattern as hosts.md).
- **memory_mirror_hosts.json** (root; tracked status unconfirmed — API listing truncated): 3 IPs **plus per-host usernames** (`Red`/`pale`/`black`). Same exposure class as the human-deleted `hosts.md`.
- **memory_mirror.py / agent_portal.py: 0 IPs** — no scrub concern there.

## NEW finding for the human gate
The human deleted `memory/llm/hosts.md` on GitHub to stop the leak, but if `memory_mirror_hosts.json` is tracked, **the same host table (IPs + usernames) is still public through a different file**. The scrub decision should explicitly include: untrack+gitignore `memory_mirror_hosts.json` and token-ize `agents.json`, not just redact doc .md files. History note: if any commit ever carried these, in-place redaction leaves them in history (purge = force-push rewrite).

Confidence: high on local-tree measurements (direct file reads); medium on "≈84 tracked" (API-confirmed root subset + memory/ proxy; untracked-vs-tracked per-file not verified without live git).
