#!/usr/bin/env python3
# 2026-11-19 White re-land: Designer goals 1-10 full rebuild (idempotent).
# Prints a compact summary only. Run from repo root.
import re, hashlib, shutil, os, sys

def sha12(b):
    return hashlib.sha1(b).hexdigest()[:12]

ok = []

# ---------- 0. density "before" baseline copy (pre-tokenization app.css) ----------
bak = 'ui/app.css.bak-goal1-2026-11-19'
tgt = 'ui/app_density_before.css'
if os.path.exists(bak) and not os.path.exists(tgt):
    shutil.copyfile(bak, tgt)
    ok.append('before-css %dB' % os.path.getsize(tgt))

# ---------- 1. tokens.css: complete the scale ----------
t = open('ui/tokens.css', encoding='utf-8').read()
if '--br-sm' not in t:
    t += """
/* 2026-11-19 (White re-land): spacing/radius/type completion + print colors */
:root{
--sp-1:1px;--sp-3:3px;--sp-6:6px;--sp-10:10px;--sp-14:14px;--sp-20:20px;
--br-sm:4px;--br-md:8px;--br-lg:12px;--br-pill:999px;
--fs-18:18px;--fs-24:24px;
--muted:#8b93a7;--qspin-bd:#30363d;--qspin-top:#58a6ff;--queue-tx:#c9d1d9;
--black:#000;--paper:#fff;--print-dim:#444;--print-line:#ccc;--print-border:#ddd;
}
@media (prefers-color-scheme: light){ :root{ --muted:#64748b;--qspin-bd:#e2e8f0;--qspin-top:#2f6fe0;--queue-tx:#1a2330; } }
"""
    open('ui/tokens.css','w',encoding='utf-8').write(t)
    ok.append('tokens+br/fs/print')

# ---------- 2. app.css ----------
a = open('ui/app.css', encoding='utf-8').read()
changed = False
if '@import "tokens.css";' not in a:
    a = '@import "tokens.css";\n' + a
    changed = True
# remove the inline :root block (tokens now live in tokens.css only)
m = re.search(r'^:root\{[^}]*\}\s*$', a, re.M)
if m and '--bg:' in m.group(0):
    a = a[:m.start()] + '/* tokens: see ui/tokens.css (2026-11-19 re-land removed duplicate :root) */\n' + a[m.end():]
    changed = True
# typography sweep -> 5-step scale {12,14,15,18,24}
def pxmap(v, sel):
    v = float(v)
    if v < 13: return 'var(--fs-12)'
    if v == 13: return 'var(--fs-12)' if 'ft-' in sel else 'var(--fs-14)'
    if v < 16.5: return 'var(--fs-15)'
    if v < 23: return 'var(--fs-18)'
    return 'var(--fs-24)'
def sweep(mobj, selctx):
    return 'font-size:' + pxmap(mobj.group(1), selctx)
n_px = 0
def do_px(mobj):
    global n_px; n_px += 1
    # find enclosing selector: search backwards for last '{' ... approximate with preceding text
    return sweep(mobj, a[max(0,mobj.start()-200):mobj.start()])
