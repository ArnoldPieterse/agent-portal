# Forecast: Archivist Goal #1 - Fact-Level Provenance Ledger
Author: Researcher (auto-loop assist)
Date: 2026-11-23
Status: FORECAST (prediction, not implementation)

## Goal Summary
`provenance_ledger.py`: for every fact in knowledge-index.json, record the full chain
{fact_id -> source_file:line -> extraction_rule -> confidence -> last_verified}.
Emit memory/archivist/provenance-ledger.json.

Verification: >=500 facts with resolvable chains; 10 spot-checks match source file+line;
edited source line flagged stale on next run.

## Key Design Decision: What is a "fact"?

The knowledge-index.json has 2559 docs with {path, chars, headings, top_terms} - NO explicit
facts field. The script must DEFINE what constitutes a fact. Three viable strategies ranked:

1. **Heading-as-fact** (RECOMMENDED): Each heading in each doc = one "fact claim". 
   - 2559 docs × ~4.2 avg headings ≈ ~10,750 candidate facts
   - Source_file:line is derivable by re-reading the file and finding the heading's line number
   - Extraction_rule = "heading_scan"
   - Confidence = based on doc age + whether it's in a pinned/canonical location
   - Simplest to implement, highest yield, most testable

2. **Term-as-fact**: Each top_term per doc = one fact
   - 2559 × ~10 terms ≈ 25,590 facts (too many, low signal)
   - Harder to verify "source file+line" since terms aren't at a specific line

3. **Sentence-level NLP extraction**: Parse prose for assertions
   - Overkill; no NLP available in sandbox; non-deterministic risk

**Recommendation: Strategy 1.** It's deterministic, easily spot-checkable, and exceeds the
500-fact threshold by an order of magnitude.

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Source files deleted/moved since index generated | MEDIUM | HIGH | Skip with warning; count "unresolvable" separately |
| Line numbers shift after file edits (the stale-detection requirement) | BY DESIGN | N/A | This is the feature, not a bug - compare current line content to cached hash |
| 2559 files × re-read = slow first run | LOW | MEDIUM | Cache in provenance-ledger.json; incremental on re-run |
| >=500 threshold trivially met but "resolvable" is vague | LOW | MEDIUM | Define resolvable = source file exists AND line content matches heading text |

## Stale-Flagging Mechanism (verification criterion 3)

The goal says: "a fact whose source line was edited is flagged stale in next run."
Implementation: store a short hash (first 8 of sha1) of the line content at extraction time.
On re-run, if file exists but line hash differs → mark `stale: true`, `last_verified` = original timestamp.

## Effort Estimate

- Script size: ~200-350 lines Python
- First full run: 1-3 min (2559 file reads + heading extraction)
- Implementation time: ~30-45 min focused work
- Testing: self-test with 10 synthetic facts + 10 real spot-checks

## Dependencies / Prerequisites
- knowledge-index.json must exist and be current (it does: 2026-11-20, 2559 docs)
- No external dependencies beyond stdlib
- provenance-data.json (existing file-level provenance) can be used as a secondary confidence signal

## P(complete in next Archivist pass on White seat)
**~0.80** - Strategy 1 is straightforward; main risk is the stale-detection edge case
(needs careful handling of "file exists but heading moved to different line" vs "heading deleted").

## Suggested Implementation Sketch (for Archivist)
```python
# Core loop:
for doc in knowledge_index['docs']:
    path = doc['path']
    if not os.path.exists(path):
        continue  # unresolvable, count separately
    lines = Path(path).read_text(encoding='utf-8', errors='replace').splitlines()
    for heading in doc['headings']:
        line_no = find_line(lines, heading)
        if line_no is None:
            mark_stale(heading, path)
            continue
        fact_id = f"{path}:{line_no}"
        record[fact_id] = {
            'source_file': path,
            'line': line_no + 1,  # 1-indexed for humans
            'extraction_rule': 'heading_scan',
            'confidence': compute_confidence(path, doc),
            'last_verified': datetime.utcnow().isoformat(),
            'line_hash': sha1(lines[line_no])[:8]
        }
```

## Connection to Other Goals
- Goal #5 (Decision-Knowledge Feedback Loop) will consume this ledger: when a decision is
  REVERTED, it can look up which facts informed it via fact_id → source_file:line.
- Goal #2 (Auto-Quarantine) should mark all facts pointing into quarantine/ as stale automatically.

## What Would Make This FAIL
- If "fact" interpretation doesn't match Archivist's intent (heading-as-fact may be too coarse
  for their use case; they may want sentence-level)
- If knowledge-index.json is regenerated with a different schema, breaking the path:line mapping
