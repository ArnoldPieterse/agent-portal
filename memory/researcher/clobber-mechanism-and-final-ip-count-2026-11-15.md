# Researcher — mirror-clobber mechanism resolved + final IP gate number (2026-11-15, from White)

Host: **White** (canonical). Both open measurement gaps closed as far as any sandbox can close them.

## 1. Clobber mechanism — RESOLVED with config evidence
- `memory_mirror.py` L36-55: push allowlist = `git ls-files` output (+ INTERNAL_ONLY hosts.md). Root docs (incl. **agent_portal.py**, **index.html**) are White-canonical: push on hash mismatch **regardless of mtime**; pull never touches them.
- GitHub trees API (`main`, sha 33162711): `agent_portal.py` **tracked** (blob 4b24d984, 95480 B), `index.html` tracked (be32d99d, 68569 B). => both are in every mirror push.
- **Consequence:** edits to these files made in remote sandboxes (Black/Pale/Red) can NEVER survive — White's copy re-serves them each ~5-min cycle. Every "regression" of the /api/provenance dead-code hunk reported this thread was pre-convergence mirror lag, not a new clobber source.
- Live pin on White: `agent_portal.py` sha `29ca92639845` (CLEAN — provenance block L1685-1691 returns in both branches; 0 IPs), mtime 14:12, stable since. `index.html` = `2ba6e29a9d35` (Designer v2 acceptance target).
- **Process rule (for Orchestrator/Mechanic):** root-doc edits land on White only (or via the mirror allowlist); remote-sandbox edits are write-only-vanishing. No further re-application of the dead-code fix is owed by anyone.
- Residual: upstream HEAD blob (95480 B) < local clean file (100915 B) => today's clean endpoints **not yet committed/pushed to GitHub**; public repo still shows the older portal. Next auto-commit/daily-commit on White closes it.

## 2. Final IP gate number — best estimate 85, bounded 85-148
- White full-tree scan this round: **114 files / 300 occ** (earlier same-round scan: 148). Delta = transient host-local dirs (`truncation-probe` 7, `uploads` 12, `_bootstrap_test` 10) that appear/disappear per sandbox activity.
- 114 - 29 (transient-dir files) = **85** — independently converges on Archivist's Pale full-tree count (85f/173o). Best estimate for the human gate: **~85 shared-surface files**; hard bounds 85 (clean surface) to 148 (White with all transients).
- Exact *tracked* count remains one command on White: `git grep -l "192\.168\." | wc -l` (Orchestrator has mingit + AgentPortal_V1-git; clone is stale 11-12 so needs a fetch first, or run on human's machine).
- Special cases that must be named in the scrub decision:
  - `agents.json` — tracked PUBLIC, **6 IPs** (functional: agent->studio routing breaks if redacted in place; use placeholder + gitignored local override).
  - `memory_mirror_hosts.json` — PUBLIC (raw 200 on main, verified last round), **3 IPs + per-host usernames**; deliberately allowlisted (`!` entry) for memory_mirror.py's internal operation. Deleting hosts.md did NOT close this leak class.
  - `index.html` — tracked, 1 IP occurrence.
  - `agent_portal.py` — clean, 0 IPs (nothing to scrub).

## Corrections to my own record
- Last round's "~84 tracked" was an unverified estimate; superseded by the bounded 85-148 with best estimate 85 above.
- The "mirror clobber bug" framing in earlier rounds is corrected: it is **by design** (White-canonical one-way push); the defect was agents editing non-canonical copies, which has now been ruled on by Orchestrator.
