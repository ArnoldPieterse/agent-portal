# LLM planning chain - 2026-11-25

sig `d7416e786ecc` | sources: 30d=llm-single-draft 15d=llm-single-draft 7d=llm-single-draft

## 30-day plan - llm-single-draft (A by sole-draft)
> only one valid draft
- **Commenting on posts** (day 1-5, lane fleet) - Initial engagement loop active via custom input handling. | gates: Custom input detection (not in queue - schedulable ~day 1: seat frees + work time)
- **Generate daily social media posts** (day 2-4, lane fleet) - Automated content generation pipeline operational. | gates: Custom input detection (not in queue - schedulable ~day 1: seat frees + work time)
- **Making phone calls** (day 3-10, lane fleet) - Voice-based outreach capability enabled. | gates: Mic access (not in queue - schedulable ~day 1: seat frees + work time)
- **Writing valid tenders** (day 4-14, lane fleet) - Document processing and tender submission live. | gates: Camera access (not in queue - schedulable ~day 1: seat frees + work time)
- **Making money (revenue channels live)** (day 4-12, lane fleet) - Revenue streams activated via integrated capabilities. | gates: Custom input detection (not in queue - schedulable ~day 1: seat frees + work time), Camera access (not in queue - schedulable ~day 1: seat frees + work time)
- **Predicting markets** (day 5-20, lane researcher) - Market prediction models deployed and running. | gates: -
- **Positive money income (net > 0)** (day 19-26, lane fleet) [closes cycle] - Fleet achieves net positive financial status. | gates: Making money (revenue channels live) (ends day 12)

## 15-day plan - llm-single-draft (A by sole-draft)
> only one valid draft
- **Commenting on posts** -> parent Commenting on posts (day 0-5) - Full execution window within 15-day plan; gated by Custom input detection.
  - day 0-1: Implement Custom input detection capability to satisfy gate (schedulable ~day 1: seat frees + work time).
  - day 2-5: Execute commenting workflow on social media posts using verified custom input.
- **Generate daily social media posts** -> parent Generate daily social media posts (day 0-4) - Full execution window within 15-day plan; gated by Custom input detection.
  - day 0-1: Verify Custom input detection capability is live (shared gate with Commenting on posts).
  - day 2-4: Generate and publish daily social media content using the active input pipeline.
- **Making phone calls** -> parent Making phone calls (day 0-10) - Full execution window within 15-day plan; gated by Mic access.
  - day 0-1: Implement Mic access capability to satisfy gate (schedulable ~day 1: seat frees + work time).
  - day 2-10: Execute outbound and inbound phone call workflows using verified mic input.
- **Writing valid tenders** -> parent Writing valid tenders (day 0-14) - Full execution window within 15-day plan; gated by Camera access.
  - day 0-1: Implement Camera access capability to satisfy gate (schedulable ~day 1: seat frees + work time).
  - day 2-14: Draft, validate, and submit tenders using camera-captured documentation.
- **Making money (revenue channels live)** -> parent Making money (revenue channels live) (day 0-12) - Full execution window within 15-day plan; gated by Custom input detection and Camera access.
  - day 0-1: Ensure both Custom input detection and Camera access gates are satisfied (both schedulable ~day 1).
  - day 2-12: Activate revenue channels and process transactions using verified input and camera capabilities.
- **Predicting markets** -> parent Predicting markets (day 0-15) - Partial execution window; starts day 5, continues past day 15.
  - day 5-15: Run market prediction models on researcher lane; no gates required. Continues to day 20 of the 30-day plan.
- **Positive money income (net > 0) - prep** -> parent Positive money income (net > 0) (day 0-15) - Prep phase only; outcome starts day 19, but depends on 'Making money' ending day 12.
  - day 0-12: Ensure 'Making money (revenue channels live)' completes successfully by day 12 to satisfy the dependency gate for positive income.
  - day 13-15: Verify net revenue calculations and prepare financial reporting infrastructure for the day 19 start.

## 7-day plan - llm-single-draft (A by sole-draft)
> only one valid draft
- **Implement Custom input detection capability** -> parent Commenting on posts (day 0-1) - Gate implementation for social media workflows
  - day 0-0: Scaffold Custom input detection module and define API contract
  - day 1-1: Deploy Custom input detection to production seat and verify signal integrity
- **Execute commenting workflow on social media posts** -> parent Commenting on posts (day 2-5) - Active execution of commenting tasks using verified custom input
  - day 2-3: Run first batch of social media comments using Custom input detection pipeline
  - day 4-5: Continue commenting workflow; verify engagement metrics and log outcomes
- **Verify Custom input detection capability is live** -> parent Generate daily social media posts (day 0-1) - Shared gate verification for content generation pipeline
  - day 0-0: Integrate Custom input detection into content generation scaffold
  - day 1-1: Execute end-to-end test of input pipeline to confirm readiness for day 2 start
- **Generate and publish daily social media content** -> parent Generate daily social media posts (day 2-4) - Daily content generation and publication cycle
  - day 2-2: Generate first daily post using active input pipeline and publish
  - day 3-4: Continue daily generation cycle; monitor publication success rate
- **Implement Mic access capability** -> parent Making phone calls (day 0-1) - Gate implementation for voice communication workflows
  - day 0-0: Scaffold Mic access driver and configure audio input parameters
  - day 1-1: Deploy Mic access to production seat and validate audio capture quality
- **Execute outbound and inbound phone call workflows** -> parent Making phone calls (day 2-7) - Active phone call execution using verified mic input; continues in the 15-day plan
  - day 2-3: Run first batch of outbound calls and handle inbound requests via Mic access
  - day 4-7: Sustain phone call workflow; log call outcomes and continue in the 15-day plan
- **Implement Camera access capability** -> parent Writing valid tenders (day 0-1) - Gate implementation for documentation capture workflows
  - day 0-0: Scaffold Camera access module and define image capture standards
  - day 1-1: Deploy Camera access to production seat and verify image resolution and stability
- **Draft, validate, and submit tenders using camera-captured documentation** -> parent Writing valid tenders (day 2-7) - Tender drafting and validation cycle; continues in the 15-day plan
  - day 2-3: Capture initial documentation via Camera access and draft first tender
  - day 4-7: Validate tender compliance and submit; continue drafting cycle in the 15-day plan
- **Ensure both Custom input detection and Camera access gates are satisfied** -> parent Making money (revenue channels live) (day 0-1) - Dual gate verification for revenue channel activation
  - day 0-0: Scaffold integration layer linking Custom input detection and Camera access
  - day 1-1: Verify both gates are live and synchronized for revenue processing
- **Activate revenue channels and process transactions using verified input and camera capabilities** -> parent Making money (revenue channels live) (day 2-7) - Revenue channel activation and transaction processing; continues in the 15-day plan
  - day 2-3: Activate first revenue channel and process initial transactions
  - day 4-7: Scale transaction processing; monitor revenue flow and continue in the 15-day plan
- **Predicting markets - prep** -> parent Predicting markets (day 0-4) - Preparation phase for market prediction models starting day 5
  - day 0-2: Scaffold market prediction model environment and ingest historical data
  - day 3-4: Run initial model training cycles and validate baseline accuracy before day 5 start
- **Positive money income (net > 0) - prep** (day 0-7) - Dependency tracking and financial infrastructure preparation
  - day 0-7: Prepare financial reporting infrastructure and verify net revenue calculation logic for day 19 start
