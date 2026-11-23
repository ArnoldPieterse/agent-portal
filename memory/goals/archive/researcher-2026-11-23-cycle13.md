# Researcher - 10 goals (set 2026-11-23, cycle-13)

Focus: Production Hardening & Self-Sustaining Operations. Cycle 13 makes the research layer production-grade: reproducible, cost-aware, and self-validating.

1. **Evidence Reproducibility Checker** - `python memory/researcher/evidence_repro.py`: for each evidence leaf in the last cycle, verify the referenced command/script still produces the same result (within tolerance). Flag non-reproducible evidence as STALE. Verified: >=20 evidence leaves checked; a deliberately modified script causes its evidence to be flagged; output is JSON with leaf_path, reproducible bool, delta.

2. **Research Cost Tracker** - `python memory/researcher/research_cost.py`: track token cost per research task (from portal logs); compute cost-per-fact-discovered and cost-per-goal-closure; emit weekly report to memory/researcher/cost-report-<week>.md. Verified: report shows cost breakdown by task type; a high-cost task (>3x median) is flagged with optimization suggestion; JSON output available.

3. **Source Quality Scoring** - `python memory/researcher/source_quality.py`: maintain a quality score (0-100) for each source in the KB based on: recency, citation count by other agents, contradiction rate, and domain authority. Emit memory/researcher/source-scores.json. Verified: >=50 sources scored; top 5 are from domains with >3 citations; a source that was contradicted twice drops below 60.

4. **Hypothesis Validation Pipeline** - `python memory/researcher/hypothesis_pipeline.py`: formalize the research workflow: (1) state hypothesis, (2) define falsification test, (3) execute test, (4) record result with confidence interval, (5) update KB if validated. Emit structured records to memory/researcher/hypotheses.jsonl. Verified: 3 hypotheses processed end-to-end; each has all 5 fields; a falsified hypothesis updates the KB entry with correction.

5. **Cross-Source Consistency Monitor** - `python memory/researcher/consistency_monitor.py`: periodically check that facts from different sources about the same subject don't contradict; emit conflict alerts to memory/researcher/conflicts-<date>.md. Verified: a deliberately injected contradiction is detected within 1 pass; alert includes both source paths and the conflicting values; no false positives on consistent data.

6. **Research Task Auto-Router** - `python memory/researcher/task_router.py`: given a research question, classify it (fact-lookup / synthesis / novel-investigation) and route to the cheapest sufficient method (KB search / web search / deep multi-source investigation). Log routing decisions. Verified: 10 test questions routed; fact-lookups never use deep investigation; routing log shows cost savings vs "always deep" baseline.

7. **Knowledge Decay Predictor** - `python memory/researcher/decay_predictor.py`: for each KB fact, predict when it will become stale based on: source update frequency, domain volatility (tech > law > math), and last verification date. Emit a prioritized re-verification queue to memory/researcher/reverify-queue.json. Verified: >=100 facts have decay predictions; top 10 are from high-volatility domains; a fact from a stable source has >365 day predicted freshness.

8. **Research Confidence Calibrator** - `python memory/researcher/confidence_calib.py`: track the researcher's stated confidence vs actual accuracy (from Verifier feedback); compute calibration score (Brier score or ECE); adjust future confidence statements toward calibration. Verified: >=20 predictions have known outcomes; Brier score computed; a miscalibrated range (>15% gap) is flagged with correction factor.

9. **Automated Literature Survey** - `python memory/researcher/auto_survey.py`: for a given topic, auto-gather all relevant KB leaves + web sources, extract key claims, produce a structured survey with topic, claims array (claim, source, confidence), contradictions array, gaps array. Verified: 2 surveys produced; each has >=5 claims with resolvable sources; at least one gap is identified per survey.

10. **Research SLA Dashboard** - Add `/api/research/sla` endpoint: shows avg_response_time, p95_response_time, accuracy_rate, open_questions_count, oldest_open_question_age. Data from portal logs + open-questions-log. Verified: endpoint returns valid JSON; values match manual calculation from logs within 10%; oldest question age is in hours.
