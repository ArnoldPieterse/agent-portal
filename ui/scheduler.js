// Provenance: created 2026-11-23 (White + assistant) during scheduled-task consolidation.
// Live in-process scheduler timers. Self-mounts at end of <main>; no index.html edit needed.
(function () {
  if (window.__schedPanel) return; window.__schedPanel = true;
  var css = document.createElement('style');
  css.textContent = [
    '#schedPanel{margin:14px 0;border:1px solid rgba(120,160,255,.25);border-radius:8px;padding:10px 12px;font-size:12px}',
    '#schedPanel h3{margin:0 0 8px;font-size:13px;letter-spacing:.4px;display:flex;justify-content:space-between}',
    '#schedPanel .row{display:grid;grid-template-columns:170px 64px 1fr 90px 92px;gap:8px;padding:3px 4px;border-top:1px solid rgba(120,160,255,.12);align-items:center}',
    '#schedPanel .row.head{border-top:none;opacity:.55;text-transform:uppercase;font-size:10px}',
    '#schedPanel .cd{font-variant-numeric:tabular-nums;text-align:right}',
    '#schedPanel .ok{color:#6fd68b}#schedPanel .bad{color:#ff7b72}#schedPanel .run{color:#79c0ff}',
    '#schedPanel button{background:none;border:1px solid rgba(120,160,255,.3);border-radius:4px;color:inherit;font-size:10px;padding:1px 6px;cursor:pointer}',
    '#schedPanel .paused{opacity:.45}'
  ].join('');
  document.head.appendChild(css);
  var box = document.createElement('div');
  box.id = 'schedPanel';
  box.innerHTML = '<h3><span>IN-PROCESS SCHEDULER <span style="opacity:.5">(1 schtask: PortalRun → guardian; rest timed in python)</span></span><span id="schedMeta"></span></h3>' +
    '<div class="row head"><span>job</span><span>every</span><span>note</span><span class="cd">next in</span><span>last / act</span></div>';
  var main = document.querySelector('main') || document.body;
  main.appendChild(box);

  function fmt(s) {
    if (s < 0) s = 0;
    var h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), ss = Math.floor(s % 60);
    return (h ? h + 'h ' : '') + m + 'm ' + String(ss).padStart(2, '0') + 's';
  }
  function everyLabel(i) { return i >= 86400 ? Math.round(i / 86400) + 'd' : i >= 3600 ? (i / 3600) + 'h' : (i / 60) + 'm'; }

  function esc(t) { var d = document.createElement('span'); d.textContent = t || ''; return d.innerHTML; }

  function render(data) {
    var now = data.now;
    var rows = '';
    var okc = 0, badc = 0;
    data.jobs.forEach(function (j) {
      if (j.last_rc === 0 || j.last_rc === null) okc++; else badc++;
      var cdCls = j.running ? 'cd run' : 'cd';
      var cdTxt = j.paused ? 'paused' : j.running ? 'running…' : fmt(j.next_run - now);
      var lastCls = j.last_rc === 0 || j.last_rc === null ? 'ok' : 'bad';
      var lastTxt = j.last_run ? ('rc ' + j.last_rc) : 'never';
      if (j.last_err && j.last_rc !== 0) lastTxt += ' · ' + esc(j.last_err.slice(0, 40));
      var btn = j.paused ? '<button data-a="resume" data-j="' + j.name + '">run</button>' : '<button data-a="pause" data-j="' + j.name + '">pause</button> ';
      rows += '<div class="row' + (j.paused ? ' paused' : '') + '"><span>' + esc(j.name) + '</span><span>' + everyLabel(j.interval) +
        '</span><span title="' + esc(j.note) + '" style="opacity:.6">' + esc(j.note.slice(0, 48)) + '</span>' +
        '<span class="' + cdCls + '">' + cdTxt + '</span><span class="' + lastCls + '">' + lastTxt + ' ' + btn + '</span></div>';
      // action cell: keep grid simple — put buttons in note tooltip? No: append to last cell
    });
    box.querySelectorAll('.row:not(.head)').forEach(function (r, i) { r.remove(); });
    var frag = document.createElement('div');
    frag.innerHTML = rows;
    while (frag.firstChild) box.appendChild(frag.firstChild);
    // wire buttons (re-rendered each tick)
    box.querySelectorAll('button').forEach(function (b) {
      b.onclick = function () {
        fetch('/api/scheduler', {method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({job: b.dataset.j, action: b.dataset.a})}).catch(function () {});
      };
    });
    document.getElementById('schedMeta').textContent = okc + ' ok · ' + badc + ' failing';
  }

  setInterval(function () {
    fetch('/api/scheduler').then(function (r) { return r.json(); }).then(render).catch(function () {});
  }, 2000);
})();
