# BUILDER — open items (r24/V102)

## r36 delta (V102 close-out, 2026-11-13 12:26) — new facts pinned from group
- Designer reference `ws-b-increment1/index.html` sha256-12 = **`b82dd3b77f4e`** (CORRECTED this round; supersedes earlier-pasted `4e7a19b43779` — Designer's real-spec cross-check caught white-on-#B26A00 warning badge = 4.24:1 < AC-1 floor, fixed to #8F5200). File is Pale-only, ABSENT on Black mount per fresh walk → port step 2 stays queued (diff-reconcile only, P1 hash-first); byte-parity checkable against `b82dd3b77f4e` the moment a seat unblocks.
- Archivist datum: `ui-upgrades-r4.md` is NOT lost — lives on Pale at `memory/portal/ui-upgrades-r4.md`, 5375 B, sha256 `00a0a9db…364846`. Re-drop gate reworded: copy from Pale → Black `_default`; Verifier cross-checks that hash on landing. (Contradicts nothing: Verifier's "0 hits fleet-wide" was Black-mount-scoped.)
- Scribe's V102 record survived truncation (5374 B) but the 3 bookkeeping updates still un-executed — their lane, no gate impact.
- Builder seat re-green 12:26 (terminal+python run; agents.json WinError 2 = absent, no reparse on this mount); drop state unchanged → P8 STOP holds, zero code changes legal until H1/H2 fire.


## MEETING V102 — upgrade planning, 2026-11-13 12:18 (recorded by Builder; group apply verdict below)
File-access check (fresh, my seat):
- `uploads/` ABSENT from _default; no AgentPortal_V1 anywhere on Black (recursive search); C:\Projects\AgentPortal → Access denied from sandbox. Re-drop has NOT landed.
- ui-upgrades-r4.md still absent on Black → **P8 STOP condition holds: zero index.html edits legal today.**
- Harness fresh-green 12:18: selftest compliant 23/23 x2, stub-broken→exit 1, pre-upgrade→exit 1, incomplete→BLOCKED exit 2; `SELFTEST: PASS`. run_checks on drop target → BLOCKED exit 2 (v102_runcounts.log).
Gate state: G0/G1/G2/G3 ALL blocked on the single human action. No agent seat can unblock (UNC write denied r19/r20; loopback policy-blocked in sandbox).
APPLY-AS-A-GROUP verdict: staged, zero code changes legal this round. Execution order the moment the drop lands:
1. Step 0 — Verifier/Mechanic host-side: `python portal-upgrade\run_checks.py` → read `RESULT: PASS - exit 0` line (G0).
2. Step 1 — Builder: `check_black_models.py` builder-q8 verdict (raw Qwen3.8-27B-Q8_0 fallback if alias absent, flagged not silent).
3. Step 2 — Builder UI port per P1–P7 (P1 sha256-12 index.html == feb9e6a79a26ea02 FIRST) + AC-1..AC-5 cross-check once ui-upgrades-r4.md readable (P8).
4. Step 3 — Verifier: `run_checks.py --live` host-side (G3).
5. White baseline commit — human runs `git-toolkit\init_repo.py C:\Projects\AgentPortal\AgentPortal_V1` (MinGit-x verified 2.56.1; no-push-until-keys-rotated advisory stands).
6. Close-out — Scribe closes memory/portal/upgrades-2026-11-12.md; BUNDLE-SHA256.txt regen LAST if TODO.md touched.
Ask (unchanged, single unblocker): human re-drop of bundle INCL ui-upgrades-r4.md to Black _default + `verify_drop_env.py` gate on White.
r35 delta (12:21, Builder seat): file access FULLY GREEN this round — terminal + python both run; no reparse point on Black mount (agents.json WinError 2 = absent here, junction localized to White _default per Mechanic). Designer WS-B Increment-1 reference (`ws-b-increment1/index.html`) verified ABSENT from Black _default — it is a Pale-only artifact, so sha256 pin + port wait for merge-lane reachability (queued as Step 2, diff-reconcile only, P1 hash-first unchanged). Scribe's 3 V102 bookkeeping updates truncated mid-turn → flagged to Scribe for re-run.
r36 delta (Builder seat): DESIGNER HASH CHANGE absorbed — port-source baseline is now sha256-12 `b82dd3b77f4e` (supersedes `4e7a19b43779`; badge contrast fix #B26A00→#8F5200, all 15 token pairs ≥5.13:1). Step-2 byte-parity check updated to compare against `b82dd3b77f4e`. Archivist's Pale copy of ui-upgrades-r4.md (`00a0a9db…64846`) closes "missing content" → H2 is now a hash-compare, not recovery. Drop state re-verified ABSENT on Black (uploads/ + AgentPortal_V1) → P8 STOP holds; no agent-side code change legal until H1/H2 fire.

## PLAN — portal update, round 6 (planning meeting 2026-11-13)
Gate state: run_checks.py harness ALL-GREEN on fresh runs today (selftest: compliant 23/23 x2, stub-broken→1, pre-upgrade→1, incomplete→BLOCKED exit 2). Single unblocker = human re-drop to Black `_default` (uploads/AgentPortal_V1 absent; UNC write denied from every agent seat per Verifier r20).
Lanes:
- Step 0 (post-drop, HOST-SIDE): `python portal-upgrade\run_checks.py` → RESULT: PASS. Owner: Verifier/Mechanic.
- Step 1 (Builder, host-side post-drop): `check_black_models.py` builder-q8 verdict. Researcher r11: alias ABSENT on Black → keep raw Qwen3.8-27B-Q8_0 THIS drop; flag routing reconsideration (no Q8 repo on Black .99).
- Step 2 (Builder, my lane): UI port into index.html per Designer spec — per-agent color+monogram identity across roster/avatars/names; ■ Stop visible only while streaming + armed second click; ↺ Reset arm-then-confirm 3s via named constant at top of script; file links as relative-path chips, drive letters rejected at render. S1–S5 contract already marker-encoded in fixture (8c rows PASS).
- Step 3: `run_checks.py --live` host-side (sandbox loopback policy-blocked). Owner: Verifier.
- Post-drop hardening: git baseline commit via `git-toolkit\init_repo.py` (stdlib+subprocess; git via PATH or MinGit-x — r21) — MUST run on White by human (UNC writes denied from all seats); MinGit-x EXTRACTED + git 2.56.1 verified on Black.
- Close-out: Scribe closes memory/portal/upgrades-2026-11-12.md; if TODO.md touched → regen BUNDLE-SHA256.txt LAST (self-reference rule).
DECISION NEEDED FROM HUMAN: re-drop bundle to Black `_default` + run `verify_drop_env.py` gate on White.

## MEETING NOTES — r21 (planning meeting cont., 2026-11-13)
Verified from my seat this round:
1. Harness fresh-green re-run: selftest PASS (compliant 23/23 x2, stub-broken→exit 1, pre-upgrade→exit 1, incomplete→BLOCKED exit 2). No regressions since r20b.
2. Bundle AgentPortal_V1 STILL absent from _default → G0/G2(all)/G3 remain blocked on human re-drop. No change to ask.
3. ui-upgrades-r4.md still absent everywhere on Black (searched *ui-upgrades*) → P8 gate stands: if the drop lacks it, STOP before any index.html edit; escalate Designer/Scribe.
4. git-toolkit approach corrected in memory (see above); White baseline run unchanged: human runs `python <agent-folder>\git-toolkit\init_repo.py C:\Projects\AgentPortal\AgentPortal_V1` — git.exe now resolvable via MinGit-x next to the script if PATH lacks git.
DECISIONS REQUESTED: (a) Human: re-drop bundle incl. ui-upgrades-r4.md + run verify_drop_env.py gate on White; (b) Orchestrator: confirm drop manifest lists ui-upgrades-r4.md so P8 is checkable at G0; (c) Scribe: keep close-out order — BUNDLE-SHA256.txt regen LAST if TODO.md touched.

## Open items (r19, updated)
- [x] mini memory + todo created (this file pair)
- [x] git-toolkit: vendored dulwich from GitHub sdist → pure-Python init_repo.py, fixture self-tested (init→commit→verify→idempotent) — SUPERSEDED by r21/r28 (git-binary path; no vendor/)
- [x] lint_js.py mode-reset fix (Verifier r13): r14 applied; VERIFIED both directions today — repro_ok.js → LINT OK, repro_broken.js → FAIL "unclosed '{' at line 2". Regression artifacts kept: portal-upgrade/repro_{ok,broken}.js
- [ ] O2 (Scribe named Builder/Mechanic): baseline commit on White — human runs `git-toolkit\init_repo.py C:\Projects\AgentPortal\AgentPortal_V1`; git binary REQUIRED (PATH or MinGit-x\cmd\git.exe next to script)
- [x] MinGit-x extracted on Black; `git --version` → 2.56.1.windows.1 verified (r21, 2026-11-13) — local git available IF bundle lands in Z:\
- [ ] r21 correction: init_repo.py is stdlib+subprocess (PATH or MinGit-x\cmd\git.exe), NOT dulwich; no vendor/ dir. Memory corrected.
- [x] r22 (this round): accepted Verifier r20b fix — init_repo.py IndentationError(line 42) fixed by Verifier, py_compile OK re-verified from Black; fresh-init→baseline commit 8cc7fe5 + idempotent re-run proven by Verifier. README-inside-toolkit references removed from my files (only _selftest fixture carries a README).
- [ ] after White repo init: sync memory/builder/* into canonical tree + pointer line in memory/INDEX.md (pending Orchestrator O3 ratification)
- [ ] stream_contract_test.js T1–T6 execution — host-gated (no node on Black); lint says structurally sound, Verifier r13 confirmed

## PASS CRITERIA — r21 planning meeting (2026-11-13), per Verifier's ask: criteria up front, no self-pass
Every change in my lane lands with its pass line written here BEFORE the edit; verification always from a different seat (Verifier adjudicates).
- G0 Integrity (post-drop, host-side): run_checks.py → stdout line `RESULT: PASS - exit 0` (read the line, not ERRORLEVEL).
- G1 Binding: Mechanic P2 order holds — load builder-q8 on Black + smoke BEFORE Orchestrator flips agents.json; I confirm my seat answers post-flip. Fallback if alias still absent at drop: raw Qwen3.8-27B-Q8_0, flagged not silent (Researcher r11).
- G2 UI port = Increment 1 (identity/Stop/Reset/chips, NO /api/manifest; manifest additive later per Designer):
  - P1 edit base: sha256-12 of index.html must equal shipped baseline `feb9e6a79a26ea02` BEFORE any edit — no edits on unverified bytes (Mechanic P1 diff gate)
  - P2 identity tokens generated from the agents.json roster — zero hardcoded agent names in the diff
  - P3 ■ Stop: stream-only, armed second click; arm timeout a named constant
  - P4 ↺ Reset: arm-confirm, 3s window as a named constant at top of script
  - P5 file chips: relative paths clickable; drive-letter/absolute rejected or flagged non-clickable with warning badge (not color alone)
  - P6 lint_js.py on modified index.html → `LINT OK`
  - P7 selftest still green: compliant 23/23, broken→1, pre-upgrade→1, incomplete→BLOCKED(exit 2)
  - P8 spec canonicality: ui-upgrades-r4.md must EXIST in the post-drop tree with AC-1..AC-5 + `NAMED_ARM_MS = 3000` (I read it from the drop, not claim it). r21 finding: file ABSENT on Black _default — Designer's persistence is Pale-side only; if missing from the drop → STOP, escalate to Designer/Scribe before any edit. My P1-P7 stay valid standalone; ACs are the cross-check set once readable.
- G3 Live (host-side): run_checks.py --live → PASS line; /api/chat + /api/memory + /api/file incl. path-traversal guard. Verifier adjudicates from the RESULT block.
Holds (no work until unblocked):
- ALL index.html edits: pending human re-drop to Black _default + G2-P1 hash match
- ui-upgrades-r4.md absent on Black _default as of r21 (per-seat drift, same class as Scribe's missing INDEX.md on Red) — AC-1..AC-5 unverified from my seat until the drop carries it
- Fleet Status stub (WS-A, Builder+Mechanic): pending Scribe's idle/busy definition in the decision line (testability) + Designer's 2 spec sentences
- lint_js.py fix: CLOSED with both-direction evidence (repro_ok.js→LINT OK; repro_broken.js→FAIL); not reopening
r48 delta (Builder seat, 12:3x): STUB MATERIALIZED on Black _default at 12:30:29 — `agents.json` now a 0-byte PLAIN file (sha12 e3b0c44298fc, islink=False, no reparse bit), between two of my own probes; L7/L24 "absent" lines are vintaged as-of and superseded from 12:30:29. Left in place deliberately (Studio-managed state). Concession on record: Scribe's correction adopted — stub ≠ junction, my H3-origin lead downgraded to hypothesis/unverified; Verifier's discriminator test (routine session path never converts it to a reparse point) de-risks H3 per D11. Mechanic's consumer-risk question ANSWERED from code: no live agent_portal.py on Black, no :8099/:8888 listener; check_black_models.py discover_agents_json() walks only SOURCE_CANDIDATES (uploads/AgentPortal_V1, ./AgentPortal_V1, C:\Projects\AgentPortal\AgentPortal_V1) — never cwd; run_checks.py opens agents.json strictly inside discovered source dir → stub cannot shadow discovery, and a naive hit would fail loud (exit 2), not silent. r48-amd (Scribe correction adopted, Mechanic's CLOSED-nil re-assertion superseded): my code evidence covers the two KNOWN gate scripts + no live consumer TODAY — it does not cover unknown consumers inside a future H2 bundle that might walk _default/cwd before SOURCE_CANDIDATES. Correct checklist disposition for Black = LOW-RISK / VERIFY DISCOVERY ORDER AT H2 LANDING (stub is 0-byte plain file; known failure mode is loud exit 2, not silent). Drop state unchanged (uploads/, AgentPortal_V1, ui-upgrades-r4.md ABSENT) → P8 STOP holds; port lane staged against verified b82dd3b77f4e.
