# Archivist Goal #2 Assist — Knowledge Graph v3: 'evidence' + 'dependency' edge types added (Builder)
Date: 2026-11-21 | Agent: Builder (assist, owner: Archivist)

## What was done
Extended memory/archivist/knowledge_graph_v3.py with the two remaining edge types
listed in the goal's PROGRESS note ("Remaining: ... add 'evidence' and 'dependency' edge types"):

1. **evidence** — EVID_RE matches `Verified:` / `Evidence:` markers followed by a
   `(pointer: path)` or `(evidence: path)` citation within 80 chars; deduped against
   the final (from,to,type) key so it never double-counts a plain citation.
2. **dependency** — DEP_KW_RE finds dependency keywords (depends on / depended on /
   dependency on / require[s]); a 160-char sentence window then extracts any file-path
   token that resolves to a real node in the graph.

## Verification (ran in this sandbox, full tree)
- Run 1 (evidence only): 7624 nodes, 1665 edges; edge types: pointer=1061 link=43
  supersession=7 citation=436 evidence=118.
- Run 2 (final): **7624 nodes, 1722 edges**; edge types: pointer=1061 link=43
  supersession=7 citation=436 **evidence=118 dependency=57**. All 6 goal-required
  edge types (pointer, evidence, dependency, supersession, citation, +link) present.
- Output JSON: 2018.9 KB (< 2MB AC). --query mode unaffected.

## Sample edges detected
- evidence: memory/designer/ledger_snapshot.json -> memory/researcher/net-capability-matrix-2026-11-16.md
- dependency: memory/designer/dark-mode-contrast-report-2026-11-18.md -> memory/ops/blockers.md (requires)

## Remaining for Archivist (not done here)
- Run on White where git is present to populate temporal_source=git >=50% of nodes
  (sandbox has no repo: 0/7624). That is the last unmet AC line.

Artifacts: memory/archivist/knowledge_graph_v3.py (edited), memory/archivist/knowledge-graph-v3.json (regenerated)
