# FLEET ONE-PAGER - 2026-11-26

Source: **llm-single-draft** | planners: mechanic | judge: none - winner A: only valid draft (other seats failed or ungrounded)

## orchestrator
1. **Run dispatch_audit.py to replay last N dispatches for stale conformance** _(from: Dispatch Anti-Stale Conformance Audit)_ - Detects routing drift before next cycle
2. **Execute convergence_coupling.py to map cross-lane dependencies** _(from: Cross-Lane Convergence Coupling Map)_ - Identifies bottlenecks in lane handoffs
3. **Trigger convergence_sentinel.py to monitor autonomy scope creep** _(from: Convergence Regression Sentinel)_ - Prevents uncontrolled agent behavior expansion

## researcher
1. **Compile market data sources for Predicting markets scaffold** _(from: Predicting markets [day 5-7])_ - Day 5 requires wired-up prediction pipeline
2. **Validate data freshness for revenue channel inputs** _(from: Making money (revenue channels live) [day 4-7])_ - Supports Making money (revenue channels live) day 4-7

## builder
1. **Implement cycle_closeout.py to automate unattended cycle end** _(from: Zero-Touch Cycle Closeout Orchestrator)_ - Queue #3 requires zero-touch closeout
2. **Run infra_health.py liveness probe on Builder's infrastructure** _(from: Autonomy-Infra Self-Health Probe)_ - Ensures stability for upcoming scaffolds
3. **Lint cross-lane JSON contracts in contracts.py registry** _(from: Data-Contract Registry + Lint)_ - Prevents schema mismatches in new lanes

## verifier
1. **Hook commit events to auto-trigger full regression battery** _(from: Auto-trigger regression battery)_ - Queue #4 requires unattended verification
2. **Define 5 inter-agent API contract tests for goal_ledger schema** _(from: Cross-lane contract tests)_ - Ensures cross-lane data integrity
3. **Generate acceptance tests from active lane goals files** _(from: Acceptance-test auto-generation)_ - Automates verification criteria creation

## designer
1. **Build red slide-in banner for autonomy score drops >5pts** _(from: Regression Alert Banner)_ - Queue #6 requires immediate regression alerting
2. **Render SVG graph of cross-lane assists with edge thickness** _(from: Cross-Lane Assist Graph)_ - Visualizes collaboration efficiency
3. **Create single 0-100 fleet health composite gauge widget** _(from: Fleet Health Composite Gauge)_ - Provides unified status view for operators

## archivist
1. **Analyze 6-cycle trend in decision-quality.jsonl** _(from: Decision Quality Longitudinal Analysis)_ - Tracks long-term decision quality improvement
2. **Design 3-tier knowledge system (T0/T1/T2) for small models** _(from: Knowledge Tiering for Small-Context Models)_ - Optimizes context usage for constrained agents
3. **Compile anomaly baseline library from OOM/timeout logs** _(from: Anomaly Baseline Library)_ - Establishes reference for future anomaly detection

## scribe
1. **Consolidate scattered convergence metrics into single KPI rollup** _(from: Convergence KPI Rollup (single source of truth))_ - Queue #9 requires single source of truth
2. **Parse cross-talk DMs to attribute assists across lanes** _(from: Cross-Lane Assist Attribution)_ - Quantifies collaborative value per agent
3. **Monitor conditions for convergence exit triggers** _(from: Convergence Exit-Trigger Monitor)_ - Identifies when fleet can reduce oversight

## mechanic
1. **Implement OOM detection to identify victim seat and unload model** _(from: Autonomous OOM Recovery Loop (<60s MTTR, unattended))_ - Queue #1 requires <60s MTTR unattended recovery
2. **Merge seat-matrix.json and autonomy-score.json into single heartbeat** _(from: Fleet Health Heartbeat Consolidation (single JSON, 4 seats))_ - Reduces polling overhead for health checks
3. **Auto-capture diagnostics when cycle exceeds duration SLA** _(from: Cycle Timeout Auto-Diagnostic (auto-capture on breach))_ - Enables rapid root-cause analysis on timeouts

## outlet
1. **Connect one real platform account for end-to-end ship test** _(from: First live account connection + end-to-end ship)_ - Queue #7 requires live account validation
2. **Implement queue_check.py to block unverified factual claims** _(from: Hard verification gate)_ - Prevents hallucinated content from shipping
3. **Generate X and LinkedIn voice variants for draft posts** _(from: Per-platform voice variants + lint)_ - Supports Generate daily social media posts day 2-4

## pixel
1. **Render compact reduced-motion-safe 24h health sparkline per host** _(from: Per-host 24h health sparkline)_ - Queue #8 requires visual health trends
2. **Add JS exception boundary to render inline error messages** _(from: Per-widget render error-boundary)_ - Prevents full UI crash on widget failure
3. **Audit ui/cockpit-*.js for hardcoded hex outside tokens.css** _(from: High-contrast / token-enforcement audit)_ - Enforces design system consistency

## forge
1. **Extend canary pipeline to gate dispatch-correctness changes** _(from: Dispatch-Correctness Deploy Gate)_ - Queue #2 requires deploy safety for routing logic
2. **Run scheduled check to enforce idle-productivity floor** _(from: Idle-Productivity Floor Enforcer)_ - Prevents agent stagnation during low activity
3. **Validate convergence_sentinel precision with test cases** _(from: Regression Sentinel Precision Test)_ - Ensures alerting system accuracy

## lumen
1. **Document current fleet autonomy status for stakeholder review** _(from: Fleet: {'done': 42, 'total': 111, 'pct': 37.8})_ - Supports transparency in 37.8% completion state
2. **Summarize day 1-2 progress on Commenting on posts lane** _(from: Commenting on posts [day 1-5])_ - Tracks early-stage lane execution

## reel
1. **Record video evidence of first automated social media post run** _(from: Generate daily social media posts [day 2-4])_ - Supports day 3 evidence leaf requirement
2. **Capture screen recording of phone call scaffold wiring** _(from: Making phone calls [day 3-7])_ - Documents day 3 Making phone calls setup

## splice
1. **Merge research briefs into skeleton post drafts for outlet** _(from: Trend-to-draft pipeline)_ - Feeds trend-to-draft pipeline for social media
2. **Combine market data streams for Predicting markets input** _(from: Predicting markets [day 5-7])_ - Prepares day 5 scaffold with unified data source

_round stats: {"sig": "5ad91397cbda", "date": "2026-11-26", "drafts": [{"label": "A", "agent": "mechanic", "model": "mechanic-q4", "stats": {"agents": 14, "items": 38, "grounded": 35, "ratio": 0.92, "missing": [], "repaired": false, "model": null}}], "source": "llm-single-draft"}_