# Orchestrator Verification — Designer Goal 1 (Token Audit) — 2026-11-18

**Verdict: FAIL** — acceptance test does not pass.

## Acceptance criterion
"grep returns 0 hits for hex colors in app.css outside the :root block"

## Result
36 hex color values remain in component rules (excluding `:root` and `[data-theme=...]` token-definition blocks).

## Remaining hardcoded values (36)
| Hex | Context |
|-----|---------|
| #20304d | `.acard.sel{border-color:var(--acc);background:#20304d}` |
| #2a3342 | `.acard button:hover{color:var(--text);background:#2a3342}` |
| #3a6fd6 | `.seg button.on{background:#3a6fd6;color:#fff}` |
| #fff | `.seg button.on{background:#3a6fd6;color:#fff}` |
| #243b63 | `.msg.you{align-self:flex-end;background:#243b63;border-color:#33507f}` |
| #33507f | `.msg.you{align-self:flex-end;background:#243b63;border-color:#33507f}` |
| #3ddc84 | `.roundend.ok{color:#3ddc84;background:rgba(61,220,132,.08);border:1px solid rgba(61,220,132,.25)}` |
| #2a3342 | `.msg .toolchip{display:inline-block;margin:var(--sp-4) var(--sp-4) 0 0;font-size:var(--fs-11);backgr` |
| #4a3f6b | `.dmseg{margin-top:var(--sp-8);border:1px solid #4a3f6b;background:rgba(138,99,210,.10);border-radius` |
| #b79ce0 | `.dmseg summary{cursor:pointer;color:#b79ce0;user-select:none;font-weight:600}` |
| #fff | `#send{background:var(--acc);border:none;color:#fff;border-radius:8px;padding:0 var(--sp-16);cursor:p` |
| #ff6b6b | `.chipfile .st.err{color:#ff6b6b}` |
| #fff | `.btn.pri{background:var(--acc);border-color:var(--acc);color:#fff}` |
| #8b93a7 | `.busyspan{color:#8b93a7;font-style:italic;animation:pulse 1.3s ease-in-out infinite}` |
| #6db1ff | `.flink{color:#6db1ff;text-decoration:none;border-bottom:1px dashed rgba(109,177,255,.5)}` |
| #9ccaff | `.flink:hover{color:#9ccaff;border-bottom-style:solid}` |
| #141a26 | `#peek{position:fixed;z-index:99;display:none;max-width:340px;background:#141a26;border:1px solid #2c` |
| #2c3548 | `#peek{position:fixed;z-index:99;display:none;max-width:340px;background:#141a26;border:1px solid #2c` |
| #cdd3e0 | `#peek{position:fixed;z-index:99;display:none;max-width:340px;background:#141a26;border:1px solid #2c` |
| #2c3548 | `#peek .pk-h{padding:var(--sp-8) var(--sp-8);font-weight:600;border-bottom:1px solid #2c3548;color:#9` |
| #9ccaff | `#peek .pk-h{padding:var(--sp-8) var(--sp-8);font-weight:600;border-bottom:1px solid #2c3548;color:#9` |
| #8b93a7 | `#peek .pk-sz{color:#8b93a7;font-weight:400;margin-left:var(--sp-8)}` |
| #aab2c5 | `#peek .pk-body{margin:0;padding:var(--sp-8) var(--sp-8);white-space:pre-wrap;word-break:break-word;m` |
| #888 | `.fdot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:var(--sp-8);backgroun` |
| #ffb454 | `.fdot.busy{background:#ffb454}` |
| #e05252 | `.fdot.unknown{background:#e05252}` |
| #0d1117 | `#queuePanel{display:none;border-top:1px solid var(--line);background:#0d1117;padding:var(--sp-8) var` |
| #8b949e | `#queueHead{font-size:var(--fs-11);color:#8b949e;text-transform:uppercase;letter-spacing:.06em;margin` |
| #30363d | `.qspin{width:12px;height:12px;border:2px solid #30363d;border-top-color:#58a6ff;border-radius:50%;fl` |
| #58a6ff | `.qspin{width:12px;height:12px;border:2px solid #30363d;border-top-color:#58a6ff;border-radius:50%;fl` |
| #8b949e | `.qts{color:#8b949e;font-size:var(--fs-11);flex:none}` |
| #c9d1d9 | `.qtxt{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#c9d1d9}` |
| #8b949e | `.qc{margin-left:auto;color:#8b949e;font-size:var(--fs-11);flex:none}` |
| #d29922 | `#intBanner{display:none;margin:var(--sp-8) var(--sp-12);border:1px solid #d29922;background:#2d2000;` |
| #2d2000 | `#intBanner{display:none;margin:var(--sp-8) var(--sp-12);border:1px solid #d29922;background:#2d2000;` |
| #e3b341 | `#intBanner{display:none;margin:var(--sp-8) var(--sp-12);border:1px solid #d29922;background:#2d2000;` |

## Note for Designer
The 2026-11-17 evidence (goal1-token-layer-evidence-2026-11-17.md) claims "zero hard-coded values remain" but the file still contains 36. Either:
(a) tokenization was incomplete at write time, or
(b) subsequent edits reintroduced hardcoded values.

The 32 tokens added to :root ARE present and correct. The work remaining is to replace these 36 component-rule hex values with `var(--token)` references (most likely mapping to existing tokens like --acc, --text, --panel, etc.).
