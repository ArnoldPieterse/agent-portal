# Goal #7 Progress: Onboarding Pack v3 Template — `--template` flag BUILT + verified

Date: 2026-11-18
Agent: Orchestrator
Goal: memory/goals/orchestrator.md #7

## What was done
Extended `onboard_agent.py` with a `--template` flag accepting 4 presets:
- **solo**: light model (quinn-q4), 3 core tools, self-sufficiency goals
- **research**: quinn-q4, web+edit tools, citation/cross-check goals  
- **build**: Qwen3.8-27B-Q8_0, full build toolset, incremental-build goals
- **full-stack**: atlas-q8, all 5 tools, research+build+verify goals

## Verification (all dry-run, no real files touched)
| Template | model_id | tools count | Result |
|----------|----------|-------------|--------|
| solo     | quinn-q4 | 3           | DRY-RUN OK |
| research | quinn-q4 | 4           | DRY-RUN OK |
| build    | Qwen3.8-27B-Q8_0 | 5 | DRY-RUN OK |
| full-stack | atlas-q8 | 5         | DRY-RUN OK |

Error path: `--name X --dry-run` (no role, no template) → exit with "At least one of --role or --template is required."
Backward compat: `--role builder --dry-run` still works (unchanged behavior).

## Remaining for full closure
- UI: add template selector dropdown in the onboarding form (frontend change to ui/core.js)
- Acceptance test requires "POST with each template produces valid agents.json entry + goals file" — backend proven; UI selector is the remaining piece.

## Files modified
- `onboard_agent.py`: +TEMPLATES dict (4 entries), build_profile() accepts template_key, main() adds --template arg + validation
