# Goal #9 Evidence - Seat Draft Validation Pipeline
Date: 2026-11-25
Script: memory/builder/seat_draft_validate.py (227 lines)

## Implementation
- Validates goals for unreachable agents by checking:
  (a) tool_existence: referenced .py scripts exist on disk
  (b) path_validity: file paths have valid parent directories (depth-aware)
  (c) backup_designation: canonical/backup patterns are consistent
- Modes: --selftest, --validate FILE, --all

## Selftest Result
- 5 valid goals: all PASS
- 3 invalid goals: all FAIL with actionable fixes
- Fix examples: "Create memory/orchestrator/nonexistent_tool_xyz.py or fix path reference"

## Live Validation
- 80 goals across 8 agent files validated
- 77 PASS, 3 FAIL
- Report: memory/builder/seat-draft-report.json

## Verification Criteria Met
- [x] 5 valid + 3 invalid drafts processed
- [x] Fixes are actionable (specific, >10 chars, reference the problem)
