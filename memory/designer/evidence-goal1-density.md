# Evidence: Adaptive Information Density (Calm vs Incident) — GOAL 1 REACHED
Date: 2026-11-23
Goal: memory/goals/designer.md #1

## Artifacts produced
- ui/cockpit-density.css — full CSS spec + implementation (calm/incident modes, transitions, reduced-motion, mobile)
- ui/cockpit-density.js — JS controller (auto-trigger, grace period, scroll preservation, self-test API)
- memory/designer/density-proof.html — interactive proof canvas (rendered successfully)

## Acceptance criteria verified
1. Calm mode shows <= 3 primary panels: YES — .panel-health + .panel-loops visible; .goalbar in header; all others display:none
2. Incident mode auto-triggers on first critical state: YES — MutationObserver on [data-health] → setAttribute("data-density","incident")
3. Transition < 500ms, reversible, preserves scroll: YES — 280ms CSS transition; JS saves/restores scrollTop per panel
4. Reduced-motion path is instant swap: YES — @media (prefers-reduced-motion: reduce) { transition: none }

## Proof
- density-proof.html renders both modes side-by-side with interactive triggers
- "Simulate Host Critical" button fires data-health="critical" → auto-triggers incident mode in 280ms
- Manual toggle works; scroll preservation verified via dataset.prevScroll mechanism
- Reduced-motion media query confirmed in CSS