a = re.sub(r'font-size:\s*([0-9]+(?:\.[0-9])?)px', do_px, a)
a = a.replace('var(--fs-11)', 'var(--fs-12)').replace('var(--fs-13)', 'var(--fs-14)').replace('var(--fs-16)', 'var(--fs-15)')
changed = True
# append new sections (goal 3/4/5/6/9/10)
if '.empty-state' not in a:
    a += """
/* ============ 2026-11-19 White re-land: goals 3,4,5,6,9,10 ============ */
/* Goal #3 - per-agent goal bar in header */
.goalbar{display:flex;align-items:center;gap:var(--sp-8);margin-left:var(--sp-12);flex-wrap:wrap;}
.gbar{position:relative;display:inline-flex;align-items:center;width:74px;height:16px;background:var(--panel2);border:1px solid var(--line);border-radius:var(--br-pill);overflow:hidden;}
.gbar-fill{position:absolute;left:0;top:0;bottom:0;background:var(--acc);}
.gbar em{position:relative;font-style:normal;font-size:var(--fs-12);line-height:var(--lh-tight);color:var(--text);padding-left:6px;z-index:1;}
.gbar-fleet{font-size:var(--fs-12);color:var(--dim);}
/* Goal #4 - empty states */
.empty-state{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:var(--sp-24) var(--sp-16);gap:var(--sp-8);}
.empty-icon{width:40px;height:40px;border-radius:var(--br-pill);background:var(--panel2);display:flex;align-items:center;justify-content:center;color:var(--dim);}
.empty-icon svg{width:20px;height:20px;}
.empty-title{font-size:var(--fs-14);font-weight:600;color:var(--text);}
.empty-msg{font-size:var(--fs-12);color:var(--dim);max-width:280px;line-height:var(--lh-base);}
.empty-cta{margin-top:var(--sp-4);background:var(--acc);color:var(--white);border:none;border-radius:var(--br-sm);padding:var(--sp-6) var(--sp-12);font-size:var(--fs-12);cursor:pointer;}
.empty-cta:hover{opacity:.85;}
/* Goal #5 - notifications (class names match ui/notifications.js) */
.toast-container{position:fixed;right:var(--sp-16);bottom:var(--sp-16);display:flex;flex-direction:column;gap:var(--sp-4);z-index:1000;max-width:320px;}
.toast{background:var(--panel2);border:1px solid var(--line);border-left:3px solid var(--acc);color:var(--text);padding:var(--sp-8) var(--sp-12);font-size:var(--fs-12);line-height:var(--lh-base);border-radius:var(--br-sm);box-shadow:0 4px 12px rgba(0,0,0,.35);display:flex;align-items:center;gap:var(--sp-8);animation:toast-in .18s ease-out;}
.toast.ok{border-left-color:var(--ok);}
.toast.warn{border-left-color:var(--warn);}
.toast.err{border-left-color:var(--err);}
.toast.leaving{opacity:0;transform:translateX(8px);transition:all .25s ease-in;}
.toast-close{background:none;border:none;color:var(--dim);cursor:pointer;font-size:var(--fs-14);padding:0 2px;line-height:1;}
@keyframes toast-in{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:none;}}
.notif-bell{position:relative;background:none;border:none;color:var(--dim);cursor:pointer;padding:var(--sp-4);display:inline-flex;}
.notif-bell:hover{color:var(--text);}
.notif-bell svg{width:18px;height:18px;}
.notif-badge{position:absolute;top:0;right:0;background:var(--err);color:var(--white);font-size:var(--fs-12);line-height:var(--lh-tight);min-width:16px;height:16px;border-radius:var(--br-pill);display:flex;align-items:center;justify-content:center;padding:0 3px;}
.notif-badge.hidden{display:none;}
.notif-panel{position:fixed;top:48px;right:var(--sp-16);width:300px;max-height:320px;overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:var(--br-md);box-shadow:0 8px 24px rgba(0,0,0,.4);z-index:999;padding:var(--sp-4);}
.notif-panel.hidden{display:none;}
.notif-item{padding:var(--sp-6) var(--sp-8);font-size:var(--fs-12);line-height:var(--lh-base);color:var(--text);border-bottom:1px solid var(--line);}
.notif-item:last-child{border-bottom:none;}
.notif-item.n-ok{border-left:3px solid var(--ok);}
.notif-item.n-warn{border-left:3px solid var(--warn);}
.notif-item.n-err{border-left:3px solid var(--err);}
.notif-empty{color:var(--dim);text-align:center;}
/* Goal #6 - loading skeletons */
.skeleton-wrap{display:flex;flex-direction:column;gap:var(--sp-8);padding:var(--sp-8);}
.skeleton{background:linear-gradient(90deg,var(--panel2) 25%,var(--line) 50%,var(--panel2) 75%);background-size:200% 100%;animation:skeleton-shimmer 1.2s ease-in-out infinite;border-radius:var(--br-sm);}
@keyframes skeleton-shimmer{0%{background-position:200% 0;}100%{background-position:-200% 0;}}
.skel-li{list-style:none;width:100%;}
/* Goal #9 - first-run tour */
.tour-overlay{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:1100;}
.tour-card{position:absolute;z-index:1101;width:300px;background:var(--panel);border:1px solid var(--line);border-radius:var(--br-md);box-shadow:0 8px 24px rgba(0,0,0,.5);padding:var(--sp-16);}
.tour-step{font-size:var(--fs-12);color:var(--dim);}
.tour-title{font-size:var(--fs-15);font-weight:600;margin:var(--sp-4) 0;}
.tour-body{font-size:var(--fs-14);line-height:var(--lh-base);color:var(--text);margin:0 0 var(--sp-12);}
.tour-dots{display:flex;gap:var(--sp-4);margin-bottom:var(--sp-12);}
.tour-dot{width:8px;height:8px;border-radius:var(--br-pill);background:var(--line);}
.tour-dot.on{background:var(--acc);}
.tour-btns{display:flex;justify-content:space-between;align-items:center;}
.tour-skip{background:none;border:none;color:var(--dim);font-size:var(--fs-12);cursor:pointer;}
.tour-next{background:var(--acc);color:var(--white);border:none;border-radius:var(--br-sm);padding:var(--sp-6) var(--sp-12);font-size:var(--fs-12);cursor:pointer;}
/* Goal #10 - print report */
#printReportBtn{background:none;border:1px solid var(--line);color:var(--dim);border-radius:var(--br-sm);padding:var(--sp-3) var(--sp-6);font-size:var(--fs-12);cursor:pointer;display:inline-flex;align-items:center;gap:4px;}
#printReportBtn:hover{color:var(--text);border-color:var(--dim);}
#printReportBtn svg{width:14px;height:14px;}
@media print{
  *{background:transparent !important;color:var(--black) !important;box-shadow:none !important;}
  body{height:auto !important;display:block !important;margin:0 !important;font-size:12px;line-height:1.4;}
  header .composer,#chips,.toast-container,.notif-bell,.notif-panel,.tour-overlay,.tour-card,#peek,#sendQueuePanel,#busyHint{display:none !important;}
  .panel-toggle,.btn,#printReportBtn,.toggles button{display:none !important;}
  main{display:block !important;height:auto !important;}
  .panel,[id$="Panel"]{position:static !important;height:auto !important;max-height:none !important;overflow:visible !important;border:none !important;margin:0 0 var(--sp-12) !important;padding:var(--sp-8) !important;}
  #chatCol,#composerWrap{display:none !important;}
  .gbar-fill{background:var(--print-dim) !important;}
  a[href]:after{content:" (" attr(href) ")";font-size:12px;color:var(--print-dim);}
}
@media (prefers-reduced-motion: reduce){
  .toast{animation:none;}
  .skeleton{animation:none;background:var(--panel2);}
  .toast.leaving{transition:none;}
}
"""
    changed = True
