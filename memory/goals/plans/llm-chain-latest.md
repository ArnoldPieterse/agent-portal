# LLM planning chain - 2026-11-25

sig `1b3960ae0e7c` | sources: 30d=llm-judge-local 15d=llm-judge-local 7d=llm-judge-local

## 30-day plan - llm-judge-local (A by local-rubric)
> judge seat unavailable - local rubric: grounding x4 + coverage x3 + day-fit bonus
- **Commenting on posts** (day 1-5, lane fleet) - Automated engagement loop active on social channels. | gates: Custom input detection (not in queue - schedulable ~day 1: seat frees + work time)
- **Generate daily social media posts** (day 2-4, lane fleet) - Consistent daily content output generated and published. | gates: Custom input detection (not in queue - schedulable ~day 1: seat frees + work time)
- **Making phone calls** (day 2-9, lane fleet) - Voice-based outreach and support capabilities operational. | gates: Mic access (already reached)
- **Writing valid tenders** (day 4-14, lane fleet) - Automated generation of compliant tender documents. | gates: Camera access (not in queue - schedulable ~day 1: seat frees + work time)
- **Making money (revenue channels live)** (day 4-12, lane fleet) - All revenue-generating workflows are live and processing transactions. | gates: Custom input detection (not in queue - schedulable ~day 1: seat frees + work time), Camera access (not in queue - schedulable ~day 1: seat frees + work time)
- **Predicting markets** (day 5-20, lane researcher) - Market prediction models deployed and generating signals. | gates: -
- **Positive money income (net > 0)** (day 19-26, lane fleet) [closes cycle] - Fleet achieves net positive cash flow, closing the 30-day business cycle. | gates: Making money (revenue channels live) (ends day 12)

## 15-day plan - llm-judge-local (A by local-rubric)
> judge seat unavailable - local rubric: grounding x4 + coverage x3 + day-fit bonus
- **Commenting on posts** -> parent Commenting on posts (day 1-5) - Full execution window within the 15-day plan; requires Custom input detection gate to be resolved by day 1.
  - day 0-1: Implement and verify 'Custom input detection' capability (gate) as part of 'Package top-3 workflows' or standalone sprint, ensuring seat frees + work time allocation.
  - day 1-2: Scaffold commenting workflow: define target platforms, tone guidelines, and input parsing logic using the newly enabled custom input detection.
  - day 3-4: First run: Execute automated comments on low-risk posts to validate pipeline stability and latency.
  - day 5-5: Verify engagement metrics and finalize workflow for steady-state operation; outcome completes within window.
- **Generate daily social media posts** -> parent Generate daily social media posts (day 2-4) - Full execution window within the 15-day plan; requires Custom input detection gate to be resolved by day 1.
  - day 0-1: Finalize 'Custom input detection' (gate) integration with content generation pipeline, leveraging 'Milestone Auto-Draft Trigger' infrastructure if applicable.
  - day 2-2: Scaffold daily post generator: connect custom inputs to LLM prompt templates and scheduling queue.
  - day 3-3: First run: Generate and publish first batch of daily posts; monitor for formatting errors or API failures.
  - day 4-4: Verify content quality and scheduling accuracy; outcome completes within window.
- **Making phone calls** -> parent Making phone calls (day 2-9) - Full execution window within the 15-day plan; Mic access gate is already reached, so no blocking dependencies.
  - day 2-3: Scaffold call automation: configure telephony API connections and voice synthesis parameters using existing Mic access capability.
  - day 4-5: First run: Execute test calls to verify audio quality, latency, and connection stability.
  - day 6-8: Stabilize workflow: integrate call logging with 'Daily $ ledger' and handle edge cases (no-answer, busy signals).
  - day 9-9: Verify end-to-end reliability; outcome completes within window.
- **Writing valid tenders** -> parent Writing valid tenders (day 4-14) - Execution starts day 4 and continues past day 15; requires Camera access gate to be resolved by day 1.
  - day 0-1: Implement 'Camera access' capability (gate) to enable document scanning/OCR for tender inputs, aligned with 'seat frees + work time'.
  - day 2-3: Scaffold tender generation pipeline: define template structures and integrate camera-based input parsing.
  - day 4-7: First run: Generate draft tenders for available opportunities; validate compliance with specific tender requirements.
  - day 8-12: Stabilize and refine: iterate on feedback from generated tenders, improve accuracy of extracted data, and automate submission checks.
  - day 13-15: Continues to day 14 of the 30-day plan: Finalize remaining tender drafts and prepare for post-day-15 review cycles.
- **Making money (revenue channels live)** -> parent Making money (revenue channels live) (day 4-12) - Full execution window within the 15-day plan; requires Custom input detection and Camera access gates to be resolved by day 1.
  - day 0-1: Resolve both 'Custom input detection' and 'Camera access' gates (as per previous entries) to unblock revenue channel setup.
  - day 2-3: Scaffold revenue channels: configure payment gateways, link service offerings (from tenders/social posts), and set up tracking in 'Daily $ ledger'.
  - day 4-6: First run: Activate first revenue channel (e.g., freelance tender submission or social media lead generation) and process initial transactions.
  - day 7-10: Stabilize operations: monitor transaction success rates, optimize conversion funnels, and ensure ledger accuracy.
  - day 11-12: Verify revenue flow consistency; outcome completes within window, setting up for 'Positive money income' later in the 30-day plan.
