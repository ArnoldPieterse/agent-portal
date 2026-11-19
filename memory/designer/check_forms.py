# check which escape forms exist in ui js files
c = open('ui/core.js', encoding='utf-8').read()
u = open('ui/uploads.js', encoding='utf-8').read()
checks_c = [
 ('onerror', 'window.onerror=(m,src,l)=>{try{$("stext").textContent="JS ERROR line "+l+": "+String(m).slice(0,80);}catch(_){}};'),
 ('hourglass-esc', '"\\u23f3 working\\u2026 "'),
 ('hourglass-glyph', '\u23f3 working\u2026 '),
 ('warn-fleet-esc', '$("fleetStat").textContent="\\u26a0 "+e'),
 ('warn-fleet-glyph', '$("fleetStat").textContent="\u26a0 "+e'),
 ('check-commit-esc', 'opsSay(r.committed?"\\u2713 committed: "),'),
 ('check-commit-glyph', 'opsSay(r.committed?"\u2713 committed: "),'),
 ('ops-warn-esc', '}catch(e){ opsSay("\\u26a0 "+e); }'),
 ('ops-warn-glyph', '}catch(e){ opsSay("\u26a0 "+e); }'),
]
checks_u = [
 ('files-loading', "list.innerHTML='<li class=\"fs-empty\">loading\u2026</li>'"),
 ('files-empty', 'if(!files.length){list.innerHTML=\'<li class="fs-empty">No uploads yet \u2014 drop files into uploads/ on White.</li>\';return;}'),
 ('goals-hint', '$("goalsBody").innerHTML=html||\'<div class="hint">no goal files</div>\';'),
 ('goals-err-esc', '$("goalsStat").textContent="\\u26a0 "+(o.error||"error")'),
 ('goals-err-glyph', '$("goalsStat").textContent="\u26a0 "+(o.error||"error")'),
 ('stall-esc', 't+=" \\u00b7 \\u26a0 stalled: "+h.stall_commits'),
 ('stall-glyph', 't+=" \u00b7 \u26a0 stalled: "+h.stall_commits'),
 ('blocked-esc', '<span class="gblock">\\u26a0 \'+a.blocked'),
 ('blocked-glyph', '<span class="gblock">\u26a0 \'+a.blocked'),
 ('hexes', 'const st={pass:"var(--ok)",warn:"#d9a514",fail:"#e0524d"};'),
 ('onload', 'xhr.onload=()=>{ if(xhr.status===201||xhr.status===200){ u.state="done"; u.pct=100; }'),
 ('onerror', 'xhr.onerror=()=>{ u.state="error"; u.err="network"; renderChips(); };'),
 ('busy-esc', 'sp.textContent="\\u23f3 working\\u2026 "+secs'),
 ('busy-glyph', 'sp.textContent="\u23f3 working\u2026 "+secs'),
 ('fleetstat-line', '$("goalsStat").textContent=o.fleet_done+"/"+o.fleet_total+" \u00b7 fleet "+(o.fleet_pct||0)+"%";'),
 ('goalsLoad-head', 'async function goalsLoad(){\n  try{'),
]
for n, s in checks_c: print('C', 'Y' if s in c else '-', n)
for n, s in checks_u: print('U', 'Y' if s in u else '-', n)
