#!/usr/bin/env python3
"""A6+B transform r44 FIXED (Verifier) - reproduces Builder r42 intent on 45323d09 base.
Builder's memory/builder/apply_a6_b_r42.py fails: its confirm-delete/confirm-reset anchors are
single-line but the base has multi-line handlers (L328-330, L922-925). This variant uses exact
multi-line anchors; all CSS/JS/replacement payloads are Builder's verbatim.
Base: memory/builder/index_html_a4a5_candidate_45323d09.html (md5 45323d09717ac3a9dc0e098015863d81)
"""
import hashlib, os, re

BASE = "memory/builder/index_html_a4a5_candidate_45323d09.html"
BASE_MD5 = "45323d09717ac3a9dc0e098015863d81"

def md5(p): return hashlib.md5(open(p, "rb").read()).hexdigest()
assert os.path.exists(BASE), "base candidate missing"
assert md5(BASE) == BASE_MD5, "base md5 drift - aborting"
src = open(BASE, encoding="utf-8").read()
orig_len = len(src)

def sub1(old, new, tag):
    global src
    n = src.count(old)
    assert n == 1, f"{tag}: expected exactly 1 occurrence, found {n}"
    src = src.replace(old, new)

CSS_ADD = '''/* A6+B (r42): toast system + responsive 360px layout */
#toasts{position:fixed;right:14px;bottom:14px;z-index:100;display:flex;flex-direction:column;gap:8px}
.toast{background:#2a3342;border:1px solid var(--line);border-left:3px solid var(--acc);color:var(--text);font-size:12.5px;line-height:1.35;padding:9px 13px;border-radius:9px;max-width:320px;box-shadow:0 6px 18px rgba(0,0,0,.4);animation:toastin .18s ease-out}
.toast.err{border-left-color:#d05a5a}
@keyframes toastin{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}
@media (max-width:720px){
 header{padding:8px 10px;gap:8px}
 header .hint{display:none}
 #status{font-size:11px}
 aside{width:148px}
 #msgs{padding:12px}
 #composer{padding:10px}
 #modeBar{flex-wrap:wrap;padding:8px 10px}
 .frow{flex-wrap:wrap}
 .frow>div{min-width:calc(50% - 6px)}
 .dhead,.dbody,.dfoot{padding-left:12px;padding-right:12px}
 #peek{max-width:calc(100vw - 24px)}
 .msg{max-width:88%}
 .thinkwrap{max-width:80%}
 #actSel{max-width:100%}
}
@media (max-width:480px){
 body{font-size:13.5px}
 h1{font-size:15px}
 aside{width:120px}
 .acard{padding:6px}
 #composer{gap:6px;padding:8px}
 .frow>div{min-width:100%}
 .toast{max-width:calc(100vw - 24px)}
}
'''

JS_TOAST = 'function toast(msg,kind){let t=document.getElementById("toasts");if(!t){t=document.createElement("div");t.id="toasts";document.body.append(t);}const d=document.createElement("div");d.className="toast"+(kind?" "+kind:"");d.textContent=msg;t.append(d);setTimeout(()=>{d.style.transition="opacity .3s";d.style.opacity="0";setTimeout(()=>d.remove(),320);},4000);}\n'

assert src.count("</style>") == 1, "multiple style blocks - aborting"
src = src.replace("</style>", CSS_ADD + "</style>")
sub1("function hidePeek(){", JS_TOAST + "function hidePeek(){", "toast-anchor")

sub1('alert("Name is required")', 'toast("Name is required","err")', "alert-name")
sub1('alert($("f_net").checked?"No model selected - click Scan models first":"No model available in the local Studio")',
     'toast($("f_net").checked?"No model selected - click Scan models first":"No model available in the local Studio","err")', "alert-model")
sub1('alert("A reply is still streaming - wait for it to finish (or reload the page), then reset.")',
     'toast("A reply is still streaming - wait for it to finish (or reload the page), then reset.","err")', "alert-busy")
sub1('alert("Counter reset failed: "+e)', 'toast("Counter reset failed: "+e,"err")', "alert-counter")

# --- confirm-delete: EXACT multi-line base form (L328-330) ---
old_del = ('    x.onclick=async e=>{e.stopPropagation();\n'
           '      if(!confirm(`Delete ${a.name}?`))return;\n'
           '      await fetch("/api/agents/"+a.id,{method:"DELETE"}); refresh();};')
new_del = ('    x.onclick=async e=>{e.stopPropagation(); if(!x._arm){x._arm=1; const _o=x.textContent; x.textContent="Sure?"; x.title="Click again to confirm delete"; x.style.color="#d66"; '
           'setTimeout(()=>{if(x.isConnected){x.textContent=_o;x.title="Delete";x.style.color="";} x._arm=0;},2500); return;} '
           'await fetch("/api/agents/"+a.id,{method:"DELETE"}); refresh();};')
sub1(old_del, new_del, "confirm-delete")

# --- confirm-reset: EXACT multi-line base form post alert-busy substitution (L922-924) ---
old_rst = ('$("resetBtn").onclick=async()=>{\n'
           '  if(busy){ toast("A reply is still streaming - wait for it to finish (or reload the page), then reset.","err"); return; }\n'
           '  if(!confirm("Reset conversation?\\nClears chat history and the agent-to-agent counter."))return;')
new_rst = ('$("resetBtn").onclick=async()=>{\n'
           '  const _rb=$("resetBtn");\n'
           '  if(busy){ toast("A reply is still streaming - wait for it to finish (or reload the page), then reset.","err"); return; }\n'
           '  if(!_rb._arm){ _rb._arm=1; const _ro=_rb.textContent; _rb.textContent="Confirm reset?"; _rb.title="Click again to confirm: clears chat history and the agent-to-agent counter."; _rb.style.background="var(--warn)"; setTimeout(()=>{if(_rb.isConnected){_rb.textContent=_ro;_rb.title="";_rb.style.background="";} _rb._arm=0;},3000); return;}')
sub1(old_rst, new_rst, "confirm-reset")

checks = {
    "no alert( left": len(re.findall(r"\balert\(", src)) == 0,
    "no confirm( left": len(re.findall(r"\bconfirm\(", src)) == 0,
    "two @media blocks": src.count("@media") == 2,
    "toast fn present": "function toast(msg,kind)" in src,
    "A4 panelDock absolute intact": "#panelDock{position:absolute" in src,
    "A5 acc-strong intact": "--acc-strong:#2f6fe0" in src,
    "div balance": src.count("<div") == src.count("</div>"),
    "delete arm present": 'x.textContent="Sure?"' in src and "x._arm=1" in src,
    "reset arm present": '_rb.textContent="Confirm reset?"' in src and "_rb._arm=1" in src,
}
for k, v in checks.items():
    print(f"{'PASS' if v else 'FAIL'}  {k}")
assert all(checks.values()), "post-check failed - candidate NOT written"

out_md5 = hashlib.md5(src.encode("utf-8")).hexdigest()
out = f"memory/builder/index_html_a6_b_candidate_{out_md5[:16]}.html"
open(out, "w", encoding="utf-8", newline="").write(src)
pin = out.replace("memory/builder/", "memory/verifier/")
open(pin, "w", encoding="utf-8", newline="").write(src)
print(f"\ncandidate: {out}")
print(f"pinned copy: {pin}")
print(f"size: {os.path.getsize(out)} B (base {orig_len} chars -> {len(src)} chars)")
print(f"md5:  {out_md5}")
print(f"divs: {src.count('<div')} open / {src.count('</div>')} close")
print("GATE PASS - A6+B candidate persisted (r44 fixed transform)")
