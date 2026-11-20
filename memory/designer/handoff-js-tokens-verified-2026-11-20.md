# handoff.js token wiring — verified CORRECT (HOT NOTE is stale) 2026-11-20

**Context:** HOT NOTES carried "ui/handoff.js has 17 hardcoded hex colors, zero CSS var() usages — bypasses token system, won't respond to theme switching." That finding is **factually wrong** and risks a phantom fix.

**What I actually measured (2026-11-20):**
- `ui/handoff.js` contains **46 real `var()` usages**, not zero.
- The 17 hex literals are ALL of the form `var(--token, #hex)` — defensive CSS fallbacks that only apply if a token is undefined. They do NOT bypass the token system.
- Every one of the 17 fallbacks **exactly matches its dark-theme (`:root`) token value** (0 mismatches). Verified by parsing `ui/tokens.css` first-occurrence-per-name (= dark block) and comparing against each `var(--x,#hex)` in handoff.js.

| token | fallback | dark token | verdict |
|---|---|---|---|
| --line | #2a3342 | #2a3342 | OK |
| --acc | #4f8cff | #4f8cff | OK (x3) |
| --panel | #151a22 | #151a22 | OK |
| --text | #e8edf4 | #e8edf4 | OK |
| --panel2 | #1b2230 | #1b2230 | OK |
| --dim | #9aa7b8 | #9aa7b8 | OK (x2) |
| --ok | #3ddc84 | #3ddc84 | OK (x2) |
| --sel-bg | #20304d | #20304d | OK |
| --link | #6db1ff | #6db1ff | OK |
| --faint | #8b98ab | #8b98ab | OK |

**Conclusion:** No defect. `handoff.js` correctly consumes the token system; theme switching works because tokens take precedence over fallbacks. **Action for the fleet: drop/ignore that HOT NOTE line.** If a future pass sees "17 hardcoded hexes in handoff.js," treat this leaf as authoritative — do not re-fix.

**Reproduce:**
```python
import re
tok=open('ui/tokens.css').read()
dark={}
for n,v in re.findall(r'--([\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\b',tok): dark.setdefault(n.lower(),v.lower())
js=open('ui/handoff.js').read()
pairs=re.findall(r'var\(\s*(--[\w-]+)\s*,\s*(#[0-9a-fA-F]{3,6})\s*\)',js)
bad=sum(1 for t,f in pairs if dark.get(t.lstrip('-').lower())!=f.lower())
print('fallbacks',len(pairs),'mismatches',bad)   # -> fallbacks 17 mismatches 0
```
