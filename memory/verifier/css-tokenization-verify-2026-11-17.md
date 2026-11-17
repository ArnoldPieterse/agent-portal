# Verification: CSS Tokenization Claim — FAIL (2026-11-17)

**Claim under test:** "Goal 1 CSS tokenization complete: all 28 hex colors + 9 radius/shadow/duration tokens added to :root; 0 remaining outside :root"
**Source of claim:** HOT NOTES (group memory.md), most recent entry.

## Result: FAIL — 33 unique hardcoded hex colors remain outside :root

| Line | Color | Context (truncated) |
|------|-------|---------------------|
| 6 | `#0e1116` | `:root{--bg:#0e1116;--panel:#151a22;--panel2:#1b2230;--line:#2a3342;--text:#e8edf4;--dim:#9` |
| 6 | `#151a22` | `:root{--bg:#0e1116;--panel:#151a22;--panel2:#1b2230;--line:#2a3342;--text:#e8edf4;--dim:#9` |
| 6 | `#1b2230` | `:root{--bg:#0e1116;--panel:#151a22;--panel2:#1b2230;--line:#2a3342;--text:#e8edf4;--dim:#9` |
| 6 | `#2a3342` | `:root{--bg:#0e1116;--panel:#151a22;--panel2:#1b2230;--line:#2a3342;--text:#e8edf4;--dim:#9` |
| 6 | `#e8edf4` | `:root{--bg:#0e1116;--panel:#151a22;--panel2:#1b2230;--line:#2a3342;--text:#e8edf4;--dim:#9` |
| 6 | `#9aa7b8` | `:root{--bg:#0e1116;--panel:#151a22;--panel2:#1b2230;--line:#2a3342;--text:#e8edf4;--dim:#9` |
| 23 | `#20304d` | `.acard.sel{border-color:var(--acc);background:#20304d}` |
| 34 | `#3a6fd6` | `.seg button.on{background:#3a6fd6;color:#fff}` |
| 34 | `#fff` | `.seg button.on{background:#3a6fd6;color:#fff}` |
| 41 | `#243b63` | `.msg.you{align-self:flex-end;background:#243b63;border-color:#33507f}` |
| 41 | `#33507f` | `.msg.you{align-self:flex-end;background:#243b63;border-color:#33507f}` |
| 49 | `#3ddc84` | `.roundend.ok{color:#3ddc84;background:rgba(61,220,132,.08);border:1px solid rgba(61,220,13` |
| 59 | `#4a3f6b` | `.dmseg{margin-top:var(--sp-8);border:1px solid #4a3f6b;background:rgba(138,99,210,.10);bor` |
| 60 | `#b79ce0` | `.dmseg summary{cursor:pointer;color:#b79ce0;user-select:none;font-weight:600}` |
| 81 | `#ff6b6b` | `.chipfile .st.err{color:#ff6b6b}` |
| 101 | `#8b93a7` | `.busyspan{color:#8b93a7;font-style:italic;animation:pulse 1.3s ease-in-out infinite}` |
| 103 | `#6db1ff` | `.flink{color:#6db1ff;text-decoration:none;border-bottom:1px dashed rgba(109,177,255,.5)}` |
| 104 | `#9ccaff` | `.flink:hover{color:#9ccaff;border-bottom-style:solid}` |
| 105 | `#141a26` | `#peek{position:fixed;z-index:99;display:none;max-width:340px;background:#141a26;border:1px` |
| 105 | `#2c3548` | `#peek{position:fixed;z-index:99;display:none;max-width:340px;background:#141a26;border:1px` |
| 105 | `#cdd3e0` | `#peek{position:fixed;z-index:99;display:none;max-width:340px;background:#141a26;border:1px` |
| 108 | `#aab2c5` | `#peek .pk-body{margin:0;padding:var(--sp-8) var(--sp-8);white-space:pre-wrap;word-break:br` |
| 119 | `#888` | `.fdot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:var(--sp-8)` |
| 120 | `#ffb454` | `.fdot.busy{background:#ffb454}` |
| 122 | `#e05252` | `.fdot.unknown{background:#e05252}` |
| 180 | `#0d1117` | `#queuePanel{display:none;border-top:1px solid var(--line);background:#0d1117;padding:var(-` |
| 182 | `#8b949e` | `#queueHead{font-size:var(--fs-11);color:#8b949e;text-transform:uppercase;letter-spacing:.0` |
| 184 | `#30363d` | `.qspin{width:12px;height:12px;border:2px solid #30363d;border-top-color:#58a6ff;border-rad` |
| 184 | `#58a6ff` | `.qspin{width:12px;height:12px;border:2px solid #30363d;border-top-color:#58a6ff;border-rad` |
| 187 | `#c9d1d9` | `.qtxt{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#c9d1d9}` |
| 189 | `#d29922` | `#intBanner{display:none;margin:var(--sp-8) var(--sp-12);border:1px solid #d29922;backgroun` |
| 189 | `#2d2000` | `#intBanner{display:none;margin:var(--sp-8) var(--sp-12);border:1px solid #d29922;backgroun` |
| 189 | `#e3b341` | `#intBanner{display:none;margin:var(--sp-8) var(--sp-12);border:1px solid #d29922;backgroun` |

## What IS correct
- :root block exists with 1 custom properties defined.
- Many (but not all) selectors use var() references correctly.

## Required fix
Replace each hardcoded hex above with the corresponding --token from :root, or add a new token if one doesn't exist yet. Re-run this check after fixing.

## Method
`re.findall(r'#[0-9a-fA-F](3, 8)\b', content_outside_root)` on ui/app.css.

---
**UPDATE 2026-11-17 (auto-loop pass):** HOT NOTE claims "29 props / 6 categories" but actual :root count is now **47 custom properties** (single :root block, line 8 of ui/app.css). The note is stale - file grew after the note was written. Remaining hex debt still present (see table above).
