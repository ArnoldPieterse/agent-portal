# Designer design-leg verify — r19 (PID 23704, post-restart) — 2026-11-14

Supplements `post-restart-verify-r16.md` / `-r16b.md`. NEW file per the refined LWW line (existing-file edits skip propagation under skew).

## Pre-flight
- Served-page fetch from this seat: **UNREACHABLE** — sandbox blocks 127.0.0.1, curl/powershell/tasklist/netstat all degraded on this seat (known r15/r16 surface). Fallback evidence: workspace-root `index.html` verified **byte-exact to canonical pin 9c6b08e3d98355e632a72cb871d5b60d / 67,681 B** (certutil MD5; CRLF ×965 — the LF-normalized read shows 66,716 B / 07ac2961, same file). r19 ops note records the served copy re-pinned to this exact md5, so static verification below stands in for the grep-the-served-page line; Verifier's process-level AC-A2 on PID 23704 closes the live leg.

## Byte-level (AC-A2-1 subset, shared with Verifier)
| check | result |
|---|---|
| filesPanel ≥4 | PASS x4 |
| /api/uploads ==3 | PASS x3 |
| ends `</html>` | PASS |
| script balance 2/2 | PASS |

## PASS (design leg)
- All `var()` tokens resolve — no broken custom properties (11 defined in the single :root, all used names covered).
- Keyboard: bare `:focus-visible{outline:2px solid var(--focus);outline-offset:2px}` covers EVERY control incl. checkboxes/links; Enter=send (Shift+Enter newline), commit-box Enter→commit both wired.
- A11y: `role="status"` x2 + aria-live polite; busy indicator renders ticking `⏳ working… Ns` (per-second interval, removed on first frame).
- DM lock chip: `<details class=dmseg><summary>🔒 private → {recipient}</summary>` — collapsed by default, body via textContent (XSS-safe). Emoji is the \uD83D\uDD12 escape in source; raw-byte grep for 🔒 will 0-hit by design.
- Thinking bubble: details/summary + textContent append per chunk — no innerHTML anywhere in the stream path (L252-260 crash regression looks fixed).
- Files panel: fsFmtSize/fsFmtTime live; load-on-open + ↻ only. Ops panel: prune button present, git message input enabled, opsLoad wired.
- Server MIME rule (agent_portal.py): `mimetypes.guess_type` → .html renders as page, .md as text. PASS per file-links.md.
- Contrast (computed, WCAG relative luminance) on the live dark family: text/panel 14.84, dim/panel 7.15, acc/panel 5.43, warn 8.56, ok 9.79, err 6.29, focus-ring 7.95-8.61, stop #ff8f8f 7.96 — all ≥4.5.

## FAIL (concrete)
1. **Token family mismatch vs the r60 lock.** Live :root is a dark family (--bg #0e1116 / --panel #151a22 / --text #e8edf4 / --dim #9aa7b8 / --acc #4f8cff / --ok/--warn/--err / --focus #7fb0ff). **Zero** occurrences of any locked design-tokens.md hex (no #F4F5FA/#FFFFFF/#1A2233/#5C6478/#DDE1EC/#3949AB/#2E7D32/#8F5200), no light/dark theme switch. The lock (11-13 17:35) predates the r19 re-pin (~22:0x) and says "every future portal UI merge must use these tokens" → as written, the live page is non-conforming. NEEDS ORCHESTRATOR ADJUDICATION: migrate live page to locked family, or re-scope the lock to mock-only + document the dark family. Not a Designer unilateral call (no index.html writes owed from me since r16).
2. **alert()/confirm() in flow** — 4 alert + 2 confirm: agent-editor validation (L906-907), Reset busy-guard `alert("A reply is still streaming…")` (design-debt #1 says this must be an inline banner) + `confirm("Reset conversation?")`, counter-reset failure alert, delete confirm. Checklist §3 FAIL.
3. **Panel discipline** — each of fleet/files/ops only toggles its own panel: no one-open-at-a-time logic, no outside-click-to-close handler (only the attach menu has one). Checklist §2 FAIL.
4. **Layout shift on toggle** — all three panels sit in normal flow between modeBar and #msgs (`display:none→flex`, border-bottom) → opening any pushes the message list down. Checklist "zero layout shift" FAIL. Fix: position the panel row absolutely under the toolbar, or reserve a grid area.
5. **Send button contrast 3.22:1** — white on --acc #4f8cff < 4.5 AA (14px normal text). Either darken --acc toward #2f6fe0-class or use ink text. Checklist §3/goal-3 FAIL.
6. **360px responsive (static inference, needs one visual pass)** — zero @media rules in the file; `aside` is fixed 250px → chatCol ≈109px at a 360px viewport; modeBar panel buttons render ~26px tall (<32px tap target). Checklist §0/§1 likely FAIL. Composer itself is fine (#input 44px, attach 44×44).

## Not verifiable from this seat (degraded surfaces)
Live console cleanliness on hard refresh; fleet states vs /api/fleet JSON; ops commit count vs /api/git log length; screenshots 1440×900 + 375px. These ride with Verifier's AC-A2 pass on PID 23704.

## Bottom line
Byte-level and a11y/motion legs are clean. Six concrete UI defects above, of which #1 is a design-system-of-record conflict needing Orchestrator's call, #2-#5 are small surgical fixes for Builder (panel-close logic + one-open-at-a-time ≈ 6 lines; busy-guard banner; Send contrast token), #6 needs a media-query pass. I will not touch index.html unilaterally — queue the fixes or re-scope the lock, then I re-run this sheet.

Owner: Designer. Basis: byte-exact canonical index.html (9c6b08e3) + agent_portal.py /api/f handler + design-tokens.md (2,547 B, 11-13 17:35).