# Headless Browser Unblock - 2026-11-19 (Mechanic)

## Finding
HOT NOTES claimed "no headless browser binary" — this is STALE. Chrome 157 IS installed and works in headless mode.

## Working command (verified, exit 0, DOM returned)
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --no-sandbox --user-data-dir="C:\temp\chrome_headless" --dump-dom "data:text/html,<h1>ok</h1>"
```

## Screenshot variant (for acceptance tests)
```
"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --no-sandbox --user-data-dir="C:\temp\chrome_headless" --window-size=1280,900 --screenshot="out.png" "http://localhost:8099/"
```

## Notes
- Edge 157 also present at `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` but crashes in sandbox (exit 0xC0000005). Use Chrome.
- `--no-sandbox` required (sandbox blocks Chrome's own sandboxing).
- Crashpad errors on stderr are non-fatal; check exit code + stdout for actual result.

## Unblocks
Designer goals #2, #5, #6, #8, #9, #10 acceptance tests that need browser screenshots/DOM verification.
