// Agent Portal - core app logic (agents/models/chat/goals/ops panels).
// 2026-11-16 file-modularity split: extracted from index.html.
// parent: index.html | sibling: ui/uploads.js (loads AFTER this file - keep order)
// rule: memory/portal/file-modularity.md | served by GET /ui/core.js

const $ = id => document.getElementById(id);
window.onerror=(m,src,l)=>{try{$("stext").textContent="JS ERROR line "+l+": "+String(m).slice(0,80); if(typeof window.notify==="function")window.notify("err","JS error: "+String(m).slice(0,120));}catch(_){}};
$("stext").textContent="js running…";
let agents=[], models=[], netModels=[], kbs=[], localTools=[];
let selectedId=null, mode="solo", busy=false;
let sessionId=null; // current run's activity-timeline session (one per human prompt)
let history=[]; // {speaker, content}

async function api(path, opts){ const r=await fetch(path, opts); return r.json(); }
const jpost=(p,b)=>api(p,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(b)});
const jput =(p,b)=>api(p,{method:"PUT" ,headers:{"Content-Type":"application/json"},body:JSON.stringify(b)});

function esc(s){ return (s||"").replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }
function shortModel(m){ return (m||"").split("/").pop().slice(0,26); }

async function refresh(){
  agents=((await api("/api/agents").catch(()=>({}))).agents)||[];
  const m=await api("/api/models").catch(()=>({data:[]})); models=m.data||[];   // Studio's /v1/models can stall during a generation - never let it kill the rest of refresh
  try{ kbs=(await api("/api/knowledge-bases")).knowledgeBases||[]; }catch(e){ kbs=[]; }
  localTools=((await api("/api/tools").catch(()=>({}))).local_tools)||[];
  if(!agents.find(a=>a.id===selectedId)) selectedId=agents[0]?.id||null;
  try{ const mem=await api("/api/memory"); setXtalk(mem.inter_agent_replies, mem.limit); }catch(e){}
  renderAgents();
}

function renderAgents(){
  const el=$("agentList"); el.innerHTML="";
  for(const a of agents){
    const c=document.createElement("div");
    c.className="acard"+(a.id===selectedId?" sel":"");
    c.innerHTML=`<span class="em">${a.emoji?esc(a.emoji):UI.icon("robot")}</span>
      <span class="nm"><b>${esc(a.name)}</b><span>${esc(shortModel(a.model_id))}</span></span>`;
    const g=document.createElement("button"); g.innerHTML=UI.icon("settings"); g.title="Edit profile";
    g.onclick=e=>{e.stopPropagation();openEditor(a);};
    const x=document.createElement("button"); x.innerHTML=UI.icon("close"); x.title="Delete";
    x.onclick=async e=>{e.stopPropagation();
      if(!confirm(`Delete ${a.name}?`))return;
      await fetch("/api/agents/"+a.id,{method:"DELETE"}); refresh();};
    c.append(g,x);
    c.onclick=()=>{ selectedId=a.id; renderAgents(); updateHint(); if(mode==="solo") resetChat(); };
    el.appendChild(c);
  }
  $("modeHint").textContent="";
}

let xtalkMax=0; // high-water mark: parallel streams' meta frames arrive out of order, counter only rises within a prompt
function setXtalk(n, limit){ if(typeof n==="number"&&n>xtalkMax)xtalkMax=n; $("xtalk").textContent = (mode==="group") ? (" \u00b7 "+xtalkMax+"/"+(limit==null?"\u221e":limit)+" agent\u2194agent this prompt") : ""; }

function updateHint(){
  const a=agents.find(x=>x.id===selectedId);
  $("modeHint").textContent = mode==="solo"
    ? (a?`Chatting with ${a.emoji||""} ${a.name}`:"")
    : `${agents.length} agents in the room · @Name to address one`;
}

// Multi-agent busy hint: group streams run IN PARALLEL, so several agents can be
// "working" at once - track the set, render a combined line, clear per stream end.
const busyNames=new Set();
function renderBusyHint(){ const b=$("busyHint"); if(!b)return;
  if(busyNames.size){ const n=[...busyNames];
    b.textContent="\u23f3 "+(n.length>1?n.join(", "):n[0])+(n.length>1?" are":" is")+" working\u2026";
    b.style.display="inline"; }
  else{ b.textContent=""; b.style.display="none"; } }
function setBusyHint(name){ if(name)busyNames.add(name); renderBusyHint(); if(busyNames.size)$("stopBtn").disabled=false; }
function clearBusyHint(name){ busyNames.delete(name); renderBusyHint(); if(!busyNames.size)$("stopBtn").disabled=true; }
// Send is NEVER disabled while a run is active: send() routes to the user-message queue
// (user_messages.json) which each agent picks up on its next prompt build. The button just
// relabels to "Queue" so the behavior is visible (2026-11-15: was greyed out = dead end).
function setSendQueued(q){const b=$("send");b.disabled=false;b.textContent=q?"Queue":"Send";}
let stallTimer=null;
async function stallPoll(){try{const r=await api('/api/run-state');
  if(r&&r.busy&&r.stalled){const b=$("busyHint");if(b){b.style.display="inline";
    b.textContent="\u26a0 no output for "+Math.max(1,Math.round((Date.now()-(r.last_frame_ts||Date.now()))/60000))+" min - possible Studio wedge (try \u25a0 Stop or \\RecoverAll)";}}
}catch(e){}}
function startStallPoll(){if(stallTimer)return;stallPoll();stallTimer=setInterval(stallPoll,15000);}
function stopStallPoll(){if(stallTimer){clearInterval(stallTimer);stallTimer=null;}}

