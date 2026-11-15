# Synthesis — public-repo internal-IP decision (2026-11-15)
Scribe. Supersedes the inline "DECISION NEEDED" bullet at top of TODO.md for this one open gate.

## State of the thread (all done, verified by Orchestrator on host)
- Repo `github.com/ArnoldPieterse/agent-portal` is LIVE + PUBLIC; history pushed ~13:0x, in sync rev-list 0/0. Detail: memory/ops/public-repo-agent-portal-2026-11-15.md.
- Human's deletion of `memory/llm/hosts.md` merged (21c2627); restored locally but UNTRACKED (.gitignore) so auto-sync can't re-publish; `memory_mirror.py` INTERNAL_ONLY keeps it flowing to fleet remotes (ef5e890).
- Pre-push secret scan of 446 tracked files: clean (real keys already `[redacted]`).

## The ONE open item — human decision, not agent work
Tracked files still carry internal LAN IPs. **Nothing is truncated/empty for the team to finish; this is a gate on the human.**

### Scribe's scan of the working mirror (2026-11-15)
- 116 files contain internal IPs in the local mirror copy (upper bound — includes UNTRACKED probe scripts / .bak HTML candidates). The leaf's "~50" was `git ls-files`-tracked only; exact tracked count needs a host-side `git grep` (git not available in Scribe sandbox).
- Distinct IPs, ALL RFC1918 private-range: 192.168.1.{1,50,179,245,39,99}. No public IPs, no secrets — exposure is internal topology + host-role mapping only.

### The catch that reframes the options (flag, not a pick)
"Scrub in place" is NOT free. These LIVE files need the real IPs to operate the fleet:
- agents.json, memory_mirror_hosts.json, fleet_reload.py, reboot_recover.py (mirror + boot reload target the hosts by IP)
- fleet_probe_r21.py, lan_probe.py, host_api.py, black_dual_load2.py, pale_dl.py (probes/loads hit hosts by IP)
Redacting them in place would break the internal mirror/probes/reload. So the realistic choices are:
1. **Leave as-is** — zero functional cost; RFC1918-only, low real-world risk.
2. **History purge** (rewrite + force-push) — only option that removes IPs without breaking live scripts; DISRUPTIVE: breaks remote checkouts and the mirror's git-derived allowlist until all hosts re-clone.
3. Redact in place — REJECTED as a standalone path: breaks the fleet (see catch).

## Owner + next action
- OWNER: human (decision gate). Scribe recorded; no agent may scrub/purge without explicit OK.
- If human wants an exact tracked-file count before deciding: ask Orchestrator/Researcher to run `git grep -lE '\b(?:192\.168|10)\.[0-9]{1,3}\.[0-9]{1,3}\b' -- $(git ls-files)` on the host (Scribe sandbox has no git).

## Standing rule (unchanged, all agents)
No real secrets/tokens/keys into ANY tracked file — redact as `[redacted]` before commit; daily-git + post-turn syncs publish automatically. IPs are a separate, lower-severity question from secrets.
