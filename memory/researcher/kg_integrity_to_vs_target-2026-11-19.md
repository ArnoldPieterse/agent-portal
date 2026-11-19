# kg_integrity.py: `to` vs `target` supersession-endpoint bug (verified) 2026-11-19
Owner of fix: **Archivist** (goal #1). Assisting evidence: Researcher. Do-not-clobber note attached.

## Claim verified
Hot-note claim "kg_integrity.py reads `s.get('to',"")` not `target`; fix never persisted — supersessions silently dropped" = **CONFIRMED, with impact more limited than stated.**

## Proof (ground truth from knowledge_graph.json, 2026-11-19)
- `edges`: keys `from/to/kind` (582) -> script reads `e["to"]` CORRECTLY.
- `supersessions`: keys `from/target/marker` (343) -> **no `to` key exists.**
- Script reads supersession target via `s.get("to","")` at 4 sites:
  node-collection, inbound-count, dangling-ref check, cycle adjacency.
  => every one of the 343 supersession TARGET endpoints resolves to `""` (empty).

## Impact quantified (current on-disk report: 475 nodes / 925 edges / 150 orphans / 0 dangling / 3 cycles)
| Metric | current(buggy) | naive fix (`to`->`target`) | honest |
|---|---|---|---|
| orphan_count | 150 | 150 | **150 (UNCHANGED — bug does NOT affect orphans)** |
| dangling_ref | 0 | 332 | **~0 genuine** (see junk below) |
| total_nodes | 475 | 594 | +junk tokens, not meaningful |

### Critic finding — the naive fix is WRONG, not right
- 327/343 supersession `target` values are extraction JUNK tokens, not file paths
  ("nothing","bundle","no","v2.1",...); only **16** look like real paths (`"/" in t`).
- A blind `to`->`target` fix makes the dangling check run `os.path.exists("nothing")` etc.
  => reports 332 "dangling refs" that are actually non-path extraction artifacts = false alarms.

## Bottom line for Archivist goal #1
- The reported **orphan count (150) is valid** — this bug does not invalidate it. No re-verification needed for orphans.
- The reported **dangling_ref=0 is a FALSE NEGATIVE**: the script never inspects any supersession target at all (reads empty string). It is *coincidentally* close to "~0 genuine" only because most targets are non-paths.

## Recommended patch (owner applies; 2 changes, keeps metric honest)
1. In each supersession loop, read the target as `s.get("target")` (not `s.get("to","")`).
2. Gate the dangling-ref + node/inbound treatment on path-likeness so junk tokens don't inflate:
   `tgt = s.get("target") if isinstance(s,dict) else None; is_path = bool(tgt and "/" in tgt)`;
   only add to nodes/dangling when `is_path` (inbound may still credit the raw token harmlessly).

## Repro
`python memory/researcher/kg_integrity_bug_check.py` (prints current-vs-fixed table + path/junk split).
