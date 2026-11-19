// Fleet Status Strip (Mechanic c5#8, Builder assist 2026-11-19)
// Injects a compact per-host status strip into the ops panel.
// Self-contained: fetches /api/fleet/status and renders dots + latency.
(function(){
  if(window.__fleetStatusLoaded) return;
  window.__fleetStatusLoaded = true;

  const HOSTS = ["white","black","red","blue"];
  const COLORS = { green:"#4caf50", amber:"#ff9800", red:"#f44336" };

  function dotColor(host){
    if(!host) return "#666";
    if(!host.reachable) return COLORS.red;
    const d = host.disk_pct, m = host.mem_pct;
    if((d && d >= 85) || (m && m >= 90)) return COLORS.amber;
    return COLORS.green;
  }

  function render(el, data){
    const overall = data.overall || "green";
    const badge = { green:"● GREEN", amber:"● AMBER", red:"● RED" }[overall] || "?";
    let html = `<span class="fs-badge" style="color:${COLORS[overall]||'#666'};font-weight:600">${badge}</span>`;
    const hosts = data.hosts || {};
    for(const h of HOSTS){
      const info = hosts[h] || {};
      const c = dotColor(info);
      const lat = info.latency_ms != null ? `${info.latency_ms}ms` : "—";
      html += `<span class="fs-host" title="${h}: ${info.reachable?'up':'down'}, latency ${lat}">` +
        `<span class="fs-dot" style="background:${c}"></span>` +
        `<span class="fs-name">${h}</span>` +
        `<span class="fs-lat">${lat}</span></span>`;
    }
    if(data.last_check){
      html += `<span class="fs-ts" title="Last check">${new Date(data.last_check*1000).toLocaleTimeString()}</span>`;
    }
    el.innerHTML = html;
  }

  function load(){
    const body = $("opsBody");
    if(!body) return;
    let strip = $("fleetStatusStrip");
    if(!strip){
      strip = document.createElement("div");
      strip.id = "fleetStatusStrip";
      strip.className = "fs-strip";
      strip.setAttribute("role","status");
      strip.setAttribute("aria-label","Fleet status");
      body.insertBefore(strip, body.firstChild);
    }
    fetch("/api/fleet/status").then(r=>{ if(!r.ok) throw new Error(r.status); return r.json(); })
      .then(d=>render(strip, d))
      .catch(e=>{ strip.innerHTML = `<span style="color:var(--dim);font-size:11px">⚠ fleet status unavailable</span>`; });
  }

  // Auto-load when ops panel opens (hook into existing opsLoad)
  const _origOpsLoad = window.opsLoad;
  if(_origOpsLoad){
    window.opsLoad = async function(){ await _origOpsLoad(); load(); };
  }
  // Also load on first paint if ops panel already open
  if($("opsPanel") && $("opsPanel").classList.contains("open")) load();
})();
