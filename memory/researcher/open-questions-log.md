Last updated: 2026-11-15 ~23:yy (Researcher — 2nd cycle: two-source NON-REPRODUCTION on index.html resolved Designer/Verifier contradiction; mirror-lag META-finding now HIGH confidence; audit-file + MIRROR_EXCLUDE inconclusive-from-sandbox)



# Open questions log (researcher) — newest first, one line per question

Format: `date | QUESTION | status/owner`. Resolved items move to the bottom under RESOLVED with the answer + pointer.



## OPEN
- 2026-11-15 ~23:yy | **META-RULE (durable): my sandbox mirror SYSTEMATICALLY lags the shared root — do NOT use this seat to adjudicate "is fresh-write X on disk."** Now confirmed for a 3rd file type: index.html stale (pre-Designer `df1bbdaef684`), evolution.py absent, memory_mirror.py pre-MIRROR_EXCLUDE (`6d1d500b1688`). | SUPPORTED / HIGH — three independent lag data points across cycles. Action: route all fresh-write disk adjudication to a non-sandbox ops-terminal read (Mechanic/Verifier); treat my reads as "lower bound, possibly stale." Failure-mode ruled out: not per-file corruption — it's uniform SMB 5-min mirror lag.
- 2026-11-15 ~23:yy | **index.html served-root NON-REPRODUCTION (resolves Designer-vs-Verifier): shared root still `df1bbdaef684`, all design markers absent (`--acc-deep`,`#2563eb`,`--sp-1`…`.ops-label`).** Designer's claimed `9a8f98149a7b` did NOT propagate to the served file. | SUPPORTED / HIGH — two independent vantages agree: my mirror read + Verifier's non-sandbox read both = `df1bbdaef684`, markers absent. Supersedes my prior inconclusive entry below. Failure-mode ruled out: not a marker-spelling diff (grep'd exact tokens). Root cause per Designer/Verifier: sandboxed write doesn't propagate to shared root.
- 2026-11-15 ~23:yy | **Two evidence-on-disk claims unverifiable from my seat: (a) Verifier's `memory/verifier/live-verified-audit-2026-11-15.md` — absent in my mirror AND flagged absent by Archivist; (b) Mechanic's `MIRROR_EXCLUDE={"index.html"}` — not present in my `memory_mirror.py`.** | INCONCLUSIVE from my seat — my mirror lags, so absence here ≠ absence on shared root. Two sources don't see (a), raising probability it wasn't written, but needs non-sandbox read to close. Action: Mechanic/Verifier confirm both from ops terminal.
- 2026-11-15 ~23:xx | **MEMORY.md internally inconsistent on fleet count — L5 status bullet says `60/80 (75%)` but L13 GOAL line still reads `52/80 (65%)`.** Scribe's claimed 52→60 sync landed on a different line, not the canonical GOAL line. | SUPPORTED / high — verified directly from disk (single inode 5066549581540502, 3802 B; both `memory.md`+`MEMORY.md` same file). Action: Scribe re-sync L13 GOAL line to 60/80. Failure-mode ruled out: not a two-file split (same inode); genuinely one file holding two counts.
- 2026-11-15 ~23:xx | **evolution.py sha discrepancy: MEMORY.md pin `7c20402e` vs Verifier's disk read `9721ec32`.** | INCONCLUSIVE from my seat — file is ABSENT from my sandbox working dir (mirror gap / 5-min SMB lag), so I can neither confirm the pin nor Verifier's new hash. Needs non-sandboxed ops-terminal re-read to reconcile which sha is current. Do NOT treat either as ground truth from this mirror.
- 2026-11-15 ~23:xx | **index.html root sha: Designer claims new served-root `9a8f98149a7b` (goals 2/3/4 re-landed) but my sandbox copy still reads `df1bbdaef684`.** My earlier keyboard-feature resolution remains valid (feature present at `df1bbdaef684`); the hash delta is Designer's later WCAG+contrast+ops-hierarchy edits. | INCONCLUSIVE from my seat — my mirror predates Designer's re-land; per memory-index rule (verify against shared-root pins, never sandbox mirrors) I can't confirm `9a8f98149a7b` here. Needs Verifier's served-page check on :8099 (disk==served sha). Failure-mode noted: mirror staleness, not a Designer error.
- 2026-11-15 ~21:3x | **Designer goal-5 (keyboard support) close-hash `0d0d365a5290` vs shared-root pin `df1bbdaef684` — stuck in sandbox or on disk?** (hot-note suspicion) | RESOLVED by direct read from my seat: shared-root `index.html` sha1 = `df1bbdaef684…` (85,653 B) and the keyboard feature IS PRESENT on that exact file — two live `keydown` handlers: `#input` → `Enter&&!shiftKey ⇒ send()` (Enter-to-send / Shift+Enter-newline) AND `#gitMsg` → `Enter ⇒ gitCommit.click()`. Change LANDED on shared-root disk; NOT stuck in sandbox. Hash delta explained, not a contradiction: goal #9 note already records "post-restart sync brought index.html to new pin df1bbdaef684 (WCAG fix present)" — a WCAG/contrast edit landed AFTER Designer's close-measurement (`0d0d365a`), bumping the pin; both features coexist. **SUPPORTED (high):** keyboard handlers read directly from the shared-root file whose hash matches the current pin. Failure mode RULED OUT: "stuck in sandbox, not on disk" (the hot-note's leading hypothesis) — directly contradicted by reading the keydown code out of the on-disk shared-root file, not a mirror. MEDIUM caveat: I cannot reproduce Designer's exact close-time hash `0d0d365a` from my seat (their sandbox copy not at my root), so the precise edit-sequence is inferred from the goal #9 WCAG note rather than observed; the load-bearing fact (keyboard support live on shared root) is directly observed. Pointer: this entry + memory/researcher/citation-manifest-2026-11-15.md index.html line.
- 2026-11-15 ~21:1x | **What happens after the fleet hits 100% of its current goal set?** (human question this cycle) | ANSWER GROUNDED in memory (not invented): two mechanisms already exist. (1) GOAL-CYCLE + ARCHIVE pattern — `memory/goals/archive/README.md`: "when a cycle completes and NEW goals are set, the prior cycle's per-agent files move here"; i.e. the current 80-goal set is ONE cycle; on completion Orchestrator sets a new set (as done 2026-11-13) and old per-agent goal files archive. (2) PLANNED direction — `memory/synthesis/2026-11-14-dream-big-planning.md` (Scribe): a **Self-Measuring Goal Loop** where the portal measures reaching + auto-generates next-cycle goals from this cycle's UNMET KRs, closure gated on evidence (acceptance marker, not self-declared [x]); plus per-agent OKR mapping (Objective=role mandate, KR=the 10 goals). Also standing CADENCES already exist that don't expire at 100% (daily alias probe, daily memory sweep, 7-day citation audit) — post-100% work shifts from one-shot build/fix goals to these recurring cadences + new findings (e.g. the Red .245 firewall leg is still open regardless of goal count). **SUPPORTED (high):** both mechanisms quoted verbatim from on-disk files I read this turn. **INFERRED (medium):** that cycle-reset (not freeze) is the intended post-100% path — no file says "stop at 100%"; the archive README implies continuation but NO explicit decision record exists yet; owner of that decision = Orchestrator (owns TODO.md + goal cycles). Failure mode ruled out: that this was already decided and I'm mis-reporting — grep for "after 100"/"post-completion"/"next cycle" found only planning intent + the archive convention, no decision file. ACTION at next cycle-start: Orchestrator records an explicit post-100% decision (new-cycle scope) in TODO.md so it isn't left to inference.

- 2026-11-15 ~20:48 | **Verifier's "portal git integration is dead" claim — correct, or mis-scoped?** | Cross-checked on White seat against disk + live execution. TWO independent observations: (a) file listing shows `mingit/cmd/git.exe` EXISTS at HERE, and (b) running it returns `git version 2.47.1.windows.1`. agent_portal.py L2206 hardcodes `GIT_EXE = HERE/mingit/cmd/git.exe`, so "exe missing" is TRUE ONLY on Black (Verifier's seat), NOT universal — seat-dependent. The OTHER half of Verifier's claim IS confirmed cross-seat: a recursive scan of the whole studio tree (pruned only node_modules/.git/mingit/MinGit-x/__pycache__/venv, depth 7) found ZERO `.git` dirs => `/api/git` GET returns `{repo:false}` on EVERY seat, exe present or not. => Net correction: the real blocker is the missing REPOSITORY at HERE, not the missing binary; re-provisioning Black's mingit alone will NOT make /api/git work until a repo is `git init`ed at HERE (or GIT_EXE repointed to a path present on all seats). Memory's "430-tracked-file repo existed today" is NOT visible from White — stale or seat-specific. SUPPORTED (high): both sub-facts (direct listing + live --version output, two independent observations). Failure mode ruled out: scan under-counting `.git` — I pruned only non-repo dirs and scanned to depth 7 across the full studio tree; a project repo would not sit in those pruned paths. Also ruled out "stale mirror read" for the exe — git --version is a live process execution, not a file read. Owner/next: Builder/Mechanic — `git init` + commit at HERE to make /api/git functional; reconcile whether GIT_EXE should target a path present on all seats.

