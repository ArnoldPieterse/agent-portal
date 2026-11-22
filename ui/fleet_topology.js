/* FleetTopology — live SVG topology of fleet hosts + agent nodes (Designer goal #9).
   2026-11-17 file-modularity split: extracted from memory/designer/fleet_topology_demo.html.
   parent: index.html (markup-only shell) | siblings: ui/core.js, ui/uploads.js, ui/app.css
   rule doc: memory/portal/file-modularity.md | served by GET /ui/* route on :8099.
   Data source: GET /api/fleet -> { ts, ttl, hosts:[{host,base,agents[],models[],state,last_seen}] }
   State -> color reuses portal tokens (var(--ok)/var(--warn)/var(--err)) via ui/app.css .ft-* block.
   API: FleetTopology.render(containerEl, { live:true, sample?, fallback? }); SAMPLE exported. */
/* FleetTopology — live SVG topology of fleet hosts + agent nodes (Designer goal #9).
   Data source: GET /api/fleet -> { ts, ttl, hosts:[{host,base,agents[],models[{id,quant}],generations,state,last_seen,reason,loading:{agent,model,since}|null,queued:int}] }
   State -> color reuses the existing .fdot palette: idle=--ok, busy=--warn, unknown=--dot-err.
   Usage (after ui/core.js): FleetTopology.render(document.querySelector('#fleetTopo'), { live:true });
   Dependency-free. Self-contained SVG + HTML tooltip/detail card. */
