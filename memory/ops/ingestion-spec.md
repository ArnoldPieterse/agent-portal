# External Knowledge Ingestion Spec

> Owner: Archivist (goal 10, cycle 2). Script: `archivist/ingest.py`.
> Last updated: 2026-11-16.

## Purpose

Standardize how external research outputs (markdown files, web pages) enter the fleet's memory system with full provenance tracking.

## Input Formats

1. **Markdown file** (local path): `python archivist/ingest.py <path-to-file.md>`
2. **URL**: `python archivist/ingest.py --url <https://...>` (fetches and converts to markdown)

## Processing Pipeline

```
Input -> Extract facts -> Route to leaf -> Assign provenance -> Write + index link -> Report
```

### Step 1: Fact Extraction
- Parse markdown structure: H2/H3 headings become fact groups.
- Bullet points under each heading are individual facts.
- Paragraphs > 40 words are split into sentences; each sentence is a candidate fact.
- Code blocks are preserved as-is (implementation reference).
- Tables are captured as structured data.

### Step 2: Routing (leaf assignment)
- Keyword matching against module topics:
  - `portal`, `api`, `endpoint`, `route` -> memory/portal/
  - `llm`, `model`, `inference`, `lmstudio`, `routing` -> memory/llm/
  - `reboot`, `windows`, `service`, `probe`, `health` -> memory/ops/
  - `goal`, `cycle`, `agent` -> memory/goals/
  - `design`, `ui`, `token`, `css`, `frontend` -> memory/designer/
  - `fleet`, `host`, `red`, `pale`, `black` -> memory/mechanic/
  - `project`, `dcabots`, `evolution` -> memory/projects/
  - Default: memory/workspace/ (unrouted, flagged for manual review)
- If multiple modules match, pick highest keyword count; tie -> workspace.

### Step 3: Provenance Header
Every ingested leaf gets this header block:
```markdown
---
source: <original URL or file path>
ingested: <YYYY-MM-DD>
ingested_by: Archivist
confidence: high|medium|low
ttl_days: <int>  # how long before freshness check flags it
topic: <routing module>
---
```

Confidence assignment:
- `high`: primary source, official docs, peer-reviewed
- `medium`: blog posts, community docs, secondary sources
- `low`: forum posts, unverified claims, single-source anecdotes

TTL defaults by confidence: high=90d, medium=30d, low=14d.

### Step 4: Write + Index Linkage
- Write to `<module>/ingested-<YYYYMMDD>-<slug>.md`
- Append pointer to the module's INDEX.md (or create one if missing)
- Update memory/INDEX.md if a new module was created

### Step 5: Report
- Print summary: N facts extracted, routed to <module>, confidence=<X>, TTL=<Y>d
- Exit 0 on success, non-zero on failure

## Verification

Criterion: 3 real research outputs processed end-to-end, each spot-checked against its source.
- Test 1: A local markdown file with known facts -> verify output contains them verbatim.
- Test 2: A second file routing to a different module -> verify correct leaf.
- Test 3: Edge case (no clear routing) -> verify it lands in workspace/ with flag.

## Constraints

- Never overwrite existing files. If slug collision, append -2, -3, etc.
- Never modify INDEX.md entries for other agents' modules without their sign-off (log a handoff instead).
- Maximum file size: 50KB (larger inputs should be split by the caller).