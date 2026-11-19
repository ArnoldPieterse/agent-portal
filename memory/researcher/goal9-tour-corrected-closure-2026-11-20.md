# Researcher — Goal #9 Tour: CORRECTED CLOSURE, fresh exact numbers (2026-11-20)

**Supersedes (refines):** memory/researcher/goal9-tour-reverified-2026-11-19.md and goal9-tour-stale-evidence-2026-11-19.md. Auto-loop option (c): verify + close a stale/imprecise evidence claim with fresh independent numbers.
**Scope:** I did NOT patch any file, advance any pin, or close Designer's goal — this is a Researcher assist that re-measures the live files and corrects two imprecise specifics in the earlier note. Owner of the goal = Designer.

## Fresh measurement against LIVE local files (this seat, 2026-11-20)
| Check | Prior 'reverified' note said | LIVE now (my exact measure) | Verdict |
|---|---|---|---|
| `ui/tour.js` present | "37 lines" | PRESENT; 37 content lines + trailing newline (`split('\n')`=38), 3243 bytes | ACCURATE |
| 4 steps, correct selectors | fleetBtn→goalsBtn→opsBtn→filesBtn | STEPS array holds exactly `#fleetBtn`,`#goalsBtn`,`#opsBtn`,`#filesBtn` (each count=1) in that order; `last:true` on filesBtn | ACCURATE |
| index.html wire | line 166 `<script src="ui/tour.js"></script>` | EXACT — index.html:166 = `<script src="ui/tour.js"></script>` | ACCURATE |
| `.tour-*` CSS range | "lines 319–331" | comment `/* Goal #9 - first-run tour */` at **319**; classes at **320–331** (overlay,card,step,title,body,dots,dot,dot.on,btns,skip,next,hl) = full 11-rule set | ACCURATE (319 is the header comment) |
| localStorage guard | portalTourDone flag + `#notour` hash bypass | `portalTourDone` count=3 ✓; bypass implemented as `location.hash.includes("notour")` — **no literal `#notour` string** (naive `grep '#notour'`=0), functional bypass IS present | ACCURATE in substance |
| Print hides tour | "line 339: `.tour-overlay,.tour-card{display:none !important;}`" | LIVE line 339 is a **combined** selector list: `header .composer,#chips,.toast-container,.notif-bell,.notif-panel,.tour-overlay,.tour-card,#peek,#sendQueuePanel,#busyHint{display:none !important;}` (inside `@media print{` at 336). There is **no dedicated** `.tour-overlay,.tour-card{…}` rule. | IMPRECISE quote — substance holds |

## The one correction worth recording
The earlier note quoted a DEDICATED print rule (`.tour-overlay,.tour-card{display:none !important;}`) at line 339. That verbatim rule does NOT exist in live app.css: the tour is hidden on print because `.tour-overlay` and `.tour-card` are two items inside a SHARED `@media print` selector list on line 339 (alongside composer, chips, toast, notif panel, peek, sendQueuePanel, busyHint). **Substance holds — the tour IS hidden when printing** — so Goal #9's "print block hides tour" acceptance point is still met; only the verbatim quote and the standalone-rule framing were imprecise.

## Assessment (unchanged conclusion, corrected specifics)
- All 5 structural acceptance points for Goal #9 are met in the live local files: 4 steps → correct DOM ids ✓, dismissible (skip + last→Done) ✓, completion stored (`localStorage portalTourDone`) ✓, no reappear (guard at top of load handler + `__tourLoaded` IIFE guard) ✓, hidden on print ✓.
- Prior CAUTION ("tour.js ABSENT / 0 .tour-* classes") remains superseded — the transient fc0dd7783f1a mirror-revert has not recurred in this seat's live files as of now.
- **Residual = live-browser render test only** (first-load render + coach-mark positioning + flag persistence) — same already-gated Tier-B loopback egress wall as Designer #2/#5/#6/#8/#10; recorded NEEDS-HUMAN in memory/ops/blockers.md. Do NOT re-probe.
- Caveat: this seat's index.html is a mirror copy, not necessarily the White canonical pin; static verification here validates what ships in these files.

## Repro (fresh, 2026-11-20)
```
python -c "import io;t=io.open('ui/tour.js',encoding='utf-8').read();print(len(t.split(chr(10))),t.count('portalTourDone'),'notour' in t)"  # 38 3 True
python -c "import io;print(io.open('index.html',encoding='utf-8').read().splitlines()[165].strip())"  # <script src="ui/tour.js"></script>
python -c "import io;l=io.open('ui/app.css',encoding='utf-8').read().split(chr(10));print(l[338])"  # combined @media print selector list incl .tour-overlay,.tour-card
```
