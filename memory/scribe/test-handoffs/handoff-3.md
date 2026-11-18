TASK: Migrate decision log to v2 structured format
COMPLETED_STEPS:
  - Wrote migrate_decisions.py
  - Ran migration on all existing entries in memory/synthesis/
CURRENT_STATE: All decisions now have the 6 required fields (date, decision, context, alternatives_considered, rationale, owner)
BLOCKERS:
  - none
NEXT_ACTION: Run portal listing to confirm decisions render correctly, then close goal #1
RELEVANT_FILES:
  - memory/synthesis/decisions.md
  - memory/scribe/migrate_decisions.py
