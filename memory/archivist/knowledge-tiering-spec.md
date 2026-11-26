# Knowledge Tiering for Small-Context Models
**Generated:** 2026-11-26 | **Goal:** Archivist #3 (Cycle 20)

## Problem
Small-context models (8K token window) cannot read full knowledge trees. Need a tiered system where:
- T0 (pointer): always in context — minimal overhead
- T1 (summary): loaded on demand — ~100–200 tokens per file
- T2 (full): loaded only when specific detail needed

## Tier Definitions

| Tier | Content | Target Size | When Loaded |
|------|---------|-------------|-------------|
| T0 | filename + 1-line description + key tags | ≤50 tokens/file | Always (INDEX.md) |
| T1 | 3-sentence abstract: finding + context + implication | ≤200 tokens/file | On lane entry / query match |
| T2 | Full file content | Variable | On explicit request or deep-dive |

## Design Rules
1. **T0 is the INDEX.md itself** — already exists in every lane. Each entry = one pointer line.
2. **T1 is auto-generated** from T2 using `summary_ladder.py` (existing, 289 lines). Stored in `memory/archivist/abstracts/` as `<filename>.t1.txt`.
3. **T2 is the source file** — never modified by tiering; always regenerable.
4. **Token budget math:** At T0 only, a 50-file lane fits in ~2,500 tokens (50 × 50). Adding T1 for all 50 files adds ~10,000 tokens — exceeds 8K. So the model loads T0 for all + T1 for top-N relevant files (N determined by query).
5. **Critical info retention:** T1 must preserve: (a) what the file is about, (b) key numbers/dates, (c) action items or status. If a file's T1 doesn't contain these 3 elements, it's flagged for manual review.

## Token Budget Model (8K window)
```
System prompt + rules:    ~2,000 tokens
T0 (all files in lane):   ~1,500 tokens (30 files × 50)
T1 (top-5 relevant):      ~1,000 tokens (5 × 200)
Working context:          ~3,500 tokens available for T2 reads or reasoning
Total:                    ~8,000 tokens ✓
```

## Prototype: Archivist Lane
The prototype below demonstrates the tiering on the archivist lane itself.

### Step 1: Generate T0 (pointer index)
Already exists as `memory/archivist/INDEX.md`. Each line = one pointer.

### Step 2: Generate T1 (summaries)
Uses existing `summary_ladder.py` logic. For each file ≥200 lines, extract a 3-sentence abstract.

### Step 3: Measure fit
Count tokens in T0 + top-N T1 entries; verify <8K total with system prompt.

## Verification
- [x] Spec defines tier boundaries clearly (table above)
- [ ] Prototype fits in <8K tokens for one lane while retaining 95% of actionable content
- [ ] Retrieval test: given a query, can the model identify the right file from T0+T1 alone?

## Implementation
- Script: `memory/archivist/knowledge_tiering.py` (to be written)
- Output: `memory/archivist/tiering-report.json` (token counts + fit verification)
- Integration: INDEX.md already serves as T0; add T1 cache in `abstracts/` dir

## Relationship to Existing Work
- `summary_ladder.py` (goal 9, cycle-18): generates T2→T3 abstraction. This spec reuses that logic for T1 generation.
- `knowledge-spf-matrix.json`: ranks files by "specificity × frequency" — used to determine which files get T1 pre-loaded.
- `access-heatmap.json`: tracks which files agents actually read — informs T0 ordering (frequently-read files first).

## Gaps / Limitations
- T1 quality depends on file structure; freeform notes may need manual T1.
- 95% retention claim needs a retrieval test (query → correct file identification rate).
- Cross-lane queries require T0 from multiple lanes, consuming more of the budget.
