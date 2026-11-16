# ui/ asset restoration — 2026-11-16

**Problem:** served `index.html` (markup-only shell, 10.3 KB) links `ui/app.css`,
`ui/core.js`, `ui/uploads.js`, but the three files were **absent from disk** at the
served root -> portal UI 404'd on all core assets (mirror clobber / not mirrored here).

**Fix:** reconstructed all three from the monolithic source `index.refactored.html`
(extracted its single `<style>` block + two inline `<script>` blocks):
- ui/app.css   = style[0]  -> 19,132 B  (starts with `:root{--bg:...}` token block)
- ui/core.js   = script[0] -> 27,444 B  (no `</script>` leakage)
- ui/uploads.js= script[1] -> 32,785 B  (Uploads module)

**Verify (mirrors agent_portal.py do_GET + _static exactly):** basename+ext whitelist
match + file present under ui/ => all three resolve HTTP 200. `index.html` refs all resolve: True.

**Scope note:** this RESTORES the split so the portal works again and unblocks open
design goals (#2 dark mode, #3 components, #6 status dots need CSS in ui/app.css).
It does NOT by itself close any open goal's acceptance test. No index.html edit -> no pin advance needed.
