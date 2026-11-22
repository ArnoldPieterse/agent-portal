# ARIA Accessible-Name Audit — Portal (2026-11-21)
Owner: Designer. Goal #1 (WCAG 2.1 AA), ARIA leg. Status: **audit complete; fixes pending repin.**

## Command
```
python memory/designer/aria_audit.py
```
Exit code = number of gaps (0 clean). Reusable; run after any index.html markup change.

## Result: 49 interactive elements, 18 flagged
Script checks each control for an accessible name via aria-label / aria-labelledby /
wrapping `<label>` / sibling `<label for="id">` / visible text. Sibling labels WITHOUT
a `for` attribute do NOT count (WCAG 4.1.2 — name must be programmatically associated).

### Genuine fixable gaps (17)
| Element | Issue | Fix |
|---|---|---|
| `button#edClose` | only `title="Close"` (weak/AT-dependent fallback) | add `aria-label="Close"` |
| `select#actSel` | no label, populated dynamically | add `aria-label="Session"` |
| 15× settings-dialog fields (`f_name`,`f_emoji`,`f_color`,`f_blurb`,`f_persona`,`f_studio`,`f_key`,`f_ragstudio`,`f_ragkey`,`f_model`,`f_temp`,`f_maxtok`,`f_reasoning`,`f_maxtools`,`f_kb`) | sibling `<label>Name</label><input>` — visible but NOT programmatically linked (no `for`, not wrapping) | add `for="<id>"` to each matching `<label>` |

Root cause: the settings dialog form uses `<label>X</label><input id="f_x">` as siblings.
The text is on-screen, so sighted users are fine, but AT has no name→control association.

### Non-issues (3, excluded from fix list)
| Element | Why not a gap |
|---|---|
| `input#filePick`, `input#dirPick` (type=file) | both `hidden`/display:none — never rendered or operable by users |
| `textarea#input` (chat box) | uses placeholder as name; borderline (placeholder-only names are discouraged but present). Optional: wrap in `<label>` or add aria-label. |

## Fix path (next step, blocked on repin)
index.html is PINNED (memory_mirror.py PIN_FILES) — direct edits revert on next mirror cycle.
The `for=` additions + `aria-label`s must land via the canonical-repin procedure
(`memory/designer/index_html_CANONICAL_<sha12>_YYYY-MM-DDx.html` + update PIN_FILES + commit).
After that, re-run `python memory/designer/aria_audit.py` -> expect gaps down to <=1 (chat textarea) or 0.

## Goal #1 status
- Contrast leg: **PASS** (both themes, see wcag-audit-2026-11-20.md).
- ARIA leg: audit DONE, 17 genuine gaps identified + fix path defined; fixes pending repin.
- Keyboard leg: still PENDING (see wcag-audit-2026-11-20.md §2).
Goal NOT yet closable — needs keyboard re-verification + the label/aria fixes landed and re-audited clean.