function resetChat(){ history=[]; $("msgs").innerHTML=""; sessionId=null; }
// ---- Sticky auto-scroll (2026-11-13): pin to bottom while streaming, but never yank the view
// down while the user has scrolled up to re-read; re-pins at the bottom or on the next send.
let stickOn=true;
function stickScroll(force){ if(force)stickOn=true; if(stickOn)$("msgs").scrollTop=$("msgs").scrollHeight; }
$("msgs").addEventListener("scroll",()=>{ const el=$("msgs"); stickOn=(el.scrollHeight-el.scrollTop-el.clientHeight)<60; });
// ---- Per-mode message persistence (2026-11-13): refresh no longer clears the conversation.
// A MutationObserver on #msgs serializes visible bubbles + history into localStorage per mode;
// setMode restores the slot, \u21ba Reset clears it. Restored agent bubbles are re-linkified so
// file-token hover peeks work exactly as in a live bubble.
const LS_PREFIX="portal_msgs_";
const lsKey=()=>LS_PREFIX+mode;
let saveTimer=null;
function scheduleSave(){ if(saveTimer)return; saveTimer=setTimeout(saveMsgs,400); }
function saveMsgs(){
  saveTimer=null;
  try{
    const bubbles=[...$("msgs").children].map(d=>{
      const who=d.querySelector(".who"), body=d.querySelector(".body");
      return {n:who?who.textContent:"",c:(who&&who.style.color)||"",y:d.classList.contains("you"),t:body?body.textContent:""};
    }).slice(-200);
    localStorage.setItem(lsKey(),JSON.stringify({bubbles,history:history.slice(-120),ts:Date.now()}));
  }catch(e){} // quota/private mode - persistence is best-effort, never break chat
}
function restoreMsgs(){
  let data=null; try{ data=JSON.parse(localStorage.getItem(lsKey())||"null"); }catch(e){}
  if(!data||!Array.isArray(data.bubbles)||!data.bubbles.length)return false;
  history=Array.isArray(data.history)?data.history:[];
  for(const b of data.bubbles){
    const d=document.createElement("div"); d.className="msg"+(b.y?" you":"");
    if(!b.y){ const w=document.createElement("div"); w.className="who"; if(b.c)w.style.color=b.c; w.textContent=b.n||""; d.appendChild(w); }
    const body=document.createElement("div"); body.className="body"; body.textContent=b.t||""; d.appendChild(body);
    $("msgs").appendChild(d);
    if(!b.y&&(b.t||"").trim())linkifyFiles(body,b.t); // re-wire file-link hover for restored bubbles
  }
  stickScroll(true);
  return true;
}
$("stopBtn").onclick=()=>{ if(!busyNames.size&&mode!=="group")return; stopRequested=true; lastConcluded=true; activeCtrls.forEach(c=>c.abort());
  if(runId){ jpost('/api/run-stop',{run_id:runId}).catch(()=>{}); } }; // Stop button: abort solo streams / tell the backend run engine to stop cleanly (it finishes teardown + verdict)

function addBubble(name, color, emoji, isYou){
  const d=document.createElement("div");
  d.className="msg"+(isYou?" you":"");
  d.innerHTML=(isYou?"":`<div class="who" style="color:${color||"var(--dim)"}">${esc(emoji||"")} ${esc(name)}</div>`);
  const body=document.createElement("div"); body.className="body"; d.appendChild(body);
  $("msgs").appendChild(d); stickScroll();
  return d;
}

// Mirror of server _effective_reply: strip invisible chars Python's str.strip()
// removes but JS trim() does not (e.g. U+0085), require leading [SILENT] with
// nothing meaningful after it - so display-drop and counter-count always agree.
// Fallback only - the backend meta.silent flag is authoritative. Lenient so a
// stray "." / "ok" after [SILENT] still counts as silence rather than re-opening the loop.
let lastConcluded=false; // set by streamReply when the server meta says the debate concluded
let noOutputNames=new Set(); // agents whose FINAL reply was an empty completion this prompt (shown as "(no output)")
let roundBubbles=[];    // agent bubbles created during the current send() - stamped with marked concluded when the round ends on [CONCLUDED]
let stopRequested=false; // Stop button clicked - closes the current run as concluded (user authority)
const activeCtrls=new Set(); // in-flight /api/chat streams, aborted by Stop button
const stripConcluded=t=>(t||"").replace(/^\[concluded\][\s:\-.\u2013\u2014]*/i,"");
const isSilent=t=>{const s=((t||"").replace(/[\u0085\u180e\u200b-\u200f\u202a-\u202e\u2060\ufeff]/g,"")).trim();if(!/^\[silent\]/i.test(s))return false;const rest=s.slice(8).replace(/^[\s:.\-\u2013\u2014]+/,"").trim();return !rest||/^(ok|okay|sure|nothing|no|fine|cool|agree)[.!]*$/i.test(rest);};

