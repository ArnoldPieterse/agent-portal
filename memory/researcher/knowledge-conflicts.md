# Knowledge Conflict Report
Generated: 2026-11-23 (conflict_detector.py)
Scanned: 300 files, extracted 121 factual claims
Conflicts found: 4

## Conflict 1: black / vram

- **Values found:** 16, 32
- **Total mentions:** 2
- **Suggested resolution:** `16` (appears in 50% of mentions)

| Source | Line | Value | Context |
|--------|------|-------|---------|
| `\memory\builder\hotload-catalog-refresh-2026-11-22.md` | 5 | **16** | 2. GPU specs stale: all 4 hosts are 2× RTX 5090 32GB = 64GB  |
| `\memory\builder\hotload-catalog-refresh-2026-11-22.md` | 5 | **32** | 2. GPU specs stale: all 4 hosts are 2× RTX 5090 32GB = 64GB  |

## Conflict 2: fleet / agent_count

- **Values found:** 0, 2, 3, 8
- **Total mentions:** 16
- **Suggested resolution:** `8` (appears in 75% of mentions)

| Source | Line | Value | Context |
|--------|------|-------|---------|
| `\memory\archivist\assist-scribe-goals2-3-5-reverify-2026-11-20.md` | 6 | **8** | - Goal 2 (Cycle Narrative v2): `cycle_narrative.py --cycle 7 |
| `\memory\archivist\evidence-assist-scribe-relevance-map-2026-11-20.md` | 16 | **8** | - All 8 agents have exactly 30 ranked files |
| `\memory\archivist\evidence-scribe-goal10-agent-digest-2026-11-22.md` | 8 | **8** | Executed `python memory/scribe/weekly_summary.py --agent <na |
| `\memory\archivist\evidence-scribe-goal10-assist-2026-11-22.md` | 13 | **8** | - Ran for all 8 agents (orchestrator, researcher, builder, a |
| `\memory\archivist\evidence-scribe-goal8-timeline-verify-2026-11-20.md` | 8 | **8** | \| 2026-11-13 \| 10 (all dated <= 2026-11-13) \| 8 agents \| |

## Conflict 3: portal / port

- **Values found:** 1235, 1600, 8099, 8790, 8888
- **Total mentions:** 100
- **Suggested resolution:** `8099` (appears in 89% of mentions)

| Source | Line | Value | Context |
|--------|------|-------|---------|
| `\memory\archivist\citation-audit-cycle5-report.md` | 27 | **8099** | \| 7 \| http://white:8099/api/todo/prune \| WARN \| InvalidU |
| `\memory\archivist\citation-audit-cycle5-report.md` | 28 | **8099** | \| 8 \| http://pale:8099/api/fleet \| WARN \| InvalidURL: no |
| `\memory\archivist\citation-audit-cycle5-report.md` | 29 | **8099** | \| 9 \| http://white:8099/api/fleet \| WARN \| InvalidURL: n |
| `\memory\archivist\citation-audit-cycle5-report.md` | 30 | **8099** | \| 10 \| http://red:8099/api/settings/lan-access/start \| WA |
| `\memory\archivist\citation-audit-cycle5-v2-report.md` | 28 | **8099** | \| `http://pale:8099api/fleet` \| `http://pale:8099/api/flee |

## Conflict 4: white / vram

- **Values found:** 32, 58
- **Total mentions:** 3
- **Suggested resolution:** `32` (appears in 67% of mentions)

| Source | Line | Value | Context |
|--------|------|-------|---------|
| `\memory\builder\hotload-catalog-refresh-2026-11-22.md` | 5 | **32** | 2. GPU specs stale: all 4 hosts are 2× RTX 5090 32GB = 64GB  |
| `\memory\builder\hotload-catalog-refresh-2026-11-22.md` | 5 | **32** | 2. GPU specs stale: all 4 hosts are 2× RTX 5090 32GB = 64GB  |
| `\memory\builder\hotload-catalog-refresh-2026-11-22.md` | 18 | **58** | - `vram_plan.py`: per-host usage 84–91%, only White triggers |
