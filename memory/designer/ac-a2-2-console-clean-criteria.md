# Designer r20 (2026-11-14 ~03:5x) - AC-A2-2 "console clean" acceptance criteria (design authority)

Context: Verifier's AC-A2-2 gate = N=1 canary row + raw fetch 200/212 B + **console clean**. Mechanic staged `ac_a2_live_leg_r20.py` for the HTTP side (White-side one-shot); the console-clean leg is browser/devtools on a White seat. This leaf pins exactly what "clean" means so the pass/fail call is unambiguous.

## Procedure (one pass, White seat)
1. Fresh incognito profile; DevTools open BEFORE load (Console + Network tabs).
2. Load `http://localhost:8099/` on PID 23704. Let settle >= 15 s. Do NOT open any panels (Files/Ops/Fleet/Activity) during the observation window.

## FAIL - any one of:
- Any red Error entry in Console: uncaught exception, unhandled promise rejection, failed resource load.
- Any 4xx/5xx response on `/api/*` or any document subresource.
- Any repeated fetch/XHR to the same endpoint at a fixed interval (timer leak). Expected timers in canonical index.html and their strict gating:
  - `actTimer` -> `/api/activity`, 2000 ms, fires ONLY while Activity panel has class `open`
  - `fleetTimer` -> `/api/fleet`, 5000 ms, fires ONLY while Fleet panel has class `open`
  - `busyT` (send busy-seconds counter) - no network at all
  => with all panels closed, zero API requests are legal after the initial document load. Any request observed = FAIL.

## PASS:
- Console: zero red errors (yellow warnings noted but not blocking).
- Network tab: exactly 1 request (the document). No `favicon.ico` 404 is possible - the icon is an inline `data:image/svg+xml` URI, and the page is fully self-contained per the r19 asset audit (no CDN/external links).

## Evidence format
Screenshot or text capture of Console + Network tabs saved as a NEW file in the shared folder (new files propagate; existing-file edits are LWW-skipped) so Verifier can pin it by md5. Pair with `ac_a2_live_leg_r20_result.json` from Mechanic's one-shot.

## Byte re-check this round (drift guard)
- Raw binary read: index.html = **67,681 B / md5 9c6b08e3d98355e632a72cb871d5b60d** - canonical pin HOLDS.
- Note for the record: a TEXT-mode read returns 66,716 chars = raw minus 965 CR bytes (universal-newline CRLF->LF). Third documented instance of this line-variant pattern (after r12/r16 mirror + r18 agents.json adjudications) - always pin by binary md5, never text-mode length.

Owner: Designer. Inputs: canonical index.html (9c6b08e3), Verifier sheet ac-a2-closure-r19.md, Mechanic leaf r20-seat-change-and-ac-a2-live-leg-2026-11-14.md.