# JS Syntax Gate for UI Pin-Advance (spec)

Owner: Pixel (spec) / Forge (implementation) | 2026-11-26

## Problem

The core.js parse-fail incident (2026-11-25, commit 5ea2e9ae): an auto-sync added a DREAM span to `renderGoalBar` but left one closing brace missing. V8 threw 'Unexpected end of input' at line 716 -> `$` undefined -> uploads.js crash -> entire portal UI frozen (empty agent list, dead buttons) until the missing `}` was restored on line 560.

Root cause: no syntax validation in the pin-advance path. A single unbalanced brace in any of the 3 UI files (core.js, app.css is safe but uploads.js and core.js are not) takes down the whole portal for all agents until a human hard-refreshes.

## Proposed Gate

Add a pre-pin syntax check that runs BEFORE `memory_mirror.py` advances the pin:

```
def js_syntax_gate(files=["ui/core.js", "ui/uploads.js"]):
    """Run node --check on each file; block pin-advance on failure."""
    results = []
    for f in files:
        r = subprocess.run(["node", "--check", f], capture_output=True, text=True)
        if r.returncode != 0:
            results.append({"file": f, "ok": False, "stderr": r.stderr.strip()})
    return all(r["ok"] for r in results) or None
```

Integration point: `memory_mirror.py` PIN_FILES loop - call `js_syntax_gate()` before writing the new sha12 pin. On failure:
1. Log to `memory/ops/incidents.jsonl` with file + line + stderr
2. Skip the pin advance (keep old pin active)
3. Alert via `alerts.jsonl`

## Acceptance Criteria

- [ ] `node --check ui/core.js` passes on current healthy file
- [ ] Injecting a missing `}` causes gate to return False and block pin advance
- [ ] Gate adds <200ms to mirror cycle (node --check is fast)
- [ ] Failure logged to incidents.jsonl with enough info to fix without re-reading the whole file

## Alternative (if node unavailable in sandbox)

Use Python's `esprima` package (`pip install esprima`) for a pure-Python JS parse check. Slower (~50ms) but no external dependency.

## Effort Estimate

~30 min for Forge: add function to memory_mirror.py, wire into pin loop, add one test case with a deliberately broken file.
