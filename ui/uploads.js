// Agent Portal - uploads panel (files & folders -> shared agent folder via POST /api/upload).
// 2026-11-16 file-modularity split: extracted from index.html.
// parent: index.html | sibling: ui/core.js (loads BEFORE this file - keep order)
// rule: memory/portal/file-modularity.md | served by GET /ui/uploads.js

// ---- Uploads: files & folders -> shared agent folder (uploads/) via POST /api/upload ----
const attachBtn=$("attach"), amenu=$("attachMenu"), filePick=$("filePick"), dirPick=$("dirPick");
let pendingUploads=[];   // {rel, size, state:'uploading'|'done'|'error', pct, err, xhr}
function fmtSize(n){ if(n==null)return""; if(n>=1048576)return (n/1048576).toFixed(1)+" MB"; if(n>=1024)return (n/1024).toFixed(1)+" KB"; return n+" B"; }
function chipRow(){ let r=$("chips"); if(!r){ r=document.createElement("div"); r.id="chips"; $("composer").insertBefore(r,$("input")); } return r; }
function renderChips(){ const r=chipRow(); r.innerHTML="";
  for(const u of pendingUploads){ const c=document.createElement("span"); c.className="chipfile";
    const nm=document.createElement("span"); nm.className="nm"; nm.textContent=u.rel; nm.title=u.rel;
    const sz=document.createElement("span"); sz.className="sz"; sz.textContent=fmtSize(u.size);
    const st=document.createElement("span"); st.className="st"+(u.state==="error"?" err":"");
    st.textContent = u.state==="uploading" ? (u.pct??0)+"%" : (u.state==="done" ? "\u2713" : ("\u2717 "+(u.err||"failed")));
    const x=document.createElement("button"); x.textContent="\u2715"; x.title="remove";
    x.onclick=()=>{ if(u.xhr&&u.state==="uploading")u.xhr.abort(); pendingUploads=pendingUploads.filter(v=>v!==u); renderChips(); };
    c.append(nm,sz,st,x); r.appendChild(c); }
  if(!busy)$("send").disabled=pendingUploads.some(u=>u.state==="uploading"); }
function uploadFile(rel, blob, size){ const u={rel,size:(size!=null?size:blob.size),state:"uploading",pct:0}; pendingUploads.push(u); renderChips();
  const xhr=new XMLHttpRequest(); u.xhr=xhr;
  xhr.upload.onprogress=e=>{ if(e.lengthComputable){ u.pct=Math.round(100*e.loaded/e.total); renderChips(); } };
  xhr.onload=()=>{ if(xhr.status===201||xhr.status===200){ u.state="done"; u.pct=100; if(typeof window.notify==="function")window.notify("ok","Upload complete: "+u.rel); }
    else { u.state="error"; try{u.err=JSON.parse(xhr.responseText).error||("HTTP "+xhr.status);}catch(_){u.err="HTTP "+xhr.status;} } renderChips(); };
  xhr.onerror=()=>{ u.state="error"; u.err="network"; if(typeof window.notify==="function")window.notify("err","Upload failed: "+u.rel); renderChips(); };
  xhr.open("POST","/api/upload"); xhr.setRequestHeader("X-Rel-Path",encodeURIComponent(rel)); xhr.send(blob); }
attachBtn.onclick=e=>{ e.stopPropagation(); amenu.hidden=!amenu.hidden; };
document.addEventListener("click",e=>{ if(!e.target.closest("#attachWrap"))amenu.hidden=true; });
amenu.querySelector('[data-act="files"]').onclick=()=>{ amenu.hidden=true; filePick.click(); };
amenu.querySelector('[data-act="folder"]').onclick=()=>{ amenu.hidden=true; dirPick.click(); };
filePick.onchange=()=>{ for(const f of filePick.files) uploadFile("uploads/"+f.name.replace(/\\/g,"/"), f, f.size); filePick.value=""; };
dirPick.onchange=()=>{ for(const f of dirPick.files) uploadFile("uploads/"+f.webkitRelativePath.replace(/\\/g,"/"), f, f.size); dirPick.value=""; }
// Drag & drop: files and folders (folders walked recursively via webkitGetAsEntry)
const composerEl=$("composer");
["dragenter","dragover"].forEach(ev=>composerEl.addEventListener(ev,e=>{ e.preventDefault(); composerEl.classList.add("dragover"); }));
composerEl.addEventListener("dragleave",e=>{ if(e.relatedTarget&&composerEl.contains(e.relatedTarget))return; composerEl.classList.remove("dragover"); });
composerEl.addEventListener("drop",async e=>{ e.preventDefault(); composerEl.classList.remove("dragover");
  const entries=[...e.dataTransfer.items].map(i=>i.webkitGetAsEntry?i.webkitGetAsEntry():null).filter(Boolean);
  if(!entries.length){ for(const f of e.dataTransfer.files) uploadFile("uploads/"+f.name.replace(/\\/g,"/"), f, f.size); return; }
  for(const en of entries) await walkEntry(en, "uploads/"+en.name); });
async function readAllEntries(rd){ const all=[]; let batch; do{ batch=[]; await new Promise(r=>rd.readEntries(batch,r)); all.push(...batch); }while(batch.length>0); return all; }
async function walkEntry(en, rel){ if(en.isFile){ en.file(f=>uploadFile(rel, f, f.size), ()=>{}); }
  else if(en.isDirectory){ const kids=await readAllEntries(en.createReader()); for(const k of kids) await walkEntry(k, rel+"/"+k.name); } }