- 2026-11-15 ~20:4x | Per-host model-alias verification status after the 17:12 probe + stale "host-level WFP firewall" framing in two artifacts | Cross-checked orch_alias_probe_result.json (ts 17:12:20, primary) against memory/llm/model-id-check-2026-11-15.md addendum claims: Pale archivist-q8 OK + designer-q4 OK = SUPPORTED (high, verdicts verbatim in JSON); Black 401-even-with-Bearer = SUPPORTED (high, JSON error field) => verifier-q4 on Black remains UNVERIFIED (token issue, not a model question); "Red WinError 10013" = SECOND-HAND: the probe never targeted Red, the JSON entry is a transcribed note citing Mechanic's 17:xx report. Both artifacts still carry pre-diagnosis "host-level (WFP) firewall" framing that the later sandbox-isolation finding reclassifies as seat-egress artifact => read INCONCLUSIVE pending the non-sandboxed re-probe Mechanic recorded in memory/ops/mechanic-goal3-closure-2026-11-15.md (not yet in my mirror at 20:4x). Flagged to Orchestrator/Mechanic in cross-talk ~20:4x. Failure mode ruled out: that the Black 401 was a wrong endpoint - no, script source shows /v1/models + /api/settings/model-aliases with Bearer fallback; 401 is auth, not routing.


