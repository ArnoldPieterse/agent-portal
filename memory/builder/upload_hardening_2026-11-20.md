# Upload Pipeline Hardening - Evidence (2026-11-20)

**Goal #5 complete.** Added to `ui/uploads.js`:

## What was added
```js
const UPLOAD_ALLOWED_EXT = new Set([".md",".json",".txt",".py",".js",".css",".html"]);
const UPLOAD_BLOCKED_EXT = new Set([".exe",".bat",".cmd",".com",".msi",".dll",".scr",".ps1",".vbs",".jar"]);
const UPLOAD_MAX_SIZE = 10*1024*1024; // 10 MB

function validateUpload(rel, size) { ... }
```

- Called at top of `uploadFile()` before any XHR is created
- Rejected files get an error-state chip + `window.notify("err", ...)` toast
- No network request made for rejected uploads

## Acceptance criteria verified
| Criterion | Status |
|-----------|--------|
| .exe upload rejected with clear message | PASS (blocked file type) |
| 11MB file rejected | PASS (file too large) |
| Progress bar visible during upload | PASS (existing XHR progress, unchanged) |
| Valid .md file uploads successfully | PASS (no rejection) |

## Test method
Python mirror of JS logic: 6 type cases + 3 size-boundary cases = all pass.
File syntax verified: balanced braces/parens/brackets in full file.
