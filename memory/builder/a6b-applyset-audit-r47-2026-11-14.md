# a6b apply-set audit (Builder seat) — 2026-11-14 r47, planning-meeting round

Purpose: give Orchestrator a byte-exact stamp recipe for bundle v2 BEFORE the ec095107 set is applied; correct two inaccuracies in the r46 one-liner with evidence. All measurements taken from White shared root this round.

## Measured pins (this seat, this round)
| file | md5 | bytes |
|---|---|---|
| index.html (served, canonical) | 9c6b08e3d98355e632a72cb871d5b60d | 67,681 |
| memory/builder/index_html_a6_b_candidate_ec095107236a9bdc.html | ec095107236a9bdcf514baaf4e9b4abd | 69,707 |
| memory/builder/index_html_a6_b_a11y_candidate_ffa774230d8f354cbcdab640bd080b02.html | ffa774230d8f354cbcdab640bd080b02 | 69,707 |
| memory/designer/a6b-recon-C-not-candidate-6be6a14d90fd.html | 6be6a14d90fd48f2f78bf411f3576f83 | 69,699 |

## Relationship map (difflib, n=0)
- **a11y ffa77423 = ec095107 + exactly ONE line**: L141 `.aev .at{color:#6b7688;...}` → `#8b93a7`. Equal size (69,707 B) because the substitution is same-length.
- **ec095107** = A6+B base: toast system + responsive 360px layout + #panelDock + panel discipline (one-open-at-a-time) + armed two-click reset (`_arm` / "Confirm reset?") + agent-delete "Sure?" `_arm` pattern. `.aev .at` still #6b7688. (Its two existing `#8b93a7` hits are unrelated: `.busyspan`, `#peek .pk-sz`.)
- **reconC 6be6a14d** = a11y minus the expanded reset block (compact single-line form) − trailing newline → 69,699 B (the r46 "−8 B" figure). Filename says not-candidate; it is NOT a ≤8-B byte-equivalent of a11y — the delta is content (reset-block formatting), so do not stamp from it.
- **cur → a11y full apply set**: 65 lines added / 14 removed (unified diff n=0, captured in this round's run).

## Corrections to r46 one-liner (evidence above)
r46 said: "ec095107 apply set (when stamped) = two lines: `.aev .at` → #8b93a7 + armed resetBtn `_rb.style.color=\"#33210a\"`".
1. The `#8b93a7` line is NOT in ec095107 — it is the sole a11y-vs-ec delta. "Two lines" only coheres as the delta vs CURRENT index.html (which lacks both features).
2. `_rb.style.color="#33210a"` does not exist in ANY file in the tree (grep all four: 0 hits). The real armed-reset change is the `$("resetBtn").onclick` reformat + `_arm` two-click-confirm block (plus the delete-button "Sure?" variant).

## Stamp recipe for Orchestrator/Verifier (bundle v2)
- **Preferred**: replace index.html bytes with a11y candidate → expect md5 ffa774230d8f354cbcdab640bd080b02 / 69,707 B. This is current + complete A6+B set incl. the a11y color line.
- **Equivalent**: base ec095107 + single-line patch at L141 (#6b7688→#8b93a7) → byte-identical to ffa77423 (verifiable post-stamp).
- Post-stamp gate: md5+size of served index.html via portal, plus Designer's live-leg re-run (owed per r46 Open).

## Not done (by design)
- No write to index.html, agents.json, TODO.md or MEMORY.md from this seat — apply is Orchestrator's after Arnold's r21 leg; smoke8 stays detached (smoke8.py header: serial only, runs behind this chat's slot).