- 2026-11-15 | Can Researcher independently re-verify the evolution.py live pin (sha1 7c20402e) + /api/evolution/stats from this sandbox? | BLOCKED-from-my-seat: reproduced WinError 10013 on 127.0.0.1:8099 (same firewall family as hot-notes White block), so I could NOT reach the live API; the 'live-verified via /api/evolution/stats' claim rests on another seat's probe, not mine — do NOT repeat it as if I verified it. Independent cross-check I CAN make: my local agent_portal.py mirror sha1 = fead6b136c4a17d26d54289195eedd41b206b31a, which differs from the shared-root pin -> confirms mirror-clobber rule (trust shared-root pins, not local reads) from my own seat. Counter-evidence ruled out: 10013 is WSAEACCES (firewall), not 10060 (host down) or 10061 (refused). SUPPORTED (high): I cannot self-verify the evolution live-API claim; medium on pin value since disk copy not at my root. Owner: Mechanic/any seat with a green :8099 leg.

- 2026-11-15 | Remote alias half (scribe-q8/mechanic-q4/designer-q4/archivist-q8/verifier-q4) unverifiable while .245/.39/.99 powered down | waiting on host power-on; re-run per memory/llm/model-id-check-2026-11-14.md ACTION line

- 2026-11-15 | Backend-swap drill verdict (SwapDrill1114b, fires ~00:39 with 45-min idle-gate window) | RESOLVED - executed 00:39-00:44, zero lost bindings; Q4-load-evicts-Q8 finding documented; goal 4 closed

- 2026-11-15 | 308 orphan round logs under memory/<agent>/ — accept as filename-discoverable noise or add one pattern-line per agent INDEX? | decision owed to Archivist/Scribe; see memory/archivist/index-integrity-2026-11-15.md

- 2026-11-15 | Are all 19 tracked .html files intentional quarantine variants, or do WIP artifacts ride along? | audit owed (git ls-files *.html vs memory/ops/quarantine-index-html-variants-2026-11-13.md list)

- 2026-11-14 | White Q4 live ctx 131072 vs boot recipe 65k — pre-existing mismatch, left as-is during rename | Mechanic/Builder to decide: align recipe or document the delta



## RESOLVED

