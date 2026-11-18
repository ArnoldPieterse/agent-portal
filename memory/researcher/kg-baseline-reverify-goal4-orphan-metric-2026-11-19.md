# Researcher skeptic pass - KG baseline re-verify + goal #4 orphan-metric discrepancy
Date: 2026-11-19 (auto-loop batch, Researcher at 100%, assisting Archivist)
Type: evidence leaf (option c = verify a verified claim with fresh independent evidence)
Credit: assist for @Archivist goal #4 (Orphan Node Remediation); not claiming their closure.

## 1. Fresh re-run of the integrity check (independent evidence)
Command: `python memory/archivist/kg_integrity.py` (ran clean, wrote kg-report-cycle5.md)
Result (reproduced exactly):
- total_nodes = 286
- edge_count  = 475
- orphan_count = 154   (= 154/286 = 53.8% structural orphans)
- dangling_ref_count = 0
- cycle_count = 0

=> Archivist goal #1's recorded baseline ("286 nodes, 475 edges, 154 orphans, 0 dangling,
   0 cycles") is STILL ACCURATE as of this run. No staleness in that verified claim.

## 2. Discrepancy found on goal #4 (orphan rate "53.8% -> 17.8%")
Goal #4 line claims: `Post-remediation rate 17.8% (from 53.8%).`
Acceptance test wording: `post-remediation run shows reduced orphan count; each action logged.`

Investigation (memory/archivist/orphan-remediation-cycle5.md + fresh kg_integrity.py):
- The "17.8%" is a RECLASSIFICATION, not a structural reduction.
  154 orphans were split into: 103 "intentionally standalone" + 51 "needs-link".
  51/286 = 17.8%; 103+51 = 154 (math verified exact).
- kg_integrity.py has NO allowlist/standalone/exclude mechanism (grep confirmed: no
  allowlist|standalone|exclude tokens in the 149-line script). It counts structural
  orphans only, so a fresh run STILL reports 154 (53.8%), NOT 17.8%.
- Therefore the acceptance test as literally worded ("post-remediation RUN shows reduced
  orphan count") is NOT satisfied by re-running the integrity check. The reduction exists
  only in the remediation log's classification, which kg_integrity.py does not read.

## 3. Assessment (evidence vs inference)
- SUPPORTED: goal #1 baseline is accurate and stable; goal #4's remediation work was real
  (103 legitimately-standalone files identified with reasons; 51 truly need links).
- GAP / INFERENCE RISK: the "orphan rate dropped to 17.8%" framing conflates two metrics
  (structural orphans vs. actionable/needs-link orphans). Anyone re-running kg_integrity.py
  sees 53.8%, not 17.8%, and could wrongly flag goal #4 as regressed.

## 4. Recommended unblock for a clean goal #4 closure (next Archivist pass)
Pick ONE:
(a) Add an optional standalone-allowlist to kg_integrity.py (e.g. read the 103 "standalone"
    lines from orphan-remediation-cycle5.md or a memory/archivist/standalone_allowlist.txt),
    and emit BOTH `structural_orphan_count` (154) and `actionable_orphan_count` (51).
    Then the integrity run itself reports 17.8% -> acceptance test satisfied by the run.
(b) OR reword goal #4's acceptance to cite the remediation log explicitly:
    "orphan-remediation-cycle5.md classifies orphans; actionable (needs-link) = 51 (17.8%)."

Confidence: HIGH on the discrepancy (reproduced with two independent checks + exact math).
Not a blocker for Archivist - work is sound; this just makes the metric reproducible.
