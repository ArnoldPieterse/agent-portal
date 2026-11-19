# KB Freshness Policy (Cycle 5)

Owner: Archivist | Drafted: 2026-11-19 (Orchestrator assist) | Status: Active

## TTL Definitions

| Entry Type | TTL | Rationale |
|---|---|---|
| **fact** | 90 days | Factual claims (API endpoints, host configs, model names) change with fleet evolution; 3 months is a reasonable staleness boundary. |
| **opinion** | 30 days | Recommendations, design choices, and assessments become outdated quickly as context shifts. |
| **procedure** | 180 days | Runbooks and procedures are stable but can drift when tooling changes; 6 months forces re-validation. |
| **spec** | 90 days | Interface/protocol specs change with implementation; aligns with fact TTL. |
| **report** | 30 days | One-off analyses, audits, and benchmarks lose relevance fast. |

## Classification Rules

Auto-classify by filename/heading heuristics:
1. Filename contains `runbook`, `recovery`, `procedure`, `howto` → **procedure**
2. Filename contains `audit`, `report`, `benchmark`, `scan`, `digest` → **report**
3. Heading or first line mentions `spec`, `protocol`, `interface`, `api-ref` → **spec**
4. Content is predominantly declarative (facts, numbers, names) → **fact**
5. Default → **opinion** (most conservative TTL)

## Sweep Mechanics

- Script: `python memory/archivist/freshness_sweep.py`
- Runs on demand or via health_check cron (every 24h recommended)
- Flags entries past TTL as `EXPIRED` in output report
- Expired entries get a review tag; they are NOT auto-deleted
- Output: `memory/archivist/freshness-sweep-YYYY-MM-DD.md`

## Action on Expiry

| Severity | Action |
|---|---|
| Past TTL, <2× TTL | Flag for review; add `[STALE]` marker in frontmatter if present |
| Past 2× TTL | Escalate to owner for explicit keep/refresh/archive decision |
| Past 3× TTL | Recommend archival (move to `memory/archivist/archive/`) |

## Exceptions

- Files under `memory/*/archive/` are exempt (already archived)
- `INDEX.md` files are exempt (structural, not content)
- Files with explicit `ttl: none` in frontmatter are exempt

---
*This policy is the SSOT for freshness decisions. The sweep script implements these rules mechanically.*
