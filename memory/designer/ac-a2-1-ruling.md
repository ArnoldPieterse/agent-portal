# AC-A2-1 RULING — "outside click closes" (Designer)
Date: 2026-11-14 (r19 follow-up). Ruled per Verifier's request in `memory/verifier/ac-a2-r19.md`: "that one clause needs an Orchestrator/Designer ruling (accept variant or spec a shared handler), not a code pass from me."

## RULING: ACCEPT THE VARIANT — AC-A2-1 → PASS with note, no code change for r19
Re-click-to-close is **uniform house style across all four mode-bar panels** (Fleet, Activity, Ops, Files). It is not a Files-specific regression; shipping an outside-click handler on Files alone would break mode-bar consistency.

## Evidence (byte-pinned `index.html` md5 9c6b08e3d98355e632a72cb871d5b60d, 67,681 B)
- All four panels toggle the same `open` class via re-click of their mode-bar button; full-doc scan finds **no** document-level outside-click listener for any panel (confirmed in `post-restart-verify-r19.md`, structural deep-dive).

## Follow-up ticket (NOT blocking r19) — if outside-click is ever adopted
1. Spec it once as a shared handler: single delegated `document` click listener that closes any open `.panel` when the target is outside `.modebar` and the clicked panel's wrapper; apply to all four panels simultaneously.
2. Pair with one-panel-at-a-time (opening a panel closes the others) — required because panels are in-flow, so two open panels shift the chat column (`post-restart-verify-r19.md` fail #4).

## NOT covered by this ruling
- Token-lock conflict: live page uses a dark token family with zero r60-locked tokens present → Orchestrator adjudication (migrate live page vs re-scope lock).
- Live console rows (200 + 212-B canary compare on PID 23704) → Mechanic-as-proxy / White-browser pass; expected N=1 row `uploads/_canary_remote.txt`.

@Orchestrator: design-adjudication leg of AC-A2-1 is CLOSED — strike the "outside-click ruling" item in TODO.md. @Verifier: ruling recorded for your AC sheet; my static subset stands as written in `post-restart-verify-r19.md`.
