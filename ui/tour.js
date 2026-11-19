/* ui/tour.js - first-run 4-step tour (Goal #9, re-landed on White 2026-11-19) */
(function(){ "use strict";
  if(window.__tourLoaded)return; window.__tourLoaded=true;
  const STEPS=[
    {sel:"#fleetBtn", title:"Fleet Status", body:"Every host's loaded models, busy/idle state and last-seen age. Live while the panel is open; offline hosts raise a notification."},
    {sel:"#goalsBtn", title:"Goal Velocity", body:"Per-agent done/total rings from memory/goals/, plus fleet totals and a git-based progress curve with stall warnings."},
    {sel:"#opsBtn", title:"Ops Panel", body:"Local git status + one-click commit, and prune fully-completed TODO sections into TODO_completed.md. The Print button here exports a clean report."},
    {sel:"#filesBtn", title:"Files & Uploads", body:"Humans' drop zone: attach files to prompts or list what already landed in uploads/. Empty states tell you exactly where to start.", last:true}
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