async function streamReply(agent, kind, silentTarget){
   setBusyHint(agent.name);
   try{ return await streamReplyCore(agent, kind, silentTarget); }
   finally{ clearBusyHint(agent.name); } // parallel: this stream is done even if others still run
}
async function streamReplyCore(agent, kind, silentTarget){
   const d=addBubble(agent.name, agent.color, agent.emoji, false);
   let ctrl=null; // AbortController for this stream - Stop button aborts it
   roundBubbles.push(d);
   if(kind==="cross-talk"){
     const chip=document.createElement("span");
     chip.style.cssText="margin-left:auto;font-size:var(--fs-12);color:var(--dim)";
     chip.textContent="\u21bb agent-to-agent"; chip.title="reply to another group member (unlimited by default - finite cap only when budget OFF; ends early on [CONCLUDED])";
     d.querySelector(".who").appendChild(chip);
   }
   const body=d.querySelector(".body");
   lastConcluded=false;
   // Busy indicator: ticking "working… Ns" until the first visible frame (content/thinking/tool).
   let busyT=null, busySecs=0;
   const startBusy=()=>{ if(busyT)return; busySecs=0;
     const sp=document.createElement("span"); sp.className="busyspan"; sp.textContent="\u23f3 working\u2026 0s"; body.appendChild(sp);
     busyT=setInterval(()=>{busySecs++; if(sp.isConnected)sp.textContent="working\u2026 "+busySecs+"s";},1000); };
   const stopBusy=()=>{ if(busyT){clearInterval(busyT);busyT=null;} const sp=body.querySelector(".busyspan"); if(sp)sp.remove(); };
   startBusy(); // modeBar busy-hint is owned by the streamReply wrapper above
   let res;
   try{
     ctrl=new AbortController(); activeCtrls.add(ctrl);
      res=await fetch("/api/chat",{signal:ctrl.signal,method:"POST",headers:{"Content-Type":"application/json"},
       body:JSON.stringify({agent_id:agent.id, mode, kind:kind||"prompt", messages:history, session:sessionId||undefined})});
   }catch(e){ if(ctrl&&(e.name==="AbortError"||stopRequested)){ stopBusy(); return ""; } stopBusy(); addBubble("error","var(--err)","!",false).querySelector(".body").textContent=String(e); return ""; }
   const reader=res.body.getReader(); const dec=new TextDecoder(); let buf="";
   let full="", thinkEl=null, toolRow=null, metaSilent=false, metaConcluded=false, stop=false;
   try{
     while(true){
       const {done,value}=await reader.read(); if(done)break;
       buf+=dec.decode(value,{stream:true});
       let idx;
       while((idx=buf.indexOf("\n\n"))>=0){
         const frame=buf.slice(0,idx); buf=buf.slice(idx+2);
         for(const line of frame.split("\n")){
           if(!line.startsWith("data: "))continue;
           const p=line.slice(6);
           if(p==="[DONE]"){stop=true;break;} // NOT an early return - post-processing below (silent merge / concluded chip) must still run
           let o; try{o=JSON.parse(p);}catch(e){continue;}
           if(o.error){ body.textContent="error: "+o.error; return ""; }
           if(o.blocked){ body.textContent="\u23f8 "+o.blocked; return null; }
           if(o.model_load){ let ln=d.querySelector(".loadnote"); if(!ln){ln=document.createElement("div");ln.className="loadnote";d.appendChild(ln);} ln.textContent="\u23f3 "+o.model_load; stickScroll(); }
           if(o.meta){ if(typeof o.meta.inter_agent_replies==="number")setXtalk(o.meta.inter_agent_replies,o.meta.limit); if(o.meta.silent)metaSilent=true; if(o.meta.concluded)metaConcluded=true; }
           if(o.content){ stopBusy(); full+=o.content; body.textContent=full; stickScroll(); }
           if(o.thinking){ // thinking stays in this agent's own bubble, per message (only silences are merged)
             if(!thinkEl){thinkEl=document.createElement("details");thinkEl.className="think";
               const s=document.createElement("summary");s.textContent="thinking";
               const tb=document.createElement("div");tb.className="tbody";thinkEl.append(s,tb);d.appendChild(thinkEl);}
             stopBusy(); thinkEl.querySelector(".tbody").textContent+=o.thinking; stickScroll(); }
           if(o.tool){ stopBusy(); if(!toolRow){toolRow=document.createElement("div");d.appendChild(toolRow);}
             const chip=document.createElement("span");chip.className="toolchip";
             const tn=o.tool.name||(o.tool.function&&o.tool.function.name)||"tool";
             chip.innerHTML=UI.icon("wrench")+" "+esc(tn); toolRow.appendChild(chip); }
         }
         if(stop)break;
       }
       if(stop)break;
     }
   }finally{ stopBusy(); if(ctrl)activeCtrls.delete(ctrl); }
   if(metaSilent||isSilent(full)){ // silence is only knowable once the response is final (meta frame / full text)
     if(silentTarget){ d.remove(); silentTarget.note(agent.name); }   // group: merge into ONE shared pill
     else{ d.classList.add("silentmsg"); body.textContent="\uD83D\uDD07 stayed silent"; stickScroll(); } // solo: small dim pill in place
     return ""; }
   if(metaConcluded){ lastConcluded=true; const s=stripConcluded(full); body.textContent=s; stickScroll();
     const chip=document.createElement("span");chip.className="conclchip";chip.style.cssText="margin-left:auto;font-size:var(--fs-12);color:var(--ok)";
     chip.textContent="\u2713 concluded"; chip.title="discussion reached a natural conclusion - round ended";
     d.querySelector(".who").appendChild(chip); if(!renderDms(body,s))linkifyFiles(body,s); return s; }
   if(/stopped before completing its tool calls/i.test(full)){ // Studio harness note = turn ended MID-TASK (promised edits never ran)
     const chip=document.createElement("span");chip.className="warnchip";
     chip.style.cssText="margin-left:auto;font-size:var(--fs-12);color:var(--warn)";
     chip.textContent="\u26A0 tool calls truncated - task incomplete";
     chip.title="the model stopped before running its tool calls - the promised work was NOT done";
     d.querySelector(".who").appendChild(chip); }
   if(!full.trim()){ // empty completion: show it (blank bubbles hide who went quiet) and count as "nothing new"
     body.textContent="\u2014 (no output) \u2014"; body.style.color="var(--dim)";
     noOutputNames.add(agent.name); return ""; }
   if(!renderDms(body,full))linkifyFiles(body,full);
   return full;
 }

