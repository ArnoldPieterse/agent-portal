/* ui/tour.js - first-run 4-step tour (Goal #9, re-landed on White 2026-11-19).
   2026-11-23 hardening: overlay can no longer get stuck over the UI (render failure
   rolls back; Esc + backdrop click dismiss; sweeper removes card-less overlays). */
(function(){ "use strict";
  if(window.__tourLoaded)return; window.__tourLoaded=true;
  const STEPS=[
    {sel:"#fleetBtn", title:"Fleet Status", body:"Every host's loaded models, busy/idle state and last-seen age. Live while the panel is open; offline hosts raise a notification."},
    {sel:"#goalsBtn", title:"Goal Velocity", body:"Per-agent done/total rings from memory/goals/, plus fleet totals and a git-based progress curve with stall warnings."},
    {sel:"#opsBtn", title:"Ops Panel", body:"Local git status + one-click commit, and prune fully-completed TODO sections into TODO_completed.md. The Print button here exports a clean report."},
    {sel:"#filesBtn", title:"Files & Uploads", body:"Humans' drop zone: attach files to prompts or list what already landed in uploads/. Empty states tell you exactly where to start.", last:true}
  ];
  let step=0, overlay=null, card=null, hl=null;
  function unhl(){ if(hl){hl.classList.remove("tour-hl"); hl=null;} }
  function place(){ unhl(); const t=document.querySelector(STEPS[step].sel); if(!t)return; t.classList.add("tour-hl"); hl=t;
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
    overlay.appendChild(card);
    try{ document.body.appendChild(overlay); render(); }
    catch(e){ overlay.remove(); overlay=null; card=null; return; } // 2026-11-23: never leave a bare/stuck overlay that eats clicks
    overlay.addEventListener("click",function(e){ if(e.target===overlay)close(); }); // backdrop click dismisses (stuck overlay made mode bar unclickable)
  }
  window.addEventListener("keydown",function(e){ if(e.key==="Escape"&&overlay)close(); }); // Esc dismisses
  setInterval(function(){ document.querySelectorAll(".tour-overlay").forEach(function(o){
    if(o!==overlay || !o.querySelector(".tour-card")) o.remove(); }); },2000); // sweep stuck/foreign overlays
  function close(){ unhl(); if(overlay){overlay.remove();overlay=null;card=null;} try{localStorage.setItem("portalTourDone","1");}catch(_){} }
  window.addEventListener("load",function(){ let done=false; try{done=localStorage.getItem("portalTourDone")==="1";}catch(_){} if(!done && !location.hash.includes("notour"))setTimeout(function(){ let d=false; try{d=localStorage.getItem("portalTourDone")==="1";}catch(_){} if(!d)start(); },800); });
})();
