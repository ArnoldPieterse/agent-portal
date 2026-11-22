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