function attachLine(){ const done=pendingUploads.filter(u=>u.state==="done"); if(!done.length)return "";
  const list=done.slice(0,15).map(u=>u.rel+(u.size!=null?" ("+fmtSize(u.size)+")":"") );
  let s="\n\n[Attached in shared folder: "+list.join(", ")+(done.length>15?" \u2026and "+(done.length-15)+" more files":"")+"]";
  const failed=pendingUploads.filter(u=>u.state==="error").length; if(failed)s+=(" ("+failed+" upload(s) failed - not attached)"); return s; }

async function send(){
  if(busy){ const t=$("input").value.trim(); if(t){queueMsg(t); $("input").value="";} return; }
  let text=$("input").value.trim();
  const attLine=attachLine();
  if(!text&&!attLine)return;
  if(attLine)text+=(text?"\n\n":"")+attLine;
  pendingUploads=[]; renderChips();   // attachments captured into the message now
  const me=agents.find(a=>a.id===selectedId);
  if(mode==="solo"&&!me)return;
  stickOn=true;   // re-pin auto-scroll on every human send
  history.push({speaker:"You",content:text});
  addBubble("You","",null,true).querySelector(".body").textContent=text;
  $("input").value=""; busy=true; setSendQueued(true); startHeartbeat(); startStallPoll();
  roundBubbles=[]; // fresh per human prompt (also bounds memory in solo mode)
  sessionId=(mode==="group"?"g":"s")+"-"+Date.now().toString(36)+"-"+Math.random().toString(36).slice(2,7); actFollow();
  noOutputNames.clear(); stopRequested=false; activeCtrls.clear();
  let adopted=false;   // true if we adopt an already-live backend run instead of starting one
  try{
    if(mode==="solo"){
      const full=await streamReply(me);
      if(full)history.push({speaker:me.name,content:full});
    }else{
      // GROUP RUNS ARE BACKEND-OWNED (2026-11-15): the whole pass/cross-talk/nudge loop runs in a
      // portal daemon thread; we only attach to its journaled SSE stream. A hard refresh no longer
      // cancels anything - bootRestore re-attaches below and replays from the journal.
      const resp=await fetch("/api/group-run",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text})});
      const j=await resp.json().catch(()=>({}));
      if(!resp.ok){ throw new Error((j&&j.error)||("group run start failed (HTTP "+resp.status+")")); }
      sessionId=j.run_id; actFollow();
      await attachRun(j.run_id);
    }
  }catch(e){
    const em=String(e);
    const m2=/group run is already in progress \((g-[a-z0-9]+-[a-f0-9]+)\)/i.exec(em);
    if(mode==="group"&&m2){
      // A backend run is already live (scheduled task / another tab started it while this one
      // was idle): adopt it instead of showing a dead-end error, and route the message through
      // the UMQ where agents pick it up on their next prompt build.
      adopted=true;
      adoptLiveRun({run_id:m2[1],busy:true},()=>{
        addBubble("queued","var(--agent-purple)","\u2709",false).querySelector(".body").textContent=
          "group run already in progress - attached to its live output; your message is queued and the agents will pick it up";
      });
      queueMsg(text);
    }else{ addBubble("error","var(--err)","!",false).querySelector(".body").textContent=em; }
  }
  if(adopted){ umqPoll(); renderQueue(); return; }   // keep busy/heartbeat for the adopted run
  busy=false; busyNames.clear(); renderBusyHint(); setSendQueued(false); stopStallPoll(); $("input").focus(); stopHeartbeat(); saveHistoryServer(true); umqPoll(); renderQueue();
}

