# Context Handoff Template

Standard format for passing context between agents. Every field is REQUIRED.

## Format

```
TASK: <one-line description of what needs to be done>
COMPLETED_STEPS:
  - <step 1 already done>
  - <step 2 already done>
CURRENT_STATE: <where things stand right now, 1-3 sentences>
BLOCKERS:
  - <blocker or "none">
NEXT_ACTION: <the single next concrete step to take>
RELEVANT_FILES:
  - <path/to/file1>
  - <path/to/file2>
```

## Validation Rules

1. All 6 field headers must be present (TASK, COMPLETED_STEPS, CURRENT_STATE, BLOCKERS, NEXT_ACTION, RELEVANT_FILES)
2. TASK must be non-empty
3. COMPLETED_STEPS must have at least one bullet
4. CURRENT_STATE must be non-empty
5. BLOCKERS may say "none" but must not be empty
6. NEXT_ACTION must be non-empty
7. RELEVANT_FILES must have at least one path

## Example

```
TASK: Migrate decision log entries to v2 structured format
COMPLETED_STEPS:
  - Wrote migration script (migrate_decisions.py)
  - Ran on 10 existing entries
CURRENT_STATE: 8/10 entries migrated; 2 have missing 'alternatives_considered' field
BLOCKERS:
  - None
NEXT_ACTION: Fill in alternatives_considered for the 2 incomplete entries, re-run validation
RELEVANT_FILES:
  - memory/synthesis/decisions.md
  - memory/scribe/migrate_decisions.py
```
