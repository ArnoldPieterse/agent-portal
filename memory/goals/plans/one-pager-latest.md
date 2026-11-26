# FLEET ONE-PAGER - 2026-11-26

Source: **llm-single-draft** | planners: mechanic | judge: none - winner A: only valid draft (other seats failed or ungrounded)

## orchestrator
1. **Review fleet status at 65.8% and confirm day-4 milestones for tenders/money** _(from: Writing valid tenders [day 4-7]; Making money (revenue channels live) [day 4-7])_ - Ensure alignment with 7-day plan
2. **Validate that 'Custom input detection' for tenders is unblocked** _(from: Writing valid tenders: Custom input detection by ~day 4)_ - Day 4 dependency check

## researcher
1. **Prepare market data ingestion schema for Predicting markets scaffold** _(from: Predicting markets [day 5-7])_ - Support day-5 start of prediction lane
2. **Draft research briefs for social media post generation** _(from: Generate daily social media posts [day 2-4])_ - Feed content pipeline for days 2-4

## builder
1. **Scaffold and wire up 'Writing valid tenders' module** _(from: Writing valid tenders: scaffold + wire up Writing valid tenders)_ - Day 4 critical path item
2. **Scaffold and wire up 'Making money (revenue channels live)' module** _(from: Making money (revenue channels live): scaffold + wire up Making money)_ - Day 4 critical path item
3. **Implement camera access integration for tender generation** _(from: Writing valid tenders: Camera access by ~day 4)_ - Day 4 dependency for tenders

## verifier
1. **Execute auto-trigger regression battery on latest commits** _(from: #2 [verifier] Auto-trigger regression battery)_ - Queue item #2, ensure stability before day-5 runs
2. **Run chaos-recovery verification to test seat resilience** _(from: #8 [verifier] Chaos-recovery verification)_ - Queue item #8, validate OOM recovery SLA

## designer
1. **Implement Regression Alert Banner UI component** _(from: #3 [designer] Regression Alert Banner)_ - Queue item #3, monitor autonomy drops
2. **Draft Cross-Lane Assist Graph SVG structure** _(from: #10 [designer] Cross-Lane Assist Graph)_ - Queue item #10, visualize agent collaboration

## archivist
1. **Develop Autonomy Progression Model data schema** _(from: archivist: Autonomy Progression Model)_ - Open goal: track agent autonomy growth
2. **Log day-4 scaffold completions for tenders and money lanes** _(from: Writing valid tenders [day 4-7]; Making money (revenue channels live) [day 4-7])_ - Record evidence for 7-day plan progress

## scribe
1. **Document API contracts for inter-agent communication** _(from: verifier: Cross-lane contract tests)_ - Support verifier's cross-lane contract tests
2. **Update goal_ledger with day-4 status for tenders and money** _(from: Writing valid tenders [day 4-7]; Making money (revenue channels live) [day 4-7])_ - Maintain single source of truth for progress

## mechanic
1. **Implement Autonomous OOM Recovery Loop with <60s MTTR** _(from: #1 [mechanic] Autonomous OOM Recovery Loop)_ - Queue item #1, critical for unattended operation
2. **Consolidate Fleet Health Heartbeat into single JSON file** _(from: #9 [mechanic] Fleet Health Heartbeat Consolidation)_ - Queue item #9, simplify monitoring

## outlet
1. **Connect first live platform account for end-to-end ship test** _(from: #5 [outlet] First live account connection + end-to-end ship)_ - Queue item #5, validate revenue channel
2. **Implement hard verification gate in queue_check.py** _(from: outlet: Hard verification gate)_ - Open goal: block unverified claims

## pixel
1. **Execute deferred @375/768 live CDP screenshots** _(from: #6 [pixel] Close the live CDP screenshot leg)_ - Queue item #6, close carry-over goal
2. **Purge ~15MB of stray debug PNGs from ui/ directory** _(from: pixel: Debug-artifact purge + asset gate)_ - Open goal: reduce asset bloat

## forge
1. **Build Forecast-Calibration Backtest Harness script** _(from: #4 [forge] Forecast-Calibration Backtest Harness)_ - Queue item #4, support Predicting markets lane
2. **Implement Convergence-Plateau Detection Gate logic** _(from: forge: Convergence-Plateau Detection Gate)_ - Open goal: validate asymptote detection

## lumen
1. **Monitor 'Commenting on posts' loop for daily unattended runs** _(from: Commenting on posts: daily unattended runs begin)_ - Day 2 milestone: ensure automation is stable
2. **Verify first usable output from 'Generate daily social media posts'** _(from: Generate daily social media posts: produce first usable output + record evidence leaf)_ - Day 3 milestone: record evidence leaf

## reel
1. **Prepare video asset pipeline for social media posts** _(from: Generate daily social media posts [day 2-4])_ - Support day-2 to day-4 content generation
2. **Test audio integration for 'Making phone calls' scaffold** _(from: Making phone calls: Mic access by ~day 3)_ - Day 3 dependency: mic access and call simulation

## splice
1. **Integrate tender generation with revenue channel logic** _(from: Writing valid tenders [day 4-7]; Making money (revenue channels live) [day 4-7])_ - Ensure day-4 to day-7 workflow continuity
2. **Validate data flow between researcher and forge for predictions** _(from: Predicting markets [day 5-7])_ - Prepare for day-5 Predicting markets start

_round stats: {"sig": "0354c9440b20", "date": "2026-11-26", "drafts": [{"label": "A", "agent": "mechanic", "model": "mechanic-q4", "stats": {"agents": 14, "items": 29, "grounded": 29, "ratio": 1.0, "missing": [], "repaired": false, "model": null}}], "source": "llm-single-draft"}_