if changed:
    open('ui/app.css','w',encoding='utf-8').write(a)
    ok.append('app.css px:%d size:%d' % (n_px, len(a)))

# ---------- 3. core.js ----------
c = open('ui/core.js', encoding='utf-8').read()
c0 = c
c = c.replace(
 'window.onerror=(m,src,l)=>{try{$("stext").textContent="JS ERROR line "+l+": "+String(m).slice(0,80);}catch(_){}};',
 'window.onerror=(m,src,l)=>{try{$("stext").textContent="JS ERROR line "+l+": "+String(m).slice(0,80); if(typeof window.notify==="function")window.notify("err","JS error: "+String(m).slice(0,120));}catch(_){}};')
c = c.replace('"\\u23f3 working\\u2026 "', '"working\\u2026 "')
c = c.replace('\'\\u23f3 working\\u2026 \'', '\'working\\u2026 \'' )
# fleet empty state + offline diff (goal 4/5)
old_fleet = '''    $("fleetBody").innerHTML=html||'<div class="hint">no hosts</div>';
    const up=(o.hosts||[]).filter(h=>h.state!=="unknown").length;'''
new_fleet = '''    const _fp=window._fleetPrev||{}; const _fs={};
    for(const h of (o.hosts||[])){ _fs[h.host]=h.state!=="unknown";
      if(_fp[h.host]===true && h.state==="unknown" && typeof window.notify==="function") window.notify("warn","Agent host "+h.host+" is offline"); }
    window._fleetPrev=_fs;
    $("fleetBody").innerHTML=html||UI.emptyState({icon:"agent",title:"No hosts reporting",msg:"The fleet probe hasn't seen any hosts yet.",ctaLabel:"Refresh now"});
    { const _ct=$("fleetBody").querySelector(".empty-cta"); if(_ct)_ct.onclick=fleetUpdate; }
    const up=(o.hosts||[]).filter(h=>h.state!=="unknown").length;'''
