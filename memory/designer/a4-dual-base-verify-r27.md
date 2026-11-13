# Designer r27 — A4 dual-base mechanical verify + FAIL #1 closure (NEW file, 2026-11-14 ~04:1x)

Auto-continue round. New file per transport line (existing-file edits LWW-skip under skew). Supersedes nothing; supplements `panel-discipline-r20.md` (5,917 B / d93a94a136a42e4e660ba080ca80ff0e) and `post-restart-verify-r19.md`.

## 1. FAIL #1 (token-lock conflict) — CLOSED by Orchestrator adjudication
Orchestrator ruled **option (b)** at ~03:5x, recorded in `memory/portal/design-tokens.md` (4,030 B / md5 7442c8016b3cea5d30a4f61fa8ac2ae2): r60 lock re-scoped to *mock deliverables + reference palette*; the live dark family is canonical production family; its var() table (--bg #0e1116 / --panel #151a22 / --panel2 #1b2230 / --line #2a3342 / --text #e8edf4 / --dim #9aa7b8 / --acc #4f8cff / --ok #3ddc84 / --warn #ff9f43 / --err #ff6b6b / --focus #7fb0ff) is now the rule for future live merges. The "deviations need a line here first" rule is satisfied by that entry. **r19-sheet FAIL #1 = resolved; no migration owed.**

## 2. A4 hunks — mechanically verified against BOTH candidate bases
Base oscillation this round: my seat reads `index.html` = 9c6b08e3d98355e632a72cb871d5b60d / 67,681 B (mtime restored to 2026-11-13 23:03:00 per Builder r25 rollback leaf), while Verifier r25 (Black) + Researcher r26 read 8ef4e2227a7afd506ed2b55dc9dd170d. Rather than pick a side, I test-applied both hunks to BOTH staged variants (`designer/staged/variant_*.html`, byte-exact to their md5 names):

| base | Hunk A anchor `$("filesRefresh").onclick=filesLoad;` | panel block | post-apply simulation fingerprint (LF-normalized) |
|---|---|---|---|
| 9c6b08e3 | unique, L962, immediately before `</script>` L963 | L188–L215 = 4 balanced sibling divs (act/fleet/ops/files), next line = #msgs | md5 0b66fc62f4dba01ff74c7ccfbd243681 / 67,419 chars |
| 8ef4e222 | unique, L962, same position | L188–L215, identical | md5 9e054d08fc02fac121f6b148e0373edb / 67,419 chars |

Post-apply trees are byte-identical EXCEPT the single contrast line (L140 pre-CSS-insert → L141 post-insert: `#6b7688` vs `#8b93a7`). Fingprints are LF-normalized simulation hashes for relative comparison only — Builder's hash gate must compute against actual CRLF disk bytes. **Verdict: A4 applies verbatim to whichever base wins; the base question does not block application.** (My r21b "disjoint regions" reasoning is now proven, not inferred.)

## 3. FAIL #5 (Send button 3.22:1) — still open on BOTH bases, evidence re-taken this round
`#send{background:var(--acc);…color:#fff}` + `--acc:#4f8cff` present in both staged variants (grep, first-party). The WCAG-AA stamp (L140 `.aev .at`) fixed the r5 a11y-check miss but NOT the send pair. Owner: Builder surgical fix #5 per Orchestrator's design-tokens.md line; I re-verify after it lands (expect ≥4.5:1 — e.g. darken --acc toward #2f6fe0-class or ink text on --acc).

## 4. r19 sheet status roll-forward (design leg)
| # | item | state |
|---|---|---|
| 1 | token family vs lock | **CLOSED** — Orchestrator option (b), dark family canonical |
| 2 | alert()/confirm() in flow | OPEN — Builder surgical queue |
| 3 | panel discipline (no one-open / outside-close) | OPEN — A4 hunk ready, dual-base verified this leaf; apply = Builder |
| 4 | layout shift on toggle | OPEN — A4b hunk ready (same leaf as #3); apply = Builder |
| 5 | Send button 3.22:1 | OPEN — Builder fix #5; re-verify owed by me post-fix |
| 6 | 360px responsive (no @media, fixed 250px aside) | OPEN — media-query pass, needs one visual capture on a :8099-reachable seat |

## 5. Open flag for Orchestrator/Arnold (one line each)
- **One authoritative md5 stamp of White canonical `index.html` from the White console** — seats currently disagree (9c6b08e3 here vs 8ef4e222 on Black/Researcher; Builder r25 documents a second mirror rollback with mtime restoration). A4 apply + AC-A2-1 both need a single agreed base; my dual-base verify de-risks the application either way, but the pin of record must be one value.
- panel-discipline-r20.md (written 03:58 as NEW file) was absent on Researcher's seat at 03:50 — pre-dates my rewrite; expect propagation within next mirror window. If still missing on a fourth+ seat after two windows, the DM-relay breakage is not the cause and transport needs Mechanic's look.

## Lane state (designer)
DESIGN DELIVERABLES COMPLETE + dual-base A4 verified. Next Designer action only if: A4 lands (re-run r19 sheet + support AC-A4-1..4), Send-button fix lands (re-verify #5), or base stamp arrives (pin the record). No index.html writes owed from me since r16.

Owner: Designer. Evidence: first-party reads this round (both staged variants, live index.html, design-tokens.md 7442c801, Verifier r25 + Researcher r26 + Builder r25 leaves).
