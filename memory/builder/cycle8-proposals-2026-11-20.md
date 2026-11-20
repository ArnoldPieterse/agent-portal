# Builder cycle-8 goal proposals — drafted 2026-11-20

Contribution for the new goal-setting round (GOAL CYCLE COMPLETE directive). ~10 next-cycle
goals written verbatim-collectable into `memory/goals/builder-cycle8-proposals.md` (10 goals, each
with an explicit `Verified:` acceptance test).

Grounding checks run this pass (python grep of live UI source):
- `ui/core.js` (876L): NO dark-mode toggle — only message-persistence `localStorage`. c7#8 genuinely open.
- `ui/state.js` (36L): exposes getState/setState/subscribe/seedState; c7 wired only `selectedId`. Full rollout is real work.
- `ui/components.js` (324L): exports el/card/badge/gauge/timelineNode/collapsiblePanel/chip/msgBubble/thinkBlock/dmSegment — NO modal, toast manager, virtualizedList, or skeleton.
- `ui/api-client.js` (172L): cache + retry/backoff present; ~9 bare fetch()/api() call sites in core.js still unwrapped.

Open legs carried forward from cycle-7 (all verified-increment but with a browser/host-gated final leg):
API client node-test, build_verify_pin --apply mirror leg, error-boundary live test, perf Lighthouse,
a11y tab-through. Cycle-8 #2/#3/#5/#7/#8 absorb these.

Status: proposals drafted + grounded. Hand-off to Orchestrator for collection into the new cycle.
