// Provenance: created 2026-11-23 (White + assistant) during scheduled-task consolidation.
// Live in-process scheduler timers. Mounts at top of #chatCol (NOT main: main is a
// flex row and an extra item there crushed the chat column). Collapsible, collapsed by default.
(function () {
  if (window.__schedPanel) return; window.__schedPanel = true;
  var css = document.createElement('style');
  css.textContent = [
    '#schedPanel{border-bottom:1px solid rgba(120,160,255,.2);font-size:12px;background:rgba(120,160,255,.04)}',
    '#schedPanel .shead{display:flex;align-items:center;gap:8px;padding:5px 16px;cursor:pointer;user-select:none}',
    '#schedPanel .shead:hover{background:rgba(120,160,255,.07)}',
    '#schedPanel .shead b{font-size:11px;letter-spacing:.4px;text-transform:uppercase;opacity:.85}',
    '#schedPanel .smeta{margin-left:auto;font-variant-numeric:tabular-nums}',
    '#schedPanel .ok{color:#6fd68b}#schedPanel .bad{color:#ff7b72}#schedPanel .run{color:#79c0ff}',
    '#schedPanel .srows{display:none;padding:4px 12px 10px;max-height:320px;overflow-y:auto}',
    '#schedPanel.open .srows{display:block}',
    '#schedPanel .row{display:grid;grid-template-columns:150px 52px 1fr 84px 96px;gap:8px;padding:3px 4px;border-top:1px solid rgba(120,160,255,.12);align-items:center}',
    '#schedPanel .row.head{border-top:none;opacity:.55;text-transform:uppercase;font-size:10px}',
    '#schedPanel .cd{font-variant-numeric:tabular-nums;text-align:right}',
    '#schedPanel .row span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}',
    '#modeHint{white-space:nowrap}',
    '#schedPanel button{background:none;border:1px solid rgba(120,160,255,.3);border-radius:4px;color:inherit;font-size:10px;padding:1px 6px;cursor:pointer}',
    '#schedPanel .paused{opacity:.45}'
  ].join('');
  document.head.appendChild(css);
  var box = document.createElement('div');
  box.id = 'schedPanel';
  box.innerHTML =
    '<div class="shead" id="schedToggle">' +
      '<span style="font-size:12px">&#9201;</span>' +
      '<b>In-process scheduler</b>' +
      '<span style="opacity:.5;font-size:11px">(1 schtask: PortalRun -&gt; guardian; rest timed in python)</span>' +
      '<span class="smeta" id="schedMeta">loading...</span>' +
    '</div>' +
    '<div class="srows">' +
      '<div class="row head"><span>job</span><span>every</span><span>note</span><span class="cd">next in</span><span>last / act</span></div>' +
    '</div>';
  var col = document.getElementById('chatCol');
  (col || document.body).insertBefore(box, (col && col.firstChild) || null);

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
      var cdTxt = j.paused ? 'paused' : j.running ? 'running...' : fmt(j.next_run - now);
      var lastCls = j.last_rc === 0 || j.last_rc === null ? 'ok' : 'bad';
      var lastTxt = j.last_run ? ('rc ' + j.last_rc) : 'never';
      if (j.last_err && j.last_rc !== 0) lastTxt += ' - ' + esc(j.last_err.slice(0, 28));
      var btn = j.paused ? '<button data-a="resume" data-j="' + j.name + '">run</button>' : '<button data-a="pause" data-j="' + j.name + '">pause</button> ';
      rows += '<div class="row' + (j.paused ? ' paused' : '') + '"><span>' + esc(j.name) + '</span><span>' + everyLabel(j.interval) +
        '</span><span title="' + esc(j.note) + '" style="opacity:.6">' + esc(j.note.slice(0, 48)) + '</span>' +
        '<span class="' + cdCls + '">' + cdTxt + '</span><span class="' + lastCls + '">' + lastTxt + ' ' + btn + '</span></div>';
    });
    var rowsEl = box.querySelector('.srows');
    rowsEl.querySelectorAll('.row:not(.head)').forEach(function (r) { r.remove(); });
    var frag = document.createElement('div');
    frag.innerHTML = rows;
    while (frag.firstChild) rowsEl.appendChild(frag.firstChild);
    box.querySelectorAll('button').forEach(function (b) {
      b.onclick = function () {
        fetch('/api/scheduler', {method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({job: b.dataset.j, action: b.dataset.a})}).catch(function () {});
      };
    });
    var meta = document.getElementById('schedMeta');
    meta.innerHTML = '<span class="ok">' + okc + ' ok</span>' + (badc ? ' <span class="bad">' + badc + ' failing</span>' : '');
  }

  document.getElementById('schedToggle').onclick = function () { box.classList.toggle('open'); };
  setInterval(function () {
    fetch('/api/scheduler').then(function (r) { return r.json(); }).then(render).catch(function () {});
  }, 2000);
})();
