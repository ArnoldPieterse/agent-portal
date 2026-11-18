// Agent Portal - core app logic (agents/models/chat/goals/ops panels).
// 2026-11-16 file-modularity split: extracted from index.html.
// parent: index.html | sibling: ui/uploads.js (loads AFTER this file - keep order)
// rule: memory/portal/file-modularity.md | served by GET /ui/core.js

const $ = id => document.getElementById(id);
window.onerror=(m,src,l)=>{try{$("stext").textContent="JS ERROR line "+l+": "+String(m).slice(0,80);}catch(_){}};
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
    c.innerHTML=`<span class="em">${esc(a.emoji||"🤖")}</span>
      <span class="nm"><b>${esc(a.name)}</b><span>${esc(shortModel(a.model_id))}</span></span>`;
    const g=document.createElement("button"); g.textContent="⚙"; g.title="Edit profile"; g.setAttribute("aria-label","Edit agent profile");
    g.onclick=e=>{e.stopPropagation();openEditor(a);};
    const x=document.createElement("button"); x.textContent="✕"; x.title="Delete"; x.setAttribute("aria-label","Delete agent");
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
  if(runId){ jpost('/api/run-stop',{run_id:runId}).catch(()=>{}); } }; // ■ Stop: abort solo streams / tell the backend run engine to stop cleanly (it finishes teardown + verdict)

