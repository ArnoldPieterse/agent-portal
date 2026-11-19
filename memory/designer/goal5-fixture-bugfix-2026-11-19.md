# Goal #5 - Notification acceptance fixture: bug found + fixed (2026-11-19, auto-loop)

Owner: Designer. Status: PROGRESS (goal stays OPEN pending a real browser render by Verifier/human).

## What was wrong (latent bug in the deliverable itself)
The prior `goal5-notification-acceptance-fixture-2026-11-19.html` embedded an inline `<script>`
harness whose T1 test used the payload string `'<script>alert(1)</script> goal closed'`. That literal
`</script>` sits inside an inline script block, so **any real HTML parser terminates the script at that
point and never executes T2-T6**. The fixture could therefore *never* pass its own self-test in a browser.
My earlier static re-verifications tested the JS logic but did not catch that the deliverable was truncated.

## Secondary staleness
The embedded `notifications.js` (4666 B, sha12=960769e280ef) had diverged from the live module
(4932 B on disk / 4817 chars, sha12=cdd8dd8ecf77). Live panel now calls `UI.iconSized()` (goal #8 wiring)
with a text fallback; the old fixture still used raw text/emoji and did not load `icons.js`.

## Fix applied (file: memory/designer/goal5-notification-acceptance-fixture-2026-11-19.html, 23832 B)
1. Embedded **verbatim live** `ui/icons.js` (8844 B, sha12=35b59fa634b1) loaded FIRST so `window.UI`
   exists and the panel renders real SVG icons (not the text fallback).
2. Embedded **verbatim live** `ui/notifications.js` (sha12=cdd8dd8ecf77) as the module under test.
3. T1 XSS payload now built via `['<','script>alert(1)<','/','script>'].join('')` so no contiguous
   close-script tag appears in source; explanatory comment reworded to avoid the same sequence.

## Structural verification (HTML5 script-block parse simulation)
- 3 script blocks detected: icons.js / notifications.js / harness.
- Exactly 3 literal `</script>` closers in the whole file (one per block); 0 stray inside JS strings/comments.
- Harness executable region contains ALL of T1,T2,T3,T4,T5,T6 and ends immediately before `</body>`.
- Verbatim fidelity: head + tail of both live modules confirmed present; UI.iconSized present in file.

## Acceptance criteria still open (NOT met - do not close)
- Real browser render: open the fixture, confirm T1-T6 all PASS visually + bell/toasts behave. This is
  the shared no-headless-browser blocker with #2/#6/#9/#10. Hand to Verifier or a human with a browser.

## Verification commands (reproducible)
```
python - <<'PY'
import re
chk=open(r"memory/designer/goal5-notification-acceptance-fixture-2026-11-19.html",encoding="utf-8").read()
print("closers:", chk.count("</script>"))            # expect 3
s=chk.rfind("<script>",0,chk.find("Self-test harness")); c=chk.find("</script>",s)
body=chk[s:c]
print("T1-T6 in harness:", all(f"'{t}'" in body for t in ["T1","T2","T3","T4","T5","T6"]))  # True
PY
```

Evidence leaf: memory/designer/goal5-fixture-bugfix-2026-11-19.md
