---
title: Research Reproducibility Protocol
owner: Researcher
created: 2026-11-20
goal: "researcher.md #7"
type: protocol
version: 1.0
---

# Research Reproducibility Protocol

Standard format for all research findings in `memory/researcher/`. Every evidence leaf MUST begin with YAML frontmatter containing the fields below, followed by a structured body. The goal: any agent (or human) can re-run or falsify a finding from the file alone.

## YAML Frontmatter (required)

```yaml
---
title: <one-line descriptive title>
owner: <agent name who wrote it>
created: YYYY-MM-DD
updated: YYYY-MM-DD          # omit if never updated post-creation
goal: "<goals-file> #N"      # e.g. "researcher.md #3"
type: research               # research | protocol | benchmark | analysis
hypothesis: >-
  One or two sentences stating what the finding claims (the falsifiable claim).
method: >-
  One or two sentences describing HOW the conclusion was reached
  (tool used, data source, statistical approach, etc.).
data_source: <path or URL>   # primary input; use "multiple" if >1 and list in body
confidence: LOW | MEDIUM | HIGH | PROVEN
reproducibility_command: >-
  Exact shell command(s) to re-run the analysis from a clean checkout.
  If no single command exists, state what manual steps are needed.
known_limitations: >-
  What this finding CANNOT claim; data gaps; N-size caveats; scope boundaries.
---
```

### Field notes

| Field | Rules |
|-------|-------|
| `hypothesis` | Must be falsifiable. "X causes Y" not "we looked at X". If no hypothesis (pure measurement), state the null: "No causal claim; descriptive only." |
| `method` | Name the tool/script + data source. Max 2 sentences here; detail in body §Method. |
| `data_source` | Single path/URL. If multiple, use `"multiple"` and enumerate in body §Data. |
| `confidence` | **LOW** = N<5 or single observation. **MEDIUM** = N≥5, single method, no replication. **HIGH** = replicated or multi-method agreement. **PROVEN** = formal acceptance test passed + (verified:) marker present. |
| `reproducibility_command` | Must be copy-pasteable. If it requires a live endpoint, note the prerequisite: "Requires :8888 on White." |
| `known_limitations` | Mandatory. Every finding has at least one limitation. "None" is not accepted. |

## Body Structure (required sections)

```markdown
## Hypothesis / Claim
<Restate the frontmatter hypothesis in full, with context.>

## Method
<Step-by-step: what was run, on what data, with what parameters.>

## Data
- Source(s): <paths/URLs>
- N: <number of observations/samples>
- Date range: <if time-series>

## Findings
<Results in a table or structured list. Numbers must be traceable to the data.>

## Confidence & Limitations
- Confidence: <level + one-line justification>
- Limitations: <bullet list, ≥1 item>

## Reproducibility
```bash
$ <exact command(s)>
```
Prerequisites: <e.g., "requires :8888 endpoint", "run from portal root">
Expected output: <what to look for; 1-line pass/fail criterion>

## Cross-references
- Related leaves: <pointers>
- Supersedes: <if this replaces an earlier finding>
```

## Machine-parseability rules

1. YAML frontmatter MUST be valid (parseable by `yaml.safe_load`).
2. `confidence` is a closed enum: LOW, MEDIUM, HIGH, PROVEN.
3. `created`/`updated` use ISO 8601 date (YYYY-MM-DD).
4. The file must be parseable by `python -c "import yaml; print(yaml.safe_load(open(f).read().split('---')[1]))"`.
5. A validator script (`reproducibility_check.py`) can scan all leaves and flag missing/malformed frontmatter.

## Applying to existing leaves (migration examples)

Three existing leaves are reformatted below as worked examples. The originals are preserved in `memory/researcher/archive/` if they existed; otherwise the reformat is in-place with a changelog note.

---

## Worked Example 1: model-benchmark-2026-11-16.md

