// Verifier: Fleet tab UI render test (2026-11-22, host names + load queue).
// Run from the repo root with any Node >= 18:
//   node memory/verifier/fleet_ui_render_test.js
// Renders ui/fleet_topology.js against a minimal DOM stub with SAMPLE data (which carries
// a loading + queued host) and re-runs the verbatim row-building loop from ui/core.js
// fleetUpdate(). Fails (non-zero exit) if: the topology SVG misses any of the 4 named
// hosts, the load-queue line/box is missing on the loading host, or the row markup lacks
// the loading/queued chips. No network access needed.
const fs = require("fs");
const path = require("path");
const ROOT = path.resolve(__dirname, "..", "..");

function fakeEl() {
  const el = { _html: "", style: {}, children: {},
    set innerHTML(v) { this._html = v; }, get innerHTML() { return this._html; },
    setAttribute() {},
    querySelector(sel) { if (!this.children[sel]) this.children[sel] = fakeEl(); return this.children[sel]; },
    querySelectorAll: () => [], addEventListener() {} };
  return el;
}
// make `window` an alias of the real global object, as in a browser
Object.defineProperty(globalThis, "window", { get() { return globalThis; }, configurable: true });
const els = {};
global.document = { readyState: "complete",
  getElementById(id) { if (!els[id]) els[id] = fakeEl(); return els[id]; } };
eval(fs.readFileSync(path.join(ROOT, "ui", "fleet_topology.js"), "utf8"));
const FT = global.window.FleetTopology;
if (!FT || !FT.render) throw new Error("FleetTopology did not attach to window");
global.FleetTopology = FT;

// 1) render SAMPLE into a stub container and inspect the generated SVG
const container = fakeEl();
FT.render(container, { sample: FT.SAMPLE });   // opts.sample IS the dataset
const svg = container.children[".ft-svg"]._html || "";
if (!svg) throw new Error("no SVG produced");
const must = ["White (local)", ">Pale<", ">Black<", ">Red<", 'class="ft-loadline"', "⏳ Q8_0 · 1 queued", "active · "];
for (const m of must) if (!svg.includes(m)) throw new Error("SVG missing: " + m);
// the loading host gets the taller box (58); the others stay 46
const h58 = (svg.match(/height="58"/g) || []).length;
const h46 = (svg.match(/height="46"/g) || []).length;
if (h58 !== 1) throw new Error("expected exactly one 58px host box, got " + h58);
if (h46 !== 3) throw new Error("expected three 46px host boxes, got " + h46);

// 2) verbatim copy of the row-building loop from ui/core.js fleetUpdate()
function esc(s){ return (s||"").replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }
var o = FT.SAMPLE;
var now = o.ts, html = "";
for(const h of (o.hosts||[])){
  const age=h.last_seen?Math.max(0,Math.round(now-h.last_seen)):"–";
  const st=h.state==="busy"?"busy":h.state==="idle"?"idle":h.state==="unauth"?"UNAUTH (up - key missing/expired)":"UNKNOWN";
  const models=h.models.length?h.models.map(m=>esc(m.id)+(m.quant?" ("+esc(m.quant)+")":"")).join(", "):"— none loaded —";
  let lq="";
  if(h.loading){ lq+=' · <span class="fload" title="Model load in progress on this host (one at a time)">⏳ loading '+esc(h.loading.model||"?")+' for '+esc(h.loading.agent||"?")+'</span>'; }
  if(h.queued>0){ lq+=' · <span class="fload fload-wait" title="Waiting their turn in the per-host load queue">'+h.queued+' queued</span>'; }
  const act=h.active||[];
  const who=act.length?act:(h.agents||[]);
  html+='<div class="frow-h"><span class="fdot '+h.state+'"></span><b>'+esc(h.host)+'</b>'+
    '<span class="hint"> · '+st+(h.reason?" · "+esc(h.reason):"")+" · last seen "+age+"s ago</span>"+
    '<div class="fmodels">'+models+lq+'</div>'+
    '<div class="hint" style="margin-left:16px">'+(act.length?"now":"home")+': '+(who.length?who.map(esc).join(", "):"none")+(act.length&&h.agents.length?" · home: "+h.agents.map(esc).join(", "):"")+'</div></div>';
}
if (!html) throw new Error("row loop produced no HTML");
const mustRows = ["White (local)", ">Pale<", ">Black<", ">Red<",
  "⏳ loading Q8_0 for Archivist", "1 queued",
  "now: Orchestrator, Scribe", "home: none"];
for (const m2 of mustRows) if (!html.includes(m2)) throw new Error("ROWS missing: " + m2);
console.log("fleet UI render test PASS: 4 named hosts, load-queue line in topology, loading/queued chips in rows");
process.exit(0);