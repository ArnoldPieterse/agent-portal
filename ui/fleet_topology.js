/* FleetTopology — live SVG topology of fleet hosts + agent nodes (Designer goal #9).
   2026-11-17 file-modularity split: extracted from memory/designer/fleet_topology_demo.html.
   parent: index.html (markup-only shell) | siblings: ui/core.js, ui/uploads.js, ui/app.css
   rule doc: memory/portal/file-modularity.md | served by GET /ui/* route on :8099.
   Data source: GET /api/fleet -> { ts, ttl, hosts:[{host,base,agents[],models[],state,last_seen}] }
   State -> color reuses portal tokens (var(--ok)/var(--warn)/var(--err)) via ui/app.css .ft-* block.
   API: FleetTopology.render(containerEl, { live:true, sample?, fallback? }); SAMPLE exported. */
/* FleetTopology — live SVG topology of fleet hosts + agent nodes (Designer goal #9).
   Data source: GET /api/fleet -> { ts, ttl, hosts:[{host,base,agents[],models[{id,quant}],generations,state,last_seen,reason}] }
   State -> color reuses the existing .fdot palette: idle=--ok, busy=--warn, unknown=--dot-err.
   Usage (after ui/core.js): FleetTopology.render(document.querySelector('#fleetTopo'), { live:true });
   Dependency-free. Self-contained SVG + HTML tooltip/detail card. */
(function (root) {
  "use strict";

  var STATE_COLOR = { idle: "var(--ok, #3ddc84)", busy: "var(--warn, #ff9f43)", unknown: "var(--dot-err)" };
  var STATE_LABEL = { idle: "idle", busy: "busy", unknown: "unknown" };

  // Fallback dataset (real /api/fleet schema) so the diagram renders even with no egress.
  var SAMPLE = { ts: Date.now() / 1000, ttl: 30, hosts: [
    { host: "White (local)", base: "http://127.0.0.1:8888", agents: ["Orchestrator","Researcher","Builder","Verifier","Designer","Archivist","Scribe","Mechanic"], models: [{id:"atlas-q8",quant:"Q8"},{id:"scribe-q8",quant:"Q8"}], generations: 0, state: "idle", last_seen: null, reason: "" },
    { host: "Black .244", base: "http://[LAN-IP]:8888", agents: ["Builder","Verifier"], models: [{id:"atlas-q8",quant:"Q8"}], generations: 1, state: "busy", last_seen: null, reason: "" },
    { host: "Red .245", base: "http://IP_RED:8888", agents: ["Mechanic"], models: [{id:"mech-q4",quant:"Q4"}], generations: 0, state: "unknown", last_seen: null, reason: "unreachable" }
  ]};

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
      return { h:h, i:i, cx:cx, hostY:hostY, agentY:agentY, portal:portal, W:W, H:H,
        agents: agents.map(function(a,j){ return { name:a, x:ax0 + j*26, y:agentY }; }) };
    });
  }

  function svgNode(node){
    var h = node.h, color = STATE_COLOR[h.state] || STATE_COLOR.unknown;
    var s = "";
    s += '<line x1="'+node.cx+'" y1="'+(node.hostY+26)+'" x2="'+node.portal.x+'" y2="'+(node.portal.y-18)+'" class="ft-link"/>';
    node.agents.forEach(function(a){
      s += '<line x1="'+node.cx+'" y1="'+(node.hostY+34)+'" x2="'+a.x+'" y2="'+(a.y-7)+'" class="ft-agentlink"/>';
      s += '<g class="ft-agent"><circle cx="'+a.x+'" cy="'+a.y+'" r="6"/><title>'+esc(a.name)+'</title></g>';
    });
    var bw = 150, bh = 46, bx = node.cx - bw/2, by = node.hostY - bh/2;
    s += '<g class="ft-host" data-i="'+node.i+'" tabindex="0" role="button" aria-label="'+esc(h.host)+' '+esc(STATE_LABEL[h.state]||h.state)+', '+(h.agents?h.agents.length:0)+' agents">'+
         '<rect x="'+bx+'" y="'+by+'" width="'+bw+'" height="'+bh+'" rx="12"/>'+
         '<circle cx="'+(bx+16)+'" cy="'+node.hostY+'" r="7" class="ft-state" style="fill:'+color+'"/>'+
         '<text x="'+(bx+30)+'" y="'+(node.hostY-4)+'" class="ft-hostname">'+esc(h.host)+'</text>'+
         '<text x="'+(bx+30)+'" y="'+(node.hostY+12)+'" class="ft-subline">'+(h.agents?h.agents.length:0)+' agents · '+(h.generations||0)+' gen'+(h.state==="unknown"?" · "+esc(h.reason||"unreachable"):"")+'</text>'+
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
    return '<div class="ft-tt-head"><span class="ft-state" style="background:'+(STATE_COLOR[h.state]||STATE_COLOR.unknown)+'"></span>'+esc(h.host)+' <em>'+esc(STATE_LABEL[h.state]||h.state)+'</em></div>'+
           '<div class="ft-tt-row"><b>base</b> '+esc(h.base)+'</div>'+
           '<div class="ft-tt-row"><b>gens</b> '+(h.generations||0)+' · <b>last seen</b> '+fmtAge(h.last_seen)+(h.reason?' ('+esc(h.reason)+')':'')+'</div>'+
           '<div class="ft-tt-row"><b>models</b> '+models+'</div>';
  }

  function detailHTML(h){
    var models = (h.models||[]).map(function(m){return '<li>'+esc(m.id)+(m.quant?' <span class="ft-quant">'+esc(m.quant)+'</span>':'')+'</li>';}).join("") || "<li class='ft-empty'>no models loaded</li>";
    var agents = (h.agents||[]).map(function(a){return '<span class="ft-chip">'+esc(a)+'</span>';}).join(" ") || '<span class="ft-empty">no agents bound</span>';
    return '<div class="ft-dt-head"><span class="ft-state" style="background:'+(STATE_COLOR[h.state]||STATE_COLOR.unknown)+'"></span><b>'+esc(h.host)+'</b> <em>'+esc(STATE_LABEL[h.state]||h.state)+'</em></div>'+
           '<div class="ft-dt-base">'+esc(h.base)+'</div>'+
           '<div class="ft-dt-sub">Models ('+(h.models?h.models.length:0)+')</div><ul class="ft-models">'+models+'</ul>'+
           '<div class="ft-dt-sub">Agents ('+(h.agents?h.agents.length:0)+')</div><div class="ft-agents">'+agents+'</div>';
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
