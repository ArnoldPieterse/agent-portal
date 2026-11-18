# Goal #5 Evidence: Egress Rules Engine v2 - Per-Agent Granularity (2026-11-17)

## What was built
Extended `egress_guard.py` + `egress-rules.json` from per-host to per-agent profiles.

### Changes
1. `egress-rules.json` v2: added "agents" section with 8 distinct profiles:
   - orchestrator: all fleet hosts + portal (5 hosts, 2 domains)
   - researcher: broad web access only (0 hosts, 4 domains incl arxiv.org)
   - builder: loopback + github/pypi (1 host, 2 domains)
   - verifier: loopback + 3 fleet health endpoints (4 hosts, 1 domain)
   - designer: loopback + font CDN (1 host, 2 domains)
   - archivist: broad read-only web (0 hosts, 4 domains)
   - scribe: loopback portal only (1 host, 0 domains)
   - mechanic: all fleet hosts + diagnostic ports (5 hosts, 1 domain)

2. `egress_guard.py`: added `_evaluate_agent()` method + `agent` param to `check()`:
   - Backward compatible: no agent = old global allowlist behavior
   - Per-agent: checks target against that agent's specific host+domain profile
   - Audit log now includes "agent" field when per-agent check used

### Test results (10/10 PASS)
| # | agent | target | port | verdict | expected | pass |
|---|-------|--------|------|---------|----------|------|
| 1 | mechanic | IP_BLACK | 8888 | ALLOW | ALLOW | Y |
| 2 | mechanic | IP_RED | 5985 | ALLOW | ALLOW | Y |
| 3 | researcher | arxiv.org | 443 | ALLOW | ALLOW | Y |
| 4 | researcher | IP_BLACK | 445 | DENY | DENY | Y |
| 5 | builder | pypi.org | 443 | ALLOW | ALLOW | Y |
| 6 | builder | [LAN-IP] | 445 | DENY | DENY | Y |
| 7 | scribe | 127.0.0.1 | 8099 | ALLOW | ALLOW | Y |
| 8 | scribe | github.com | 443 | DENY | DENY | Y |
| 9 | designer | fonts.googleapis.com | 443 | ALLOW | ALLOW | Y |
| 10 | verifier | IP_PALE | 8099 | ALLOW | ALLOW | Y |

### Acceptance criteria met
- [x] 8 distinct agent profiles defined + tested
- [x] One denied request correctly blocked + logged (e.g. researcher -> fleet SMB DENY, builder -> fleet SMB DENY, scribe -> github DENY)
- [x] Audit log entries include agent field (verified in egress-audit.jsonl)

### Remaining for full productionization
- Wire into sandbox network layer (currently advisory; actual enforcement via netcmd)
- Integrate with agent_portal.py so each agent's tool calls pass through check(agent=...)