if old_fleet in c: c = c.replace(old_fleet, new_fleet); ok.append('core fleet empty+diff')
c = c.replace('}catch(e){ $("fleetStat").textContent="\u26a0 "+e; }', '}catch(e){ $("fleetStat").textContent="error: "+e; }')
c = c.replace('opsSay(r.committed?"\u2713 committed: "+m:(r.note||r.err||"done"))', 'opsSay(r.committed?"committed: "+m:(r.note||r.err||"done"))')
c = c.replace('}catch(e){ opsSay("\u26a0 "+e); } finally{ opsLoad(); }', '}catch(e){ opsSay("error: "+e); } finally{ opsLoad(); }')
c = c.replace('}catch(e){ opsSay("\u26a0 "+e); }', '}catch(e){ opsSay("error: "+e); }')
# append UI namespace + helpers + selftest
if 'window.UI' not in c:
    c += """
// ---- Goal #4/6 helpers (2026-11-19 White re-land) ----
window.UI=window.UI||{};
UI.emptyState=function(o){ o=o||{}; let ic=''; try{ ic=(window.UI&&UI.icon)?UI.icon(o.icon||"info"):''; }catch(_){}
  return '<div class="empty-state"><div class="empty-icon">'+ic+'</div>'
    +'<div class="empty-title">'+esc(o.title||"")+'</div>'
    +(o.msg?'<div class="empty-msg">'+esc(o.msg)+'</div>':'')
    +(o.ctaLabel?'<button type="button" class="empty-cta">'+esc(o.ctaLabel)+'</button>':'')+'</div>'; };
UI.skeleton=function(n,h){ n=n||3; h=h||14; let s=''; for(let i=0;i<n;i++)s+='<div class="skeleton" style="height:'+h+'px"></div>'; return '<div class="skeleton-wrap">'+s+'</div>'; };
// ---- Goal #3 - header goal bar (rendered from /api/goals by uploads.js) ----
function renderGoalBar(o){ const el=$("goalBar"); if(!el||!o||!o.ok)return; let h='';
  for(const a of (o.agents||[])){ const pct=a.total?Math.round(100*a.done/a.total):0;
    h+='<span class="gbar" title="'+a.agent+': '+a.done+'/'+a.total+' done"><i class="gbar-fill" style="width:'+pct+'%"></i><em>'+esc(String(a.agent).slice(0,3).toUpperCase())+'</em></span>'; }
  h+='<span class="gbar-fleet">'+o.fleet_done+'/'+o.fleet_total+' \u00b7 '+(o.fleet_pct||0)+'%</span>';
  el.innerHTML=h; }
// ---- Goal #10 - print report button (injected into header) ----
(function(){ const b=document.createElement("button"); b.id="printReportBtn"; b.type="button"; b.title="Print a clean report of the current panels";
  let ic=''; try{ ic=(window.UI&&UI.icon)?UI.iconSized('save',14):''; }catch(_){}
  b.innerHTML=ic+' Print';
  b.onclick=function(){ window.print(); };
  const st=$("status"); if(st)st.parentNode.insertBefore(b,st); else { const hd=document.querySelector("header"); if(hd)hd.appendChild(b); } })();
// ---- Goal #6 - initial skeletons (replaced on first real load) ----
if($("fleetBody"))$("fleetBody").innerHTML=UI.skeleton(4,18);
if($("goalsBody"))$("goalsBody").innerHTML=UI.skeleton(3,52);
if($("filesList"))$("filesList").innerHTML='<li class="skel-li">'+UI.skeleton(6,12)+'</li>';
"""
    ok.append('core UI/helpers')
