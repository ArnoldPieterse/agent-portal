# Builder r41 — persist_a4a5_candidate_r40.py FIXED + RERUN VERIFIED (2026-11-14 ~06:4x)
Closes the last agent-executable item Verifier r40 flagged for me ("@Builder: fix the ROOT computation"). Extends, does not retract, `a4a5-apply-r35-closeout` and `a4a5-lineage-and-revert-r38`.

## Fix
- Root cause confirmed as Verifier diagnosed: `os.path.dirname` ×2 on `<root>/memory/builder/x.py` resolves to `<root>/memory`, so the script-pin gate hit `FileNotFoundError: Z:\memory\apply_a4_a5_r35.py` on every seat.
- r40-fix (in-file): ROOT = 3× dirname; plus fallback to Verifier's pinned transform copy `memory/verifier/apply_a4_a5_r35_pinned_copy.py` when the root copy is absent — same pin a20fc8d0…, assert still enforces it. No root writes anywhere.

## First-party rerun (this round, this seat)
`python memory/builder/persist_a4a5_candidate_r40.py` → exit 0, full output:
- GATE PASS: base 67,681 B / 9c6b08e3d98355e632a72cb871d5b60d (root index.html untouched, still pre-stamp canonical)
- sandbox apply: A5 4/4 anchors, A4-B css+markup, A4-A js; crlf_consistent True; js_byte_exact True
- PERSIST OK ×2: `memory/builder/index_html_a4a5_candidate_45323d09.html` = **68,633 B / 45323d09717ac3a9dc0e098015863d81**; `memory/builder/apply_a4_a5_r35.py` = **5,949 B / a20fc8d0cf9fdd8d0f1c73b558c63b89**
- Fingerprint re-confirmed: --acc-strong ×5, panelToggles ×4, panelClose ×2, dom_order_ok True

## Cross-seat pin table (re-hashed from disk this round)
| file | size / md5 |
|---|---|
| memory/builder/index_html_a4a5_candidate_45323d09.html | 68,633 B / 45323d09717ac3a9dc0e098015863d81 |
| memory/verifier/index_html_a4a5_candidate_45323d09.html | 68,633 B / 45323d09717ac3a9dc0e098015863d81 (byte-identical) |
| memory/builder/apply_a4_a5_r35.py | 5,949 B / a20fc8d0cf9fdd8d0f1c73b558c63b89 |
| memory/verifier/apply_a4_a5_r35_pinned_copy.py | 5,949 B / a20fc8d0cf9fdd8d0f1c73b558c63b89 (byte-identical) |

## Builder lane status: EXHAUSTED
All agent-executable A4/A5 work is done and evidenced. Remaining gates are non-agent from any seat I can reach:
1. **Arnold (White console)**: exec `memory/mechanic/ac_a2_live_leg_r21.py` + devtools capture per Designer criteria, then stamp root index.html from the 45323d09 candidate (verify 68,633 B / full 32-char md5 before pinning). Per r38 ruling: do NOT re-apply from a remote seat — mirror would revert it (churn + SKEW_SUSPECT risk).
2. **Orchestrator**: synthesis INDEX append (Scribe handoff `index-pointer-handoff-r38.md`) + White-side md5s of the escalation trio (my r38: agents.json b8b033d5 vs their 2d5433db, same size different content — add to Arnold's White sweep list).
3. **Designer**: re-run sheet against new fingerprint after stamp lands.

Owner: Builder. Basis: first-party script execution + hashlib re-hashes from disk, this seat, 2026-11-14 ~06:4x.