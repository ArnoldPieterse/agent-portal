# Builder r35 — A4+A5 hash-gated apply: LANDED (2026-11-14 ~08:2x)

## What ran
`apply_a4_a5_r35.py` (hash-gated one-shot) against base **67,681 B / 9c6b08e3d98355e632a72cb871d5b60d** (Verifier r34 canonical ruling; gate PASS).

- **A5** (designer r28 spec): 4/4 anchors — `--acc-strong:#2f6fe0` token added; `.seg button.on`, `#send`, `.btn.pri` switched to `var(--acc-strong)`. Fingerprint: exactly **5** occurrences of `--acc-strong` in file.
- **A4 Hunk B (CSS)**: `#modeBar` gained `position:relative`; new rule `#panelDock{position:absolute;top:100%;left:0;right:0;z-index:30;display:flex;flex-direction:column}`.
- **A4 Hunk B (markup)**: the 28 panel lines (actPanel→filesPanel incl. close) moved into `<div id="panelDock">` inside `#modeBar`, after stopBtn, before modeBar's own close. DOM order verified: stopBtn < panelDock-open < actPanel < filesPanel-close < msgs.
- **A4 Hunk A (JS)**: byte-exact block inserted after `$("filesRefresh").onclick=filesLoad;` — `panelToggles` map (act/fleet/ops/files), `panelClose(k)` (delegates to owning btn.click so actTimer/fleetTimer cleanup still runs), document-level outside-click handler. Braces/parens balanced.

## First bug + fix (honest note)
First run FAILED post-check: `crlf_consistent=False`. Root cause: inserted JS block ended without trailing `\r` directly before the original `\n</script>` → 1 bare LF at offset 68602. Fix: `+ b"\r"` on the insertion; restored base from backup (`index.html.pre-a4a5-r35.bak`) and re-ran clean.

## New canonical candidate (on disk now, this seat)
- **size**: 68,633 B
- **md5**: `45323d09717ac3a9dc0e098015863d81`
- bare LF: 0; scripts 2/2; ends `</html>`
- string counts (changed vs old canonical due to A4 JS refs): filesPanel 4→5, filesBtn 6→7, opsBtn 3→4, actPanel 7, fleetPanel 6

## For Verifier / Designer
Re-count against the NEW fingerprint above (old r19 counts are stale by +1 each on the toggle ids). Apply is local to this seat's index.html only — White-console stamp/pin remains Arnold's human leg per transport rule; backup preserved at `index.html.pre-a4a5-r35.bak`.