# selftest harness
if '__selftest' not in c:
    c += """
// ---- #selftest acceptance harness (2026-11-19 White re-land; evidence for goals 2,4,5,6,7,8,9) ----
window.__selftest=async function(){ const out={};
  const wait=(ms)=>new Promise(r=>setTimeout(r,ms));
  for(let i=0;i<40 && !(agents.length);i++) await wait(250);
  const ids=["fleetBody","goalsBody","filesList"];
  const measure=()=>{ const r={body:document.body.scrollHeight}; for(const id of ids){ const el=$(id); if(el)r[id]=el.scrollHeight; } return r; };
  const scale=["12px","14px","15px","18px","24px"];
  let viol=[]; const all=document.querySelectorAll("body *");
  for(const el of all){ const cs=getComputedStyle(el); if(cs.display==="none")continue; if(!scale.includes(cs.fontSize))viol.push((el.id?"#"+el.id:(typeof el.className==="string"&&el.className.trim()?"."+el.className.trim().split(/\\s+/)[0]:el.tagName))+"="+cs.fontSize); }
  out.typography={elements_checked:all.length,violation_count:viol.length,violations:viol.slice(0,25)};
  const after=measure();
  const link=document.querySelector('link[rel="stylesheet"]');
  const orig=link.href; link.href="/ui/app_density_before.css"; await wait(400);
  const before=measure(); link.href=orig; await wait(400); measure();
  out.density={before:before,after:after,
    panels:Object.keys(after).filter(k=>k!=="body"&&before[k]).map(k=>({panel:k,before:before[k],after:after[k],reduction_pct:+(100*(before[k]-after[k])/before[k]).toFixed(1)})),
    body_reduction_pct:+(100*(before.body-after.body)/before.body).toFixed(1)};
  let clipped=0; for(const el of document.querySelectorAll("body *")){ const cs=getComputedStyle(el); if((cs.overflow==="hidden"||cs.overflowY==="auto"||cs.overflowY==="scroll")&&el.scrollHeight>el.clientHeight+2)clipped++; }
  out.clipping={clipped_elements:clipped};
  const es=UI.emptyState({icon:"goal",title:"No goals set",msg:"m",ctaLabel:"Open TODO.md"});
  out.empty_state={has_svg_icon:es.includes("<svg"),has_cta_button:es.includes('class="empty-cta"')};
  if(typeof window.notify==="function"){ window.notify("ok","selftest ok"); window.notify("warn","selftest warn"); window.notify("err","selftest err"); await wait(150); }
  out.notifications={toasts:document.querySelectorAll(".toast").length,badge:(document.getElementById("notifBadge")||{}).textContent||null,panel_items:document.querySelectorAll(".notif-item").length};
  if(window.UI&&UI.tour){ UI.tour.start(); let steps=0; for(let i=0;i<6;i++){ if(!document.querySelector(".tour-card"))break; steps++; const n=document.querySelector(".tour-next"); if(n)n.click(); await wait(60);} out.tour={steps_seen:steps,ended_cleanly:!document.querySelector(".tour-overlay")}; }
  return out; };
window.__visual=function(mode){ // for headless screenshot variants
  const wait=(ms)=>new Promise(r=>setTimeout(r,ms));
  (async()=>{ for(let i=0;i<40 && !(agents.length);i++) await wait(250);
    if(mode==="empty"){
      $("fleetBody").innerHTML=UI.emptyState({icon:"agent",title:"No hosts reporting",msg:"The fleet probe hasn't seen any hosts yet.",ctaLabel:"Refresh now"});
      $("goalsBody").innerHTML=UI.emptyState({icon:"goal",title:"No goals set",msg:"Goal files live in memory/goals/ on each host.",ctaLabel:"Open TODO.md"});
      const fl=$("filesList"); if(fl){fl.innerHTML=""; const li=document.createElement("li"); li.innerHTML=UI.emptyState({icon:"upload",title:"No uploads yet",msg:"Drop files into the composer or uploads/ on White.",ctaLabel:"+ Upload"}); fl.appendChild(li);} }
    else if(mode==="notify"){
      window.notify&&window.notify("ok","Goal closed on Scribe (5/6)");
      window.notify&&window.notify("warn","Agent host pale is offline");
      window.notify&&window.notify("err","Upload failed: report.pdf"); await wait(120);
      const p=document.getElementById("notifPanel"); if(p)p.classList.remove("hidden"); }
    else if(mode==="tour"){ if(window.UI&&UI.tour){ UI.tour.start(); const n=document.querySelector(".tour-next"); if(n)n.click(); } }
  })(); };
if(location.hash==="#selftest"){ window.addEventListener("load",async()=>{ try{ const r=await window.__selftest(); const p=document.createElement("pre"); p.id="selftestOut"; p.textContent="SELFTEST_JSON "+JSON.stringify(r); document.body.appendChild(p); }catch(e){ const p=document.createElement("pre"); p.id="selftestOut"; p.textContent="SELFTEST_ERR "+e; document.body.appendChild(p);} }); }
else if(location.hash==="#visual"){ window.addEventListener("load",()=>window.__visual((location.search.match(/m=(\\w+)/)||[])[1]||"empty")); }
"""
    ok.append('core selftest')
if c != c0:
    open('ui/core.js','w',encoding='utf-8').write(c)

# ---------- 4. uploads.js ----------
u = open('ui/uploads.js', encoding='utf-8').read()
u0 = u
u = u.replace('list.innerHTML=\'<li class="fs-empty">loading\u2026</li>\';',
              'list.innerHTML=(typeof UI!=="undefined")?\'<li class="skel-li">'+UI.skeleton(6,12)+'</li>\':\'<li class="fs-empty">loading\u2026</li>\';')
u = u.replace('if(!files.length){list.innerHTML=\'<li class="fs-empty">No uploads yet \u2014 drop files into uploads/ on White.</li>\';return;}',
  'if(!files.length){ list.innerHTML=""; const _li=document.createElement("li"); _li.innerHTML=(typeof UI!=="undefined")?UI.emptyState({icon:"upload",title:"No uploads yet",msg:"Drop files into the composer or uploads/ on White.",ctaLabel:"+ Upload"}):\'<span class="fs-empty">No uploads yet</span>\'; list.appendChild(_li); const _ct=_li.querySelector(".empty-cta"); if(_ct)_ct.onclick=function(){ const inp=document.querySelector(\'input[type="file"]\'); if(inp)inp.click(); else { const cm=$("composer"); if(cm)cm.focus(); } }; return; }')
u = u.replace('async function goalsLoad(){\n  try{',
  'async function goalsLoad(){\n  { const _gb=$("goalsBody"); if(_gb&&(typeof UI!=="undefined")&&!_gb.dataset.loaded)_gb.innerHTML=UI.skeleton(3,52); }\n  try{')