// File links: path-like tokens in a FINAL bubble that exist in the workspace become clickable
// .flink anchors (hover = peek popover with first lines via /api/file; click = open /api/file/raw).
function showPeek(e,path,info){ const pk=$("peek"); if(!pk)return;
  pk.innerHTML=""; const h=document.createElement("div");h.className="pk-h";h.textContent=info.name||path;
  if(info.size!=null){const sz=document.createElement("span");sz.className="pk-sz";sz.textContent=(info.size/1024).toFixed(1)+" KB";h.appendChild(sz);}
  const b=document.createElement("pre");b.className="pk-body";
  b.textContent=info.binary?"(binary file - click to open)":((info.head||"")+(info.truncated?"\u2026":""));
  pk.append(h,b);pk.style.display="block";movePeek(e); }
function movePeek(e){ const pk=$("peek"); if(!pk)return;
  const r=pk.getBoundingClientRect(); let x=e.clientX+14,y=e.clientY+12;
  if(x+r.width>innerWidth-8)x=Math.max(8,e.clientX-r.width-10);
  if(y+r.height>innerHeight-8)y=Math.max(8,e.clientY-r.height-10);
  pk.style.left=x+"px";pk.style.top=y+"px"; }
function hidePeek(){ const pk=$("peek"); if(pk)pk.style.display="none"; }
// ---- Private messaging between agents ([DM @Name]) ----
// Privacy is enforced server-side (agent_portal.to_openai_messages redacts per viewer).
// This only renders the HUMAN view: public text as-is, each DM as a collapsed lock chip
// the operator can expand (the human owns every agent - transparency for debugging).
function renderDms(body, full){
  const re=/\[DM\b\s*@?\s*([^\]\n]+?)\s*\]/gi;
  const marks=[]; let m;
  while((m=re.exec(full)))marks.push({i:m.index,e:m.index+m[0].length,t:m[1].trim()});
  if(!marks.length)return false;
  body.textContent="";
  let prev=0;
  marks.forEach((mk,ix)=>{
    const pub=full.slice(prev,mk.i);
    if(pub.trim()){const d=document.createElement("div");d.className="dmpub";d.textContent=pub;body.appendChild(d);linkifyFiles(d,pub);}
    const end=ix+1<marks.length?marks[ix+1].i:full.length;
    const dmBody=full.slice(mk.e,end).trim();
    const el=document.createElement("details");el.className="dmseg";
    const s=document.createElement("summary");s.textContent="\uD83D\uDD12 private \u2192 "+mk.t;
    s.title="private message - only "+mk.t+" can see this content in the group (other agents see a lock chip)";
    const b=document.createElement("div");b.className="dmbody";b.textContent=dmBody;
    el.append(s,b); body.appendChild(el); linkifyFiles(b,dmBody);
    prev=end; });
  return true;
}
function linkifyFiles(el,text){
  if(!el||!text)return;
  const rx=/[\w./\\-]+\.[A-Za-z0-9]{1,8}/g;        // file tokens (must end in an extension)
  const rxf=/(?<![\w./\\-])(?:[\w-]+\/)+/g;      // folder tokens (end in /, no ext needed)
  const cands=[],seen=new Set(); let m;
  for(const r of [rx,rxf]) while((m=r.exec(text))&&cands.length<12){
    const t=m[0]; if(/^(https?:|www\.)/i.test(t)||t.includes(" "))continue;
    const clean=t.replace(/^[./\\]+/,""); if(!clean||seen.has(clean))continue; seen.add(clean); cands.push(clean); }
  if(!cands.length)return;
  Promise.all(cands.map(c=>fetch("/api/file?path="+encodeURIComponent(c)).then(r=>r.ok?r.json():null).catch(()=>null)))
   .then(res=>{
     if(!el.isConnected||el.textContent!==text)return; // bubble changed meanwhile -> skip
     const byPath={}; res.forEach(o=>{if(o&&o.path)byPath[o.path]=o;});
     const paths=Object.keys(byPath); if(!paths.length)return;
     paths.sort((a,b)=>b.length-a.length);
     el.textContent=""; let rest=text,guard=0;
     while(rest&&guard++<64){
       let best=null,bi=-1;
       for(const p of paths){const i=rest.indexOf(p);if(i>=0&&(bi<0||i<bi||(i===bi&&p.length>best.length))){best=p;bi=i;}}
       if(!best)break;
       if(bi>0)el.appendChild(document.createTextNode(rest.slice(0,bi)));
       const a=document.createElement("a");a.className="flink";a.href="/api/file/raw?path="+encodeURIComponent(best);
       a.target="_blank";a.rel="noopener";a.textContent=best;
       const info=byPath[best];
       a.addEventListener("mouseenter",e=>showPeek(e,best,info));
       a.addEventListener("mousemove",movePeek);
       a.addEventListener("mouseleave",hidePeek);
       el.appendChild(a); rest=rest.slice(bi+best.length); }
     if(rest)el.appendChild(document.createTextNode(rest));
   });
}

