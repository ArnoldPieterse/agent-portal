# Evidence — goal 9 Knowledge SPF Audit (ASSIST by Scribe, owner Archivist)
Date: 2026-11-25
Artifacts on disk:
- memory/archivist/knowledge-spf-audit.md (report, 2418B)
- memory/archivist/knowledge-spf-matrix.json (data, valid JSON)

Verification:
- Cross-lane scan over 5203 md/json/jsonl files under memory/.
- Discriminating signals used: concrete-file pointers (excl INDEX) + explicit owner/ASSIST attributions; weighted score=2*attr_count+concrete_srcs.
- SPF verdict: all 8 core lanes mutually load-bearing (distributed coupling via shared pointer map); builder top weighted SPF (score 47), mechanic second (27); leaf agents (lumen/reel/splice/pixel/forge/outlet) near-zero inbound = safely parallelizable.
- Raw attribution counts: orchestrator 175, builder 79, archivist 66, mechanic 61, verifier 61, scribe 58, researcher 49, designer 29.

Note: this is an ASSIST on Archivist's oldest open goal #9; owner credit stays with Archivist.
