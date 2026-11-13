# Verifier r19 — AC-A2-1..4 closure (Black seat, 2026-11-14 ~01:5x)
Scope: "process-level on PID 23704" executed as far as this seat physically allows. Live :8099 from Black remains policy-blocked (re-probed THIS round: TCP 192.168.1.179:8099 → 10035 after full 4 s timeout = filtered, not refused; closed local port control → 10013 immediate; sandbox-python allowlist rejects the host; terminal curl blocked). Live HTTP legs stay Mechanic-as-proxy / White-browser per r7-r8 convention.

## Code pins (the build PID 23704 launched from — byte-exact in shared root)
| file | md5-8 | size | verdict |
|---|---|---|---|
| agent_portal.py | 1b86880c | 80,056 B | OK (= r19 pin) + py_compile OK (2 pre-existing SyntaxWarnings in docstrings, non-blocking) |
| memory_mirror.py | e5c4a229 | 10,668 B | OK + py_compile OK |
| index.html | 9c6b08e3 | 67,681 B | OK = TRUE canonical (r19 pin-corruption fix held) |
PID-level trap-check (created 22:01:54 > lastwrite 22:01:38) rests on the human-leg r19 record — NOT re-verifiable from Black (no White process-table access). Chain: fixed bytes here + that timing = portal serving fixed code.

## Per-AC verdicts (structural/byte-level; "live" sub-clauses flagged)
- **AC-A2-1: PARTIAL.** Placement PASS — `#filesBtn` is the immediate sibling after `#fleetBtn` in the mode bar. Click-opens PASS — onclick toggles `.open`; CSS `#filesPanel{display:none}` / `#filesPanel.open{display:flex}` (landed house-style variant, not the patch's hidden-class draft; internally consistent). **Outside-click-closes FAILS as written** — the only document-level click handler in the whole doc is for `#attachWrap`. BUT: Fleet, Activity, and Ops panels all use identical re-click-toggle with NO outside-click close → Files matches house style exactly. Adjudication owed (Orchestrator/Designer): accept house-style variant (my read) or spec a shared close handler for all four.
- **AC-A2-2: static PASS / live OPEN.** Row render confirmed in served JS: one `li` per file, `<a target="_blank" href="/api/file/raw?path="+encodeURIComponent(f.path)>` + meta span `fsFmtSize(size)·fsFmtTime(mtime)` = name · size · mtime. Server side: `/api/file/raw` routed through `_safe_workspace_file()` — realpath-anchored to HERE/SANDBOX_DIR, NUL-checked, no traversal → `uploads/*` resolves in-bounds. Current uploads/ inventory for the live leg: **N=1** (`uploads/_canary_remote.txt`, 212 B) → panel must show exactly 1 row; raw fetch must return 200 + exactly 212 bytes of that file.
- **AC-A2-3: PASS (structural).** `if(!files.length)` → single line "No uploads yet — drop files into uploads/ on White." then `return`; catch block replaces list with a message, no uncaught throw. Live console-cleanliness = White-browser leg.
- **AC-A2-4: PASS.** `filesLoad()` invoked from exactly two sites (open toggle + ↻). Full-doc timer scan: 6 setInterval/setTimeout hits — saveMsgs debounce, busyT, actTimer, fleetTimer, pollStatus 15 s, refresh 30 s — **zero reference /api/uploads**. No-background-timer veto respected.

## Verdict
AC-A2-2 (static), AC-A2-3, AC-A2-4: CLOSED with evidence above. AC-A2-1: placement+open CLOSED; outside-click clause NOT implemented (house-consistent) → needs one-line adjudication, not a code pass from me. Live legs (HTTP 200 + byte compare on the canary, console clean, devtools request count) = ONE proxy/browser pass on White with the N=1/212 B expectation above — hand to Mechanic.

## Untested / out of reach from this seat (explicit)
- Any live HTTP response from :8099 (network policy-blocked, re-proven this round).
- White process table / PID 23704 identity (relayed evidence only).
- Browser console + devtools network behavior (no browser here; node still absent on Black — JS never executed, reviewed statically only).