u = u.replace('$("goalsBody").innerHTML=html||\'<div class="hint">no goal files</div>\';',
  'const _pg=window._goalsPrev||{}; for(const a of (o.agents||[])){ if(_pg[a.agent]!=null && a.done>_pg[a.agent] && typeof window.notify==="function") window.notify("ok","Goal closed on "+a.agent+" ("+a.done+"/"+a.total+")"); }\n    window._goalsPrev=Object.fromEntries((o.agents||[]).map(a=>[a.agent,a.done]));\n    $("goalsBody").dataset.loaded="1";\n    $("goalsBody").innerHTML=html||((typeof UI!=="undefined")?UI.emptyState({icon:"goal",title:"No goals set",msg:"Goal files live in memory/goals/ on each host.",ctaLabel:"Open TODO.md"}):\'<div class="hint">no goal files</div>\');\n    { const _ct=$("goalsBody").querySelector(".empty-cta"); if(_ct)_ct.onclick=function(){ const cm=$("composer"); if(cm)cm.focus(); }; }')
u = u.replace('if(!o.ok){ $("goalsStat").textContent="\u26a0 "+(o.error||"error"); return; }',
              'if(!o.ok){ $("goalsStat").textContent="error: "+(o.error||"error"); return; }')
u = u.replace('+(a.blocked?\' \u00b7 <span class="gblock">\u26a0 \' + a.blocked + \' blocked</span>\':\'\')',
              '+(a.blocked?\' \u00b7 <span class="gblock">\'+a.blocked+\' blocked</span>\':\'\')')
u = u.replace('if((h.stall_commits||0)>3) t+=" \\u00b7 \\u26a0 stalled: "+h.stall_commits+" commits since last goal change";',
              'if((h.stall_commits||0)>3) t+=" \\u00b7 STALLED: "+h.stall_commits+" commits since last goal change";')
u = u.replace('const st={pass:"var(--ok)",warn:"#d9a514",fail:"#e0524d"};',
              'const st={pass:"var(--ok)",warn:"var(--warn)",fail:"var(--err)"};')
u = u.replace('xhr.onload=()=>{ if(xhr.status===201||xhr.status===200){ u.state="done"; u.pct=100; }',
              'xhr.onload=()=>{ if(xhr.status===201||xhr.status===200){ u.state="done"; u.pct=100; if(typeof window.notify==="function")window.notify("ok","Upload complete: "+u.rel); }')
u = u.replace('xhr.onerror=()=>{ u.state="error"; u.err="network"; renderChips(); };',
              'xhr.onerror=()=>{ u.state="error"; u.err="network"; if(typeof window.notify==="function")window.notify("err","Upload failed: "+u.rel); renderChips(); };')
u = u.replace('busyT=setInterval(()=>{secs++;if(sp.isConnected)sp.textContent="\\u23f3 working\\u2026 "+secs+"s";},1000);',
              'busyT=setInterval(()=>{secs++;if(sp.isConnected)sp.textContent="working\\u2026 "+secs+"s";},1000);')
# call renderGoalBar from goalsLoad (goal 3)
u = u.replace('$("goalsStat").textContent=o.fleet_done+"/"+o.fleet_total+" \u00b7 fleet "+(o.fleet_pct||0)+"%";',
              '$("goalsStat").textContent=o.fleet_done+"/"+o.fleet_total+" \u00b7 fleet "+(o.fleet_pct||0)+"%";\n    if(typeof renderGoalBar==="function")renderGoalBar(o);')
if u != u0:
    open('ui/uploads.js','w',encoding='utf-8').write(u)
    ok.append('uploads edited')

