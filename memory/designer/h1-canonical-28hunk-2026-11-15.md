# Designer — H1 canonical 28-hunk script (2026-11-15 ~14:0x)

## What happened this round
Mirror clobbered the shared tree AGAIN mid-round: index.html + agent_portal.py back to
baseline (no goals, .frow collision L92/L120) AND the canonical script reverted from
Verifier's `4b5f45b83459` (H1x) / my 28-hunk edit back to the original `b06619152f2e`
(26 hunks, no H1). So BOTH parallel H1 fixes were lost; no merge conflict remained —
just a gap. I re-landed H1 as the single canonical hunk set (H1a CSS rename, H1b JS
template) in this script.

## Canonical artifact
`memory/designer/goals-patch-apply-2026-11-15.py` — **sha cb7246efedf6**, 16893 bytes,
28 hunks (26 original + H1a/H1b). H1 anchors: post-M3c 12px CSS rule; JS line is
`html+='<div class="frow">...` — PLAIN single quotes, no backslashes (verified by hexdump;
Python repr shows `\'` which is display-only — do not trust it for anchor text).

## Verification (this round, on the live shared tree)
- Pass 1 from clobbered baseline: applied 28 / skipped 0, py_compile OK, 9/9 post-checks PASS
- Pass 2 idempotency: applied 0 / skipped 28, byte-identical SHAs (portal aa5c3e675dae, index 7759471414c3)
- Gate greps: exactly ONE `.frow` CSS rule (L92 dialog-form flex); `.frow-h{` at L120;
  `class="frow-h"` in JS template L680; goalsPanel + /api/goals present

## DEPLOY CAVEAT (new, important)
This script exists on WHITE (that's where the human runs it), so it is NOT mirror-immune —
the White->shared mirror will revert my shared copy to White's version. If White still holds
`b06619152f2e`, the human MUST pull `cb7246efedf6` from the portal first. Pre-flight one-liner:
```
python -c "import hashlib;print(hashlib.sha256(open(r'memory\designer\goals-patch-apply-2026-11-15.py','rb').read()).hexdigest()[:12])"
```
expect `cb7246efedf6`; if it prints `b06619152f2e`, re-copy the script from the portal
(relative path memory/designer/goals-patch-apply-2026-11-15.py) before running.

Supersedes: my 13:5x "H1 landed" note (that tree state was clobbered within minutes).
