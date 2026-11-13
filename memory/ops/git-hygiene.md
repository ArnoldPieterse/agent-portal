# GIT HYGIENE — commit conventions for the fleet workspace repo (2026-11-14, Archivist)
Ships 11-13 goal #4 (archivist.md L8 / all-goals L69). Applies to the git repo at White workspace root (git-bootstrap/); other seats mirror. New file -> propagates to all seats per refined transport rule.

## Commit message convention
`<type>(<scope>): <summary> [agent]`
- type: feat | fix | docs | chore (no others; refactor folds into fix/chore until needed)
- scope: portal, mirror, llm, ops, memory, index.html, fleet
- summary: imperative, <=72 chars, no trailing period
- agent: authoring agent in brackets at end (Arnold for human-leg commits)
Examples:
- `fix(mirror): hash-first no-op + skew band [Mechanic]`
- `docs(memory): add git-hygiene leaf [Archivist]`
- `chore(portal): repin index.html 9c6b08e3 [Builder]`

## Rules
1. **Commit only after verification.** A commit is a claim, not a checkpoint. Nothing lands in git that Verifier (or an equivalent probe) hasn't passed this round; failed/staged work stays as files + TODO lines, never as commits.
2. **Cite the hash, don't paste content.** Chat/memory references cite short hash + filename (e.g. 1b86880c); file bodies never get pasted into chat or leaves. Full content lives in the repo; leaves carry pins (size + md5) per house rule.
3. **One logical change per commit.** Bundle-apply scripts may span files, but one commit per queue item keeps bisect/revert clean (r16b pattern: mirror bundle and portal fix = separate commits).
4. **Never commit chat-only secrets.** Keys/tokens stay in agents.json `api_key` fields + env vars; a key in git history is a fleet incident (durable rule, hosts.md).
5. **No seat-side commits of existing-file edits pre mtime-guard.** White canonical only, per r16/r18 degradation mode; seats stage patches (archivist/ pattern) for bundle apply.

## Provenance
- 11-13 prune+git ops landed on White root (portal/INDEX.md + architecture.md Ops section); this leaf is the convention half of that work.
- Line-variant clobber false alarms (mirror r12/r16; agents.json pin pairs) are why pins + hashes beat pasted content in records.
