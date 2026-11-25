// ui/deeplink.js — RECONSTRUCTABLE URL (2026-11-25)
// Encodes the full dashboard view state into the address bar so any view can be
// shared/bookmarked and reconstructed exactly on load:
//   http://<host>:8099/#/goals?a=forge&m=group
//     page  : goals|activity|fleet|files|ops   (existing hash router; absent = chat home)
//     a     : selected agent id/name in the left list
//     m     : solo|group composer mode
// Also supports the /page/<name>.html path form with the same ?a=&m= query.
// PITFALL (2026-11-25): core.js declares a top-level `let history=[]` which SHADOWS
// window.history for every later script - always call window.history.replaceState here.
// State changes rewrite the bar via history.replaceState (no history spam).
// Every state transition is appended to memory/ops/ui-state.jsonl via POST /api/ui/state
// (fire-and-forget; falls back to localStorage when the endpoint is absent) so the
// fleet can see which views humans are working in. Memory index: memory/ops/ui-state.jsonl
(function(){
  var PAGES={activity:"actPanel",fleet:"fleetPanel",ops:"opsPanel",files:"filesPanel",goals:"goalsPanel"};
  var agentMap=null, writing=false, lastLog="";

  function pageFromHash(){var m=(location.hash||"").match(/^#\/(\w+)/);return (m&&PAGES[m[1]])?m[1]:null;}
  function pageFromPath(){var m=location.pathname.match(/^\/page\/(\w+)\.html/);return (m&&PAGES[m[1]])?m[1]:null;}
  function page(){return pageFromHash()||pageFromPath();}

  // query params live in location.search for /page/*.html, after "?" in the hash otherwise
  function qp(name){
    try{
      var s=location.search||"";
      if(s){var v=new URLSearchParams(s).get(name);if(v!==null)return v;}
      var i=(location.hash||"").indexOf("?");
      if(i>=0){var v2=new URLSearchParams(location.hash.slice(i+1)).get(name);if(v2!==null)return v2;}
    }catch(e){}
    return null;
  }

  function loadAgentMap(){
    fetch("/api/agents").then(function(r){return r.json();}).then(function(d){
      var list=Array.isArray(d)?d:(d.agents||[]);
      agentMap={};
      list.forEach(function(a){var k=String(a.name||a.id).toLowerCase();agentMap[k]=a.id;});
    }).catch(function(){});
  }

  function currentAgent(){
    var c=document.querySelector("#agentList .acard.sel");
    if(!c)return null;
    var da=c.getAttribute("data-agent");          // exact id (core.js renderAgents sets it)
    if(da)return da;
    var t=(c.textContent||"").toLowerCase();      // legacy fallback: fuzzy name match
    if(agentMap){for(var k in agentMap){if(t.indexOf(k)>=0)return agentMap[k];}}
    return null;
  }
  function currentMode(){
    var g=document.getElementById("mGroup");
    if(!g)return "solo";
    return (g.classList.contains("on")||g.getAttribute("aria-pressed")==="true")?"group":"solo";
  }

  function buildURL(){
    var p=page(), a=currentAgent(), m=currentMode();
    var q=[];
    if(a)q.push("a="+encodeURIComponent(String(a).toLowerCase()));
    if(m!=="solo")q.push("m="+m);
    var qs=q.length?("?"+q.join("&")):"";
    if(/^\/page\//.test(location.pathname))return location.origin+location.pathname+qs; // path form keeps its query slot
    return location.origin+location.pathname+(p?("# "+p).replace(" ","/")+qs:"");
  }

  function writeURL(){
    if(writing)return; writing=true;
    try{
      var p=page(), a=currentAgent(), m=currentMode();
      var q=[];
      if(a)q.push("a="+encodeURIComponent(String(a).toLowerCase()));
      if(m!=="solo")q.push("m="+m);
      var qs=q.length?("?"+q.join("&")):"";
      if(/^\/page\//.test(location.pathname)){
        window.history.replaceState(null,"",location.pathname+qs);
      }else{
        var h=p?("# "+p).replace(" ","/")+qs:"";
        window.history.replaceState(null,"",location.pathname+location.search+h);
      }
      logState(p,a,m);
    }catch(e){}
    writing=false;
  }

  function logState(p,a,m){
    var key=(p||"chat")+"|"+(a||"")+"|"+(m||"solo");
    if(key===lastLog)return; lastLog=key;
    var rec={ts:new Date().toISOString(),page:p||"chat",agent:a||null,mode:m||"solo",url:location.href};
    try{fetch("/api/ui/state",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(rec)}).catch(function(){});}catch(e){}
    try{
      var ls=JSON.parse(localStorage.getItem("portal_ui_state_log")||"[]");
      ls.push(rec); if(ls.length>200)ls=ls.slice(-200);
      localStorage.setItem("portal_ui_state_log",JSON.stringify(ls));
    }catch(e){}
  }

  // ---- restore on load -------------------------------------------------
  // ?a= accepts an agent id ("researcher"), a name ("Researcher") or the 3-letter
  // chip code ("res"). Matching is EXACT - the old substring match let "arc" hit
  // "researcher". Cards carry data-agent=<id> (core.js renderAgents).
  function agentIdFor(want){
    want=String(want||"").toLowerCase();
    if(!want)return null;
    if(agentMap&&agentMap[want])return agentMap[want];            // name -> id
    for(var k in (agentMap||{})){                                  // chip code or raw id
      if(want.length===3&&k.slice(0,3)===want)return agentMap[k];
      if(String(agentMap[k]).toLowerCase()===want)return agentMap[k];
    }
    return want;                                                   // assume already an id
  }
  function restore(){
    var m=qp("m"), a=qp("a");
    if(m==="group"){var g=document.getElementById("mGroup");if(g)try{g.click();}catch(e){}}
    if(a){
      var tries=0;
      var t=setInterval(function(){
        tries++;
        var id=agentIdFor(a); // re-resolve each tick: agentMap may still be loading
        var cards=document.querySelectorAll("#agentList .acard");
        var hit=null;
        for(var i=0;i<cards.length;i++){if(cards[i].getAttribute("data-agent")===(id||"")){hit=cards[i];break;}}
        if(hit){clearInterval(t);try{hit.click();}catch(e){}}
        else if(tries>40)clearInterval(t); // ~8s: agent list never rendered (or unknown id)
      },200);
    }
  }

  // ---- copy-link button -------------------------------------------------
  function addLinkBtn(){
    var bar=document.getElementById("goalBar");
    if(!bar||document.getElementById("linkBtn"))return;
    var b=document.createElement("button");
    b.id="linkBtn"; b.title="Copy reconstructable link for this exact view";
    b.textContent="\u29C9 Link";
    var first=bar.querySelector("button")||bar.firstChild;
    bar.insertBefore(b,first);
    b.onclick=function(){
      writeURL();
      var url=location.href, done=function(){
        b.textContent="\u2713 Copied";
        if(typeof window.notify==="function"){try{window.notify("ok","Reconstructable link copied: "+url);}catch(e){}}
        setTimeout(function(){b.textContent="\u29C9 Link";},1500);
      };
      if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(url).then(done).catch(function(){fallback();});}
      else fallback();
      function fallback(){var ta=document.createElement("textarea");ta.value=url;document.body.appendChild(ta);ta.select();try{document.execCommand("copy");done();}catch(e){}document.body.removeChild(ta);}
    };
  }

  // renderGoalBar (core.js) rewrites #goalBar innerHTML on every poll - keep Link alive
  function watchGoalBar(){
    var bar=document.getElementById("goalBar");
    if(!bar||typeof MutationObserver==="undefined")return;
    new MutationObserver(function(){ if(!document.getElementById("linkBtn"))addLinkBtn(); }).observe(bar,{childList:true});
  }

  // ---- wiring ------------------------------------------------------------
  loadAgentMap();
  document.addEventListener("DOMContentLoaded",function(){
    addLinkBtn();
    watchGoalBar();
    restore();
    setTimeout(writeURL,800); // initial bar sync after first render
    setInterval(function(){if(page())writeURL();},2500);
    var al=document.getElementById("agentList"), mb=document.getElementById("modeBar");
    if(al)al.addEventListener("click",function(){setTimeout(writeURL,120);});
    if(mb)mb.addEventListener("click",function(){setTimeout(writeURL,120);});
    window.addEventListener("hashchange",function(){setTimeout(writeURL,150);});
  });
  if(document.readyState!=="loading"){addLinkBtn();watchGoalBar();restore();}
})();
