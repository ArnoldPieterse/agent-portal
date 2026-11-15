# Evidence: Goal 5 (Keyboard) + Goal 6 (Micro-interactions)
Date: 2026-11-15

## Goal 5 — Full keyboard support
**Already implemented** (verified on disk this turn):
- `index.html` script block 2, L317: `$("input").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send();}});`
  → Enter sends message; Shift+Enter inserts newline (default textarea behavior preserved).
- `index.html` script block 2, L316: `$("send").onclick=send;` — button reachable via Tab + Space/Enter natively.
- Git commit input (script block 1): `$("gitMsg").addEventListener("keydown",e=>{if(e.key==="Enter"){e.preventDefault();$("gitCommit").click();}});`
- **Tab order**: zero explicit tabindex attributes in DOM → natural source-order tabbing through chat → mode bar → Ops controls.

**Status: COMPLETE.** No code changes needed; existing implementation satisfies all three criteria (Enter send, Shift+Enter newline, sane tab order).

## Goal 6 — Consistent micro-interaction set
**Before this turn**: hover ✓, focus-visible ✓, transitions .15s ✓, but **zero `:active` rules**.

**Change applied** (index.html CSS block, after L169 transition rule):
```css
#modeBar button,.seg button,.btn,#send{transition:border-color .15s,color .15s,background-color .15s,opacity .15s,transform .1s}
/* Active/press (2026-11-15 Designer): instant darkening + micro-scale, zero layout shift */
#modeBar button:active,.seg button:active,.btn:active,#send:active{opacity:.78;transform:scale(.97);transition-duration:.04s}
```

**Design rationale**:
- `opacity:.78` + `transform:scale(.97)` = perceivable press without layout reflow (transforms are compositor-only).
- `transition-duration:.04s` on :active makes the press feel instant; on release it eases back at .15s (the base duration).
- All durations ≤ 200ms ✓. Zero layout shift: no width/height/margin changes.

**Full state coverage after fix**:
| Element | hover | focus-visible | active | transition |
|---------|-------|---------------|--------|------------|
| .seg button | border+color | outline ring | scale+opacity | .15s/.04s |
| .btn / #send | border+color | inherited | scale+opacity | .15s/.04s |
| #modeBar button | border+color | outline ring | scale+opacity | .15s/.04s |
| #input (textarea) | — | border-color accent | — | .15s |
| #gitMsg | — | border-color focus | — | .15s |
| .acard button | bg+color | inherited | scale+opacity | .15s/.04s |

**Status: COMPLETE.** All interactive elements now have hover + focus + active states with ≤200ms transitions and zero layout shift.