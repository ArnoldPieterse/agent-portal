/* ui/notifications.js - toast + bell notification system (Goal #5, re-landed on White 2026-11-19) */
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
    t.title="Click to dismiss";
    t.onclick=function(){ dismiss(t); };   // 2026-11-22: click anywhere on the toast dismisses it (× still works)
    const x=el("button","toast-close"); x.type="button"; x.setAttribute("aria-label","Dismiss notification"); let xi=''; try{ xi=(window.UI&&UI.icon)?UI.iconSized('close',10):''; }catch(_){} x.innerHTML=xi||'×'; x.onclick=function(e){ e.stopPropagation(); dismiss(t); };
    t.appendChild(x); c.appendChild(t);
    const bell=ensureBell(); if(bell){ items.push({kind:kind,msg:msg}); if(items.length>50)items=items.slice(-50); unread++; renderBadge(); renderPanel(); }
    setTimeout(function(){ dismiss(t); },TTL); };
})();
