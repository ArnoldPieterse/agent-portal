/* cockpit-topology.js — Fleet Topology Live Graph
   Cycle-12 Goal 7 | Designer | 2026-11-24
   4-host fleet as live topology: nodes=hosts, edges=model assignments,
   node size=VRAM utilization, edge thickness=data volume.
*/
const TopologyGraph = (() => {
  let canvas = null, ctx = null;
  let hosts = [], edges = [];
  let animFrame = null;

  function init(root) {
    canvas = root || document.querySelector('[data-topology]') || document.getElementById('topology-canvas');
    if (!canvas) { console.warn('[TopologyGraph] no canvas found'); return; }
    ctx = canvas.getContext('2d');
    resize();
    window.addEventListener('resize', resize);
    loadData();
  }

  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = Math.max(300, rect.height);
    render();
  }

  async function loadData() {
    try {
      const resp = await fetch('/api/fleet/topology');
      const data = await resp.json();
      hosts = data.hosts || [];
      edges = data.edges || [];
    } catch (e) {
      // Fallback: render empty state
      hosts = [{id:'white',status:'unknown'},{id:'red',status:'unknown'},
               {id:'blue',status:'unknown'},{id:'green',status:'unknown'}];
    }
    render();
  }

  function render() {
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const w = canvas.width, h = canvas.height;
    const cx = w / 2, cy = h / 2;
    const radius = Math.min(w, h) * 0.35;

    // Draw edges first (behind nodes)
    edges.forEach(e => {
      const from = hosts.find(hh => hh.id === e.from);
      const to = hosts.find(hh => hh.id === e.to);
      if (!from || !to) return;
      const fp = nodePos(from, cx, cy, radius);
      const tp = nodePos(to, cx, cy, radius);
      ctx.beginPath();
      ctx.moveTo(fp.x, fp.y);
      ctx.lineTo(tp.x, tp.y);
      ctx.lineWidth = Math.min(4, (e.volume || 1) * 0.5 + 1);
      const down = from.status === 'down' || to.status === 'down';
      ctx.strokeStyle = down ? 'rgba(136,146,164,0.3)' : 'rgba(79,195,247,0.5)';
      if (down) ctx.setLineDash([4, 4]); else ctx.setLineDash([]);
      ctx.stroke();
    });

    // Draw nodes
    hosts.forEach((host, i) => {
      const pos = nodePos(host, cx, cy, radius);
      const size = 12 + (host.vram || 0) * 0.3; // VRAM utilization scales size

      ctx.beginPath();
      ctx.arc(pos.x, pos.y, size, 0, Math.PI * 2);
      if (host.status === 'down') {
        ctx.fillStyle = 'rgba(136,146,164,0.4)'; // desaturated
      } else if (host.status === 'warn') {
        ctx.fillStyle = '#ff9800';
      } else {
        ctx.fillStyle = '#4fc3f7';
      }
      ctx.fill();

      // Host label
      ctx.font = '11px -apple-system, sans-serif';
      ctx.fillStyle = host.status === 'down' ? 'rgba(136,146,164,0.7)' : '#e0e0e0';
      ctx.textAlign = 'center';
      ctx.fillText(host.id.toUpperCase(), pos.x, pos.y + size + 14);

      // VRAM label
      if (host.vram) {
        ctx.font = '9px -apple-system, sans-serif';
        ctx.fillText(`${Math.round(host.vram*100)}%`, pos.x, pos.y + size + 26);
      }
    });

    // Simplified mode for narrow viewports
    if (canvas.width < 768) {
      ctx.font = '10px sans-serif';
      ctx.fillStyle = '#8892a4';
      ctx.textAlign = 'left';
      ctx.fillText('Simplified topology (narrow view)', 10, h - 10);
    }
  }

  function nodePos(host, cx, cy, radius) {
    const idx = hosts.indexOf(host);
    const angle = (idx / hosts.length) * Math.PI * 2 - Math.PI / 2;
    return { x: cx + Math.cos(angle) * radius, y: cy + Math.sin(angle) * radius };
  }

  // Public API for live updates
  function updateHost(hostId, data) {
    const host = hosts.find(h => h.id === hostId);
    if (host) Object.assign(host, data);
    render();
  }

  function destroy() { cancelAnimationFrame(animFrame); window.removeEventListener('resize', resize); }

  return { init, updateHost, render, destroy };
})();
