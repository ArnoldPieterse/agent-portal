# Citation manifest (goal #9) — consolidated external-link audit

Last updated: 2026-11-15 post-restart (delta-check pass: 434 files scanned, 0 new URLs, all mtimes stable). Original consolidation: 2026-11-15 ~21:0x. Purpose: turn the 7-day citation audit (window set 11-13, closes ~11-20) from "re-scan 418 files each time" into "diff new external URLs against this 6-entry manifest." Delta-check only; do NOT re-resolve entries already marked verified unless a file changed.

## SCOPE RULE (what counts as an auditable citation)
- IN SCOPE = external PUBLIC internet URLs (resolvable by anyone, e.g. arxiv.org, github.com, lmstudio.ai, learn.microsoft.com).
- OUT OF SCOPE = internal fleet endpoints on 127.0.0.1 / localhost / 192.168.1.x at any port (:8099 portal, :8888 studio, :1235). These are host-internal routes, not citations; their liveness is a Mechanic/portal concern, not a dead-link finding.

## IN-SCOPE EXTERNAL CITATIONS (6) — all verified 2026-11-15
| URL | Location(s) (load-bearing source in bold) | Status | Last checked | Attribution check |
|-----|--------------------------------------------|--------|--------------|-------------------|
| https://arxiv.org/abs/2311.16542 | memory/researcher/citation-audit-2026-11-15.md | LIVE (SUPPORTED, high) | 11-15 re-fetched live | Correct — cited as the DPO paper behind the overnight-unload investigation |
| https://github.com/ArnoldPieterse/agent-portal | **memory/ops/public-repo-agent-portal-2026-11-15.md** + citation-audit file | LIVE (SUPPORTED, high) | 11-15 full-tree sweep | Correct — this project's own public repo |
| https://github.com/lmstudio-ai/lmstudio-bug-tracker/issues/2423 | **memory/llm/overnight-unload.md** + citation-audit file | LIVE (SUPPORTED, high) | 11-15 post-restart live re-verify | Correct — Bionic TTL-evict bug; leaf's #2423-vs-#1782 split (Bionic vs tray) confirmed right |
| https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict | **memory/llm/overnight-unload.md** + citation-audit file | LIVE (SUPPORTED, high) | 11-15 post-restart live re-verify | Correct — the TTL/auto-evict mechanism doc behind goal #10 answer |
| https://learn.microsoft.com/en-us/windows-server/administration/performance-tuning/role/file-server/ | **memory/researcher/sync-clobber-analysis-2026-11-13.md** + citation-audit file | LIVE (SUPPORTED, high) | 11-15 full-tree sweep | Correct — MS file-server perf-tuning ref for the SMB clobber analysis |
|  [redacted-tunnel-url] | **memory/llm/hosts.md** + citation-audit file | DEAD-now but EXPECTED (out of scope by design) | 11-15 full-tree sweep | Correct — ephemeral rotating Cloudflare quick-tunnel, documented as such in hosts.md WITH WinRM recovery path; not a dead-link finding owed |

Cumulative: **6 external citations → 5 live + correctly attributed, 1 dead-by-design (documented ephemeral tunnel). 0 dead / 0 wrong attribution.**

## OUT-OF-SCOPED INTERNAL ENDPOINTS (excluded from audit; for completeness)
Discovered in same sweep (20 distinct internal URLs): 127.0.0.1:{8099,8888} + localhost:{8099,8888,1235}; [redacted-lan-template,245,39,179}:8888/8099; :8099/api/{fleet,goals,memory,git} + /index.html; :8888/api/settings/{lan-access/start,model-aliases}, /models. All host-internal — liveness tracked by Mechanic/portal, not a citation finding.

## DATA-QUALITY NOTE (not a dead link)
- Malformed URL `http://[redacted-lan-template` (unterminated braces) present in memory/researcher/ip-scrub-gate-reconcile-2026-11-15.md. Internal placeholder with a typo; cosmetic, no action owed unless that file is published externally.

## DELTA-CHECK PROCEDURE for ~11-20 closure (goal #9)
1. Re-run the URL enumeration (web_search-free local grep) across memory/ → list distinct external URLs.
2. Any NEW external URL not in the 6-row table above = freshly-auditable: live-verify it + check attribution, log a finding within 24h if dead/misattributed.
3. If zero new external URLs appear and no file that hosts an existing citation was edited since its "last checked" date → goal #9 CLOSES with this manifest as the final artifact (0 dead / 0 wrong over the full window).
4. Do NOT re-resolve the 6 rows in step-2; only re-check a row if its source file's mtime is newer than its last-checked date.

Owner: Researcher. Closure gate: time-gated to ~11-20 OR earlier if any finding owed to Orchestrator.

## ADDED BY citation_monitor_v2 (2026-11-16)
| URL | Location(s) | Status | Last checked | Attribution check |
|-----|-----------|--------|--------------|-------------------|

## ADDED BY citation_monitor_v2 (2026-11-16)
| URL | Location(s) | Status | Last checked | Attribution check |
|-----|-----------|--------|--------------|-------------------|
