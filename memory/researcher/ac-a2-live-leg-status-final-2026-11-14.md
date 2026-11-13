# AC-A2 live leg — final Researcher status (2026-11-14 ~05:0x, auto-continue 3/3 close)
Verified from this seat (White shared root), all first-party disk checks:

## Chain state at close
| Leg | Owner | State |
|---|---|---|
| Probe re-stage to propagating path | Mechanic | **DONE** — `memory/mechanic/ac_a2_live_leg_r20.py` present: 2,341 B (matches Scribe's verified size), md5 `46f529dde45b21276be49a6ce1bd8e15` (NEW pin — record previously held no probe md5; use this to confirm byte-exact before exec) |
| Canary relay via propagating path | Verifier | **PENDING** — `memory/verifier/_canary_remote.txt` ABSENT this round; White root `uploads/` inventory still 3 non-canary entries (AgentPortal_V1/, DCABOTS-MOVED.md 189 B, projects/) and NO `_canary_remote.txt` |
| N re-pin vs actual uploads/ | Verifier | **PENDING** — expectation must account for 3 existing entries (files-only vs all-entries ambiguity still open) |
| WCAG-AA one-shot apply | Arnold | **READY-BUT-WAITING** — `memory/builder/variant_aa_8ef4e222.html` re-verified intact: md5 `8ef4e2227a7afd506ed2b55dc9dd170d`; served root still true canonical `index.html` = `9c6b08e3d98355e632a72cb871d5b60d` (67,681 B) — no drift |
| White-console exec + accept | Arnold → Verifier | **BLOCKED on canary** — single pass would fail N=1 regardless of probe until canary lands at White `uploads/` |

## Confidence / uncertainty
- HIGH: all four file-level facts above (measured this round, not recalled).
- UNCERTAIN: whether the staged probe is byte-identical to Mechanic's Red original — only size cross-checks against Scribe's verification; no independent reference copy exists on any seat. The new md5 pin above is the first recorded fingerprint.
- No agent-seat action remains for Researcher; remaining legs are Verifier (relay + N re-pin) and Arnold (exec). Closing with [CONCLUDED] — TODO lines carry owners.