// ---- Backend group-run attachment (2026-11-15) ----
// The run engine lives in agent_portal.py; /api/run-events replays the journaled SSE frames
// from seq 0 and live-tails them. Re-rendering here mirrors streamReplyCore's bubble semantics.
let runId=null, runCtrl=null;
const runTurns={};   // agent name -> per-turn render state for the current phase
function runTurn(agentName,kind){
  const ag=agents.find(a=>a.name===agentName);
  const d=addBubble(ag?ag.name:agentName,ag?ag.color:'var(--queue-dim)',ag?ag.emoji:'\ud83e\udd16',false);
  if(kind==="cross-talk"){
    const chip=document.createElement("span");
    chip.style.cssText="margin-left:auto;font-size:var(--fs-12);color:var(--dim)";
    chip.textContent="\u21bb agent-to-agent"; chip.title="reply to another group member";
    d.querySelector(".who").appendChild(chip); }
  const body=d.querySelector(".body");
  let busyT=null,secs=0;
  const sp=document.createElement("span");sp.className="busyspan";sp.textContent="\u23f3 working\u2026 0s";body.appendChild(sp);
  busyT=setInterval(()=>{secs++;if(sp.isConnected)sp.textContent="working\u2026 "+secs+"s";},1000);
  const t={d,body,thinkEl:null,toolRow:null,full:"",stopBusy(){ if(busyT){clearInterval(busyT);busyT=null;} const s=body.querySelector(".busyspan"); if(s)s.remove(); }};
  runTurns[agentName]=t; return t;
}
function runFinishTurn(agentName,kind){
  const t=runTurns[agentName]; if(!t)return "";
  t.stopBusy();
  const full=t.full;
  delete runTurns[agentName];
  if(isSilent(full)){ t.d.remove(); return ""; }   // silence: merge out (round-end notes cover it)
  if(/stopped before completing its tool calls/i.test(full)){
    const chip=document.createElement("span");chip.className="warnchip";
    chip.style.cssText="margin-left:auto;font-size:var(--fs-12);color:var(--warn)";
    chip.textContent="\u26a0 tool calls truncated - task incomplete";
    t.d.querySelector(".who").appendChild(chip); }
  if(!full.trim()){ t.body.textContent="\u2014 (no output) \u2014"; t.body.style.color="var(--dim)"; return ""; }
  const s=stripConcluded(full);
  t.body.textContent=s;
  if(!renderDms(t.body,s))linkifyFiles(t.body,s);
  history.push({speaker:agentName,content:full});
  return full;
}
function handleRunEvent(ev){
  if(ev.run==="start")return;   // human prompt bubble already exists (local send) or came from restored history
  if(ev.run==="nudge"){
    history.push({speaker:"You",content:ev.text});
    addBubble("auto-continue","var(--agent-purple)","\u21bb",false).querySelector(".body").textContent=ev.text; stickScroll(); return; }
  if(ev.run==="phase")return;
  if(ev.run==="end"){
    const v=ev.verdict||{};
    if(v.note){ const w=document.createElement("div");w.className="thinkwrap";
      const p=document.createElement("div");p.className="roundend "+(v.cls||"dim");p.textContent=v.note;
      w.appendChild(p);$("msgs").appendChild(w);stickScroll(); }
    return; }
  if(ev.turn){ runTurn(ev.agent,ev.kind); return; }
  if(ev.done){ runFinishTurn(ev.agent,ev.kind); return; }
  if(ev.frame){
    const t=runTurns[ev.agent]; if(!t)return;
    const o=ev.frame;
    if(o.error){ t.stopBusy(); t.body.textContent="\u26a0 "+o.error; delete runTurns[ev.agent]; return; }
    if(o.blocked){ t.stopBusy(); t.body.textContent="\u23f8 "+o.blocked; delete runTurns[ev.agent]; return; }
    if(o.model_load){ let ln=t.d.querySelector(".loadnote"); if(!ln){ln=document.createElement("div");ln.className="loadnote";t.d.appendChild(ln);} ln.textContent="\u23f3 "+o.model_load; stickScroll(); return; }
    if(o.meta){ if(typeof o.meta.inter_agent_replies==="number")setXtalk(o.meta.inter_agent_replies,o.meta.limit);
      if(o.meta.concluded){ lastConcluded=true;
        const chip=document.createElement("span");chip.className="conclchip";
        chip.style.cssText="margin-left:auto;font-size:var(--fs-12);color:var(--ok)";chip.textContent="\u2713 concluded";
        t.d.querySelector(".who").appendChild(chip); } }
    if(o.content){ t.stopBusy(); t.full+=o.content; t.body.textContent=t.full; stickScroll(); }
    if(o.thinking){ if(!t.thinkEl){t.thinkEl=document.createElement("details");t.thinkEl.className="think";
      const s=document.createElement("summary");s.textContent="thinking";
      const tb=document.createElement("div");tb.className="tbody";t.thinkEl.append(s,tb);t.d.appendChild(t.thinkEl);}
      t.stopBusy(); t.thinkEl.querySelector(".tbody").textContent+=o.thinking; stickScroll(); }
    if(o.tool){ t.stopBusy(); if(!t.toolRow){t.toolRow=document.createElement("div");t.d.appendChild(t.toolRow);}
      const chip=document.createElement("span");chip.className="toolchip";
      const tn=o.tool.name||(o.tool.function&&o.tool.function.name)||"tool";
      chip.textContent="\ud83d\udee0 "+tn; t.toolRow.appendChild(chip); }
    return; }
}
let runLastSeq=0, attachedRunId=null; // cursor continuity across re-attaches (2026-11-15)
async function attachRun(rid, startCursor){
  runId=rid;
  if(runCtrl){try{runCtrl.abort();}catch(e){}}
  runCtrl=new AbortController();
  await new Promise(res=>{
    (async()=>{
      try{
        const resp=await fetch("/api/run-events?run="+encodeURIComponent(rid)+"&cursor="+(startCursor||0),{signal:runCtrl.signal});
        if(!resp.ok)throw new Error("run stream HTTP "+resp.status);
        const reader=resp.body.getReader();const dec=new TextDecoder();let buf="";
        // Fast-forward (2026-11-15): re-attaching to a run that's been going a while used to
        // replay every token frame from seq 0 (multi-MB journal -> minutes of frozen UI, no
        // visible "current progress"). Now frames older than ~60s are skipped for DOM purposes
        // (their text is kept in history) and the live turn's bubble is recreated, so CURRENT
        // output shows within seconds.
        const cutoff=Date.now()-60000;
        let fast=true, skipped=0, ffText={}, pendingTurn={};
        while(true){
          const {done,value}=await reader.read();if(done)break;
          buf+=dec.decode(value,{stream:true});
          let idx;
          while((idx=buf.indexOf("\n\n"))>=0){
            const chunk=buf.slice(0,idx);buf=buf.slice(idx+2);
            for(const line of chunk.split("\n")){
              if(!line.startsWith("data: "))continue;
              let ev;try{ev=JSON.parse(line.slice(6));}catch(e){continue;}
              if(typeof ev.seq==="number"&&ev.seq>runLastSeq)runLastSeq=ev.seq;
              const old=fast&&typeof ev.ts==="number"&&ev.ts<cutoff&&ev.run!=="end";
              if(old){
                skipped++;
                if(ev.turn)pendingTurn[ev.agent]=ev.kind;
                else if(ev.done){const tx=ffText[ev.agent]||"";if(!isSilent(tx))history.push({speaker:ev.agent,content:tx});delete pendingTurn[ev.agent];delete ffText[ev.agent];}
                else if(ev.frame&&ev.frame.content)ffText[ev.agent]=(ffText[ev.agent]||"")+ev.frame.content;
                continue;
              }
              fast=false;
              if(skipped>0){const w=document.createElement("div");w.className="thinkwrap";
                const p=document.createElement("div");p.className="roundend dim";
                p.textContent="\u23e9 fast-forwarded "+skipped+" earlier frames - showing recent + live output";
                w.appendChild(p);$("msgs").appendChild(w);stickScroll();skipped=0;}
              if(ev.frame&&ev.agent&&!runTurns[ev.agent]&&pendingTurn[ev.agent]){
                runTurn(ev.agent,pendingTurn[ev.agent]);delete pendingTurn[ev.agent];}
              handleRunEvent(ev);
            }
          }
        }
      }catch(e){ if(!(e&&e.name==="AbortError"))addBubble("error","var(--err)","\u26a0",false).querySelector(".body").textContent="run stream lost: "+e; }
      finally{ res(); }
    })();
  });
  runId=null;
}