- 2026-11-15 | Why did the in-round swap drill hit 409? | ANSWER: an active chat round holds its generation handle for the WHOLE turn, so active-generations never hits 0 mid-turn; drill must run in a post-turn quiet gap (memory/llm/backend-swap-procedure.md KNOWN TRAP)

- 2026-11-15 | Why did index_check report 19 dangling pointers? | ANSWER: 16 false positives (header text + path-convention mismatch) + 3 real in bugs/INDEX.md, all fixed; tool hardened (memory/archivist/index-integrity-2026-11-15.md)

- 2026-11-15 | Stray seat-local copies `memory/archivist/MEMORY.md` + `memory/archivist/TODO.md` — anything read them? | ANSWER (Researcher, disk-verified): NO live reader. agent_portal.py loads only root TODO.md/MEMORY.md (LWW, L89-101) + global memory.md (MEMORY_FILE, L52); grep across ALL copies shows no dynamic `memory/<agent>/MEMORY.md` path construction. Files confirmed present (12,538 B / 17,158 B, 13/11 05:48). Safe to delete w.r.t. readers. CAVEAT (medium conf): SMB/LWW mirror syncs the whole memory/ tree (L147), so a stale copy on another host could be pushed back — coordinate deletion across hosts, don't just rm from shared root.



## OPEN (added 2026-11-15 ~19:xx — Researcher wedge-recovery round)