// ---- Activity timeline (per-session audit log, /api/activity, 2026-11-12) ----
let actTimer=null;
const actIcons={start:"play",tool:"wrench",end:"check",blocked:"alert",error:"warning",aborted:"stop",readmem:"book",storemem:"save"};
function actRender(evts){
  const body=$("actBody"); if(!body)return;
  body.innerHTML="";
  if(!evts.length){ body.textContent="(no events yet for this session)"; return; }
  for(const e of evts){
    let x=e.event;
    if(e.event==="start")x="started ("+e.kind+(e.mode==="group"?", group":"")+")";
    else if(e.event==="tool")x="tool: "+(e.tool||"?");
    else if(e.event==="end")x="done in "+(e.dur??0)+"s · "+(e.chars??0)+" chars"+(e.silent?" · silent":"")+(e.concluded?" · concluded":"");
    else if(e.event==="blocked")x="blocked: "+(e.detail||"agent-to-agent limit");
    else if(e.event==="error")x="error: "+(e.error||"?");
    else if(e.event==="aborted")x="aborted (client stop)";
    else if(e.event==="readmem")x="memory lookup · "+(e.chars??0)+" chars in "+(e.dur??0)+"s";
    else if(e.event==="storemem")x=(e.stored?"note stored: ":"no note: ")+esc(e.note||"(none)")+" ("+(e.dur??0)+"s)";
    const div=document.createElement("div"); div.className="aev";
    const col=(agents.find(a=>a.name===e.agent)||{}).color||"var(--dim)";
    div.innerHTML=`<span class="at">${new Date(e.ts*1000).toLocaleTimeString([],{hour12:false})}</span><span class="an" style="color:${col}">${esc(e.agent||"?")}</span><span>${actIcons[e.event]?UI.icon(actIcons[e.event]):'•'}</span><span class="ax">${esc(x)}</span>`;
    body.appendChild(div);
  }
  body.scrollTop=body.scrollHeight;
}
async function actUpdate(){
  const sel=$("actSel"); if(!sel)return;
  try{
    const o=await api(sel.value?"/api/activity?session="+encodeURIComponent(sel.value):"/api/activity");
    if(sel.value){ actRender(o.events||[]); $("actStat").textContent=(o.events||[]).length+" events"; }
    else{
      const cur=sel.value;
      sel.innerHTML="";
      const op0=document.createElement("option"); op0.value=""; op0.textContent="(recent sessions)"; sel.appendChild(op0);
      for(const s of o.sessions||[]){
        const op=document.createElement("option"); op.value=s.session;
        op.textContent=s.session+"  ("+s.events+" ev, "+new Date(s.last_ts*1000).toLocaleTimeString([],{hour12:false})+")";
        sel.appendChild(op);
      }
      const s=(o.sessions||[])[0];
      $("actStat").textContent=s?"newest: "+s.session:"";
    }
  }catch(e){ $("actStat").textContent="error: "+e; }
}
function actFollow(){ // panel open -> jump to the session this run just started
  const sel=$("actSel"); if(!sel||!sessionId||!$("actPanel").classList.contains("open"))return;
  if([...sel.options].some(o=>o.value===sessionId))sel.value=sessionId;
  else{ const op=document.createElement("option");op.value=sessionId;op.textContent=sessionId+" (current)";sel.prepend(op);sel.value=sessionId; }
  actUpdate();
}
$("actBtn").onclick=async()=>{
  const open=$("actPanel").classList.toggle("open");
  $("actBtn").classList.toggle("on",open);
  if(open){
    await actUpdate(); // fill the recent-sessions dropdown
    if(!$("actSel").value&&sessionId){ // prefer the CURRENT run if it already has events
      const o=await api("/api/activity?session="+encodeURIComponent(sessionId));
      if((o.events||[]).length)actFollow(); else actUpdate();
    }
    if(actTimer)clearInterval(actTimer);
    actTimer=setInterval(()=>{ if($("actPanel").classList.contains("open"))actUpdate(); },2000); // live while open
  }else if(actTimer){ clearInterval(actTimer); actTimer=null; }
};
$("actRefresh").onclick=()=>actUpdate();
$("actSel").onchange=()=>actUpdate();
// ---- Fleet status panel (/api/fleet, 2026-11-13 round-table) ----
let fleetTimer=null;
async function fleetUpdate(){
  try{
    const o=await api("/api/fleet");
    const now=o.ts||Date.now()/1000;
    let html="";
    for(const h of (o.hosts||[])){
      const age=h.last_seen?Math.max(0,Math.round(now-h.last_seen)):"–";
      const st=h.state==="busy"?"busy":h.state==="idle"?"idle":h.state==="unauth"?"UNAUTH (up - key missing/expired)":"UNKNOWN";
      const models=h.models.length?h.models.map(m=>esc(m.id)+(m.quant?" ("+esc(m.quant)+")":"")).join(", "):"— none loaded —";
      // Per-host load queue (2026-11-22): in-flight model load + waiters behind it.
      let lq="";
      if(h.loading){ lq+=' · <span class="fload" title="Model load in progress on this host (one at a time)">⏳ loading '+esc(h.loading.model||"?")+'</span>'; }
      if(h.queued>0){ lq+=' · <span class="fload fload-wait" title="Waiting their turn in the per-host load queue">'+h.queued+' queued</span>'; }
      (h.host_loading||[]).forEach(m=>{ lq+=' · <span class="fload" title="Studio is loading this model right now - started by the host itself (boot auto-load or manual reload), not via the portal queue">⏳ '+esc(m)+' (host load)</span>'; });
      // LIVE PLACEMENT (2026-11-22): primary list = agents that actually RAN on this host
      // in the last 10 min (h.active); the static agents.json home roster is secondary.
      const act=h.active||[];
      const who=act.length?act:(h.agents||[]);
      html+='<div class="frow-h"><span class="fdot '+h.state+'"></span><b>'+esc(h.host)+'</b>'+
        '<span class="hint"> · '+st+(h.reason?" · "+esc(h.reason):"")+" · last seen "+age+"s ago</span>"+
        '<div class="fmodels">'+models+lq+'</div>'+
        '<div class="hint" style="margin-left:16px">'+(act.length?"now":"home")+': '+(who.length?who.map(esc).join(", "):"none")+(act.length&&h.agents.length?" · home: "+h.agents.map(esc).join(", "):"")+'</div></div>';
    }
    const _fp=window._fleetPrev||{}; const _fs={};
    for(const h of (o.hosts||[])){ _fs[h.host]=h.state!=="unknown";
      if(_fp[h.host]===true && h.state==="unknown" && typeof window.notify==="function") window.notify("warn","Agent host "+h.host+" is offline"); }
    window._fleetPrev=_fs;
    $("fleetBody").innerHTML=html||UI.emptyState({icon:"agent",title:"No hosts reporting",msg:"The fleet probe hasn't seen any hosts yet.",ctaLabel:"Refresh now"});
    { const _ct=$("fleetBody").querySelector(".empty-cta"); if(_ct)_ct.onclick=fleetUpdate; }
    const up=(o.hosts||[]).filter(h=>h.state!=="unknown").length;
    $("fleetCount").textContent=(o.hosts||[]).length+"-host fleet · live while open (5s refresh)";
    $("fleetStat").textContent=up+"/"+(o.hosts||[]).length+" reporting · ttl "+(o.ttl||15)+"s";
  }catch(e){ $("fleetStat").textContent="error: "+e; }
}
$("fleetBtn").onclick=async()=>{
  const open=$("fleetPanel").classList.toggle("open");
  $("fleetBtn").classList.toggle("on",open);
  if(open){ await fleetUpdate(); if(fleetTimer)clearInterval(fleetTimer);
    fleetTimer=setInterval(()=>{ if($("fleetPanel").classList.contains("open"))fleetUpdate(); },5000); }
  else if(fleetTimer){ clearInterval(fleetTimer); fleetTimer=null; }
};
// ---- Ops panel (2026-11-13): local git + TODO pruning ----
async function opsLoad(){
  try{
    const o=await (await fetch("/api/git")).json();
    if(!o.repo){ $("gitStatus").textContent="no repo yet — POST /api/git {action:'init'}"; $("opsStat").textContent="no repo"; return; }
    $("gitStatus").textContent=o.status||(o.changed?"":"(clean)");
    $("gitLog").textContent=o.log||"(no commits yet)";
    $("opsStat").textContent=(o.changed?o.changed+" changed":"clean")+(o.log?(" · "+o.log.split("\n").length+" shown"):"");
  }catch(e){ $("opsStat").textContent="error: "+e; }
  opsTiles();   // host tiles refresh with the panel (2026-11-15)
  mergeQueueLoad();   // sandbox merge queue (2026-11-16)
}
async function opsTiles(){
  try{
    const o=await (await fetch("/api/ops")).json();
    const d=o.disk||{};
    $("diskTile").textContent=(d.total_gb!=null)?`disk ${d.drive} · ${d.used_gb} GB used / ${d.total_gb} GB (${Math.round(100*d.used_gb/d.total_gb)}%)\nfree ${d.free_gb} GB`:"error: "+(d.error||"no disk data");
    $("uptimeTile").textContent=`portal up · ${o.uptime_hm}\npid ${o.pid} · since ${o.started}`;
  }catch(e){ $("diskTile").textContent="error: "+e; $("uptimeTile").textContent="error: "+e; }
}
async function mergeQueueLoad(){
  const el=$("mergeQueue"); if(!el)return;
  try{
    const q=await (await fetch("/api/merge-queue")).json();
    if(!q.ok){ el.textContent="error: "+(q.error||"error"); return; }
    const evs=(q.events||[]).slice(0,5);
    if(!evs.length){ el.textContent="(empty - no diverged sandbox code files captured)"; return; }
    const esc=s=>String(s).replace(/[&<>\"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
    el.innerHTML=evs.map(e=>'<div style="margin:2px 0">'+esc(e.ts.slice(5))+' · <b>'+esc(e.file)+'</b> sha '+esc(e.sha)+' ('+e.size+' B)'
      +' <button class="btn" data-mq="'+esc(e.file)+'" style="padding:1px 8px;font-size:var(--fs-12);display:inline-flex;align-items:center;gap:4px">'+UI.iconSized('undo',12)+' restore</button></div>').join("");
    el.querySelectorAll("button[data-mq]").forEach(b=>b.onclick=async()=>{
      opsSay("restoring "+b.dataset.mq+"…");
      try{ const r=await (await fetch("/api/merge",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({file:b.dataset.mq})})).json();
        opsSay(r.ok?"restored "+r.file+" from snapshot "+r.snapshot+(r.committed?" (committed)":""):"error: "+(r.error||"restore failed"));
      }catch(e2){ opsSay("error: "+e2); } finally{ mergeQueueLoad(); }
    });
  }catch(e){ el.textContent="error: "+e; }
}
$("opsBtn").onclick=()=>{ const open=$("opsPanel").classList.toggle("open"); $("opsBtn").classList.toggle("on",open); if(open)opsLoad(); };
async function opsSay(t){ $("opsMsg").textContent=t; }
$("gitCommit").onclick=async()=>{
  const m=$("gitMsg").value.trim(); if(!m){ opsSay("type a commit message first"); return; }
  opsSay("committing…");
  try{ const r=await (await fetch("/api/git",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action:"commit",message:m})})).json();
    if(r.status&&r.status.repo){ $("gitStatus").textContent=r.status.status||"(clean)"; $("gitLog").textContent=r.status.log||"—"; }
    opsSay(r.committed?"committed: "+m:(r.note||r.err||"done")); if(r.committed)$("gitMsg").value="";
  }catch(e){ opsSay("error: "+e); } finally{ opsLoad(); }
};
$("gitMsg").addEventListener("keydown",e=>{if(e.key==="Enter"){e.preventDefault();$("gitCommit").click();}});
$("todoPrune").onclick=async()=>{
  opsSay("pruning…");
  try{ const r=await (await fetch("/api/todo/prune",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"})).json();
    opsSay(r.moved_sections?`moved ${r.moved_sections} section(s), ${r.moved_items} item(s) → TODO_completed.md (${r.completed_lines} lines${r.chunks_split?", split "+r.chunks_split+" part(s)":""})`:(r.note||"done"));
  }catch(e){ opsSay("error: "+e); }
};

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
  h+='<span class="gbar-fleet">'+o.fleet_done+'/'+o.fleet_total+' · '+(o.fleet_pct||0)+'%</span>';
  const lv=(Number.isFinite(+o.level))?+o.level:0;
  h+='<span class="gbar-level'+(lv>0?'':' zero')+'" title="Fleet level - +1 each time ALL goals reach 100% on a fresh goal set; reports in memory/levels/">Lv '+lv+'</span>';
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

// ---- #selftest acceptance harness (2026-11-19 White re-land; evidence for goals 2,4,5,6,7,8,9) ----
window.__selftest=async function(){ const out={};
  const wait=(ms)=>new Promise(r=>setTimeout(r,ms));
  for(let i=0;i<40 && !(agents.length);i++) await wait(250);
  const ids=["fleetBody","goalsBody","filesList"];
  const measure=()=>{ const r={body:document.body.scrollHeight}; for(const id of ids){ const el=$(id); if(el)r[id]=el.scrollHeight; } return r; };
  const scale=["12px","14px","15px","18px","24px"];
  let viol=[]; const all=document.querySelectorAll("body *");
  for(const el of all){ const cs=getComputedStyle(el); if(cs.display==="none")continue; if(!scale.includes(cs.fontSize))viol.push((el.id?"#"+el.id:(typeof el.className==="string"&&el.className.trim()?"."+el.className.trim().split(/\s+/)[0]:el.tagName))+"="+cs.fontSize); }
  out.typography={elements_checked:all.length,violation_count:viol.length,violations:viol.slice(0,25)};
  for(const id of ["fleetBtn","goalsBtn","filesBtn"]){ const b=$(id); if(b)b.click(); }
  await wait(1500);
  const after=measure();
  const link=document.querySelector('link[rel="stylesheet"]');
  const orig=link.href; link.href="/ui/app_density_before.css"; await wait(400);
  const before=measure(); link.href=orig; await wait(400); measure();
  out.density={before:before,after:after,
    panels:Object.keys(after).filter(k=>k!=="body"&&before[k]).map(k=>({panel:k,before:before[k],after:after[k],reduction_pct:+(100*(before[k]-after[k])/before[k]).toFixed(1)})),
    body_reduction_pct:+(100*(before.body-after.body)/before.body).toFixed(1)};
  let clipped=[]; for(const el of document.querySelectorAll("body *")){ const cs=getComputedStyle(el); if((cs.overflow==="hidden"||cs.overflowY==="auto"||cs.overflowY==="scroll")&&el.scrollHeight>el.clientHeight+2)clipped.push((el.id?"#"+el.id:(typeof el.className==="string"&&el.className.trim()?"."+el.className.trim().split(/\s+/)[0]:el.tagName))); }
  out.clipping={clipped_elements:clipped.length,ids:clipped.slice(0,12)};
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
    else if(mode==="tour"){ if(window.UI&&UI.tour){ UI.tour.start(); let g=0; while(g++<8){ const n=document.querySelector(".tour-next"); if(!n)break; n.click(); await wait(60);} } }
    else if(mode==="densitybefore"||mode==="densityafter"){
      for(const id of ["fleetBtn","goalsBtn","filesBtn"]){ const b=document.getElementById(id); if(b)b.click(); }
      await wait(1500);
      if(mode==="densitybefore")document.querySelector('link[rel="stylesheet"]').href="/ui/app_density_before.css"; }
  })(); };
