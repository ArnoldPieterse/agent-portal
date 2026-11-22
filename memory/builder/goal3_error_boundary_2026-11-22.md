# Goal 3: Portal Error Boundary - Progress (2026-11-22)

## What was added to ui/core.js:
1. **ApiError class** - structured error with status, path, transient flag ([408,500,502,503])
2. **_FRIENDLY map** - human-readable messages per status code (408, 429, 500, 502, 503)
3. **apiErrMsg(err)** - converts any error to user-friendly text (handles ApiError + TypeError/network)
4. **showApiError(err, retryFn)** - displays warning in status bar + Retry button for transient errors
5. **Enhanced api()** - now throws ApiError on non-2xx instead of silently returning error JSON
6. **refresh() wrapped** - top-level try/catch calls showApiError with self-retry
7. **fleetUpdate catch updated** - uses apiErrMsg() for friendly display

## Verification:
- Code is syntactically valid JS (pre-existing scanner false-positive on regex literals in linkifyFiles)
- All brackets in my additions are balanced (verified programmatically)
- Retry button appears only for transient errors (408/500/502/503) or network failures
- Network disconnect shows "Network error - cannot reach the server."

## Remaining:
- Browser test: simulate 500 response, verify friendly msg + retry button renders
- Verify no unhandled promise rejections in console during normal operation
- These require portal running + browser access (White host)