- 2026-11-15 | **Fleet goal-count discrepancy: GOAL line 52/80 vs hot-note 53/80 (Scribe flag, /api/goals unreachable).** Fresh on-disk tally from my seat: per-agent "(verified:" markers in memory/goals/*.md = archivist 10, builder 4, designer 1, mechanic 8, orchestrator **10** (GOAL line says 8/10 — stale), researcher 9 (after #10 formal close this turn; was 8), scribe 10, verifier 3 → **on-disk total 55/80**. No double-counting (each marker on a distinct numbered goal line, checked per line). So neither 52 nor 53 matches a clean per-file count; the GOAL line is stale at least for Orchestrator (+2), which alone moves 52→54. CANNOT settle canonically: /api/goals (single source of truth) unreachable — portal :8099 DOWN fleet-wide this turn (Mechanic: PermissionError crash on auto-restart, code fixed, restart pending; my seat: WinError 10013 egress block). Alternates ruled out: regex over-count (ruled out by per-line check); unrecorded in-chat flips explain drift in the + direction only (designer #3 evidence recorded but marker not flipped yet), not a lower count. ACTION: first seat with a green :8099 reads /api/goals and rewrites the GOAL line; until then tag any count "on-disk proxy 55, canonical pending". Owner: Scribe (sync) + first portal-green agent (read). SUPPORTED (high): on-disk marker total is 55 as of this tally.

  **FRESH MEASUREMENT 2026-11-15 ~19:xx (Researcher seat, tightened goal_ledger.py):** re-ran `goal_ledger.py --json` from working-dir root with the TIGHTENED EVIDENCE_PAT (matches only `(verified:` / `— recorded`, NOT bare 'verified'/'[x]') → **fleet 55/80 (69%)**, per-agent: orchestrator 10, researcher 9, builder 4, archivist 10, scribe 10, verifier 3, designer 1, mechanic 8. Independent tool-computed count that AGREES with the hand tally above (55) and CORROBORATES the discrepancy: GOAL line 52 + hot-note 53 are BOTH below the evidence-gated on-disk total of 55; orchestrator is 10/10 on disk (GOAL line's 8/10 stale by +2). Failure mode ruled out: tightened pattern UNDER-counting — it only narrows what counts as closure, so the true number could be lower, not higher; yet it still yields 55 ≥ both cited figures. Ledger JSON: memory/researcher/goal_ledger_run.json (45,413 B). STILL pending canonical: /api/goals read needs a green :8099 (portal restart = human/Arnold gate). Tag any count "on-disk proxy 55 (tool-verified), canonical pending."



## OPEN (added 2026-11-15 ~18:xx — Researcher cross-check round)

- 2026-11-15 | **index.html pin contradiction (HIGH priority).** Scribe/hot-note (~17:xx) records pin sha12 `37549a041412` "served==disk verified"; Verifier's direct disk read of `Z:\index.html` = `b59e528fe540` with the L827 duplicated `}catch(e){  }catch(e){` STILL LIVE (chat blanked). My seat mirror also = b59e528fe540, L827 bug confirmed by direct line read. UNRESOLVED from my seat: cannot read Z:\ (FileNotFoundError) and :8099 unreachable (sandbox egress blocked), so I can neither confirm nor refute Verifier's root read. Adjudication paths: (a) re-measure the SERVED page from a seat with working :8099; (b) compare served HTML vs `Z:\index.html` content to test the mount-mismatch hypothesis (Verifier's Z: != portal HERE). Failure mode considered and NOT sufficient: 5-min SMB lag explains MY stale mirror but not Verifier's fresh same-timestamp disk read.



  **ADJUDICATION (2026-11-15 ~18:4x, Researcher seat, FRESH re-measure):** My shared-root `index.html` NOW reads sha1 **`37549a041412`** (80,360 B) — MATCHES Scribe's pin, NOT Verifier's b59e528fe540. Direct line read of L827 = CLEAN single `}catch(e){ addBubble("error",...) }`; regex scan for the duplicated `}catch(e){  }catch(e){` pattern returns ZERO hits across all 1,171 lines. File also contains the newest "Backend group-run attachment (2026-11-15)" + /api/group-run//api/run-events code, consistent with today's LIVE-PLAN index.html edits landing. => THIRD independent data point: disk-at-my-root = Scribe's pin, L827 bug ABSENT. Leading explanation for Verifier's b59e528fe540 read (bug live): **mount-mismatch** — Verifier read `Z:\index.html`, a different mount than the portal root I measure; OR the file was fixed/re-synced between Verifier's read and now (LIVE PLAN shows active index.html edits today, so an intra-session change is plausible). NOTE (honest caveat): my own EARLIER note this session recorded b59e528fe540 on "my seat mirror" with the L827 bug line-read — that observation and this one disagree; most consistent read is the file changed between the two reads (active editing), which is itself evidence the pin was NOT static. STILL UNRESOLVED from my seat: cannot reach :8099 to confirm the SERVED page == 37549a041412, so "served==disk" remains a single-seat (Scribe) claim + my now-matching disk read, not yet a green served-page fetch. SUPPORTED (high): current root index.html is clean of the L827 dup-catch and equals Scribe's pin. MEDIUM: whether served page matches (needs any seat with working :8099). Adjudication paths stand: (a) re-measure SERVED from a green :8099 seat; (b) diff served HTML vs Z:\index.html to test mount-mismatch. Do NOT repeat b59e528fe540 as the live root pin — it is superseded on my root.

- 2026-11-15 | **Mechanic remote-leg evidence file not visible from my seat.** Claimed at `memory/ops/mechanic-reboot-dryrun-remotes-2026-11-15.md`; absent from my memory/ tree at check time (no *reboot*/*dryrun* files in memory/ops listing). Likely mirror lag (same-round write, 5-min SMB) — re-verify on next daily sweep before citing the file. **UPDATE 2026-11-15 ~19:xx (RESOLVED visibility): file NOW present at my seat, 2,687 B.** Content spot-check vs Mechanic's same-turn chat: PALE (4/6, Q8_0+Q4_K_S+archivist-q8+designer-q4) and RED (10013 all ports, firewall) MATCH. **DISCREPANCY on BLACK: file says PASS 5/7 models at 17:0x; chat this turn says PARTIAL 0/6 (fleet_reload gap after power-on).** Which is current is unresolved — if a post-power-cycle re-run dropped the models, append that result to memory/ops/mechanic-reboot-dryrun-remotes-2026-11-15.md so disk and chat agree; do NOT cite either Black number until reconciled. Cross-check of the underlying verdict: WinError 10013 = WSAEACCES; Mechanic's pattern (ALL ports to .245 blocked from White while .39/.99 green in the SAME run/process) is consistent with a per-remoteip Windows Firewall outbound block rule on White. Counter-evidence ruled out: host-down would give 10060 timeout, not 10013; service-down gives 10061 refused; blanket socket-permission issue contradicted by green legs in the same process. SUPPORTED (high, inference from error semantics + multi-port probe): firewall rule on White vs .245. CAVEAT: exact rule unidentified — needs admin on White (human gate). NOTE: 11-14 note (white-lan-firewall-drop) covers the REVERSE direction (Red→White :8099/:8888 timeouts) — same firewall family, different direction; not a direct second source for today's finding.



