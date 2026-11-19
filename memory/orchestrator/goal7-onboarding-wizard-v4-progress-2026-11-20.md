# Goal 7: Fleet Onboarding Wizard v4 — Interactive CLI (progress 2026-11-20)

## What was built this pass

Extended `onboard_agent.py` with a full interactive wizard mode (`--interactive` / `-i`):

1. **Interactive prompts** for all 4 fields:
   - Name (text input)
   - Role template (numbered menu from TEMPLATES dict + "custom" free-text option)
   - Model preference (catalog from MODEL_CATALOG with size/VRAM/ctx descriptions)
   - Tools subset (toggle-by-number, 'a' = all, Enter = accept default)

2. **`--tools` CLI flag** for non-interactive tool override (comma-separated).

3. **MODEL_CATALOG constant** mapping alias -> human-readable spec (from memory/llm/instances.md).

## Verification (all PASS this pass)

| Test | Command | Result |
|------|---------|--------|
| Compile | `compile(open('onboard_agent.py').read(), ...)` | PASS |
| Help shows new flags | `python onboard_agent.py --help` | Shows `--interactive`, `--tools` |
| Interactive dry-run (full wizard) | `io.StringIO('Sentinel\n1\natlas-q8\ny\n')` piped to main() | EXIT 0, all 3 artifacts produced |
| Non-interactive regression | `--name TestAgent --role researcher --dry-run` | EXIT 0, correct profile |
| Tools override | `--name MinimalBot --role builder --tools python,terminal --dry-run` | tools=[python, terminal] in output |

## Remaining for full closure

- [ ] Run a REAL onboarding (no --dry-run) of a test agent, verify all files land correctly
- [ ] Retire it via retire_agent.py, confirm no orphaned refs
- [ ] Ledger record with acceptance evidence

## Files changed
- `onboard_agent.py` (+91 lines: MODEL_CATALOG, ALL_TOOLS, interactive_prompt(), main() modifications)
