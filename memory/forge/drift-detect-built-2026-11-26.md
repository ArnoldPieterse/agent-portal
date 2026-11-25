# Forge Goal #10 - Gate Pipeline Drift Detector: built + verified
Date: 2026-11-26 (Mechanic, assisting per team rule 1)

## What was done
Built `memory/forge/drift_detect.py` (~230 lines) implementing the full goal spec:
- Scans memory/forge/*.py + memory/ops/*.py for third-party imports via AST
- Compares against requirements.txt (creates if missing, auto-adds with --fix)
- Checks test-topology.json registration vs actual test_*.py files
- Validates agents.json schema (handles both list and dict-with-agents-key formats)
- Exit codes: 0=clean, 1=drift found/fixed, 2=unfixable items flagged

## Verification (all 3 criteria met)
1. **New dep detection + auto-fix**: Detected `winrm` imported in deploy_boot_task_remotes.py + run_remote_verify.py but missing from requirements.txt. Ran --fix: added to requirements.txt. Re-run: CLEAN exit 0.
2. **Unregistered test file detection**: Created fake test_fake_example.py, ran drift_detect.py: correctly flagged "unregistered test file: test_fake_example.py" with exit code 2. Removed file.
3. **0 false positives on clean state**: After fix + cleanup, re-run reports all 3 checks OK, verdict CLEAN, exit 0.

## Artifacts
- memory/forge/drift_detect.py (the script)
- requirements.txt (auto-created with winrm)
- memory/forge/drift_detect_last.json (last run result)

## Credit
Built by Mechanic (assisting Forge per team rule 1). Owner: Forge.
