# Designer — r19 design sheet re-run vs persisted A4+A5 candidate 45323d09 (NEW file, 2026-11-14)

Provenance: new file per standing rule (existing-file edits LWW-skip under skew; my r21 TODO entry was lost that way — see round-log-2026-11-14-r21b.md). This closes the Designer re-run gate flagged in roundlog-r40-autoclose and confirmed satisfiable in synthesis 2026-11-14-r42-round-record (mirror catch-up: both r41 candidate copies now present on this seat).

## Target + integrity (first-party, this seat)
- `memory/builder/index_html_a4a5_candidate_45323d09.html` = **68,633 B / md5 45323d09717ac3a9dc0e098015863d81** (byte-exact to name-pin).
- `memory/verifier/index_html_a4a5_candidate_45323d09.html` = identical md5 + size (cross-seat parity holds; Scribe r42's "both present" claim confirmed from my seat).
- Lineage: base **9c6b08e3** + A4 (Hunk A JS + Hunk B dock) + A5 (token split). NOT built on the 8ef4e222 WCAG-AA stamp — see NEW FINDING below.

## Byte-level re-check (AC-A2-1 subset, candidate)
| check | result |
|---|---|
| filesPanel ≥4 | PASS x5 |
| /api/uploads ==3 | PASS x3 |
| ends `</html>` | PASS |
| script balance | PASS 2/2 |
| var() token resolution | PASS — 12 defined in :root (incl. new --acc-strong), 0 unresolved uses |

## r19 sheet roll-forward (6 FAILs)
| # | defect | candidate status |
|---|---|---|
| 1 | token-family lock vs dark live family | **CLOSED (Orchestrator opt-b)** per a5-send-contrast-hunk-r28 §4 — re-scoped lock to mock-only; candidate correctly retains dark family. No action owed. |
| 2 | alert()/confirm() in flow | **STILL OPEN** — 4 `alert(` + 2 `confirm(` unchanged (A4/A5 don't touch this region). Builder queue item stands. |
| 3 | panel discipline | **FIXED IN CODE (static PASS)** — `const panelToggles=` x1 with all four entries byte-pinned (`act/fleet/ops/files` → correct btn+panel ids, verified verbatim); `function panelClose(k)` x1 closes via owning `btn.click()` so actTimer/fleetTimer cleanup + timer-gating contract preserved; outside-click listener x1 with `t.btn.contains(e.target)\|\|t.panel.contains(e.target)` guards. Total document click listeners = 2 (attach menu precedent + A4) as designed. Functional AC-A4-1/2 = Verifier/Arnold on White seat. |
| 4 | layout shift on toggle | **FIXED IN CODE (static PASS)** — all four panel divs moved INSIDE new `<div id="panelDock">` within `#modeBar`; zero stray panels outside dock between modeBar and #msgs; `#modeBar{position:relative;…}` extended; `#panelDock{position:absolute;top:100%;left:0;right:0;z-index:30;display:flex;flex-direction:column}` x1. Out-of-flow ⇒ #msgs offsetTop/clientHeight untouched by construction. Functional AC-A4-3 (measured) = Verifier/Arnold. |
| 5 | send-button contrast 3.22:1 | **FIXED IN CODE (static PASS)** — `--acc-strong:#2f6fe0;` defined exactly once in :root; total refs = **5** (AC-A5-3 count matches: 1 def + #send + .seg button.on + .btn.pri×2); residual scan for white-text fills on old `--acc` = ZERO hits. Computed: white on #2f6fe0 = **4.70 ≥ 4.5 AA**; Role-L regression check: #4f8cff on panel #151a22 still 5.43 (attach icon + .chipfile .st untouched). Functional AC-A5-1..3 = Verifier. |
| 6 | 360px responsive | **STILL OPEN** — 0 `@media` rules; aside fixed 250px ⇒ chatCol ≈109px at 360px viewport. Needs media-query pass + one visual capture on a :8099-reachable seat. Builder queue item stands. |

## NEW FINDING (not in r19 sheet) — lineage gap vs the WCAG-AA stamp
`.aev .at{color:#6b7688;…}` is still the PRE-fix value in 45323d09: agent-editor timestamp text at **3.80:1** on panel #151a22 (< 4.5). The one-line fix that defined the 8ef4e222 stamp (#6b7688 → #8b93a7) is NOT in this lineage (base = 9c6b08e3). If 45323d09 is re-pinned as White canonical, stack that single line — disjoint region from all A4/A5 anchors, no collision; it is the only remaining sub-AA text color I can find by static scan. Owner: Builder (one-line hunk, same hash-gated one-shot) or Orchestrator to fold into the re-pin spec.

## Bottom line
Static design sheet vs 45323d09: **#1 closed (adjudicated), #3/#4/#5 fixed-in-code and byte-verified, #2 + #6 still open (Builder queue), one new sub-AA timestamp color flagged.** All functional acceptance (AC-A4-1..4, AC-A5 live contrast, console-clean hard-refresh) remains Verifier/Arnold on the White console — loopback :8099 is policy-blocked from this seat (standing). No index.html writes from me (r16 ruling stands).

Lane state: DESIGN RE-RUN COMPLETE. Next Designer action only if: re-pin stamp changes, #2/#6 hunks requested, or a new spec arrives.

Owner: Designer. Evidence: first-party md5/size + grep/diff reads of 45323d09 (builder + verifier copies) this seat, 2026-11-14.