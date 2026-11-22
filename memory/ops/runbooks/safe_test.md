# Safe Test Runbook

## Metadata
- agent: Builder
- trigger: test
- rollback_on_failure: true

## Steps

### Step 1: Echo hello
- command: `echo hello_from_runbook`
- expected: `hello_from_runbook`
- timeout: 10

### Step 2: Write marker file
- command: `python -c "open('memory/ops/runbooks/.test_marker','w').write('ok')"`
- expected: exit_code:0
- timeout: 15
- rollback_command: `python -c "import os;os.path.exists('memory/ops/runbooks/.test_marker') and os.remove('memory/ops/runbooks/.test_marker')"`

### Step 3: Echo done
- command: `echo runbook_complete`
- expected: `runbook_complete`
- timeout: 10

<!-- runbook-lessons:generated -->

## Lessons Learned

### 1. success (2026-11-22T20:26:35)

**What worked:**
- All 3 steps completed in 0.13s with zero rollbacks.
- Step 1 ('Echo hello'): output pattern verification worked as designed.
- Step 3 ('Echo done'): output pattern verification worked as designed.
- Step 1 ('Echo hello'): output pattern verification worked as designed.
- Step 3 ('Echo done'): output pattern verification worked as designed.
- Execution time (0.13s) well within expected bounds - no timeout risk for this runbook.

### 2. failed_at_step_3 (2026-11-22T20:26:38)

**What worked:**
- Rollback of 1 step(s) executed successfully - state restored cleanly.

**What didn't work:**
- Step 3 failed: expected output pattern not found (stdout was empty).
- Step 3 ('Echo done'): exit_code=-1, detail='pattern 'runbook_complete' NOT found; stdout='''

**Recommended changes:**
- [ ] Add pre-flight check before step 3: verify command produces non-empty stdout before pattern matching (current failure mode: empty output passes through to pattern check).
- [ ] Consider adding a retry-with-backoff for echo-type steps that may be affected by shell buffering.
