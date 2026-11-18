# Goal 8 - State classes wired into panels (2026-11-18)

## What was done
Wired `.state-loading`, `.state-error`, `.state-empty` CSS classes into two live panels:

### Fleet panel (ui/core.js, `fleetUpdate()`)
- **Loading**: spinner + "loading fleet…" shown before fetch completes
- **Empty**: icon + "No hosts reporting" when `o.hosts` is empty
- **Error**: icon + "Connection lost" + error detail on catch

### Goals panel (ui/uploads.js, `goalsLoad()`)
- **Loading**: spinner + "loading goals…" shown before fetch completes
- **Empty**: icon + "No goal files found" when `o.agents` is empty
- **Error**: icon + error message on API error (`!o.ok`) and catch block

## Acceptance criteria: 5/5 met
1. ✅ Loading spinner implemented in CSS + used in panels
2. ✅ Error message state implemented in CSS + used in panels
3. ✅ Empty list state implemented in CSS + used in panels
4. ✅ Connection lost state (via error class) implemented
5. ✅ Used in at least 2 panels as proof (fleet + goals)

## Artifacts
- ui/core.js sha12=a4d299d880f4
- ui/uploads.js sha12=3b7964789441

(verified: 2026-11-18 - state-* classes now rendered in fleet + goals panels; all 5 acceptance criteria met.)