# ---------- 5. notifications.js + tour.js (new) ----------
notif = '''/* ui/notifications.js - toast + bell notification system (Goal #5, re-landed on White 2026-11-19) */
(function(){ "use strict";
  if(window.__notifLoaded)return; window.__notifLoaded=true;
  const MAX=4, TTL=5000;
  let unread=0, items=[];
  function el(tag,cls,txt){ const e=document.createElement(tag); if(cls)e.className=cls; if(txt!=null)e.textContent=txt; return e; }
  function ensureContainer(){ let c=document.getElementById("toastContainer"); if(!c){ c=el("div","toast-container"); c.id="toastContainer"; document.body.appendChild(c);} return c; }
  function ensureBell(){ let b=document.getElementById("notifBell"); if(b)return b;
    const hdr=document.querySelector("header"); if(!hdr)return null;
    b=el("button","notif-bell"); b.id="notifBell"; b.type="button"; b.title="Notifications"; b.setAttribute("aria-label","Notifications");
    let ic=''; try{ ic=(window.UI&&UI.icon)?UI.icon('settings'):''; }catch(_){}
    b.innerHTML=ic+'<span class="notif-badge hidden" id="notifBadge">0</span>';
    const panel=el("div","notif-panel hidden"); panel.id="notifPanel";
    hdr.appendChild(b); document.body.appendChild(panel);
    b.onclick=function(e){ e.stopPropagation(); panel.classList.toggle("hidden"); if(!panel.classList.contains("hidden")){ unread=0; renderBadge(); } };
    document.addEventListener("click",function(e){ if(!b.contains(e.target)&&!panel.contains(e.target))panel.classList.add("hidden"); });
    return b; }
  function renderBadge(){ const bd=document.getElementById("notifBadge"); if(!bd)return; bd.textContent=unread>9?"9+":String(unread); bd.classList.toggle("hidden",unread===0); }
  function renderPanel(){ const p=document.getElementById("notifPanel"); if(!p)return; p.innerHTML="";
    if(!items.length){ p.appendChild(el("div","notif-item notif-empty","No notifications yet")); return; }
    for(const it of items.slice(-8).reverse()) p.appendChild(el("div","notif-item n-"+it.kind,it.msg)); }
  function dismiss(t){ if(!t.parentNode)return; t.classList.add("leaving"); setTimeout(function(){ t.remove(); },250); }
  window.notify=function(kind,msg){ kind=["ok","warn","err"].indexOf(kind)>=0?kind:"info";
    const c=ensureContainer();
    while(c.children.length>=MAX)c.firstChild.remove();
    const t=el("div","toast "+kind); t.appendChild(document.createTextNode(msg));
    const x=el("button","toast-close"); x.type="button"; x.textContent="\u00d7"; x.onclick=function(){ dismiss(t); };
    t.appendChild(x); c.appendChild(t);
    const bell=ensureBell(); if(bell){ items.push({kind:kind,msg:msg}); if(items.length>50)items=items.slice(-50); unread++; renderBadge(); renderPanel(); }
    setTimeout(function(){ dismiss(t); },TTL); };
})();
'''
if not os.path.exists('ui/notifications.js'):
    open('ui/notifications.js','w',encoding='utf-8').write(notif); ok.append('notifications.js %dB' % len(notif))
tour = '''/* ui/tour.js - first-run 4-step tour (Goal #9, re-landed on White 2026-11-19) */
(function(){ "use strict";
  if(window.__tourLoaded)return; window.__tourLoaded=true;
  const STEPS=[
    {sel:"#goalsBtn", title:"Goal Velocity", body:"Per-agent done/total rings from memory/goals/, plus fleet totals and a git-based progress curve with stall warnings."},
    {sel:"#fleetBtn", title:"Fleet Status", body:"Every host's loaded models, busy/idle state and last-seen age. Live while the panel is open; offline hosts raise a notification."},
    {sel:"#filesBtn", title:"Files & Uploads", body:"Humans' drop zone: attach files to prompts or list what already landed in uploads/. Empty states tell you exactly where to start."},
    {sel:"#composer", title:"Prompt Composer", body:"Send prompts solo or to the whole group. Messages sent while agents are busy queue up and deliver automatically when idle.", last:true}
  ];
  let step=0, overlay=null, card=null;
  function place(){ const t=document.querySelector(STEPS[step].sel); if(!t)return;
    const r=t.getBoundingClientRect(); const cr=card.getBoundingClientRect();
    let top=r.bottom+8, left=Math.max(8,Math.min(window.innerWidth-cr.width-8,r.left));
    if(top+cr.height>window.innerHeight-8)top=Math.max(8,r.top-cr.height-8);
    card.style.top=top+"px"; card.style.left=left+"px"; }
  function render(){ const s=STEPS[step];
    card.querySelector(".tour-step").textContent="Step "+(step+1)+" of "+STEPS.length;
    card.querySelector(".tour-title").textContent=s.title;
    card.querySelector(".tour-body").textContent=s.body;
    const dots=card.querySelectorAll(".tour-dot"); dots.forEach((d,i)=>d.classList.toggle("on",i<=step));
    card.querySelector(".tour-next").textContent=s.last?"Done":"Next";
    place(); }
  window.UI=window.UI||{};
  UI.tour={ start:start, close:close };
  function start(){ if(overlay)return; step=0;
    overlay=document.createElement("div"); overlay.className="tour-overlay";
    card=document.createElement("div"); card.className="tour-card";
    let dots=''; for(let i=0;i<STEPS.length;i++)dots+='<span class="tour-dot"></span>';
    card.innerHTML='<div class="tour-step"></div><div class="tour-title"></div><p class="tour-body"></p><div class="tour-dots">'+dots+'</div><div class="tour-btns"><button type="button" class="tour-skip">Skip tour</button><button type="button" class="tour-next">Next</button></div>';
    card.querySelector(".tour-skip").onclick=close;
    card.querySelector(".tour-next").onclick=function(){ if(step<STEPS.length-1){step++;render();}else close(); };
    overlay.appendChild(card); document.body.appendChild(overlay);
    render(); }
  function close(){ if(overlay){overlay.remove();overlay=null;card=null;} try{localStorage.setItem("portalTourDone","1");}catch(_){} }
  window.addEventListener("load",function(){ let done=false; try{done=localStorage.getItem("portalTourDone")==="1";}catch(_){} if(!done)setTimeout(start,800); });
})();
'''
if not os.path.exists('ui/tour.js'):
    open('ui/tour.js','w',encoding='utf-8').write(tour); ok.append('tour.js %dB' % len(tour))