if(location.hash==="#selftest"){ window.addEventListener("load",async()=>{ try{ const r=await window.__selftest(); const p=document.createElement("pre"); p.id="selftestOut"; p.textContent="SELFTEST_JSON "+JSON.stringify(r); document.body.appendChild(p); }catch(e){ const p=document.createElement("pre"); p.id="selftestOut"; p.textContent="SELFTEST_ERR "+e; document.body.appendChild(p);} }); }
else if((location.hash||"").startsWith("#visual")){ window.addEventListener("load",()=>window.__visual(((location.hash||"").match(/m=(\w+)/)||[])[1]||"empty")); }

// ---- Host-side load visibility (2026-11-22) ----
// /api/fleet now reports host_loading[] per host (models the Studio itself is
// mid-load on - boot auto-loads, manual reloads, not just portal queue entries).
// Independent DOM patch: while any host has a load in flight, replace the
// "no loads in flight" placeholder in that host's LOAD QUEUE section. No-op
// when nothing is loading or when another renderer already shows it.
(function(){
  let cur=[];
  async function tick(){
    try{
      const d=await api("/api/fleet");
      cur=(d.hosts||[]).filter(h=>(h.host_loading||[]).length);
      if(!cur.length){ // restore any placeholder we replaced
        document.querySelectorAll("[data-hlpatch]").forEach(el=>{el.textContent="\u00b7 no loads in flight";el.removeAttribute("data-hlpatch");});
        return; }
      const want={}; cur.forEach(h=>(h.host_loading||[]).forEach(m=>want[m]=1));
      document.querySelectorAll("#fleetPanel [class*=hint], #fleetPanel div, #fleetPanel span").forEach(el=>{
        if(el.children.length && el.textContent!=="\u00b7 no loads in flight"&&el.textContent!=="no loads in flight")return;
        if(!/no loads in flight/.test(el.textContent))return;
        // attribute to the nearest host card above this element
        let card=el, hostName="";
        for(let k=0;k<6&&card;k++){ const t=(card.textContent||""); const mm=t.match(/^(White|Black|Pale|Red)\b/); if(mm){hostName=mm[1];break;} card=card.parentElement; }
        const m=cur.find(h=>String(h.host).startsWith(hostName) && (h.host_loading||[]).length);
        if(m){ el.textContent="\u23f3 loading "+m.host_loading.join(", ")+(m.queued?" \u00b7 "+m.queued+" queued":""); el.setAttribute("data-hlpatch","1"); }
      });
    }catch(e){}
  }
  setInterval(tick,4000); setTimeout(tick,1500);
})();