let editingId=null;
function openEditor(a){
  editingId=a?a.id:null;
  $("edTitle").textContent=a?("Edit "+a.name):"New agent";
  $("f_name").value=a?.name||""; $("f_emoji").value=(a?.emoji||""); $("f_color").value=a?.color||"var(--ok)";
  $("f_blurb").value=a?.blurb||""; $("f_persona").value=a?.persona||"";
  const net=!!a?.studio;                                  // networked = agent has a remote studio base URL
  $("f_net").checked=net; $("f_studio").value=a?.studio||""; $("f_key").value=a?.api_key||"";
  $("f_ragstudio").value=a?.rag_studio||""; $("f_ragkey").value=a?.rag_api_key||"";
  $("f_scanstat").textContent=""; $("netFields").style.display=net?"":"none";
  if(net){ netModels=[]; populateModelSelect([],a?.model_id||""); scanModels(true); }   // live rescan of that host
  else { netModels=[]; populateModelSelect(models,a?.model_id||""); }
  $("f_temp").value=a?.temperature??0.7; $("f_maxtok").value=a?.max_tokens??0;
  $("f_reasoning").value=a?.reasoning||"default"; $("f_maxtools").value=a?.max_tool_calls??0;
  const tc=$("f_tools"); tc.innerHTML="";
  for(const t of localTools){const l=document.createElement("label");const c=document.createElement("input");
    c.type="checkbox";c.value=t;c.checked=(a?.tools||[]).includes(t);l.append(c,document.createTextNode(t));tc.appendChild(l);}
  $("f_runlocal").checked=a?!!(a.run_tools_local??true):true;
  $("f_rag").checked=!!a?.rag;
  $("f_memcycle").checked=(a?.mem_cycle??true); $("f_fastfirst").checked=(a?.fast_first_reply??true);
  const kb=$("f_kb"); kb.innerHTML='<option value="">(any / default knowledge base)</option>';
  for(const k of kbs){const o=document.createElement("option");o.value=k.id||k.kb_id||"";
    o.textContent=k.name||k.title||o.value;if(a?.rag_kb_id&&o.value===a.rag_kb_id)o.selected=true;kb.appendChild(o);}
  $("editor").showModal();
}
function populateModelSelect(list, cur){
  const sel=$("f_model"); sel.innerHTML="";
  for(const m of list){const o=document.createElement("option");o.value=m.id;o.textContent=m.id;if(m.id===cur)o.selected=true;sel.appendChild(o);}
  if(cur&&!list.find(m=>m.id===cur)){const o=document.createElement("option");o.value=cur;o.textContent=cur+" (current)";o.selected=true;sel.appendChild(o);}
}
async function scanModels(){
  const base=$("f_studio").value.trim(), key=$("f_key").value.trim();
  const st=$("f_scanstat");
  if(!base){ st.style.color="var(--warn)"; st.textContent="enter the Studio base URL first"; return; }
  $("f_scan").disabled=true; st.style.color=""; st.textContent="scanning "+base+" …";
  try{
    const r=await jpost("/api/scan-models",{base_url:base,api_key:key});
    const list=r.data||[];
    if(r.error&&list.length===0){ throw new Error(r.error); }
    netModels=list; populateModelSelect(list,$("f_model").value||"");
    st.style.color="var(--ok)"; st.textContent="found "+list.length+" model(s) on that host";
  }catch(e){ st.style.color="var(--err)"; st.textContent="scan failed: "+String(e).slice(0,90); }
  $("f_scan").disabled=false;
}
$("f_net").onchange=()=>{
  const net=$("f_net").checked;
  $("netFields").style.display=net?"":"none";
  if(net){ netModels=[]; populateModelSelect([],$("f_model").value||""); scanModels(); }
  else { netModels=[]; $("f_scanstat").textContent=""; populateModelSelect(models,$("f_model").value||""); }
};
$("f_scan").onclick=()=>scanModels();