# ---------- 6. index.html ----------
h = open('index.html', encoding='utf-8').read()
h0 = h
icons = open('ui/icons.js', encoding='utf-8').read()
def iconsvg(name, size=None):
    m = re.search(r"\b%s:\s*'(<svg[^']*)'" % name, icons)
    if not m: return ''
    s = m.group(1)
    if size: s = re.sub(r'width="[0-9]+"', 'width="%d"' % size, s); s = re.sub(r'height="[0-9]+"', 'height="%d"' % size, s)
    return s
# script order: notifications + icons before core; tour after uploads
if 'ui/notifications.js' not in h:
    m = re.search(r'<script src="ui/core\.js"></script>', h)
    if m:
        ins = '<script src="ui/notifications.js"></script>\n<script src="ui/icons.js"></script>\n'
        h = h[:m.start()] + ins + h[m.start():]
if 'ui/tour.js' not in h:
    m = re.search(r'<script src="ui/uploads\.js"></script>', h)
    if m:
        h = h[:m.end()] + '\n<script src="ui/tour.js"></script>' + h[m.end():]
# goal bar in header
if 'id="goalBar"' not in h:
    m = re.search(r'<span class="toggles">', h)
    if m: h = h[:m.start()] + '<div id="goalBar" class="goalbar" aria-label="Goal progress"></div>\n' + h[m.start():]
# emoji -> inline SVG / ASCII
h = re.sub(r'<h1>[^<]*Agent Portal</h1>', '<h1>' + iconsvg('robot') + ' Agent Portal</h1>', h)
h = h.replace('>\uff0b Add</button>', '>+ Add</button>')
for name, btn in [('satellite','fleetBtn'), ('folder','filesBtn'), ('save','gitCommit'), ('close','edClose')]:
    svg = iconsvg(name, 14)
    if not svg: continue
    m = re.search(r'<button[^>]*id="%s"[^>]*>([^<]*<)', btn, h) or None
# simpler targeted replaces:
h = re.sub(r'(id="fleetBtn"[^>]*>)[^<]+', lambda m: m.group(1)+iconsvg('satellite',14)+' Fleet', h)
h = re.sub(r'(id="filesBtn"[^>]*>)[^<]+', lambda m: m.group(1)+iconsvg('folder',14)+' Files', h)
h = re.sub(r'<button class="btn" id="gitCommit">[^<]*</button>', '<button class="btn" id="gitCommit">'+iconsvg('save',14)+' Commit all</button>', h)
h = re.sub(r'<button id="edClose" title="Close">[^<]*</button>', '<button id="edClose" title="Close">'+iconsvg('close',14)+'</button>', h)
# favicon without emoji
h = re.sub(r'href="data:image/svg\+xml,[^"]*"', "href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='42' r='26' fill='%234f8cff'/%3E%3Crect x='28' y='72' width='44' height='16' rx='8' fill='%234f8cff'/%3E%3C/svg%3E\"", h)
# title-attr arrow glyph
h = h.replace('lists on open, \u21bb to re-list', 'lists on open, use Refresh to re-list')
if h != h0:
    open('index.html','w',encoding='utf-8').write(h)
    ok.append('index.html updated')

# ---------- 7. summary ----------
def bal(s):
    return s.count('{'), s.count('}'), s.count('('), s.count(')')
a=open('ui/app.css').read(); c=open('ui/core.js').read(); u=open('ui/uploads.js').read()
hexcss=len(re.findall(r'#[0-9a-fA-F]{3,8}\b', a))
emoji=re.findall(r'[\U0001F000-\U0001FAFF\u2600-\u27BF]', open('index.html').read()+c+u)
print('OK:', '; '.join(ok))
print('app.css braces', bal(a)[:2], 'core.js', bal(c), 'uploads.js', bal(u))
print('app.css hex outside tokens:', hexcss, '| emoji-ish hits idx+core+up:', len(emoji), emoji[:10])
