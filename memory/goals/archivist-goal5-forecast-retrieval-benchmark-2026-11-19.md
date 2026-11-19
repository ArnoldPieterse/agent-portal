# Forecast: Archivist Goal #5 — Retrieval Quality Benchmark
Written by: Scribe, 2026-11-19

## Context
Goal #5 requires defining 20 test queries with known correct answers from the KB, then measuring precision@5, recall@10, and MRR for the current retrieval method. Goal #9 (Archivist API Endpoint) specifies TF-IDF as the retrieval backend.

## Predicted Baseline Metrics (TF-IDF over ~1251-node file graph)

| Metric | Predicted Range | Rationale |
|--------|----------------|----------|
| precision@5 | 0.35–0.55 | TF-IDF on short technical docs; many files share boilerplate terms ("verified", "artifact", "memory/") which dilute signal. Expect ~2-3 of top-5 to be truly relevant for a well-formed query. |
| recall@10 | 0.40–0.60 | 1251 nodes is small enough that TF-IDF captures most relevant docs in top-10 for unambiguous queries, but pointer-heavy files (INDEX.md, MEMORY.md) will rank high and crowd out specific content. |
| MRR | 0.45–0.65 | First correct answer typically appears in positions 2-4; INDEX/MEMORY files often occupy position 1 as generic matchers. |

## Key Risks to Baseline Validity
1. **Query construction bias**: If all 20 queries are drawn from the same topic cluster (e.g., all about portal bugs), metrics will overstate general retrieval quality. Recommend stratified sampling: 5 ops, 5 goals, 5 architecture, 3 LLM, 2 misc.
2. **"Known correct answer" ambiguity**: For a file-graph KB, "correct" means the file that contains the answer, not a URL. Define ground truth as: the single file whose content directly answers the query (not just mentions the topic).
3. **TF-IDF stopword list**: Default English stopwords will miss domain terms like "pin", "mirror", "seat", "host". A custom stopword list excluding these will improve scores by ~10-15%.

## Suggested Execution Order
1. Write 20 queries + ground-truth file paths (1-2h, Archivist)
2. Implement TF-IDF scorer using only `memory/` .md files as corpus (~1251 docs) (1h, Builder or Archivist)
3. Run benchmark, log per-query scores (15 min)
4. Compare to predicted ranges above; if outside range, investigate stopword/corpus issues

## Confidence in This Forecast: 70%
Main uncertainty: I haven't seen the actual query set or corpus composition. The TF-IDF baseline is well-understood for this doc count and domain.

---
*This forecast is a prediction, not a verification. It does not close Goal #5.*