$("edSave").onclick=async()=>{
  const b={name:$("f_name").value,emoji:$("f_emoji").value,color:$("f_color").value,blurb:$("f_blurb").value,
    persona:$("f_persona").value,model_id:$("f_model").value,temperature:parseFloat($("f_temp").value)||0,
    max_tokens:parseInt($("f_maxtok").value)||0,reasoning:$("f_reasoning").value,max_tool_calls:parseInt($("f_maxtools").value)||0,
    tools:[...document.querySelectorAll("#f_tools input:checked")].map(i=>i.value),run_tools_locally:$("f_runlocal").checked,
    rag:$("f_rag").checked,rag_kb_id:$("f_kb").value,
    mem_cycle:$("f_memcycle").checked,fast_first_reply:$("f_fastfirst").checked,
    studio:$("f_net").checked?$("f_studio").value.trim():"",
    api_key:$("f_net").checked?$("f_key").value.trim():"",
    rag_studio:$("f_net").checked?$("f_ragstudio").value.trim():"",
    rag_api_key:$("f_net").checked?$("f_ragkey").value.trim():""};
  if(!b.name.trim())return alert("Name is required");
  if(!b.model_id)return alert($("f_net").checked?"No model selected - click Scan models first":"No model available in the local Studio");
  if(editingId)await jput("/api/agents/"+editingId,b); else await jpost("/api/agents",b);
  $("editor").close(); refresh();
};
$("edClose").onclick=$("edCancel").onclick=()=>$("editor").close();
$("addAgent").onclick=()=>openEditor(null);

function setMode(m){mode=m;$("mSolo").classList.toggle("on",m==="solo");$("mGroup").classList.toggle("on",m==="group");updateHint();resetChat();restoreMsgs();}
$("mSolo").onclick=()=>setMode("solo"); $("mGroup").onclick=()=>setMode("group");
new MutationObserver(scheduleSave).observe($("msgs"),{childList:true,subtree:true,charData:true}); // per-mode persistence (2026-11-13)
// Reset mechanism: one button clears ALL conversational state - client history + bubbles,
// and the shared agent-to-agent counter (memory.md state line) via the existing endpoint.
$("resetBtn").onclick=async()=>{
  if(busy){ alert("A reply is still streaming - wait for it to finish (or reload the page), then reset."); return; }
  if(!confirm("Reset conversation?\nClears chat history and the agent-to-agent counter."))return;
  try{ const r=await jpost("/api/memory",{action:"reset"}); xtalkMax=0; setXtalk(0,r.limit); }
  catch(e){ alert("Counter reset failed: "+e); return; }
  resetChat();
  try{ localStorage.removeItem(lsKey()); }catch(e){} // \u21ba Reset clears this mode's persistence slot
};

async function pollStatus(){
  try{const s=await api("/api/status");
    const on=!s.error;
    $("sdot").classList.toggle("on",on);
    $("stext").textContent=on?("studio connected"+(s.model?": "+String(s.model).slice(-30):"")):("studio offline: "+String(s.error||"").slice(0,60));
  }catch(e){$("sdot").classList.remove("on");$("stext").textContent="studio unreachable: "+String(e).slice(0,50);}
}

