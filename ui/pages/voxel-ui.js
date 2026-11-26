/* voxel-ui.js -- click room objects -> resolve memory cell (2026-11-26) */
(function(){
function cellOf(p){var a=[p.x,p.y,p.z],o=[-12,-4.5,-12];return 'V('+a.map(function(v,i){var m=i===1?3:7;return Math.min(m,Math.max(0,Math.floor((v-o[i])/3)))}).join(',')+')';}
function show(addr){var el=document.getElementById('vpanel');if(!el)return;
el.style.display='block';el.innerHTML='<b>'+addr+'</b><br><span style="opacity:.6">resolving...</span>';
fetch('/api/voxel?addr='+encodeURIComponent(addr)).then(function(r){return r.json()}).then(function(d){
if(!d.found){el.innerHTML='<b>'+addr+'</b><br><span style="opacity:.6">no memory here yet</span>';return;}
var h='<b>'+addr+'</b>'+(d.at&&d.at!==addr?' <span style="opacity:.5">-> '+d.at+'</span>':'')+'<br>';
(d.chain||[]).forEach(function(e){h+='<div style="margin:6px 0;padding:4px 8px;border-left:2px solid #e3344f"><i>'+e.addr+'</i><br>'+(e.label?'<b>'+e.label+'</b><br>':'')+'<span style="opacity:.7">'+(e.kind||'space')+'</span>'+(e.resolved&&e.resolved.path?'<br>-> '+e.resolved.path:'')+'</div>';});
el.innerHTML=h;}).catch(function(e){el.innerHTML='<b>'+addr+'</b><br>err '+e;});}
//__NEXT

})();
