/* voxel-ui.js -- click room objects -> resolve memory cell (2026-11-26) */
(function(){
function cellOf(p){var a=[p.x,p.y,p.z],o=[-12,-4.5,-12];return 'V('+a.map(function(v,i){var m=i===1?3:7;return Math.min(m,Math.max(0,Math.floor((v-o[i])/3)))}).join(',')+')';}
function show(addr){var el=document.getElementById('vpanel');if(!el)return;
el.style.display='block';el.innerHTML='<b>'+addr+'</b><br><span style="opacity:.6">resolving...</span>';
fetch('/api/voxel?addr='+encodeURIComponent(addr)).then(function(r){return r.json()}).then(function(d){
if(!d.found){el.innerHTML='<b>'+addr+'</b><br><span style="opacity:.6">no memory here yet</span>';return;}
var h='<b>'+addr+'</b>'+(d.at&&d.at!==addr?' <span style="opacity:.5">-> '+d.at+'</span>':'')+'<br>';
(d.chain||[]).forEach(function(e){h+='<div style="margin:6px 0;padding:4px 8px;border-left:2px solid #e3344f"><i>'+e.addr+'</i><br>'+(e.label?'<b>'+e.label+'</b><br>':'')+'<span style="opacity:.7">'+(e.kind||'space')+'</span>'+(e.resolved&&e.resolved.path?'<br>-> '+e.resolved.path:'')+(e.rigid?'<br><button data-r="'+e.rigid+'" style="margin-top:4px;background:#1a2035;color:#ffd76a;border:1px solid #ffd76a;border-radius:4px;cursor:pointer">animate rigid body</button>':'')+'</div>';
 if(e.children&&e.children.length){h+='<div style="margin:2px 0 2px 10px;font-size:11px">'+e.children.map(function(c){return '<a href="#" data-v="'+c+'" style="color:#7fd4ff;margin-right:8px">sub '+c.replace(/^V\([^)]+\)/,'')+'</a>'}).join('')+'</div>';}});
el.innerHTML=h;}).catch(function(e){el.innerHTML='<b>'+addr+'</b><br>err '+e;});}
/* rigid-body pulse (2026-11-26) */
function pulseRigid(name){var m=window.__mind;if(!m||!m.rigids)return;var o=m.rigids[name];if(!o||!o.scale)return;
 if(!o.userData.__s0)o.userData.__s0=o.scale.clone();
 var t0=performance.now();(function step(){var t=(performance.now()-t0)/1000;if(t>2.4){o.scale.copy(o.userData.__s0);return;}
  o.scale.copy(o.userData.__s0).multiplyScalar(1+.16*Math.sin(t*9)*Math.exp(-t*.7));requestAnimationFrame(step);})();}
/* click room -> resolve cell (2026-11-26) */
var box=null;
function markPoint(p){var m=window.__mind;if(!m||!THREE)return;if(box)m.scene.remove(box);
 var o=[-12,-4.5,-12],f=function(v,i){return Math.min(i===1?3:7,Math.max(0,Math.floor((v-o[i])/3)))};
 box=new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.BoxGeometry(3,3,3)),new THREE.LineBasicMaterial({color:0xe3344f}));
 box.position.set(o[0]+(f(p.x,0)+.5)*3,o[1]+(f(p.y,1)+.5)*3,o[2]+(f(p.z,2)+.5)*3);m.scene.add(box);}
function init(){var m=window.__mind;if(!m||!THREE)return;
 var pel=document.getElementById('vpanel');
 if(pel)pel.addEventListener('click',function(ev){var t=ev.target;
  if(t.dataset&&t.dataset.v){ev.preventDefault();show(t.dataset.v);}
  if(t.dataset&&t.dataset.r){pulseRigid(t.dataset.r);}});
 var rc=new THREE.Raycaster(),vv=new THREE.Vector2();
 m.canvas.addEventListener('click',function(ev){var r=m.canvas.getBoundingClientRect();
  vv.set((ev.clientX-r.left)/r.width*2-1,-(ev.clientY-r.top)/r.height*2+1);
  rc.setFromCamera(vv,m.camera);var hits=rc.intersectObjects(m.scene.children,true);
  if(!hits.length)return;show(cellOf(hits[0].point));markPoint(hits[0].point);});}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();

})();