$("send").onclick=send;
$("input").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send();}});
refresh().catch(e=>console.error("refresh failed",e)).finally(updateHint).finally(bootRestore);
pollStatus();
setInterval(pollStatus,15000);
setInterval(()=>{refresh().catch(()=>{});},30000);
// ---- Files panel (/api/uploads, A2 11-13 Designer): load-on-open + ↻ only (no polling) ----
function fsFmtSize(b){return b==null?"":b<1024?b+" B":b<1048576?(b/1024).toFixed(1)+" KB":(b/1048576).toFixed(1)+" MB";}
function fsFmtTime(t){const d=new Date(t*1000),n=new Date();let s=d.toTimeString().slice(0,5);if(d.toDateString()!==n.toDateString())s=d.toLocaleDateString();return s;}
async function filesLoad(){
  const list=$("filesList");list.innerHTML=(typeof UI!=="undefined")?'<li class="skel-li">'+UI.skeleton(6,12)+'</li>':'<li class="fs-empty">loading…</li>';
  try{
    const j=await (await fetch("/api/uploads")).json();
    const files=(j&&j.files)||[];
    if(!files.length){ list.innerHTML=""; const _li=document.createElement("li"); _li.innerHTML=(typeof UI!=="undefined")?UI.emptyState({icon:"upload",title:"No uploads yet",msg:"Drop files into the composer or uploads/ on White.",ctaLabel:"+ Upload"}):'<span class="fs-empty">No uploads yet</span>'; list.appendChild(_li); const _ct=_li.querySelector(".empty-cta"); if(_ct)_ct.onclick=function(){ const inp=document.querySelector('input[type="file"]'); if(inp)inp.click(); else { const cm=$("composer"); if(cm)cm.focus(); } }; return; }
    list.innerHTML='';
    for(const f of files){
      const li=document.createElement("li");
      const a=document.createElement("a");a.href="/api/file/raw?path="+encodeURIComponent(f.path);a.target="_blank";a.textContent=f.path.replace(/^uploads\//,"");
      const m=document.createElement("span");m.className="fs-meta";m.textContent=fsFmtSize(f.size)+" · "+fsFmtTime(f.mtime);
      li.appendChild(a);li.appendChild(m);list.appendChild(li);
    }
    if(j.count>files.length){const e=document.createElement("li");e.className="fs-empty";e.textContent="… "+(j.count-files.length)+" more (cap 2000)";list.appendChild(e);}
  }catch(err){list.innerHTML='<li class="fs-empty">/api/uploads unreachable — portal down?</li>';}
}
$("filesBtn").onclick=()=>{const open=$("filesPanel").classList.toggle("open");$("filesBtn").classList.toggle("on",open);if(open)filesLoad();};
// ---- Goals panel (2026-11-15, Designer): Goal Velocity dashboard ----
// Round-topic mount node (P1, 2026-11-22): created from JS so index.html stays untouched.
{ const _tp=$("goalsPanel"); if(_tp&&!$("topicBody")&&$("goalsGit")){ const tb=document.createElement("div"); tb.id="topicBody"; _tp.insertBefore(tb,$("goalsGit")); } }
async function goalsLoad(){
  { const _gb=$("goalsBody"); if(_gb&&(typeof UI!=="undefined")&&!_gb.dataset.loaded)_gb.innerHTML=UI.skeleton(3,52); }
  try{
    const o=await (await fetch("/api/goals")).json();
    if(!o.ok){ $("goalsStat").textContent="error: "+(o.error||"error"); return; }
    const C=119.38; let html="";
    for(const a of o.agents){
      const pct=a.total?Math.round(100*a.done/a.total):0;
      const off=(C*(1-pct/100)).toFixed(1);
      html+='<div class="gtile"><div class="gring"><svg width="44" height="44" viewBox="0 0 44 44">'
        +'<circle cx="22" cy="22" r="19" fill="none" stroke="var(--line)" stroke-width="4"/>'
        +'<circle cx="22" cy="22" r="19" fill="none" stroke="'+(pct>=100?'var(--ok)':'var(--acc)')+'" stroke-width="4" stroke-linecap="round" stroke-dasharray="'+C+'" stroke-dashoffset="'+off+'"/>'
        +'</svg><span class="pct">'+pct+'%</span></div>'
        +'<div><div class="gname">'+a.agent+'</div><div class="gmeta">'+a.done+'/'+a.total+' done · '+a.open+' open'
        +(a.blocked?' · <span class="gblock">'+a.blocked+' blocked</span>':'')+'</div></div></div>';
    }
    const _pg=window._goalsPrev||{}; for(const a of (o.agents||[])){ if(_pg[a.agent]!=null && a.done>_pg[a.agent] && typeof window.notify==="function") window.notify("ok","Goal closed on "+a.agent+" ("+a.done+"/"+a.total+")"); }
    window._goalsPrev=Object.fromEntries((o.agents||[]).map(a=>[a.agent,a.done]));
    $("goalsBody").dataset.loaded="1";
    const lv=(Number.isFinite(+o.level))?+o.level:0, cyc=+o.level_cycles||0;
    const lvl='<div class="lvl-banner'+(lv>0?'':' zero')+'"><div class="lvl-num">Level '+lv+'</div>'
      +'<div class="lvl-sub">'+(cyc?('<b>'+cyc+'</b> goal cycle'+(cyc>1?'s':'')+' completed &middot; '):'')
      +'levels up when ALL goals reach 100% on a fresh goal set &middot; latest report: '
      +(o.latest_level_report?'<a href="/api/file/raw?path='+encodeURIComponent(o.latest_level_report)+'" target="_blank">'+esc(o.latest_level_report)+'</a>'
        :'<span class="hint">none yet</span>')+'</div></div>';
    $("goalsBody").innerHTML=lvl+(html||((typeof UI!=="undefined")?UI.emptyState({icon:"goal",title:"No goals set",msg:"Goal files live in memory/goals/ on each host.",ctaLabel:"Open TODO.md"}):'<div class="hint">no goal files</div>'));
    { const _ct=$("goalsBody").querySelector(".empty-cta"); if(_ct)_ct.onclick=function(){ const cm=$("composer"); if(cm)cm.focus(); }; }
    $("goalsStat").textContent=o.fleet_done+"/"+o.fleet_total+" · fleet "+(o.fleet_pct||0)+"%";
    if(typeof renderGoalBar==="function")renderGoalBar(o);
    // Round topic + queue (P1, 2026-11-22): current round focus; user can queue topics that
    // steer the goal-setting focus of following rounds.
    fetch("/api/goals/topic").then(r=>r.json()).then(rt=>{
      const el=$("topicBody"); if(!el||!rt.ok)return;
      let h="";
      const c=rt.current;
      h+='<div class="topic-card'+(c?'':' zero')+'"><div class="topic-k">Round topic</div>'
        +(c?('<div class="topic-t">'+esc(c.topic)+'</div><div class="topic-d">'+esc(c.description||"")+'</div>')
           :'<div class="topic-d hint">none set yet - the Orchestrator sets one each goal round, or queue one below</div>')+'</div>';
      const q=rt.queue||[];
      if(q.length){ h+='<div class="topic-q">'+q.map((x,i)=>'<span class="topic-qi" title="'+esc(x.description||"")+'">'+esc(x.topic)+'<button data-ti="'+i+'" title="Remove from queue">&times;</button></span>').join("")+'</div>'; }
      h+='<div class="topic-form"><input id="topicIn" placeholder="Topic for a future round (short name)…" maxlength="120">'
        +'<input id="topicDesc" placeholder="Short paragraph - what this focus should cover (optional)" maxlength="400">'
        +'<button class="btn" id="topicQueueBtn">Queue</button><span id="topicMsg" class="hint"></span></div>';
      el.innerHTML=h;
      el.querySelectorAll(".topic-qi button").forEach(b=>b.onclick=()=>{ jpost("/api/goals/topic",{action:"remove",index:+b.dataset.ti}).then(()=>goalsLoad()).catch(()=>{}); });
      const qb=$("topicQueueBtn"); if(qb)qb.onclick=async()=>{
        const tv=$("topicIn").value.trim(), dsc=$("topicDesc").value.trim();
        const msg=$("topicMsg");
        if(!tv){ msg.textContent="topic required"; return; }
        try{ const r=await jpost("/api/goals/topic",{action:"queue",topic:tv,description:dsc});
          msg.textContent=r.ok?"queued - steers the next goal round":"error: "+(r.error||""); goalsLoad(); }catch(e){ msg.textContent="error: "+e; } };
    }).catch(()=>{});
    // Git-based progress curve + stall signal (2026-11-16): goals are registered in git,
    // so the history IS the progress tracker.
    fetch("/api/goals/history").then(r=>r.json()).then(h=>{
      const el=$("goalsGit"); if(!el)return;
      if(!h.ok){ el.textContent="git progress: n/a ("+(h.error||"no repo")+")"; return; }
      const s=h.series||[]; let t="git progress (last "+(h.commits_scanned||0)+" commits): ";
      if(s.length){
        t+=s.map(x=>x.fleet_reached).join(" \u2192 ")+" \u2192 "+o.fleet_done+"/"+o.fleet_total;
        if(h.last_change_commit) t+=" \u00b7 last goal change "+h.last_change_commit.sha+" "+String(h.last_change_commit.ts).slice(5,16);
      } else t+="no goal-file changes in window";
      if((h.stall_commits||0)>3) t+=" \u00b7 STALLED: "+h.stall_commits+" commits since last goal change";
      el.textContent=t;
    }).catch(()=>{});
    // Memory Health section (Scribe goal 9, re-landed 2026-11-17): six metric cards live from /api/memory-health.
    fetch("/api/memory-health").then(r=>r.json()).then(o=>{
      const el=$("memHealthBody"); if(!el||!o.ok)return;
      const st={pass:"var(--ok)",warn:"var(--warn)",fail:"var(--err)"};
      el.innerHTML=Object.entries(o.metrics).map(([k,v])=>'<div class="mh-card" style="border-color:'+(st[v.status]||"var(--line)")+'">'
        +'<div class="mh-k">'+k+'</div><div class="mh-v">'+(v.value==null?"n/a":v.value)+'</div>'
        +'<div class="mh-d">'+(v.detail||"")+'</div></div>').join("");
    }).catch(()=>{});
  }catch(e){ $("goalsStat").textContent="error: "+e; }
}
$("goalsBtn").onclick=()=>{ const open=$("goalsPanel").classList.toggle("open"); $("goalsBtn").classList.toggle("on",open); if(open)goalsLoad(); };
// Header goal bar + Lv chip must render on page load, not only after a Goals-tab click (2026-11-22, found by Playwright test):
fetch("/api/goals").then(r=>r.json()).then(o=>{ if(o&&o.ok&&typeof renderGoalBar==="function")renderGoalBar(o); }).catch(()=>{});

$("filesRefresh").onclick=filesLoad;

// ================= USER MESSAGE QUEUE + REFRESH-SAFE STATE (2026-11-15) =================
// Human messages sent while the group is working are queued in user_messages.json
// (backend /api/user-messages). Each agent's portal prompt build injects its pending
// entries and flips its own checked flag once the request reaches Studio. The panel
// below spins per message until every in-scope agent has seen it; when idle, pending
// messages are delivered automatically as normal sends.
let lastUmq={messages:[]}; let delivering=false; let _histSig='';
function umqScope(m){const all=agents.map(a=>a.name);return ((m.mentions&&m.mentions.length)?m.mentions:all).filter(n=>all.includes(n));}
function umqDone(m){const s=umqScope(m);return !s.length||s.every(n=>(m.checked||{})[n]);}
function renderQueue(){
  const panel=$('queuePanel'),list=$('queueList');if(!panel)return;
  const rows=(lastUmq.messages||[]).filter(m=>!umqDone(m)).slice(-12);
  panel.classList.toggle('has',rows.length>0);list.innerHTML='';
  for(const m of rows){
    const s=umqScope(m),seen=s.filter(n=>(m.checked||{})[n]).length;
    const row=document.createElement('div');row.className='qrow';
    const spin=document.createElement('span');spin.className='qspin';
    const ts=document.createElement('span');ts.className='qts';ts.textContent=m.ts?m.ts.slice(11,16):'';
    const txt=document.createElement('span');txt.className='qtxt';txt.textContent=m.text;
    const c=document.createElement('span');c.className='qc';
    c.textContent=seen+'/'+s.length+' seen'+(m.mentions&&m.mentions.length?' \u00b7 @'+m.mentions.join(','):'');
    row.append(spin,ts,txt,c);list.appendChild(row);
  }
}
async function umqPoll(){try{const r=await api('/api/user-messages');if(r&&Array.isArray(r.messages)){lastUmq.messages=r.messages;renderQueue();}}catch(e){}}
function queueMsg(t){
  let mentions=null;const ms=[...new Set((t.match(/@\w+/g)||[]).map(s=>s.slice(1)))];
  if(ms.length)mentions=ms.filter(n=>agents.some(a=>a.name===n));
  api('/api/user-messages',{method:'POST',body:JSON.stringify({text:t,mode:mode,mentions:mentions})})
    .then(r=>{if(r&&r.message){lastUmq.messages=(lastUmq.messages||[]).concat([r.message]);}}).catch(()=>{});
  umqPoll();renderQueue();
}
async function settleMsg(m){
  try{await jpost('/api/user-messages/check',{id:m.id,agent:'*'});}catch(e){}
  m.checked=m.checked||{};umqScope(m).forEach(n=>m.checked[n]=true);renderQueue();
}
async function umqDeliver(){
  if(delivering)return;
  const pend=(lastUmq.messages||[]).filter(m=>!umqDone(m)).sort((a,b)=>a.ts<b.ts?-1:1);
  if(!pend.length||busy)return;
  delivering=true;
  try{for(const m of pend){if(busy)break;await settleMsg(m);$('input').value=m.text;await send();}}
  finally{delivering=false;}
}
function startHeartbeat(){jpost('/api/run-state',{busy:true,mode:mode,ts:Date.now()}).catch(()=>{});if(window.__hbT)clearInterval(window.__hbT);window.__hbT=setInterval(()=>jpost('/api/run-state',{busy:true,mode:mode,ts:Date.now()}).catch(()=>{}),5000);}
function stopHeartbeat(){if(window.__hbT)clearInterval(window.__hbT);window.__hbT=null;jpost('/api/run-state',{busy:false,mode:mode,ts:Date.now()}).catch(()=>{});}
function saveHistoryServer(force){const sig=JSON.stringify(history.slice(-200));if(!force&&sig===_histSig)return;_histSig=sig;jpost('/api/history',{mode:mode,history:history.slice(-200)}).catch(()=>{});}
async function restoreFromServer(){
  if($('msgs').children.length)return; // localStorage restore already happened
  try{
    const r=await api('/api/history?mode='+encodeURIComponent(mode));
    const h=(r&&Array.isArray(r.history))?r.history:[];
    if(!h.length)return;
    for(const e of h){
      if(e.speaker==='You'){addBubble('You','',null,true).querySelector('.body').textContent=e.content||'';}
      else{const a=agents.find(x=>x.name===e.speaker);addBubble(a?a.name:e.speaker,a?a.color:'var(--queue-dim)',a?a.emoji:'\ud83e\udd16',false).querySelector('.body').textContent=e.content||'';}
    }
    saveMsgs(); // re-seed the localStorage slot from the server copy
  }catch(e){}
}
function adoptLiveRun(r, after){
  // Adopt a backend-owned group run that is ALREADY LIVE: restore history up to its start,
  // then attach to its journaled SSE stream (fast-forward + live-tail). Shared by page-load
  // re-attach, the idle watcher, and send()'s "already in progress" fallback.
  if(runId)return;
  if(mode!=="group"){ mode="group"; $("mSolo").classList.remove("on"); $("mGroup").classList.add("on"); updateHint(); }
  $('msgs').innerHTML=''; history.length=0;
  api('/api/history?mode=group').then(h=>{
    const hist=(h&&Array.isArray(h.history))?h.history:[];
    const start=(typeof r.hist_start==="number")?Math.min(r.hist_start,hist.length):hist.length;
    for(const e of hist.slice(0,start)){
      if(e.speaker==='You'){addBubble('You','',null,true).querySelector('.body').textContent=e.content||'';}
      else{const a=agents.find(x=>x.name===e.speaker);addBubble(a?a.name:e.speaker,a?a.color:'var(--queue-dim)',a?a.emoji:'\ud83e\udd16',false).querySelector('.body').textContent=e.content||'';}
    }
    stickScroll(true); // pin to bottom after history re-render - no top-scroll flash on re-attach (2026-11-15)
    const resume=(attachedRunId===r.run_id)?runLastSeq:0; // same run already watched: skip the multi-MB replay
    if(attachedRunId!==r.run_id){ attachedRunId=r.run_id; runLastSeq=0; }
    busy=true;setSendQueued(true);startHeartbeat();startStallPoll();
    if(after)try{after();}catch(e){}
    attachRun(r.run_id,resume).then(()=>{   // stream ended (run finished/stopped): release UI state
      if(runId===null){ busy=false; setSendQueued(false); stopStallPoll(); stopHeartbeat(); saveHistoryServer(true); umqPoll(); renderQueue(); }
    });
  }).catch(()=>{});
}
let runWatchT=null;
async function runWatch(){
  // Idle watcher (2026-11-15): a group run can start while this tab is idle - scheduled task,
  // another tab, or the backend auto-continue. Poll run-state and adopt it so live progress
  // appears without a reload (previously re-attach only happened once at page load).
  if(busy||runId)return;
  try{const r=await api('/api/run-state');
    if(r&&r.busy&&r.run_id)adoptLiveRun(r);
  }catch(e){}
}
function startRunWatch(){if(runWatchT)return;runWatch();runWatchT=setInterval(runWatch,5000);}
function checkInterruptedRun(){
  // 2026-11-15: group runs are backend-owned. If one is live, RE-ATTACH and replay from the
  // journal (hard refresh no longer cancels anything). A finished/interrupted run gets its verdict shown.
  api('/api/run-state').then(r=>{
    if(!r||!r.run_id)return;
    if(r.busy&&r.status!=="interrupted"){ adoptLiveRun(r); }
    else if(r.status&&r.status!=="running"){
      const v=r.verdict||{};
      if(v.note){const w=document.createElement("div");w.className="thinkwrap";
        const p=document.createElement("div");p.className="roundend "+(v.cls||"dim");p.textContent=v.note;
        w.appendChild(p);$("msgs").appendChild(w);stickScroll();}
    }
  }).catch(()=>{});
}
function clearRunState(){jpost('/api/run-state',{busy:false,mode:mode,ts:Date.now()}).catch(()=>{});}
$('intResume').onclick=()=>{ $('intBanner').classList.remove('show');clearRunState();
  const t='Continue where you left off \u2014 pick up any unfinished work and say [CONCLUDED] when done.';
  if(busy){queueMsg(t);}else{$('input').value=t;send();} };
$('intDismiss').onclick=()=>{ $('intBanner').classList.remove('show');clearRunState(); };
function bootRestore(){ try{setMode(mode);}catch(e){} restoreFromServer(); umqPoll(); setInterval(()=>{umqPoll();umqDeliver();},1500); checkInterruptedRun(); startRunWatch(); }