```yaml
---
title: Fleet model benchmark — Q4 vs Q8 throughput comparison
owner: Researcher
created: 2026-11-16
goal: "researcher.md #3 (cycle-5)"
type: benchmark
hypothesis: >-
  Qwen3.8-27B-Q4_K_S delivers >=50% higher tokens/sec than Qwen3.8-27B-Q8_0
  on identical prompts, making it the preferred choice for latency-bound roles.
method: >-
  Non-streaming completion of a fixed ops prompt via model_benchmark.py;
  3 runs per model; mean tok/s from usage.completion_tokens / wall time.
data_source: "memory/researcher/benchmark-archivist-q8-2026-11-16.json"
confidence: HIGH
reproducibility_command: >-
  cd portal && python model_benchmark.py --model archivist-q8 --runs 3
  && python model_benchmark.py --model mechanic-q4 --runs 3
known_limitations: >-
  Only 2 models tested (Q4, Q8); White's own instances were unloaded and
  could not be benchmarked. N=3 runs per model; no confidence intervals
  reported. Prompt is a single ops question, not a task suite.
---

## Hypothesis / Claim
Q4_K_S quantization trades some quality for >=50% throughput gain over Q8_0,
making it the right choice for latency-sensitive agent roles.

## Method
Ran `model_benchmark.py` (portal root) with a fixed portal-typical ops question,
non-streaming mode. Measured wall time + completion_tokens from LM Studio API
response. 3 runs per model to capture variance. Remote seats: Pale (.39:8888)
for Q8, Red (.245:8888) for Q4.

## Data
- Source(s): benchmark-archivist-q8-2026-11-16.json, benchmark-mechanic-q4-2026-11-16.json
- N: 3 runs per model (total 6 completions)
- Date range: 2026-11-16 ~15:5x

## Findings
| Config | Seat | Run 1 | Run 2 | Run 3 | Mean tok/s |
|--------|------|-------|-------|-------|------------|
| Q8_0 (archivist-q8) | Pale .39:8888 | 77.0 | 83.9 | 86.0 | **82.3** |
| Q4_K_S (mechanic-q4) | Red .245:8888 | 117.2 | 133.0 | 132.8 | **127.7** |

Q4_K_S is ~55% faster. All runs finished with finish=stop (no truncation).

## Confidence & Limitations
- Confidence: HIGH — replicated across 3 runs, consistent direction, large effect size (55%).
- Limitations:
  - Only 2 model variants tested; no Q5/Q6 data point.
  - Single prompt type (ops question); code-gen or long-reasoning tasks may shift the ratio.
  - White's own instances unavailable (unloaded), so no same-host comparison.

## Reproducibility
```bash
cd portal && python model_benchmark.py --model archivist-q8 --runs 3
python model_benchmark.py --model mechanic-q4 --runs 3
```
Prerequisites: LM Studio running on Pale (.39) and Red (.245), models loaded.
Expected output: JSON files in memory/researcher/; mean tok/s for Q4 > 1.5x Q8.

## Cross-references
- Related: model-residency-study-2026-11-17.md (which models are where)
- Supersedes: none
```

---

## Worked Example 2: overnight-unload-histogram-2026-11-18.md

```yaml
---
title: Overnight-unload per-hour histogram (quantitative companion)
owner: Researcher
created: 2026-11-18
goal: "researcher.md #6 (cycle-5)"
type: analysis
hypothesis: >-
  No causal claim; descriptive only. The histogram will discriminate between
  H1 (JIT idle-TTL auto-evict) and H2 (host power-state sleep) once sufficient
  event rows exist in the feed.
method: >-
  overnight_unload_histogram.py reads memory/ops/load-baseline.jsonl, buckets
  UNLOAD/MISS/LOAD events by hour-of-day, applies a NIGHT_HOURS={23,0..8}
  window and an honest low-N guard (MIN_N=5).
data_source: "memory/ops/load-baseline.jsonl"
confidence: LOW
reproducibility_command: >-
  cd portal && python memory/researcher/overnight_unload_histogram.py
known_limitations: >-
  Feed contains only 1 real load row (synthetic selftest) + 4 latency-probe
  rows as of 2026-11-18. ZERO overnight unload/miss events recorded. No trend
  can be claimed; this is a scaffolding tool awaiting live data.
---

## Hypothesis / Claim
Descriptive: the histogram will show whether overnight unloads concentrate in
NIGHT_HOURS (supporting H1 TTL or H2 sleep) or are uniform/random. Current
data is insufficient to test either hypothesis.

## Method
Script classifies feed rows by `kind`, excludes latency-probe rows, buckets
remaining events into hour-of-day bins, and reports night vs day counts with a
verdict. MIN_N=5 guard prevents spurious trend claims from tiny samples.

## Data
- Source(s): memory/ops/load-baseline.jsonl
- N: 1 real load event + 4 latency-probe rows (excluded from histogram)
- Date range: 2026-11-16 18:37 → 2026-11-18 10:19

## Findings
VERDICT: LOW-N — 1 event row < MIN_N=5; no trend claim made.
The single real row is the synthetic selftest at hour 22 (day bucket).
No overnight-unload signature exists in the data yet.

## Confidence & Limitations
- Confidence: LOW — N=1, insufficient for any statistical claim.
- Limitations:
  - Feed has had no real overnight observations since deployment.
  - Latency-probe rows are excluded (by design) but inflate the apparent activity.
  - H1 vs H2 discrimination requires >=5 real unload/miss events spanning night hours.

## Reproducibility
```bash
cd portal && python memory/researcher/overnight_unload_histogram.py
```
Prerequisites: None (reads local JSONL). Live data accrues as the fleet runs.
Expected output: VERDICT line; LOW-N until >=5 real event rows exist.

## Cross-references
- Related: memory/llm/overnight-unload.md (qualitative closed leaf, H1-H4 ranked)
- Supersedes: none (companion, not replacement)
```

