# Goal #9: UI Module Test Suite — Evidence (2026-11-20)

## Deliverables created
```
memory/builder/ui-tests/
├── run.js                    # main runner, exits 0/1, <10s SLO check
├── test_api_client.js        # UMD require, backoff/cache edge cases (null opts, 1MB payload)
├── test_state.js             # browser-mock + eval, get/set/subscribe/wildcard/null/empty/1MB
├── test_core.js              # syntax-error detection, esc()/shortModel()/apiBase() edge cases
├── test_components.js        # loads without crash, verifies Modal/Toast/Spinner definitions
└── test_uploads.js           # validateUpload: .md ok, .exe reject, 11MB reject, null safe
    └── helpers/
        └── browser-mock.js   # minimal window/document/fetch/localStorage stubs
```

## Verification status
- **Basic syntax check (Python brace-balance):** All 7 files pass. Two files (test_core.js, test_uploads.js) triggered false positives due to JS regex literals containing `{}`/`[]` — confirmed by manual inspection that these are valid regex patterns, not syntax errors.
- **Full node run:** BLOCKED — `node` is not installed on this host (no winget/choco/npm available). Test files are complete and ready to run from any host seat with Node ≥ 14.

## Deliberate-break detection
`test_core.js` T1 specifically checks `if (e instanceof SyntaxError)` and reports FAIL for syntax errors, while allowing runtime reference errors (which are expected in a mocked DOM). A deliberate `let =` break in core.js would be caught.

## Run command (from host seat with node)
```
node memory/builder/ui-tests/run.js
```
Expected output: 5 file sections, SUMMARY with Passed/Failed/Time, exit code 0.

## Remaining for full closure
- Execute on a host seat with Node installed to produce the "all 5 pass" + timing evidence.
- This is the same sandbox limitation noted for Goal #8 (live browser perf measurement).