- **Predicting markets** -> parent Predicting markets (day 5-15) - Execution starts day 5 and continues past day 15; no specific gates listed, but relies on researcher lane capabilities.
  - day 5-7: Scaffold prediction models: define data sources, feature engineering pipelines, and baseline algorithms using 'Repetitive-task inventory' insights.
  - day 8-10: First run: Execute initial market predictions on historical data; validate accuracy against known outcomes.
  - day 11-13: Stabilize and refine: tune model parameters, integrate real-time data feeds, and establish confidence scoring mechanisms.
  - day 14-15: Continues to day 20 of the 30-day plan: Prepare for live prediction deployment and ongoing monitoring cycles.
- **Positive money income (net > 0) - prep** -> parent Positive money income (net > 0) (day 0-15) - Outcome starts day 19, so this entry covers prerequisite gate work and setup that must finish by day 15 to ensure the 30-day plan holds.
  - day 0-1: Ensure 'Making money (revenue channels live)' prerequisites (Custom input detection, Camera access) are fully resolved and stable.
  - day 4-12: Execute 'Making money (revenue channels live)' to establish active revenue streams; this is the direct gate for positive income.
  - day 13-15: Verify that revenue channels are generating consistent gross income and that cost tracking in 'Daily $ ledger' is accurate, preparing for net-positive calculation starting day 19.

## 7-day plan - llm-judge-local (A by local-rubric)
> judge seat unavailable - local rubric: grounding x4 + coverage x3 + day-fit bonus
- **Commenting on posts** -> parent Commenting on posts (day 0-5) - Active: Gate resolved day 1, scaffold days 1-2, first run days 3-4, verify day 5.
  - day 0-1: Implement and verify 'Custom input detection' capability (gate) as part of 'Package top-3 workflows' or standalone sprint, ensuring seat frees + work time allocation.
  - day 1-2: Scaffold commenting workflow: define target platforms, tone guidelines, and input parsing logic using the newly enabled custom input detection.
  - day 3-4: First run: Execute automated comments on low-risk posts to validate pipeline stability and latency.
  - day 5-5: Verify engagement metrics and finalize workflow for steady-state operation; outcome completes within window.
- **Generate daily social media posts** -> parent Generate daily social media posts (day 0-4) - Active: Gate integration day 1, scaffold day 2, first run day 3, verify day 4.
  - day 0-1: Finalize 'Custom input detection' (gate) integration with content generation pipeline, leveraging 'Milestone Auto-Draft Trigger' infrastructure if applicable.
  - day 2-2: Scaffold daily post generator: connect custom inputs to LLM prompt templates and scheduling queue.
  - day 3-3: First run: Generate and publish first batch of daily posts; monitor for formatting errors or API failures.
  - day 4-4: Verify content quality and scheduling accuracy; outcome completes within window.
- **Making phone calls** -> parent Making phone calls (day 2-7) - Active: Scaffold days 2-3, first run days 4-5, stabilization begins day 6 (continues in the 15-day plan).
  - day 2-3: Scaffold call automation: configure telephony API connections and voice synthesis parameters using existing Mic access capability.
  - day 4-5: First run: Execute test calls to verify audio quality, latency, and connection stability.
  - day 6-7: Stabilize workflow (start): integrate call logging with 'Daily $ ledger' and handle edge cases (no-answer, busy signals); continues in the 15-day plan.
- **Writing valid tenders** -> parent Writing valid tenders (day 0-7) - Active: Gate resolved day 1, scaffold days 2-3, first run days 4-7 (continues in the 15-day plan).
  - day 0-1: Implement 'Camera access' capability (gate) to enable document scanning/OCR for tender inputs, aligned with 'seat frees + work time'.
  - day 2-3: Scaffold tender generation pipeline: define template structures and integrate camera-based input parsing.
  - day 4-7: First run (start): Generate draft tenders for available opportunities; validate compliance with specific tender requirements; continues in the 15-day plan.
- **Making money (revenue channels live)** -> parent Making money (revenue channels live) (day 0-7) - Active: Gates resolved day 1, scaffold days 2-3, first run days 4-6, stabilization begins day 7 (continues in the 15-day plan).
  - day 0-1: Resolve both 'Custom input detection' and 'Camera access' gates to unblock revenue channel setup.
  - day 2-3: Scaffold revenue channels: configure payment gateways, link service offerings (from tenders/social posts), and set up tracking in 'Daily $ ledger'.
  - day 4-6: First run: Activate first revenue channel (e.g., freelance tender submission or social media lead generation) and process initial transactions.
  - day 7-7: Stabilize operations (start): monitor transaction success rates, optimize conversion funnels, and ensure ledger accuracy; continues in the 15-day plan.
- **Predicting markets - prep** -> parent Predicting markets (day 0-7) - Prep: Execution starts day 5; scaffold days 5-7 (continues in the 15-day plan).
  - day 5-7: Scaffold prediction models: define data sources, feature engineering pipelines, and baseline algorithms using 'Repetitive-task inventory' insights; continues in the 15-day plan.
- **Positive money income (net > 0) - prep** (day 0-7) - Prep: Ensure gates resolved day 1; execute revenue channels days 4-7 (continues in the 15-day plan).
  - day 0-1: Ensure 'Making money (revenue channels live)' prerequisites (Custom input detection, Camera access) are fully resolved and stable.
  - day 4-7: Execute 'Making money (revenue channels live)' to establish active revenue streams; this is the direct gate for positive income; continues in the 15-day plan.
