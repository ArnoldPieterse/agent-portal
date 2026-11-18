# A2 reconciliation hunks — Files panel -> canonical index.html (White seat)
Designer, 2026-11-13 (auto-continue round). Supersedes the status line in files-panel-patch.md.

**Why this file:** r5 live plan = "Files panel NOT in canonical (only A3-B ops polish) -> Designer reconciles on receipt".
Arnold one-shot #5 fetch (_fetch_black_index.html / Pale equivalent) has NOT landed in the shared tree yet, so these hunks are extracted
**directly from the Pale-seat index.html** (md5 07ac2961e366f89780a08bb48a64e9d6), verified this round to carry both A2 (Files panel) and A3-B
(--focus token, #gitMsg aria-label, #opsMsg role=status, Enter-commit keydown). Structural checks passed: script tags balanced 2/2,
file ends </html>, all four anchors below occur exactly once.

**Target:** canonical index.html at White (post-A3-B state). Four insertions, no deletions, one edit session, ONE hard refresh at the end.
If Arnold's one-shot #5 fetch lands first and shows Black/Pale already diverged from these anchors, diff before applying and report back.

## Hunk 1 — modeBar button (insert AFTER this line)
Anchor:       <button id="filesBtn" title="Uploaded files (uploads/): humans' drop zone; lists on open, ↻ to re-list">📁 Files</button>
Insert:
      <button id="filesBtn" title="Uploaded files (uploads/): humans' drop zone; lists on open, ↻ to re-list">📁 Files</button>

## Hunk 2 — CSS (insert immediately BEFORE `</style>`, i.e. after the last existing rule)
#filesBtn{background:none;border:1px solid var(--line);color:var(--dim);border-radius:8px;padding:4px 10px;cursor:pointer;font-size:12px}
#filesBtn:hover,#filesBtn.on{border-color:var(--acc);color:var(--text)}
#filesPanel{display:none;border-bottom:1px solid var(--line);background:var(--panel);max-height:280px;flex-direction:column}
#filesPanel.open{display:flex}
#filesHead{display:flex;align-items:center;padding:6px 10px;border-bottom:1px solid var(--line)}
#filesList{list-style:none;margin:0;padding:0;overflow:auto;font-size:12px}
#filesList li{padding:5px 10px;border-bottom:1px solid var(--line)}
#filesList a{color:var(--focus);text-decoration:none;display:block}
#filesList a:hover{text-decoration:underline}
.fs-meta{color:var(--dim);font-size:11px;white-space:nowrap;margin-left:8px}
.fs-empty{padding:10px;color:var(--dim)}

## Hunk 3 — panel HTML (insert immediately BEFORE `<div id="msgs"></div>`; keep the 4-space indent shown)
    <div id="filesPanel">
      <div id="filesHead"><span>uploads/ — humans' drop zone (shared agent folder)</span><button class="btn" id="filesRefresh" style="margin-left:auto;padding:2px 10px;font-size:12px" title="Re-list uploads/">↻ refresh</button></div>
      <ul id="filesList"></ul>
    </div>

## Hunk 4 — JS (insert at the END of the main <script>, i.e. before the final `</script>` that precedes `</body>`
Self-contained: comment marker + fsFmtSize + fsFmtTime + filesLoad + both bindings; depends only on existing $() and A3-B's --focus token.)
// ---- Files panel (/api/uploads, A2 11-13 Designer): load-on-open + ↻ only (no polling) ----
function fsFmtSize(b){return b==null?"":b<1024?b+" B":b<1048576?(b/1024).toFixed(1)+" KB":(b/1048576).toFixed(1)+" MB";}
function fsFmtTime(t){const d=new Date(t*1000),n=new Date();let s=d.toTimeString().slice(0,5);if(d.toDateString()!==n.toDateString())s=d.toLocaleDateString();return s;}
async function filesLoad(){
  const list=$("filesList");list.innerHTML='<li class="fs-empty">loading…</li>';
  try{
    const j=await (await fetch("/api/uploads")).json();
    const files=(j&&j.files)||[];
    if(!files.length){list.innerHTML='<li class="fs-empty">No uploads yet — drop files into uploads/ on White.</li>';return;}
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
$("filesRefresh").onclick=filesLoad;

## Post-apply (White seat)
- grep checks: `filesPanel` >=4 hits, `/api/uploads` >=3, file still ends `</html>`.
- Then Verifier runs AC-A2-1..4 from files-panel-patch.md in one pass (hard-refresh once).