// ---- Theme toggle (2026-11-22 - completes Goal #10: tokens.css had the [data-theme=light]
// family since 2026-11-17 but initTheme was never built, so the light theme was unreachable).
// Button injected into the header like printReportBtn; choice persisted per browser. ----
(function(){
  const KEY="portalTheme";
  function cur(){ let t="dark"; try{ t=localStorage.getItem(KEY)||"dark"; }catch(_){} return t==="light"?"light":"dark"; }
  window.initTheme=function(t){ if(t)try{ localStorage.setItem(KEY,t); }catch(_){}
    const v=t||cur();
    if(v==="light")document.documentElement.setAttribute("data-theme","light"); else document.documentElement.removeAttribute("data-theme"); };
  initTheme(); // apply persisted choice as early as core.js parses (script is at end of body)
  const b=document.createElement("button"); b.id="themeBtn"; b.type="button";
  b.title="Toggle light/dark theme (remembered in this browser)";
  function paint(){ let ic=''; try{ ic=(window.UI&&UI.iconSized)?(cur()==="light"?UI.iconSized("moon",14):UI.iconSized("sun",14)):''; }catch(_){}
    b.innerHTML=ic+" Theme"; }
  paint();
  b.onclick=function(){ initTheme(cur()==="light"?"dark":"light"); paint(); };
  const st=$("status"); if(st)st.parentNode.insertBefore(b,st); else { const hd=document.querySelector("header"); if(hd)hd.appendChild(b); }
})();
// ---- Keyboard shortcuts (2026-11-22): Esc closes topmost layer, "/" focuses the composer. ----
(function(){
  const PANELS=[["actBtn","actPanel"],["fleetBtn","fleetPanel"],["opsBtn","opsPanel"],["filesBtn","filesPanel"],["goalsBtn","goalsPanel"]];
  document.addEventListener("keydown",function(e){
    if(e.key==="Escape"){
      let handled=false;
      if(document.querySelector(".tour-overlay")&&window.UI&&UI.tour&&UI.tour.close){ UI.tour.close(); handled=true; }
      const ed=$("editor"); if(ed&&typeof ed.close==="function"&&ed.open){ try{ ed.close(); }catch(_){} handled=true; }
      const np=document.getElementById("notifPanel"); if(np&&!np.classList.contains("hidden")){ np.classList.add("hidden"); handled=true; }
      for(const pair of PANELS){ const p=$(pair[1]),bb=$(pair[0]); if(p&&p.classList.contains("open")&&bb){ bb.click(); handled=true; } }
      if(handled)e.preventDefault();
    } else if(e.key==="/"&&!e.ctrlKey&&!e.metaKey&&!e.altKey){
      const t=e.target,tag=t?(t.tagName||""):"";
      if(tag==="INPUT"||tag==="TEXTAREA"||tag==="SELECT"||(t&&t.isContentEditable))return;
      const inp=$("input"); if(inp){ e.preventDefault(); inp.focus(); }
    }
  });
})();