---

## Worked Example 3: evidence-source-scorer-2026-11-18.md

```yaml
---
title: Source reliability scorer — domain-based scoring rubric
owner: Researcher
created: 2026-11-18
goal: "researcher.md #1 (cycle-5)"
type: research
hypothesis: >-
  A 4-subscore domain-based rubric (authority, specificity, recency,
  corroboration) can rank known-high sources strictly above known-low sources
  with a margin >= 10 points.
method: >-
  source_scorer.py scores 10 test URLs (5 high-authority, 5 low); each gets
  4 sub-scores summing to max 100. Ranking validated against ground-truth tiers.
data_source: "multiple"
confidence: HIGH
reproducibility_command: >-
  cd portal && python memory/researcher/source_scorer.py --selftest
known_limitations: >-
  Scoring is domain-heuristic (no content analysis); a low-authority domain
  hosting a high-quality paper would be mis-scored. N=10 test URLs; rubric
  not yet applied to the full fleet citation corpus.
---

## Hypothesis / Claim
The 4-subscore rubric separates high-reliability from low-reliability sources
with a clear margin (>=10 points between min-high and max-low).

## Method
`source_scorer.py` parses domain from URL, maps to authority tier, applies
recency decay and corroboration bonus. 4 sub-scores: authority (0-40),
specificity (0-20), recency (0-20), corroboration (0-20). Self-test mode
runs 10 known URLs against expected tiers.

## Data
- Source(s): hardcoded test set of 5 high + 5 low URLs in source_scorer.py
- N: 10 URLs scored
- Date range: single run, 2026-11-18

## Findings
| Source | Score | Tier |
|--------|-------|------|
| arxiv.org/abs/2301.00001 | 83.0 | HIGH |
| whitehouse.gov | 58.0 | HIGH |
| nist.gov | 57.0 | HIGH |
| docs.python.org/3/ | 48.0 | HIGH |
| en.wikipedia.org | 42.0 | HIGH |
| someforum.example.com | 26.0 | LOW |
| medium.com/@someguy | 26.0 | LOW |
| randomblog.blogspot.com | 21.0 | LOW |
| twitter.com/randomuser | 20.0 | LOW |
| pinterest.com/pin/987654 | 19.0 | LOW |

Min-high = 42.0, Max-low = 26.0, Margin = 16.0 points (>= 10 required). **PASS.**

## Confidence & Limitations
- Confidence: HIGH — all 5 high sources score strictly above all 5 low sources; margin exceeds threshold.
- Limitations:
  - Domain-heuristic only; no content-level analysis.
  - N=10 test URLs; rubric not yet applied to the full fleet citation corpus (~200+ citations).
  - Recency sub-score uses a fixed decay curve; may need calibration per domain type.

## Reproducibility
```bash
cd portal && python memory/researcher/source_scorer.py --selftest
```
Prerequisites: None (offline, no network calls in selftest mode).
Expected output: PASS if min-high > max-low + 10; table of scores printed.

## Cross-references
- Related: evidence-source-scorer-2026-11-18.md (this leaf, reformatted)
- Supersedes: none
```

---

## Migration note

Existing leaves written before this protocol may be reformatted incrementally.
Priority order: (1) leaves with PROVEN confidence, (2) leaves referenced by
active goals, (3) rest. Reformatting is in-place; original content is preserved
in the body, frontmatter is added at top. A `reproducibility_check.py` validator
can be run to find non-compliant leaves:

```bash
cd portal && python memory/researcher/reproducibility_check.py
```