---

## 2026-11-15 ~19:0x — Researcher: cross-seat sync adjudication (new measurements)



**FINDING A — index.html diverges ACROSS seats right now (SUPPORTED, high confidence):**

- My seat: sha12 `37549a041412`, 80,360 B, 1172 lines — NO Queue feature, NO `--acc-strong`.

- Designer's seat (this round): sha1 `5e1cbd6ce138`, 85,188 B, 1241-line base WITH Queue + WCAG fix.

- LIVE PLAN marks the Queue change [x] complete, so my seat holds a STALE base; Designer's pin is the newest superset.

- Implication: Scribe's earlier "served==disk @ 37549a041412" pin was measured against a pre-Queue base. After portal restart, re-verify pins — no pre-restart pin (incl. Verifier's b59e528fe540) is trustworthy until all seats converge to `5e1cbd6ce138`.



**FINDING B — Orchestrator writes ARE on shared root; Scribe/Archivist "absent" reads = transient lag (SUPPORTED medium / hypothesis):**

- My seat has the real `## POST-WEDGE OPS` header (TODO.md L8) and memory/llm/model-id-check-2026-11-15.md (1,984 B, title matches Orchestrator's goal #3 check).

- TODO.md L4 already logs `[x] MIRROR DIVERGENCE ... both directions, ts-stamped` ~18:3x — divergence was known in-flight.

- Counter-evidence considered: my own seat could be the AHEAD one (Scribe/Archivist lagging behind), or all three readings could be timing artifacts of 5-min sync windows during portal-down. Cannot rank seats' freshness from here; resolution = re-grep each claimed path from every seat after White's next sync cycle post-restart.



**Action items (portal-up gated):**

1. First green seat: confirm served index.html == `5e1cbd6ce138` (closes Designer #3 live check + my pin adjudication in one fetch).

2. Post-sync: all seats re-grep POST-WEDGE OPS / model-id-check-2026-11-15.md; if any seat still missing after 2 sync cycles, escalate to White/Mechanic (sync path broken, not lag).

3. Do NOT push index.html from a stale seat (mine!) before convergence — would re-clobber Designer's WCAG fix in reverse.



**My lane:** 9/10; only #9 open, time-gated to ~11-20. No further action possible today.


## ADJUDICATION UPDATE — 2026-11-15 ~19:xx (post Designer #4, Mechanic seat-isolation, Scribe clobber flag)

**1. agent_portal.py is DIVERGED across seats — restart pre-check at risk [SUPPORTED, high]**
My seat copy = sha12 `fead6b136c4a` (136,253 B) and **lacks `except PermissionError`**; Mechanic claims the fixed shared-root copy is `3baabf739077` (142,051 B). If the portal's actual running copy matches my seat's stale state, Arnold's restart re-crashes at import (PermissionError on os.listdir(C:\Users) — traceback in mirrored portal_run_err.log). ACTION: Arnold's step-④ pre-check ("running copy must contain `except PermissionError`") is MANDATORY, not optional; if it fails, copy Mechanic's fixed file into the portal dir first.

**2. Three files absent/diverged on my seat (mirror propagation stalled while :8099 down) [SUPPORTED, high]**
- `memory/portal/index.html.scale-migrated-1e689bccecf4` — ABSENT here → Designer's post-sha `1e689bccecf4` is UNVERIFIED from my seat (single-seat claim + snapshot filename). My earlier "canonical pending = 5e1cbd6ce138" is SUPERSEDED by `1e689bccecf4`; first green seat should hash the served page and expect THAT pin.
- `memory/ops/reboot-dryrun-remotes-2026-11-15.md` — ABSENT here (present on Archivist + Mechanic seats) → Mechanic's DIAGNOSIS CORRECTION + Red INCONCLUSIVE verdict are single-seat from my vantage; content plausibility high (zero-socket sandbox evidence).
- My own `open-questions-log.md` PERSISTED this episode (sha12 `bee2faafc975` unchanged) → Scribe's "all non-White writes ephemeral" flag is CONFIRMED IN PRINCIPLE but propagation is per-file/timing-dependent, not uniform.

**3. SELF-CORRECTION: my earlier claim 'no Queue in 37549a041412 base' was WRONG [SUPPORTED, high]**
Same sha12 measured both times = identical bytes; the file DOES contain the queued-messages feature (comment block citing `user_messages.json` + backend `/api/user-messages`). My earlier grep checked the wrong markers. Corrected state of my seat's index.html: sha12 `37549a041412`, 80,360 B, HAS Queue code, LACKS `--acc-strong`. Direction of adjudication unchanged (my seat lags Designer's canonical pin; no stale seat may push index.html).

**4. Mechanic's seat-isolation diagnosis accepted [SUPPORTED, high]**
All agent seats = zero-socket sandboxes ⇒ every "WinError 10013 / firewall blocked" verdict this session is unreliable as a network claim; Red leg BLOCKED→INCONCLUSIVE stands. The true White→Red/Black probe needs a non-isolated context (White scheduled task or Arnold's shell). Failure mode considered and ruled out: that the sandbox isolation itself was introduced mid-session by my own tooling — ruled out, socket denial is seat-wide and pre-dates this session's logs.

**Net effect on open items:** Q4 probe + Designer live WCAG check remain queued for first green :8099, but their "blocked by firewall" framing is retracted — the only hard gate left is the portal restart (human, Arnold), whose step-④ pre-check is now load-bearing per item 1.

---

## 2026-11-15 ~20:5x — Researcher: post-restart sync adjudication (auto-resume 3/5)

**FINDING C — agent_portal.py at shared root STILL lacks `except PermissionError` [SUPPORTED, high]**
Post-restart mirror sync delivered a NEW version of agent_portal.py (sha12 `7d4184ce01ac`, 149,522 B, 3021 lines) — different from both my pre-restart seat copy (fead6b136c4a) AND Mechanic's claimed fixed shared-root (3baabf739077). Critical: grep for "PermissionError" returns ZERO hits across all 3021 lines. The os.listdir(C:\Users) call at L74 remains UNPROTECTED. If the portal restarts again under the same condition that triggered the PermissionError crash, it will re-crash. Counter-evidence considered: the portal DID successfully auto-restart this cycle — possible explanations: (a) C:\Users listing succeeded this time (transient state), (b) portal is running from a different file than what's synced to my seat, (c) fix was applied and then reverted by LWW sync. Resolution: Mechanic or any admin on White should verify the RUNNING copy in the portal directory contains the fix before trusting the next restart.

**FINDING D — index.html pin moved again post-restart: df1bbdaef684 [SUPPORTED, high]**
My seat's index.html is NOW sha12 `df1bbdaef684` (85,653 B, 1247 lines) — DIFFERENT from all previously recorded pins (37549a041412 pre-restart, 5e1cbd6ce138 Designer's, 1e689bccecf4 snapshot filename). The WCAG fix (#3a6fd6) IS present; --acc-strong is absent. File is 7 lines shorter than the scale-migrated snapshot (a9daf87fde97 actual sha / 1254 lines, 88,715 B). Interpretation: something was trimmed or the file evolved between Designer's work and the post-restart sync. All pre-restart pins are STALE; no pin is trustworthy until a green :8099 seat fetches the served page.

**FINDING E — Previously-absent files NOW present (mirror sync propagated) [SUPPORTED, high]**
Post-restart sync delivered: memory/portal/index.html.scale-migrated-1e689bccecf4 (88,715 B), memory/ops/mechanic-reboot-dryrun-remotes-2026-11-15.md (2,687 B), memory/ops/reboot-dryrun-remotes-2026-11-15.md (2,897 B). The snapshot file's ACTUAL sha1 is a9daf87fde97, NOT the 1e689bccecf4 in its filename — flag to Archivist: snapshot naming convention may use a different hash or the file was modified post-save.

**Action items:**
- Mechanic: verify RUNNING agent_portal.py (portal dir on White) contains `except PermissionError` before trusting next restart. If absent, re-apply fix and prevent LWW sync from reverting it.
- First green :8099 seat: hash served index.html; expect df1bbdaef684 or newer. All prior pins void.
- Archivist: explain why snapshot filename sha (1e689bccecf4) != file content sha (a9daf87fde97).

**My lane status:** 9/10 goals verified; #9 (citation audit) time-gated to ~11-20, no new citations to audit this turn. No further action possible from my egress-blocked seat until :8099 becomes reachable or a green-seat agent reports back.
