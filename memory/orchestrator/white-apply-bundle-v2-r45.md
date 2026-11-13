# White Apply Bundle v2 — r45 (Orchestrator, 2026-11-14 ~06:1x)

Supersedes all prior bundle versions (r40/r42/r43 lists). Single-pass checklist for Arnold's White-console operation. Every item verifiable on disk after apply.

## Item 1 — STAMP TARGET (adjudicated r45)
`memory/builder/index_html_a6_b_a11y_candidate_ffa774230d8f354cbcdab640bd080b02.html` = **ffa774230d8f354cbcdab640bd080b02 / 69,707 B** — the single stamp-ready file: A4+A5+A6+B+a11y (`#6b7688`→`#8b93a7`) in one pass. Supersedes both `45323d09` and `ec095107` as the AC-A2 re-run target. First-party verified on Orchestrator seat r45: builder + verifier copies byte-identical.

## Item 2 — AC-A2-2 LIVE LEG
Run from White console against ffa77423; produce `ac_a2_live_leg_r20/r21_result.json` (absent tree-wide for the 11th consecutive measurement). No agent seat can run this leg (loopback/egress blockage, structurally confirmed r19–r45).

## Item 3 — memory/synthesis/INDEX.md: EXACTLY SIX pointer lines, applied ONCE (top of list, newest-first)
Order: (1) r42 line, (2) r41 line — verbatim from **Scribe's** `memory/synthesis/index-pointer-addendum-r43.md` (ca4f6e45 / 2,291 B) — then batch-r40's four lines (r38/r36/r31/r40 per that file).
**De-dup adjudication:** Archivist's `memory/archivist/index-pointer-addendum-r43.md` (8a69f329 / 2,031 B) is a verified BACKUP ONLY — do NOT apply. Its two lines are alternative descriptions of the same leaves; applying both addendums would double the r41/r42 pointers. Scribe's set wins: he owns the synthesis module (source sits beside its target) and his lines carry the adjudication flags (TODO regression hash, Archivist audit flag). Formal supersession-chain footer unchanged per both authors.

## Item 4 — hosts.md: two rows
- **White row** (folder convention post-rename): Q4_K_S from `unsloth\Qwen3.8-27B-GGUF` ctx 131072 + Q8_0 from `lmstudio-community\Qwen3.8-27B-GGUF` ctx 32768; BOTH report under bare id `Qwen3.8-27B-GGUF` → count-based check is the only reliable guard. Staged in `memory/mechanic/fleet-sweep-r21-2026-11-14.md` (ef729392 / 2,183 B).
- **Black row**: from Archivist r42 batch (`index-pointer-batch-r42.md`, 8ea31427 — double-confirmed by Verifier r45 + Researcher r42).

## Item 5 — TODO.md md5 stamp + regression adjudication
Seat reads DISAGREE: 3f0ccedc/93,755 B (Scribe r42/r43, Verifier r45) vs Orchestrator seat **f5d0a54d / 147,558 B** (r43 section present). White disk is the sole adjudicator; stamp the canonical hash after apply.

## Item 6 — stray root `archivist/` folder
List on White + adjudicate Archivist batch item D. Seat-local-artifact suspicion: present only on Archivist seat; absent on Researcher + Scribe seats (both dir-verified).

## Item 7 — dcabots re-prompt
Pre-check **atlas-q8 loaded first** (unverified in r21 sweep — do not prompt against an unloaded backend).

## Item 8 — smoke8
When convenient (quinn-q4 wedge-#2 rule; portal unreachable from Red seat per r21).

## HR / fleet status
No action owed: no re-role, retirement, or binding change. agents.json 2d5433db/9,559 B binding stands. All eight agent lanes closed or human-gated.

## Notes
- Verifier r45 leaf on Orchestrator seat = 0b329570/3,085 B vs self-report b48af1af/3,028 B: content read in full and intact; delta = +57 B line-ending (CRLF) normalization in mirror — benign, no re-verify owed.
- Root index.html on Orchestrator seat holds 8ef4e222/67,681 B with the a11y fix byte-exact (`.aev .at{color:#8b93a7;...}`, zero `#6b7688`) — so ffa77423's stacked fix matches canonical; Black root 9c6b08e3 still carries the pre-fix value (Verifier r45 finding) and is NOT a stamp candidate.
