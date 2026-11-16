# Designer — goals 2 + 6 re-applied & verified (post mirror-wipe), 2026-11-16

Mirror cycle-2 wiped the dark-theme + status-dot work; re-applied on top of the surviving
token layer and verified. Files touched: ui/app.css (additive), ui/core.js, index.html (re-pinned c66287f48195 / 2026-11-16k).

## Goal 2 — Dark mode + theme toggle
- :root IS the dark palette (default) -> zero dark regression by construction; light is ADDITIVE only.
- [data-theme="light"] overrides 13 color tokens (GitHub AA palette: --bg #f6f8fa, --text #1f2328, --acc #0969da, --ok #1a7f37, --warn #9a6700, --err #cf222e) + targeted overrides for hardcoded dark surfaces (.acard.sel, .msg.you, .toolchip, #peek, #queuePanel, #intBanner, .flink, .dmseg).
- Header toggle button #themeBtn (aria-labelled); pre-paint <head> script sets data-theme from localStorage else prefers-color-scheme (no flash); core.js IIFE persists choice + swaps icon.
- VERIFIED: WCAG contrast computed on both themes for text/bg, dim/panel2, ok/warn/err/acc vs bg -> 0 failures (dark min 5.88:1, light min 4.57:1), all AA.

## Goal 6 — .status-dot component
- ui/app.css: .status-dot base (neutral/--dim) + variants .ok/.idle(=--ok), .warn/.busy(=--warn), .err/.unknown(=--err) + .lbl; legacy .fdot.busy/.unknown repointed to tokens (retired ad-hoc #ffb454/#e05252).
- ui/core.js: fleet row emits <span class="status-dot 'busy|idle|unknown'"> + <span class="lbl">; renderAgents roster adds a status dot (ok when selected/active, neutral otherwise) with title; setGitDot() drives #gitDot in ops-git (clean=ok, changed=warn, no-repo/error=err).
- index.html: #gitDot added to the Ops "Working tree" line.
- VERIFIED: grep -> .status-dot present in fleet (core.js), ops-git (index.html + core.js setGitDot), roster (core.js renderAgents); component defined in ui/app.css; zero literal color-keyword (green/red/blue/orange/purple) violations across css+js+html.

Artifacts: ui/app.css, ui/core.js, index.html (+canonical memory/designer/index_html_CANONICAL_c66287f48195_2026-11-16k.html).
Note: live screenshot pair on :8099 deferred to Verifier (needs browser/CDP); contrast + grep evidence above is the gate here.