(function (root) {
  "use strict";

  var STATE_COLOR = { idle: "var(--ok, #3ddc84)", busy: "var(--warn, #ff9f43)", unauth: "var(--acc, #4f8cff)", unknown: "var(--dot-err)" };
  var STATE_LABEL = { idle: "idle", busy: "busy", unauth: "unauth (up, no key)", unknown: "unknown" };

  // Fallback dataset (real /api/fleet schema) so the diagram renders even with no egress.
  var SAMPLE = { ts: Date.now() / 1000, ttl: 30, hosts: [
    { host: "White (local)", base: "http://127.0.0.1:8888", agents: ["Orchestrator","Researcher","Builder","Verifier"], active: ["Orchestrator","Scribe"], models: [{id:"Qwen3.8-27B-Q8_0",quant:"Q8"},{id:"Qwen3.8-27B-Q4_K_S",quant:"Q4"}], generations: 0, state: "idle", last_seen: null, reason: "", loading: null, queued: 0 },
    { host: "Pale", base: "http://IP_PALE:8888", agents: ["Designer","Archivist"], active: ["Archivist"], models: [{id:"Qwen3.8-27B-Q4_K_S",quant:"Q4"}], generations: 1, state: "busy", last_seen: null, reason: "", loading: { agent: "Archivist", model: "Q8_0", since: Date.now() / 1000 - 95 }, queued: 1 },
    { host: "Black", base: "http://IP_BLACK:8888", agents: [], active: [], models: [{id:"Qwen3.8-27B-Q4_K_S",quant:"Q4"}], generations: 0, state: "idle", last_seen: null, reason: "", loading: null, queued: 0 },
    { host: "Red", base: "http://IP_RED:8888", agents: ["Scribe","Mechanic"], active: [], models: [{id:"Qwen3.8-27B-Q8_0",quant:"Q8"}], generations: 0, state: "idle", last_seen: null, reason: "", loading: null, queued: 0 }
  ]};   // 'agents' = home roster (agents.json), 'active' = ran here in the last 10 min

  function esc(s){ return String(s==null?"":s).replace(/[&<>\"]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];}); }
  function fmtAge(ts){ if(ts==null) return "never"; var s=Math.max(0,Math.floor(Date.now()/1000-ts)); if(s<60)return s+"s ago"; if(s<3600)return Math.floor(s/60)+"m "+(s%60)+"s ago"; return Math.floor(s/3600)+"h "+Math.floor((s%3600)/60)+"m ago"; }

  function layout(hosts){
    var W = Math.max(720, hosts.length * 240), H = 380;
    var n = hosts.length || 1;
    var gapX = W / (n + 1);
    var portal = { x: W/2, y: H - 56 };
    var hostY = 96, agentY = 196;
    return hosts.map(function(h,i){
      var cx = gapX * (i+1);
      var agents = (h.agents||[]).slice(0,8);
      var span = Math.min(agents.length,7) * 26;
      var ax0 = cx - span/2 + 13;
      var bh = (h.loading || h.queued > 0 || (h.host_loading||[]).length) ? 58 : 46;   // extra line for the load queue
      return { h:h, i:i, cx:cx, hostY:hostY, agentY:agentY, portal:portal, W:W, H:H, bh:bh,
        agents: agents.map(function(a,j){ return { name:a, x:ax0 + j*26, y:agentY }; }) };
    });
  }

  function loadLine(h){
    var hl = h.host_loading||[];
    if(!h.loading && !(h.queued>0) && !hl.length) return "";
    var t = h.loading ? ("⏳ " + (h.loading.model||"?")) : "";
    if(hl.length) t += (t?" · ":"") + "⏳ " + hl.slice(0,2).join(", ") + (hl.length>2?" +"+(hl.length-2):"") + " (host)";
    if(h.queued>0) t += (t?" · ":"") + h.queued + " queued";
    return t;
  }

  function svgNode(node){
    var h = node.h, color = STATE_COLOR[h.state] || STATE_COLOR.unknown;
    var s = "";
    var pY = node.hostY + Math.max(26, node.bh/2 + 1);
    var aY = node.hostY + Math.max(34, node.bh/2 + 9);
    s += '<line x1="'+node.cx+'" y1="'+pY+'" x2="'+node.portal.x+'" y2="'+(node.portal.y-18)+'" class="ft-link"/>';
    node.agents.forEach(function(a){
      s += '<line x1="'+node.cx+'" y1="'+aY+'" x2="'+a.x+'" y2="'+(a.y-7)+'" class="ft-agentlink"/>';
      s += '<g class="ft-agent"><circle cx="'+a.x+'" cy="'+a.y+'" r="6"/><title>'+esc(a.name)+'</title></g>';
    });
    var bw = 150, bh = node.bh, bx = node.cx - bw/2, by = node.hostY - bh/2;
    var lq = loadLine(h);
    var c1 = lq ? -10 : -4, c2 = lq ? 6 : 12;   // baselines for line 1 (name) / line 2 (agents·gen)
    s += '<g class="ft-host" data-i="'+node.i+'" tabindex="0" role="button" aria-label="'+esc(h.host)+' '+esc(STATE_LABEL[h.state]||h.state)+', '+((h.active||[]).length)+' active, '+(h.agents?h.agents.length:0)+' home'+(lq?', load queue: '+esc(lq)+(h.loading&&h.queued>0?' ('+esc(h.loading.agent||'?')+')':''):"")+'">'+
         '<rect x="'+bx+'" y="'+by+'" width="'+bw+'" height="'+bh+'" rx="12"/>'+
         '<circle cx="'+(bx+16)+'" cy="'+(node.hostY+c1)+'" r="7" class="ft-state" style="fill:'+color+'"/>'+
         '<text x="'+(bx+30)+'" y="'+(node.hostY+c1)+'" class="ft-hostname">'+esc(h.host)+'</text>'+
         '<text x="'+(bx+30)+'" y="'+(node.hostY+c2)+'" class="ft-subline" title="active on this host in the last 10 min (placement is host-agnostic); home roster: '+((h.agents||[]).map(esc).join(", ")||"none")+'">'+((h.active||[]).length)+' active · '+(h.generations||0)+' gen'+(h.state==="unknown"?" · "+esc(h.reason||"unreachable"):"")+'</text>'+
         (lq ? '<text x="'+(bx+30)+'" y="'+(node.hostY+21)+'" class="ft-loadline">'+esc(lq)+'</text>' : '')+
         '</g>';
    return s;
  }

  function portalNode(node){
    var p = node.portal;
    return '<g class="ft-portal"><rect x="'+(p.x-70)+'" y="'+(p.y-18)+'" width="140" height="36" rx="10"/>'+
           '<circle cx="'+(p.x-52)+'" cy="'+p.y+'" r="6" class="ft-state" style="fill:var(--acc,#4f8cff)"/>'+
           '<text x="'+(p.x-38)+'" y="'+(p.y+4)+'" class="ft-hostname">Portal :8099</text></g>';
  }

  function tooltipHTML(h){
    var models = (h.models||[]).map(function(m){return esc(m.id)+(m.quant?" ("+esc(m.quant)+")":"");}).join(", ") || "—";
    var lq = h.loading ? ('loading '+esc(h.loading.model||'?')+' for '+esc(h.loading.agent||'?')+' · '+fmtAge(h.loading.since)+(h.queued>0?' · '+h.queued+' waiting':''))
                       : (h.queued>0 ? h.queued+' queued' : 'none');
    if((h.host_loading||[]).length) lq += (lq==='none'?'':' · ') + 'host loading '+h.host_loading.map(esc).join(", ");
    return '<div class="ft-tt-head"><span class="ft-state" style="background:'+(STATE_COLOR[h.state]||STATE_COLOR.unknown)+'"></span>'+esc(h.host)+' <em>'+esc(STATE_LABEL[h.state]||h.state)+'</em></div>'+
           '<div class="ft-tt-row"><b>base</b> '+esc(h.base)+'</div>'+
           '<div class="ft-tt-row"><b>gens</b> '+(h.generations||0)+' · <b>last seen</b> '+fmtAge(h.last_seen)+(h.reason?' ('+esc(h.reason)+')':'')+'</div>'+
           '<div class="ft-tt-row"><b>active 10m</b> '+((h.active||[]).map(esc).join(", ")||"none")+' · <b>home</b> '+((h.agents||[]).map(esc).join(", ")||"none")+'</div>'+
           '<div class="ft-tt-row"><b>load queue</b> '+lq+'</div>'+
           '<div class="ft-tt-row"><b>models</b> '+models+'</div>';
  }

  function detailHTML(h){
    var models = (h.models||[]).map(function(m){return '<li>'+esc(m.id)+(m.quant?' <span class="ft-quant">'+esc(m.quant)+'</span>':'')+'</li>';}).join("") || "<li class='ft-empty'>no models loaded</li>";
    var actChips = (h.active||[]).map(function(a){return '<span class="ft-chip">'+esc(a)+'</span>';}).join(" ") || '<span class="ft-empty">none in the last 10 minutes</span>';
    var homeChips = (h.agents||[]).map(function(a){return '<span class="ft-chip" style="opacity:.65">'+esc(a)+'</span>';}).join(" ") || '<span class="ft-empty">no agents bound at home</span>';
    var items = [];
    if(h.loading) items.push('<li><b>'+esc(h.loading.model||'?')+'</b> for '+esc(h.loading.agent||'?')+' <span class="ft-quant">'+fmtAge(h.loading.since)+'</span></li>');
    if(h.queued>0) items.push("<li class='ft-empty'>"+h.queued+" queued behind it</li>");
    (h.host_loading||[]).forEach(function(m){ items.push('<li>⏳ <b>'+esc(m)+'</b> <span class="ft-quant">host load - started by Studio, not the portal queue</span></li>'); });
    var lq = items.length ? items.join("") : "<li class='ft-empty'>no loads in flight</li>";
    return '<div class="ft-dt-head"><span class="ft-state" style="background:'+(STATE_COLOR[h.state]||STATE_COLOR.unknown)+'"></span><b>'+esc(h.host)+'</b> <em>'+esc(STATE_LABEL[h.state]||h.state)+'</em></div>'+
           '<div class="ft-dt-base">'+esc(h.base)+'</div>'+
           '<div class="ft-dt-sub">Load queue</div><ul class="ft-models">'+lq+'</ul>'+
           '<div class="ft-dt-sub">Models ('+(h.models?h.models.length:0)+')</div><ul class="ft-models">'+models+'</ul>'+
           '<div class="ft-dt-sub">Active now (last 10m)</div><div class="ft-agents">'+actChips+'</div>'+
           '<div class="ft-dt-sub">Home roster</div><div class="ft-agents">'+homeChips+'</div>';
  }

  function render(container, opts){
    opts = opts || {};
    if(!container) return;
    container.innerHTML = '<div class="ft-wrap"><svg class="ft-svg" role="img" aria-label="Fleet topology"></svg>'+
      '<div class="ft-tooltip" hidden></div><div class="ft-detail" hidden></div></div>';
    var wrap = container.querySelector(".ft-wrap");
    var svg  = container.querySelector(".ft-svg");
    var tip  = container.querySelector(".ft-tooltip");
    var det  = container.querySelector(".ft-detail");
    var data = null;

    function moveTip(e){
      var r = wrap.getBoundingClientRect();
      tip.style.left = Math.min(e.clientX - r.left + 14, r.width - 260) + "px";
      tip.style.top  = (e.clientY - r.top + 14) + "px";
    }

    function draw(d){
      data = d;
      var nodes = layout(d.hosts||[]);
      svg.setAttribute("viewBox","0 0 "+nodes[0].W+" "+nodes[0].H);
      svg.innerHTML = nodes.map(portalNode).join("") + nodes.map(svgNode).join("");
      Array.prototype.forEach.call(svg.querySelectorAll(".ft-host"), function(g){
        var h = data.hosts[+g.getAttribute("data-i")]; if(!h) return;
        g.addEventListener("mouseenter", function(e){ tip.innerHTML=tooltipHTML(h); tip.hidden=false; moveTip(e); });
        g.addEventListener("mousemove", moveTip);
        g.addEventListener("mouseleave", function(){ tip.hidden=true; });
        g.addEventListener("click", function(){ det.innerHTML=detailHTML(h); det.hidden=false; });
        g.addEventListener("keydown", function(e){ if(e.key==="Enter"||e.key===" "){ e.preventDefault(); det.innerHTML=detailHTML(h); det.hidden=false; } });
      });
    }

    function load(){
      if(opts.sample){ draw(opts.sample); return; }
      fetch("/api/fleet", {cache:"no-store"}).then(function(r){return r.json();})
        .then(draw)
        .catch(function(){ draw(opts.fallback||SAMPLE); });
    }

    load();
    if(opts.live && !opts.sample){ var iv = setInterval(load, 30000); container._ftStop=function(){clearInterval(iv);}; }
  }

  root.FleetTopology = { render: render, SAMPLE: SAMPLE };
})(typeof window!=="undefined" ? window : this);
/* Self-init: render into #fleetTopo when present (index.html markup-only shell rule). */
(function(){
  function boot(){
    var el = document.getElementById('fleetTopo');
    if (el && !el._ftBooted) { el._ftBooted = true; FleetTopology.render(el, { live: true }); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
