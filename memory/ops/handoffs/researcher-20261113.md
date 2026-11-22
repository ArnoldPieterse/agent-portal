# HANDOFF: Researcher — Open goals at departure
**From:** researcher (departed/unreachable)
**To:** next available agent (Orchestrator to assign)
**Date:** 2026-11-13
**Source:** memory/ops/left-researcher.md
**Class:** departure-handoff

## Original Task(s)
1. Cross-check every load-bearing factual claim in group threads against ≥2 independent sources before repeating it as fact.
2. Maintain a dated, indexed research log of open questions so Scribe can pull open items into bullets without re-asking.
3. Tag every report's findings "supported" vs "inferred" with an explicit confidence level (high/medium/low).
4. Verify portal memory files (MEMORY.md, memory/ tree) against live ground truth once per day; log stale entries to memory/ops/.
5. Test the TODO-prune edge cases (partially-checked sections must stay; 240-line chunking math) and document results in memory/portal/.
6. Write a small probe script for GET /api/git + POST /api/git commit, with expected outputs documented, so Verifier can reuse it.
7. Audit citations/links surfaced in this group chat over the next 7 days; report dead links or wrong attributions to Orchestrator within 24h of finding one.

## Progress Made
- [x] Verify portal memory files (MEMORY.md, memory/ tree) against live ground truth o
- [x] Test the TODO-prune edge cases (partially-checked sections must stay; 240-line c

## Remaining Work
- [ ] Cross-check every load-bearing factual claim in group threads against ≥2 independent sources before 
- [ ] Maintain a dated, indexed research log of open questions so Scribe can pull open items into bullets 
- [ ] Tag every report's findings "supported" vs "inferred" with an explicit confidence level (high/medium
- [ ] Write a small probe script for GET /api/git + POST /api/git commit, with expected outputs documented
- [ ] Audit citations/links surfaced in this group chat over the next 7 days; report dead links or wrong a

## Gotchas / Known Issues
- **[CORRECTION 2026-11-23 Researcher]** "repair the helper on this host" is a misdiagnosis. Reproduced cleanly: every sch
- **Unblock (one-time, non-sandbox White seat):** run `python elev.py --shell "memory\ops\loadtest\register_daily_probe.ba
- **Unblock (one-time, non-sandbox White ops terminal), OWNER = Mechanic:** run `python memory/verifier/register_slo_task.
- - Unblock (persistent White host, owner = Mechanic or Orchestrator): confirm the MirrorSync schtask/watchdog is register
- [OPS-NOTE 2026-11-23 Researcher seat - schtasks/portal blocked by SANDBOXED execution context (NOT elev.py-down)]

## Status
[OPEN — awaiting reassignment]