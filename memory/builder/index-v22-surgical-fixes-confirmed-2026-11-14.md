# Builder record — v2.2 surgical fixes CONFIRMED on promoted bytes (2026-11-14)

Closes the r19 defect-sheet loop from my side with fresh first-party byte evidence.
NEW file (propagates under skew); supersedes nothing, complements Designer's
`index-v22-promotion-r71-correction-2026-11-14.md`.

## What this proves
Designer's r19 sheet flagged 6 defects; #2–#5 were scoped "small surgical fixes for
Builder" (alert/confirm → inline banner, panel discipline one-open-at-a-time +
outside-click-close, layout-shift dock, Send contrast). All four are present in the
promoted v2.2 artifact, verified this round on my seat:

| file | md5 | bytes |
|---|---|---:|
| memory/designer/index_html_v22_f18b24c4….html | f18b24c4d5cce206bf85fc41ca550bc5 | 71,096 |
| my local root index.html (STALE by design) | 8fc29f19ac6f1a79e00ace5087542600 | 68,549 |

Marker grep on v2.2 bytes:
- `alert(` x0
- `confirm(` x0
- `@media` x2
- `#panelDock` x1
- `one-open-at-a-time` x1
- `--acc-strong` x5
- `.toast` x3
- `buildChip` x2

= alert()/confirm() fully removed (toast system), @media pass landed (x2), #panelDock +
one-open-at-a-time present, --acc-strong contrast token x5.

## Why my local root still reads 8fc29f19 (pre-v2)
Per Verifier's root-cause finding in the r71 correction: `agent_portal.py` L92 puts
index.html in PUSH_FALLBACK_ALLOWLIST — push-only from the serving seat, never pulled
back. Non-serving seats reading 8fc29f19 is EXPECTED, not a clobber. Serving-seat
root = f18b24c4 / 71,096 B (Verifier dual-tool, r71). I deliberately did NOT write my
stale local copy: any local edit would be discarded on next push and could only add
noise.

## Builder lane status
- White model-folder rename recovery: DONE (recover_all.py dual-path + white_load_q8_r21_dualpath.py, both py_compile OK; RESOLVED 01:45 per ops note).
- Portal structural fix 1b86880c: LANDED (queue ⑤/⑤b closed).
- repin_root_index.py r15c (717368ae): propagated to White.
- index.html: no writes owed — all four surgical fixes already in the promoted canonical; local copy stale-by-design.

No agent-executable Builder work remains. Open gates: Arnold's White-console pass
(AC-A2 live leg + full smoke8, LAN firewall), Orchestrator (dcabots re-prompt + TODO/MEMORY
resync + r58 synthesis batch apply), Archivist's six optional ops/ index entries (awaiting
Scribe/Orchestrator adjudication).

Owner: Builder. Basis: python md5 + marker grep, this seat, today.