function addBubble(name, color, emoji, isYou){
  const d=document.createElement("div");
  d.className="msg"+(isYou?" you":"");
  d.innerHTML=(isYou?"":`<div class="who" style="color:${color||"#ccc"}">${esc(emoji||"")} ${esc(name)}</div>`);
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
let roundBubbles=[];    // agent bubbles created during the current send() - stamped with ✓concluded when the round ends on [CONCLUDED]
let stopRequested=false; // ■ Stop clicked - closes the current run as concluded (user authority)
const activeCtrls=new Set(); // in-flight /api/chat streams, aborted by ■ Stop
const stripConcluded=t=>(t||"").replace(/^\[concluded\][\s:\-.\u2013\u2014]*/i,"");
const isSilent=t=>{const s=((t||"").replace(/[\u0085\u180e\u200b-\u200f\u202a-\u202e\u2060\ufeff]/g,"")).trim();if(!/^\[silent\]/i.test(s))return false;const rest=s.slice(8).replace(/^[\s:.\-\u2013\u2014]+/,"").trim();return !rest||/^(ok|okay|sure|nothing|no|fine|cool|agree)[.!]*$/i.test(rest);};

async function streamReply(agent, kind, silentTarget){
   setBusyHint(agent.name);
   try{ return await streamReplyCore(agent, kind, silentTarget); }
   finally{ clearBusyHint(agent.name); } // parallel: this stream is done even if others still run
}
async function streamReplyCore(agent, kind, silentTarget){
   const d=addBubble(agent.name, agent.color, agent.emoji, false);
   let ctrl=null; // AbortController for this stream - ■ Stop aborts it
   roundBubbles.push(d);
   if(kind==="cross-talk"){
     const chip=document.createElement("span");
     chip.style.cssText="margin-left:auto;font-size:10px;color:var(--dim)";
     chip.textContent="\u21bb agent-to-agent"; chip.title="reply to another group member (unlimited by default - finite cap only when budget OFF; ends early on [CONCLUDED])";
     d.querySelector(".who").appendChild(chip);
   }
   const body=d.querySelector(".body");
   lastConcluded=false;
   // Busy indicator: ticking "working… Ns" until the first visible frame (content/thinking/tool).
   let busyT=null, busySecs=0;
   const startBusy=()=>{ if(busyT)return; busySecs=0;
     const sp=document.createElement("span"); sp.className="busyspan"; sp.textContent="\u23f3 working\u2026 0s"; body.appendChild(sp);
     busyT=setInterval(()=>{busySecs++; if(sp.isConnected)sp.textContent="\u23f3 working\u2026 "+busySecs+"s";},1000); };
   const stopBusy=()=>{ if(busyT){clearInterval(busyT);busyT=null;} const sp=body.querySelector(".busyspan"); if(sp)sp.remove(); };
   startBusy(); // modeBar busy-hint is owned by the streamReply wrapper above
   let res;
   try{
     ctrl=new AbortController(); activeCtrls.add(ctrl);
      res=await fetch("/api/chat",{signal:ctrl.signal,method:"POST",headers:{"Content-Type":"application/json"},
       body:JSON.stringify({agent_id:agent.id, mode, kind:kind||"prompt", messages:history, session:sessionId||undefined})});
   }catch(e){ if(ctrl&&(e.name==="AbortError"||stopRequested)){ stopBusy(); return ""; } stopBusy(); addBubble("error","#ff6b6b","⚠",false).querySelector(".body").textContent=String(e); return ""; }
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
           if(o.error){ body.textContent="⚠ "+o.error; return ""; }
           if(o.blocked){ body.textContent="\u23f8 "+o.blocked; return null; }
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
             chip.textContent="🔧 "+tn; toolRow.appendChild(chip); }
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
     const chip=document.createElement("span");chip.className="conclchip";chip.style.cssText="margin-left:auto;font-size:10px;color:#3ddc84";
     chip.textContent="\u2713 concluded"; chip.title="discussion reached a natural conclusion - round ended";
     d.querySelector(".who").appendChild(chip); if(!renderDms(body,s))linkifyFiles(body,s); return s; }
   if(/stopped before completing its tool calls/i.test(full)){ // Studio harness note = turn ended MID-TASK (promised edits never ran)
     const chip=document.createElement("span");chip.className="warnchip";
     chip.style.cssText="margin-left:auto;font-size:10px;color:var(--warn)";
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
const actIcons={start:"▶",tool:"🔧",end:"✓",blocked:"⛔",error:"⚠",aborted:"■",readmem:"📖",storemem:"💾"};
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
    const col=(agents.find(a=>a.name===e.agent)||{}).color||"#ccc";
    div.innerHTML=`<span class="at">${new Date(e.ts*1000).toLocaleTimeString([],{hour12:false})}</span><span class="an" style="color:${col}">${esc(e.agent||"?")}</span><span>${actIcons[e.event]||"•"}</span><span class="ax">${esc(x)}</span>`;
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
  }catch(e){ $("actStat").textContent="⚠ "+e; }
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
  const body=$("fleetBody"), stat=$("fleetStat");
  // loading state
  body.innerHTML='<div class="fstate"><svg width="14" height="14" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="2" opacity=".3"/><path d="M8 2a6 6 0 0 1 6 6" stroke="currentColor" stroke-width="2"/></svg><span>loading…</span></div>';
  stat.textContent="";
  try{
    const o=await api("/api/fleet");
    const hosts=o.hosts||[];
    if(!hosts.length){
      body.innerHTML='<div class="fstate empty">No hosts reporting</div>';
      stat.textContent="0/0 · ttl "+(o.ttl||15)+"s";
      return;
    }
    const now=o.ts||Date.now()/1000;
    let html="";
    for(const h of hosts){
      const age=h.last_seen?Math.max(0,Math.round(now-h.last_seen)):"–";
      const st=h.state==="busy"?"busy":h.state==="idle"?"idle":"UNKNOWN";
      const models=h.models.length?h.models.map(m=>m.id+(m.quant?" ("+m.quant+")":"")).join(", "):"— none loaded —";
      html+='<div class="frow-h"><span class="fdot '+h.state+'"></span><b>'+h.host+'</b>'+
        '<span class="hint"> · '+st+(h.reason?" · "+h.reason:"")+" · last seen "+age+"s ago</span>"+
        '<div class="fmodels">'+models+'</div>'+
        '<div class="hint" style="margin-left:16px">agents: '+(h.agents.length?h.agents.join(", "):"none")+'</div></div>';
    }
    body.innerHTML=html;
    const up=hosts.filter(h=>h.state!=="unknown").length;
    stat.textContent=up+"/"+hosts.length+" reporting · ttl "+(o.ttl||15)+"s";
  }catch(e){
    body.innerHTML='<div class="fstate err"><svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1zm-.75 3.5h1.5v5h-1.5v-5zm0 6h1.5v1.5h-1.5V10.5z"/></svg><span>connection lost: "+(e.message||e)+"</span></div>';
    stat.textContent="⚠ error";
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
  }catch(e){ $("opsStat").textContent="⚠ "+e; }
  opsTiles();   // host tiles refresh with the panel (2026-11-15)
  mergeQueueLoad();   // sandbox merge queue (2026-11-16)
}
async function opsTiles(){
  try{
    const o=await (await fetch("/api/ops")).json();
    const d=o.disk||{};
    $("diskTile").textContent=(d.total_gb!=null)?`disk ${d.drive} · ${d.used_gb} GB used / ${d.total_gb} GB (${Math.round(100*d.used_gb/d.total_gb)}%)\nfree ${d.free_gb} GB`:"⚠ "+(d.error||"no disk data");
    $("uptimeTile").textContent=`portal up · ${o.uptime_hm}\npid ${o.pid} · since ${o.started}`;
  }catch(e){ $("diskTile").textContent="⚠ "+e; $("uptimeTile").textContent="⚠ "+e; }
}
async function mergeQueueLoad(){
  const el=$("mergeQueue"); if(!el)return;
  try{
    const q=await (await fetch("/api/merge-queue")).json();
    if(!q.ok){ el.textContent="⚠ "+(q.error||"error"); return; }
    const evs=(q.events||[]).slice(0,5);
    if(!evs.length){ el.textContent="(empty - no diverged sandbox code files captured)"; return; }
    const esc=s=>String(s).replace(/[&<>\"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
    el.innerHTML=evs.map(e=>'<div style="margin:2px 0">'+esc(e.ts.slice(5))+' · <b>'+esc(e.file)+'</b> sha '+esc(e.sha)+' ('+e.size+' B)'
      +' <button class="btn" data-mq="'+esc(e.file)+'" style="padding:1px 8px;font-size:11px">↩ restore</button></div>').join("");
    el.querySelectorAll("button[data-mq]").forEach(b=>b.onclick=async()=>{
      opsSay("restoring "+b.dataset.mq+"…");
      try{ const r=await (await fetch("/api/merge",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({file:b.dataset.mq})})).json();
        opsSay(r.ok?"✓ restored "+r.file+" from snapshot "+r.snapshot+(r.committed?" (committed)":""):"⚠ "+(r.error||"restore failed"));
      }catch(e2){ opsSay("⚠ "+e2); } finally{ mergeQueueLoad(); }
    });
  }catch(e){ el.textContent="⚠ "+e; }
}
$("opsBtn").onclick=()=>{ const open=$("opsPanel").classList.toggle("open"); $("opsBtn").classList.toggle("on",open); if(open)opsLoad(); };
async function opsSay(t){ $("opsMsg").textContent=t; }
$("gitCommit").onclick=async()=>{
  const m=$("gitMsg").value.trim(); if(!m){ opsSay("type a commit message first"); return; }
  opsSay("committing…");
  try{ const r=await (await fetch("/api/git",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({action:"commit",message:m})})).json();
    if(r.status&&r.status.repo){ $("gitStatus").textContent=r.status.status||"(clean)"; $("gitLog").textContent=r.status.log||"—"; }
    opsSay(r.committed?"✓ committed: "+m:(r.note||r.err||"done")); if(r.committed)$("gitMsg").value="";
  }catch(e){ opsSay("⚠ "+e); } finally{ opsLoad(); }
};
$("gitMsg").addEventListener("keydown",e=>{if(e.key==="Enter"){e.preventDefault();$("gitCommit").click();}});
$("todoPrune").onclick=async()=>{
  opsSay("pruning…");
  try{ const r=await (await fetch("/api/todo/prune",{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"})).json();
    opsSay(r.moved_sections?`✓ moved ${r.moved_sections} section(s), ${r.moved_items} item(s) → TODO_completed.md (${r.completed_lines} lines${r.chunks_split?", split "+r.chunks_split+" part(s)":""})`:(r.note||"done"));
  }catch(e){ opsSay("⚠ "+e); }
};
