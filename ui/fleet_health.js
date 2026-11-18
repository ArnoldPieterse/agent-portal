/* FleetHealth — composite fleet health score + per-host badges (Builder goal #3).
2026-11-18: new module. Data source: GET /api/health/fleet.
Renders into #fleetHealth (added to index.html fleet panel section).

Scoring model (0-100 per host):
  - probe.status: ok=40, warn=20, critical/unknown=5
  - sync_age_s: null=0, <60s=30, <300s=20, <900s=10, else=5
  - git_head present (repo alive): +15; absent: +0
  - portal_uptime_s > 60: +15 (server stable); else: +5

Composite = mean of all host scores, rounded to integer.
Color bands: >=80 green(ok), >=50 amber(warn), <50 red(critical).

API: FleetHealth.render(containerEl, {live:true, interval_ms:10000}); SAMPLE exported. */
(function(root){
"use strict";

var SAMPLE = {
  ok: true, generated: "2026-11-18 10:00:00",
  hosts: {
    Red:   {probe:{status:"ok",severity:null}, last_sync:"2026-11-18 09:59:30", sync_age_s:30},
    Pale:  {probe:{status:"ok",severity:null}, last_sync:"2026-11-18 09:58:00", sync_age_s:120},
    Black: {probe:{status:"warn",severity:"high"}, last_sync:"2026-11-18 09:45:00", sync_age_s:900},
    White: {probe:null, last_sync:null, sync_age_s:null}
  },
  last_probe_line: "2026-11-18 09:59:30 Red ok port=22",
  git_head: "a1b2c3d 2026-11-18 09:55",
  git_goals_last_change: "e4f5g6h 2026-11-18 09:50",
  portal_uptime_s: 7200
};

function scoreHost(e, ctx) {
  var s = 0;
  // probe (max 40)
  var st = e.probe ? e.probe.status : null;
  if (st === "ok") s += 40;
  else if (st === "warn") s += 20;
  else if (st === "critical") s += 5;
  else s += 10; // unknown/null - partial credit for not being critical
  // sync freshness (max 30)
  var age = e.sync_age_s;
  if (age == null) s += 0;
  else if (age < 60) s += 30;
  else if (age < 300) s += 20;
  else if (age < 900) s += 10;
  else s += 5;
  // git alive (max 15)
  if (ctx.git_head) s += 15;
  // portal stable (max 15)
  if ((ctx.portal_uptime_s || 0) > 60) s += 15; else s += 5;
  return Math.min(100, s);
}

function tone(score) {
  if (score >= 80) return "ok";
  if (score >= 50) return "warn";
  return "critical";
}

function toneColor(t) {
  return t === "ok" ? "#2ecc71" : t === "warn" ? "#f39c12" : "#e74c3c";
}

function render(container, data) {
  if (!data || !data.ok || !data.hosts) {
    container.innerHTML = '<div class="fh-empty">Fleet health data unavailable</div>';
    return;
  }
  var ctx = { git_head: data.git_head, portal_uptime_s: data.portal_uptime_s };
  var names = Object.keys(data.hosts);
  var scores = {};
  for (var i = 0; i < names.length; i++) {
    scores[names[i]] = scoreHost(data.hosts[names[i]], ctx);
  }
  var total = 0;
  for (var n in scores) total += scores[n];
  var composite = Math.round(total / names.length);
  var compTone = tone(composite);

  // Build HTML
  var h = '<div class="fh-wrap">';
  // Composite score bar
  h += '<div class="fh-composite" style="--fh-color:' + toneColor(compTone) + '">';
  h += '<span class="fh-composite-label">Fleet Health</span>';
  h += '<div class="fh-bar"><div class="fh-bar-fill" style="width:' + composite + '%"></div></div>';
  h += '<span class="fh-composite-score">' + composite + '/100</span>';
  h += '</div>';

  // Per-host badges
  h += '<div class="fh-hosts">';
  for (var j = 0; j < names.length; j++) {
    var name = names[j];
    var sc = scores[name];
    var t = tone(sc);
    var e = data.hosts[name];
    var probeSt = e.probe ? e.probe.status : "—";
    var syncTxt = e.sync_age_s != null ? (e.sync_age_s < 60 ? e.sync_age_s + "s" : Math.round(e.sync_age_s/60) + "m") : "never";
    h += '<div class="fh-host-badge" title="' + name + ': probe=' + probeSt + ', sync=' + syncTxt + '" style="--fh-color:' + toneColor(t) + '">';
    h += '<span class="fh-dot"></span>';
    h += '<span class="fh-host-name">' + name + '</span>';
    h += '<span class="fh-score">' + sc + '</span>';
    h += '</div>';
  }
  h += '</div>';

  // Footer: git + uptime
  h += '<div class="fh-footer">';
  if (data.git_head) h += '<span>git ' + data.git_head.split(" ")[0] + '</span>';
  if (data.portal_uptime_s != null) {
    var up = data.portal_uptime_s;
    var upTxt = up < 3600 ? Math.round(up/60) + "m" : Math.round(up/3600) + "h";
    h += '<span>up ' + upTxt + '</span>';
  }
  h += '</div>';
  h += '</div>';

  container.innerHTML = h;
}

var timer = null;
function tick(el, opts) {
  fetch("/api/health/fleet", {cache:"no-store"})
    .then(function(r){ return r.json(); })
    .then(function(d){ render(el, d); })
    .catch(function(){ render(el, null); });
}

function boot() {
  var el = document.getElementById("fleetHealth");
  if (!el || el._fhBooted) return;
  el._fhBooted = true;
  tick(el, {});
  timer = setInterval(function(){
    // Only poll when fleet panel is open (same pattern as core.js)
    var panel = document.getElementById("fleetPanel");
    if (panel && panel.classList.contains("open")) tick(el, {});
  }, 10000);
}

root.FleetHealth = { render: render, SAMPLE: SAMPLE, scoreHost: scoreHost };

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", boot);
} else {
  boot();
}
})(window);
