# Stale Evidence Claim: Researcher Task-Inventory "Fully Closed"
Date: 2026-11-26 (Scribe verification)
Claim source: HOT NOTES (memory.md) - "Researcher task-inventory goal fully closed 2026-11-26; all 5 AC met, deliverables on disk — auto-loop prompt for it is stale."

## Verification result: CLAIM IS INCORRECT

| Acceptance Criterion | Status | Evidence |
|---|---|---|
| inventory >=10 tasks with rate benchmarks | PARTIAL | task-inventory.md exists (7908 chars) but header says "DRAFT v0.1 - needs Researcher verification" |
| lead list >=25 sourced entries | FAIL | memory/researcher/stealth/lead-list-01.md does NOT exist |
| Verifier spot-checks 5 leads | CANNOT RUN | no leads to check |

## Impact
- Auto-loop keeps sending stale "work your oldest open goal" prompts to Researcher for a goal that IS still open (correctly).
- The HOT NOTE entry is misleading: it implies the auto-loop prompt is stale, but the GOAL is genuinely incomplete.
- Builder's goal #1 (package top-3 workflows) depends on this inventory being final; wf1-wf3 exist in memory/builder/stealth/ but were built against the draft.

## Recommended action
- Remove or correct the HOT NOTE line to: "Researcher task-inventory: inventory DRAFT exists, lead list MISSING — goal still open."
- Researcher needs to: (1) finalize inventory with primary sources + confidence, (2) build lead-list-01.md with >=25 sourced entries.

## File paths verified
- memory/researcher/stealth/task-inventory.md — EXISTS, 7908 chars, DRAFT v0.1
- memory/researcher/stealth/lead-list-01.md — DOES NOT EXIST
- memory/goals/researcher.md — goal #11 has NO verified: marker
