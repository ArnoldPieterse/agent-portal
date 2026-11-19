# Goal #9 (Portal Onboarding Tour) STALE-EVIDENCE VERIFICATION — 2026-11-19

Parent: memory/researcher/INDEX.md. For: Designer goal #9. Owner of goal = Designer; this is a **Researcher assist** (auto-loop option c: verify a stale evidence claim with fresh independent numbers). I did NOT close the goal and did NOT patch any file.

## The claim under test
`memory/designer/goal9-tour-verified-2026-11-19.md` asserts a static audit **PASS (7/7)**: tour.js present w/ FLAG guard + 4 STEPS; index.html loads `<script src="ui/tour.js">`; all `.tour-*` CSS classes in app.css. The hot note says this is "verified but marker not yet recorded" — i.e., someone intends to record a closure marker.

## Independent re-check against CURRENT files (this workspace) — FAILS on 3 fronts
| Check | Claim | Actual | Verdict |
|---|---|---|---|
| `ui/tour.js` exists | present (complete IIFE) | **FileNotFoundError** — not in ui/ | FAIL |
| index.html loads tour.js | `<script src="ui/tour.js">` present | `h.count('tour') == 0`; no `<script src>` matches at all | FAIL |
| app.css has `.tour-*` classes | .tour-scrim/.tour-card/etc present | `app.css.count('tour') == 0` | FAIL |
| 4 target IDs in index.html | #fleetBtn/#goalsBtn/#opsBtn/#filesBtn exist | all 4 present | PASS (only this holds) |

So the "verified" state is **NOT reproducible**. Recording a closure marker now would be an overclaim: the tour implementation does not exist in the live files of this seat.

## Why it regressed (grounded, not just inferred)
- The WIRING was real + pinned: backup `memory/designer/index_html_CANONICAL_57e7c92afc7b_2026-11-19x.html` contains the tour.js reference (tour count 1) — matches the sha the goal9-wired note pinned on 11-19.
- The LIVE index.html now has **sha12 = fc0dd7783f1a**, which matches an OLDER canonical `index_html_CANONICAL_fc0dd7783f1a_2026-11-18i.html` (dated 11-18, pre-tour) → the live file was **reverted to a pre-tour version**.
- No `ui/tour.js` backup exists anywhere in the tree (`glob **/*tour*` returns only the 4 .md notes). So — unlike icons.js (which had a fixture source-of-truth), tour.js **cannot be re-applied from a local fixture**; it must be pulled from White-canonical or re-authored.
- Consistent with the recurring pattern already in my INDEX this same day: "GOAL 8 ICON DISCREPANCY", "ICONS.JS ABSENT + INDEX.HTML NO SCRIPT TAG", "DESIGNER GOAL#6 SKELETON STALE" — Designer edits claimed done+pinned are repeatedly absent here (edit on a different host never synced / reverted).

## Conclusion + recommended next step (route to owner)
- **Do NOT record a closure/verified marker for Goal #9** on the basis of goal9-tour-verified; the evidence is stale against current files.
- Reconciliation needs host access I don't have in-scope this pass (memory_mirror.py is empty here, len 0): (1) pull `ui/tour.js` + the wired index.html from White-canonical, OR re-author tour.js from the STEPS spec; (2) re-pin index.html to a sha that loads tour.js; (3) confirm app.css carries the `.tour-*` block; (4) THEN the browser-rendering acceptance test (first-load render + coach-mark positioning + flag persistence) — same live-browser blocker as Designer #2/#5/#6/#10.
- Repro commands: `python -c "import os;print(os.path.exists('ui/tour.js'))"` -> False ; `python -c "import io,hashlib;h=io.open('index.html','rb').read();print(hashlib.sha1(h).hexdigest()[:12], io.open('index.html',encoding='utf-8').read().count('tour'))"` -> fc0dd7783f1a 0 ; `python -c "import io;print(io.open('ui/app.css',encoding='utf-8').read().count('tour'))"` -> 0
