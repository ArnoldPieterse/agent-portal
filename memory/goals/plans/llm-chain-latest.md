# LLM planning chain - 2026-11-24

sig `c10efa44851f` | sources: 30d=llm-judge-local 15d=llm-judge-local 7d=llm-judge-local

## 30-day plan - llm-judge-local (A by local-rubric)
> judge seat unavailable - local rubric: grounding x4 + coverage x3 + day-fit bonus
- **Commenting on posts** (day 1-5, lane fleet) - Fleet autonomously engages with social content via custom input handling. | gates: Custom input detection (not in queue - schedulable ~day 1: seat frees + work time)
- **Generate daily social media posts** (day 2-4, lane fleet) - Automated generation of daily social media content begins. | gates: Custom input detection (not in queue - schedulable ~day 1: seat frees + work time)
- **Making phone calls** (day 3-10, lane fleet) - Fleet initiates and manages voice-based communications. | gates: Mic access (not in queue - schedulable ~day 1: seat frees + work time)
- **Writing valid tenders** (day 4-14, lane fleet) - Fleet drafts and submits compliant tender documents using visual verification. | gates: Camera access (not in queue - schedulable ~day 1: seat frees + work time)
- **Making money (revenue channels live)** (day 4-12, lane fleet) - Revenue-generating workflows are active and processing transactions. | gates: Custom input detection (not in queue - schedulable ~day 1: seat frees + work time), Camera access (not in queue - schedulable ~day 1: seat frees + work time)
- **Predicting markets** (day 5-20, lane researcher) - Research agent produces market prediction models and insights. | gates: -
- **Positive money income (net > 0)** (day 19-26, lane fleet) [closes cycle] - Fleet achieves net positive financial performance, closing the 30-day cycle. | gates: Making money (revenue channels live) (ends day 12)

## 15-day plan - llm-judge-local (A by local-rubric)
> judge seat unavailable - local rubric: grounding x4 + coverage x3 + day-fit bonus
- **Commenting on posts** -> parent Commenting on posts (day 1-5) - Full execution window within the 15-day plan; dependent on Custom input detection gate.
  - day 0-1: Implement and verify 'Custom input detection' capability to satisfy the gate requirement (schedulable ~day 1).
  - day 2-5: Execute commenting workflow on social media posts using the newly enabled custom input detection.
- **Generate daily social media posts** -> parent Generate daily social media posts (day 2-4) - Full execution window within the 15-day plan; dependent on Custom input detection gate.
  - day 0-1: Finalize 'Custom input detection' capability to unlock post generation inputs (gate schedulable ~day 1).
  - day 2-4: Generate and publish daily social media posts leveraging the active custom input detection.
- **Making phone calls** -> parent Making phone calls (day 3-10) - Full execution window within the 15-day plan; dependent on Mic access gate.
  - day 0-2: Implement 'Mic access' capability to satisfy the gate requirement (schedulable ~day 1, buffer until day 2).
  - day 3-10: Execute phone call workflows using the enabled microphone access.
- **Writing valid tenders** -> parent Writing valid tenders (day 4-14) - Full execution window within the 15-day plan; dependent on Camera access gate.
  - day 0-3: Implement 'Camera access' capability to satisfy the gate requirement (schedulable ~day 1, buffer until day 3).
  - day 4-14: Draft and validate tender documents using camera-based document scanning/input.
- **Making money (revenue channels live)** -> parent Making money (revenue channels live) (day 4-12) - Full execution window within the 15-day plan; dependent on Custom input detection and Camera access gates.
  - day 0-3: Implement 'Custom input detection' and 'Camera access' capabilities to satisfy both gate requirements.
  - day 4-12: Activate revenue channels and process transactions using the enabled input and camera capabilities.
- **Predicting markets** -> parent Predicting markets (day 5-15) - Partial execution window; starts day 5 and continues past the 15-day limit.
  - day 5-10: Initialize market prediction models and begin data ingestion on lane researcher.
  - day 11-15: Refine prediction accuracy and validate outputs; continues to day 20 of the 30-day plan.
- **Positive money income (net > 0) - prep** -> parent Positive money income (net > 0) (day 0-15) - Preparation phase only; actual income realization starts day 19. Must ensure 'Making money' dependency completes by day 12.
  - day 0-3: Ensure 'Custom input detection' and 'Camera access' gates are cleared to support the 'Making money' prerequisite.
  - day 4-12: Verify that 'Making money (revenue channels live)' executes successfully, as it is a hard gate for positive income.
  - day 13-15: Audit revenue channel stability and prepare financial reporting infrastructure; actual net-positive income begins day 19 of the 30-day plan.

## 7-day plan - llm-judge-local (A by local-rubric)
> judge seat unavailable - local rubric: grounding x4 + coverage x3 + day-fit bonus
- **Commenting on posts - gate & execution** -> parent Commenting on posts (day 0-7) - Gate implementation (Custom input detection) and initial workflow execution.
  - day 0-1: Implement 'Custom input detection' capability to satisfy the gate requirement; verify integration with social media API.
  - day 2-5: Execute commenting workflow on social media posts using the newly enabled custom input detection; monitor engagement metrics.
  - day 6-7: Refine comment generation logic based on day 2-5 feedback; continues in the 15-day plan for full window completion.
- **Generate daily social media posts - gate & execution** -> parent Generate daily social media posts (day 0-7) - Gate finalization and post generation/publishing cycle.
  - day 0-1: Finalize 'Custom input detection' capability to unlock post generation inputs; ensure stable data feed.
  - day 2-4: Generate and publish daily social media posts leveraging the active custom input detection; verify content accuracy.
  - day 5-7: Analyze performance of generated posts; adjust generation parameters for subsequent days; continues in the 15-day plan.
- **Making phone calls - gate & execution** -> parent Making phone calls (day 0-7) - Mic access implementation and initial call workflow testing.
  - day 0-2: Implement 'Mic access' capability to satisfy the gate requirement; include buffer for permission handling and hardware verification.
  - day 3-7: Execute phone call workflows using the enabled microphone access; test voice recognition accuracy and latency; continues in the 15-day plan.
- **Writing valid tenders - gate & execution** -> parent Writing valid tenders (day 0-7) - Camera access implementation and initial document scanning setup.
  - day 0-3: Implement 'Camera access' capability to satisfy the gate requirement; include buffer for calibration and OCR pipeline setup.
  - day 4-7: Draft initial tender documents using camera-based document scanning/input; validate OCR accuracy against source documents; continues in the 15-day plan.
- **Making money (revenue channels live) - gate & execution** -> parent Making money (revenue channels live) (day 0-7) - Dual-gate implementation and revenue channel activation.
  - day 0-3: Implement 'Custom input detection' and 'Camera access' capabilities to satisfy both gate requirements; verify concurrent operation.
  - day 4-7: Activate revenue channels and process initial transactions using the enabled input and camera capabilities; monitor transaction success rates; continues in the 15-day plan.
- **Predicting markets - prep & initialization** -> parent Predicting markets (day 0-7) - Model initialization and data ingestion start.
  - day 5-7: Initialize market prediction models and begin data ingestion on lane researcher; establish baseline metrics for accuracy tracking; continues in the 15-day plan.
- **Positive money income (net > 0) - prep** (day 0-7) - Dependency verification and financial infrastructure preparation.
  - day 0-3: Ensure 'Custom input detection' and 'Camera access' gates are cleared to support the 'Making money' prerequisite; verify gate status in live state.
  - day 4-7: Verify that 'Making money (revenue channels live)' executes successfully as a hard gate for positive income; begin auditing revenue channel stability; continues in the 15-day plan.
