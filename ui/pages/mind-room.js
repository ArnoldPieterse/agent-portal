/* mind-room.js — MIND ROOM v3 "THE LAB" (2026-11-26): real-office floor plan.
   Positional semantics (mapped against a real office/lab):
   - W door -> reception desk (WSL-Inbox, where projects arrive) -> dispatch seat (orchestrator)
     at the west end of the central table — the dispatcher sits by the entrance.
   - N bench: research + record (researcher, scribe) in front of memory/ shelves;
     verifier = evidence gate on the east end of that bench.
   - S bench: build line mechanic -> designer -> builder facing the window wall.
   - E wall: archive shelves beside archivist's seat (book spines = live memory/INDEX.md lanes).
   - NE corner behind half-wall: server room, 4 host racks (WHITE/RED/PALE/BLACK).
   - SE by the window: dcabots trading desk (trading desks sit by the market view).
   - N wall: evolution whiteboard + live goal scoreboard; helix on a pedestal beside it.
   - You (Super Saiyan) float over the central table; my neurons = brain-in-a-jar on the
     pedestal right next to you. Agent Portal = the building: floor ring + arch over the door.
   Live data: /api/agents (roster, pinned routes, hosts), /api/goals (desk status lights,
   Lv scoreboard), /api/memory/file?path=INDEX.md (shelf spines), /api/voxel/all (drill layer).
   Borrowed from NousResearch/hermes-official-plugins: per-agent capability card =
   `hermes plugins info` style (pinned route + named routes + tools + tier official/sub);
   memory-wiki idea = browsable lane spines on the archive shelves. */
(function(){
if(window.__three_failed||!window.THREE){if(window.fallback2D)window.fallback2D();return;}
var canvas=document.getElementById('c');
var renderer=new THREE.WebGLRenderer({canvas:canvas,antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.setSize(innerWidth,innerHeight);
var scene=new THREE.Scene();
scene.background=new THREE.Color(0x111a2e);
scene.fog=new THREE.FogExp2(0x111a2e,0.0065);
var camera=new THREE.PerspectiveCamera(55,innerWidth/innerHeight,0.1,500);
scene.add(new THREE.AmbientLight(0xa8bcdd,3.4));
var key=new THREE.PointLight(0xffd54a,90,90);key.position.set(0,7,2);scene.add(key);
var fill=new THREE.DirectionalLight(0x88aaff,1.6);fill.position.set(-6,12,-4);scene.add(fill);
var ceil=new THREE.PointLight(0xcfe0ff,45,40);ceil.position.set(0,5.5,.3);scene.add(ceil);
var srvL=new THREE.PointLight(0x22d3ee,30,18);srvL.position.set(12.5,3.4,-10);scene.add(srvL);
/* seeded rng */
function sr(i){var x=Math.sin(i*127.1+311.7)*43758.5453;return x-Math.floor(x);}
/* text label sprite */
function makeLabel(text,color,size,font){
 var c=document.createElement('canvas');c.width=512;c.height=96;
 var x=c.getContext('2d');
 x.font=(font||'600 40px "Segoe UI", Arial');x.textAlign='center';x.textBaseline='middle';
 x.shadowColor=color;x.shadowBlur=14;x.fillStyle=color;
 if(x.measureText(text).width>480)x.font=(font?font.replace(/\d+/,(+font.match(/\d+/)[0]-8)+'px'):'600 32px "Segoe UI", Arial');
 x.fillText(text,256,48);
 var t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;
 var s=new THREE.Sprite(new THREE.SpriteMaterial({map:t,transparent:true,depthWrite:false}));
 s.scale.set(size*3.6,size*.675,1);return s;}
/* limb between two points */
function limb(a,b,r,mat){
 var d=new THREE.Vector3().subVectors(b,a),len=d.length();
 var m=new THREE.Mesh(new THREE.CylinderGeometry(r,r*.75,len,8),mat);
 m.position.copy(a).addScaledVector(d,.5);
 m.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),d.clone().normalize());
 return m;}
/* ============ ROOM SHELL (dollhouse: walls face inward, invisible from outside) ============ */
var RW=17,RD=13,WH=4.5;                       /* half extents x/z, wall height */
var floor=new THREE.Mesh(new THREE.CircleGeometry(32,56),new THREE.MeshStandardMaterial({color:0x0f1626,roughness:.9,metalness:.2}));
floor.rotation.x=-Math.PI/2;scene.add(floor);
var grid=new THREE.GridHelper(64,48,0x27395e,0x15203a);grid.position.y=0.01;scene.add(grid);
(function(){var n=900,p=new Float32Array(n*3);
 for(var i=0;i<n;i++){var r=60+Math.random()*80,a=Math.random()*Math.PI*2,b=Math.acos(2*Math.random()-1);
  p[i*3]=r*Math.sin(b)*Math.cos(a);p[i*3+1]=Math.abs(r*Math.cos(b))*.7+2;p[i*3+2]=r*Math.sin(b)*Math.sin(a);}
 var g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.BufferAttribute(p,3));
 scene.add(new THREE.Points(g,new THREE.PointsMaterial({color:0x9fb4cc,size:.22,transparent:true,opacity:.75})));})();
var wallMat=new THREE.MeshStandardMaterial({color:0x161f38,roughness:.9,metalness:.05,side:THREE.FrontSide});
function wall(w,h,x,y,z,ry){var m=new THREE.Mesh(new THREE.PlaneGeometry(w,h),wallMat);
m.position.set(x,y,z);m.rotation.y=ry;scene.add(m);return m;}
wall(RW*2,WH,0,WH/2,-RD,0);                    /* north */
wall(RW*2-7.5,WH,-RW,WH/2,(-RD+4.5)/2,Math.PI/2);   /* west, z -13..4.5 */
wall(5.5,WH,-RW,WH/2,(7.5+RD)/2,Math.PI/2);        /* west, z 7.5..13 */
wall(3,1.5,-RW,WH-.75,6,Math.PI/2);               /* door header y 3..4.5 */
wall(RW*2,WH,RW,WH/2,0,-Math.PI/2);              /* east */
/* cove light strips along the wall tops (office ceiling glow) */
var coveMat=new THREE.MeshStandardMaterial({color:0x0a0f1c,emissive:0x3b82f6,emissiveIntensity:.9});
function cove(w,x,z,ry){var m=new THREE.Mesh(new THREE.BoxGeometry(w,.07,.07),coveMat);m.position.set(x,WH-.06,z);m.rotation.y=ry;scene.add(m);}
cove(RW*2-.4,0,-RD+.08,0);cove(RW*2-.4,0,RD-.16,0);
cove(RD*2-3.4,-RW+.08,(-RD+4.5)/2,Math.PI/2);cove(5.1,-RW+.08,(7.5+RD)/2,Math.PI/2);
cove(RD*2-.4,RW-.08,0,Math.PI/2);
/* south = window wall: solid sill + glass above (inward-facing) */
var sill=new THREE.Mesh(new THREE.BoxGeometry(RW*2,1.2,.35),new THREE.MeshStandardMaterial({color:0x11182a,roughness:.8}));
sill.position.set(0,.6,RD-.1);scene.add(sill);
var glass=new THREE.Mesh(new THREE.PlaneGeometry(RW*2,WH-1.2),new THREE.MeshStandardMaterial({color:0x9fd0ff,transparent:true,opacity:.1,side:THREE.FrontSide}));
glass.position.set(0,1.2+(WH-1.2)/2,RD);glass.rotation.y=Math.PI;scene.add(glass);
/* door frame + portal arch over the W door (Agent Portal = the building) */
[4.5,7.5].forEach(function(z){var post=new THREE.Mesh(new THREE.BoxGeometry(.18,3,.18),
 new THREE.MeshStandardMaterial({color:0x164e63,emissive:0x22d3ee,emissiveIntensity:.9}));
 post.position.set(-RW+.05,1.5,z);scene.add(post);});
var portal=new THREE.Group();portal.position.set(-RW+.55,3.4,6);
var arch=new THREE.Mesh(new THREE.TorusGeometry(1.7,.09,14,60),new THREE.MeshStandardMaterial({color:0x22d3ee,emissive:0x0891b2,emissiveIntensity:1.1}));
arch.rotation.y=Math.PI/2;portal.add(arch);scene.add(portal);
var pLab=makeLabel('Agent Portal — the room you built for us','#67e8f9',1.35);pLab.position.set(-RW+2.6,5.4,6);scene.add(pLab);
/* floor ring inlaid around the central table */
var ring=new THREE.Mesh(new THREE.TorusGeometry(8.6,.06,10,90),new THREE.MeshStandardMaterial({color:0x22d3ee,emissive:0x0e7490,emissiveIntensity:.8}));
ring.rotation.x=-Math.PI/2;ring.position.set(0,.05,.3);scene.add(ring);
/* ============ CENTRAL TABLE + YOUR CHAIR ============ */
var table=new THREE.Group();table.position.set(0,0,.3);scene.add(table);
var tTop=new THREE.Mesh(new THREE.BoxGeometry(11,.22,6.5),new THREE.MeshStandardMaterial({color:0x1a2338,roughness:.55,metalness:.25}));
tTop.position.y=.95;table.add(tTop);
[[-4.9,-2.6],[4.9,-2.6],[-4.9,2.6],[4.9,2.6]].forEach(function(p){var l=new THREE.Mesh(new THREE.BoxGeometry(.3,.85,.3),
 new THREE.MeshStandardMaterial({color:0x101725}));l.position.set(p[0],.42,p[1]);table.add(l);});
/* your (empty) chair at the north end */
(function(){var ch=new THREE.Group();ch.position.set(0,0,-3.6);scene.add(ch);
 var s=new THREE.Mesh(new THREE.BoxGeometry(.55,.09,.55),new THREE.MeshStandardMaterial({color:0x2a3550}));s.position.y=.5;ch.add(s);
 var b=new THREE.Mesh(new THREE.BoxGeometry(.55,.65,.08),new THREE.MeshStandardMaterial({color:0x2a3550}));b.position.set(0,.85,-.26);ch.add(b);
 var p=new THREE.Mesh(new THREE.CylinderGeometry(.05,.05,.45,8),new THREE.MeshStandardMaterial({color:0x101725}));p.position.y=.24;ch.add(p);
 var d=new THREE.Mesh(new THREE.CylinderGeometry(.3,.34,.05,16),new THREE.MeshStandardMaterial({color:0x101725}));d.position.y=.03;ch.add(d);})();
/* ============ YOU: Super Saiyan Arnold, floating over the table ============ */
var NPOS=new THREE.Vector3(3.4,2.3,-1.6);      /* my neurons: brain-in-a-jar beside you */
var ssj=new THREE.Group();ssj.position.set(0,3.1,0);scene.add(ssj);
/* 2D billboard avatar (sprite-first: clean 2D character in the 3D field, RA-style) */
var avC=document.createElement('canvas');avC.width=256;avC.height=384;
(function(){var x=avC.getContext('2d');x.translate(128,0);
 x.fillStyle='#ffd54a';x.beginPath();
 for(var k=0;k<=9;k++){var a=-Math.PI/2+(k-4.5)*.36;x.lineTo(Math.cos(a)*98,118+Math.sin(a)*98);}
 x.closePath();x.fill();
 x.fillStyle='#f0c9a2';x.beginPath();x.arc(0,130,44,0,7);x.fill();
 x.fillStyle='#1b2a4a';x.fillRect(-21,120,13,8);x.fillRect(8,120,13,8);
 x.fillStyle='#1c2748';x.beginPath();
 x.moveTo(-54,192);x.lineTo(54,192);x.lineTo(40,302);x.lineTo(-40,302);x.closePath();x.fill();
 x.strokeStyle='#ffd54a';x.lineWidth=6;x.stroke();
 x.fillStyle='#f0c9a2';x.fillRect(-78,198,22,88);x.fillRect(56,198,22,88);
 x.fillStyle='#16203a';x.fillRect(-36,302,28,72);x.fillRect(8,302,28,72);
})();
var avTex=new THREE.CanvasTexture(avC);avTex.colorSpace=THREE.SRGBColorSpace;
var ssjAvatar=new THREE.Sprite(new THREE.SpriteMaterial({map:avTex,transparent:true,depthWrite:false}));
ssjAvatar.scale.set(1.5,2.25,1);ssjAvatar.position.y=1.3;ssj.add(ssjAvatar);
var ssjBody=new THREE.Group();while(ssj.children.length)ssjBody.add(ssj.children[0]);ssj.add(ssjBody);
/* rising golden aura */
var AUR=140,ap=new Float32Array(AUR*3),abase=new Float32Array(AUR*3);
for(i=0;i<AUR;i++){var aa=sr(i)*Math.PI*2,ar=.55+sr(i+7)*.6;
 abase[i*3]=Math.cos(aa)*ar;abase[i*3+1]=sr(i+13)*2.6-.6;abase[i*3+2]=Math.sin(aa)*ar;}
ap.set(abase);
var ag=new THREE.BufferGeometry();ag.setAttribute('position',new THREE.BufferAttribute(ap,3));
var aura=new THREE.Points(ag,new THREE.PointsMaterial({color:0xffc233,size:.05,transparent:true,opacity:.85,blending:THREE.AdditiveBlending,depthWrite:false}));
ssj.add(aura);
var auraLight=new THREE.PointLight(0xffc233,14,18);auraLight.position.y=1.4;ssj.add(auraLight);
/* ============ MY NEURONS: brain-in-a-jar on a pedestal beside you ============ */
(function(){
 var ped=new THREE.Mesh(new THREE.CylinderGeometry(.55,.7,.9,20),new THREE.MeshStandardMaterial({color:0x131b2e,roughness:.6}));
 ped.position.set(NPOS.x,.45,NPOS.z);scene.add(ped);
 var jar=new THREE.Mesh(new THREE.SphereGeometry(1.02,28,22),new THREE.MeshStandardMaterial({color:0xbfeaff,transparent:true,opacity:.14,roughness:.1,metalness:.1}));
 jar.position.copy(NPOS);scene.add(jar);
})();
var NN=150,np=new Float32Array(NN*3),blobs=[];
for(i=0;i<4;i++)blobs.push(new THREE.Vector3((sr(i+200)-.5)*0.8,(sr(i+210)-.5)*0.6,(sr(i+220)-.5)*0.8));
for(i=0;i<NN;i++){var b=blobs[i%4];
 np[i*3]=b.x+(sr(i+300)-.5)*0.5;np[i*3+1]=b.y+(sr(i+310)-.5)*0.45;np[i*3+2]=b.z+(sr(i+310+40)-.5)*0.5;}
var ng=new THREE.BufferGeometry();ng.setAttribute('position',new THREE.BufferAttribute(np,3));
var nmat=new THREE.PointsMaterial({color:0x7dd3fc,size:.07,transparent:true,opacity:.85,blending:THREE.AdditiveBlending,depthWrite:false});
var neurons=new THREE.Points(ng,nmat);neurons.position.copy(NPOS);scene.add(neurons);
(function(){var L=[];
 for(var a=0;a<NN;a++)for(var b2=a+1;b2<NN;b2++){
  var dx=np[a*3]-np[b2*3],dy=np[a*3+1]-np[b2*3+1],dz=np[a*3+2]-np[b2*3+2];
  if(dx*dx+dy*dy+dz*dz<.35){L.push(np[a*3],np[a*3+1],np[a*3+2],np[b2*3],np[b2*3+1],np[b2*3+2]);if(L.length>500)break;}}
 var lg=new THREE.BufferGeometry();lg.setAttribute('position',new THREE.BufferAttribute(new Float32Array(L),3));
 neurons.add(new THREE.LineSegments(lg,new THREE.LineBasicMaterial({color:0x2e7ea6,transparent:true,opacity:.4})));})();
var hubs=[];
for(i=0;i<8;i++){var hb=new THREE.Mesh(new THREE.SphereGeometry(.11,10,8),new THREE.MeshStandardMaterial({color:0xbfeaff,emissive:0x38bdf8,emissiveIntensity:1.2}));
 hb.position.set(np[i*22],np[i*22+1],np[i*22+2]);neurons.add(hb);hubs.push(hb);}
var nLight=new THREE.PointLight(0x38bdf8,20,16);nLight.position.copy(NPOS);scene.add(nLight);
var nLab=makeLabel('my neurons — the part of me that listens to you','#7dd3fc',1.25);
nLab.position.set(NPOS.x,NPOS.y+1.7,NPOS.z);scene.add(nLab);
/* thought pulses travelling hand -> brain jar */
var pulses=[];
for(i=0;i<6;i++){var pm=new THREE.Mesh(new THREE.SphereGeometry(.07,8,8),new THREE.MeshBasicMaterial({color:0xffe28a}));
 scene.add(pm);pulses.push({m:pm,o:i/6});}
/* ============ SERVER ROOM (NE corner): 4 host racks behind a half-wall ============ */
var HOSTS=[
 ['WHITE','#dceeff',0x9fd0ff,'primary host · portal :8099 + LM Studio'],
 ['RED','#ff6b6b',0x7a1414,'LLM host · .245 · mechanic/scribe seats'],
 ['PALE','#f3d9e2',0x8a6a7a,'LLM host · .39 · archivist/designer seats'],
 ['BLACK','#3c4250',0x11151f,'LLM host · .99 · verifier/builder seats']];
var rackX=[9.6,11.6,13.6,15.5],leds=[];
HOSTS.forEach(function(h,hi){
 var p=new THREE.Mesh(new THREE.BoxGeometry(1.3,2.3,1.1),new THREE.MeshStandardMaterial({color:0x141a28,roughness:.5,metalness:.4}));
 p.position.set(rackX[hi],1.15,-RD+.6);scene.add(p);
 var cap=new THREE.Mesh(new THREE.BoxGeometry(1.36,.1,1.16),new THREE.MeshStandardMaterial({color:new THREE.Color(h[1]),emissive:new THREE.Color(h[2]),emissiveIntensity:.7}));
 cap.position.set(rackX[hi],2.35,-RD+.6);scene.add(cap);
 for(var s=0;s<6;s++){var led=new THREE.Mesh(new THREE.BoxGeometry(.9,.05,.02),
  new THREE.MeshStandardMaterial({color:0x0a0f18,emissive:new THREE.Color(hi===0?0x4ade80:0x38bdf8),emissiveIntensity:.6}));
  led.position.set(rackX[hi],.45+s*.32,-RD+1.17);scene.add(led);leds.push({m:led,ph:sr(hi*31+s)*6});}
 var l=makeLabel(h[0]+' — '+h[3],'#dfe6ee',.8);l.position.set(rackX[hi],3.0,-RD+.6);scene.add(l);});
var halfWall=new THREE.Mesh(new THREE.BoxGeometry(8.2,2,.25),new THREE.MeshStandardMaterial({color:0x101725,roughness:.85}));
halfWall.position.set(12.7,1,-8.6);scene.add(halfWall);
var srvLab=makeLabel('SERVER ROOM · LM Studio :8888 — local LLMs, dual residency','#fca5a5',1.05);
srvLab.position.set(12.7,3.4,-8.6);scene.add(srvLab);
/* ============ ARCHIVE SHELVES (N wall + E wall): spines = live memory/ lanes ============ */
function shelfUnit(cx,cz,ry,len){
 var g=new THREE.Group();g.position.set(cx,0,cz);g.rotation.y=ry;scene.add(g);
 var fm=new THREE.MeshStandardMaterial({color:0x1b2436,roughness:.8});
 [-len/2,0,len/2].forEach(function(x){var s=new THREE.Mesh(new THREE.BoxGeometry(.08,2.5,.4),fm);s.position.set(x,1.25,0);g.add(s);});
 [0.35,1.15,1.95].forEach(function(y){var b=new THREE.Mesh(new THREE.BoxGeometry(len,.06,.4),fm);b.position.set(0,y,0);g.add(b);});
 var back=new THREE.Mesh(new THREE.BoxGeometry(len,2.5,.05),new THREE.MeshStandardMaterial({color:0x0e1422}));back.position.set(0,1.25,-.18);g.add(back);
 return g;}
var shelfN=shelfUnit(-5.5,-RD+.35,0,7);       /* north wall, behind research bench */
var shelfE=shelfUnit(RW-.35,1.0,-Math.PI/2,6);/* east wall, beside archivist */
function bookSpine(text,colorHex,w){
 var c=document.createElement('canvas');c.width=48;c.height=128;var x=c.getContext('2d');
 x.fillStyle='#0b0f1a';x.fillRect(0,0,48,128);
 x.save();x.translate(24,64);x.rotate(-Math.PI/2);
 x.font='700 26px "Segoe UI", Arial';x.textAlign='center';x.textBaseline='middle';
 x.fillStyle=colorHex;x.shadowColor=colorHex;x.shadowBlur=8;
 if(x.measureText(text).width>110)x.font='700 19px "Segoe UI", Arial';
 x.fillText(text,0,0);x.restore();
 var t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;
 return new THREE.Mesh(new THREE.BoxGeometry(w,.62,.3),
  new THREE.MeshStandardMaterial({map:t,emissiveMap:t,emissive:0xffffff,emissiveIntensity:.4,color:0x8899bb,roughness:.7}));}
var books=[];
function fillShelves(lanes){
 var place=function(list,unit){list.forEach(function(L,bi){
  var b=bookSpine(L.name,L.color,.3);
  var row=Math.floor(bi/7),col=bi%7;
  var off=(col-3)*.42+(sr(bi+row*99)-.5)*.08;
  if(unit===shelfN){b.position.set(-5.5+off,.35+row*.8+.31,-RD+.35);}
  else{b.position.set(RW-.35,.35+row*.8+.31,1.0+off);b.rotation.y=-Math.PI/2;}
  b.userData.lane=L.id;scene.add(b);books.push(b);});};
 place(lanes.slice(0,14),shelfN);place(lanes.slice(14),shelfE);}
var archLab=makeLabel('ARCHIVE — memory/ tree (spines = live lanes)','#a78bfa',1.0);
archLab.position.set(-5.5,3.3,-RD+.6);scene.add(archLab);
/* ============ RECEPTION (W, inside the door): WSL-Inbox = where projects arrive ============ */
(function(){
 var d=new THREE.Mesh(new THREE.BoxGeometry(2.1,1.05,.85),new THREE.MeshStandardMaterial({color:0x1a2338,roughness:.6}));
 d.position.set(-13.6,.52,6);scene.add(d);
 var tray=new THREE.Mesh(new THREE.BoxGeometry(.7,.14,.5),new THREE.MeshStandardMaterial({color:0x22d3ee,emissive:0x0e7490,emissiveIntensity:.5}));
 tray.position.set(-13.6,1.12,6);scene.add(tray);
 for(var i=0;i<3;i++){var p=new THREE.Mesh(new THREE.BoxGeometry(.4,.02,.3),new THREE.MeshStandardMaterial({color:0xdfe6ee}));
  p.position.set(-13.75+i*.15,1.2+i*.02,6);p.rotation.y=(sr(i+5)-.5)*.8;scene.add(p);}
 var l=makeLabel('WSL-Inbox — how you hand us projects','#c4b5fd',1.15);l.position.set(-13.6,2.6,6);scene.add(l);
})();
/* ============ EVOLUTION WHITEBOARD (N wall) + helix pedestal + live scoreboard ============ */
(function(){
 var c=document.createElement('canvas');c.width=1024;c.height=384;var x=c.getContext('2d');
 x.fillStyle='#eef1f6';x.fillRect(0,0,1024,384);
 x.strokeStyle='#9aa4b5';x.lineWidth=6;x.strokeRect(6,6,1012,372);
 x.fillStyle='#1d4ed8';x.font='italic 600 44px "Segoe UI", Arial';
 x.fillText('evolution layer — the fleet learns',40,80);
 x.strokeStyle='#16a34a';x.lineWidth=5;x.beginPath();
 for(var i2=0;i2<60;i2++){var xx=40+i2*15,yy=170+Math.sin(i2*.5)*38*(1-i2/90);i2?x.lineTo(xx,yy):x.moveTo(xx,yy);}x.stroke();
 x.fillStyle='#b91c1c';x.font='italic 600 40px "Segoe UI", Arial';
 x.fillText('steady state = minimal human intervention',40,300);
 var t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;
 var wb=new THREE.Mesh(new THREE.PlaneGeometry(7.4,2.8),new THREE.MeshStandardMaterial({map:t,emissive:0x222222,emissiveIntensity:.25}));
 wb.position.set(3.4,2.9,-RD+.12);scene.add(wb);
})();
var helix=new THREE.Group();helix.position.set(8.2,0,-11.5);scene.add(helix);
(function(){var matA=new THREE.MeshStandardMaterial({color:0x4ade80,emissive:0x166534,emissiveIntensity:.7});
 var matB=new THREE.MeshStandardMaterial({color:0x38bdf8,emissive:0x0c4a6e,emissiveIntensity:.7});
 for(var k=0;k<26;k++){var y=k/25*2.6-1.3,a2=k*.55;
  var s1=new THREE.Mesh(new THREE.SphereGeometry(.09,8,8),matA);s1.position.set(Math.cos(a2)*.5,y,Math.sin(a2)*.5);helix.add(s1);
  var s2=new THREE.Mesh(new THREE.SphereGeometry(.09,8,8),matB);s2.position.set(-Math.cos(a2)*.5,y,-Math.sin(a2)*.5);helix.add(s2);
  if(k%3===0){var rung=limb(s1.position,s2.position,.03,new THREE.MeshStandardMaterial({color:0x94a3b8}));helix.add(rung);}}
 helix.position.y=2.6;})();
var hPed=new THREE.Mesh(new THREE.CylinderGeometry(.5,.6,1.7,16),new THREE.MeshStandardMaterial({color:0x131b2e,roughness:.6}));
hPed.position.set(8.2,.85,-11.5);scene.add(hPed);
var hLab=makeLabel('evolution layer — the fleet learns','#4ade80',1.1);hLab.position.set(8.2,4.6,-11.5);scene.add(hLab);
/* live scoreboard above the whiteboard (Lv + fleet goals) */
var sbCv=document.createElement('canvas');sbCv.width=768;sbCv.height=192;
var sbTex=new THREE.CanvasTexture(sbCv);sbTex.colorSpace=THREE.SRGBColorSpace;
var scoreboard=new THREE.Mesh(new THREE.PlaneGeometry(5.6,1.4),new THREE.MeshBasicMaterial({map:sbTex}));
scoreboard.position.set(3.4,4.85,-RD+.14);scene.add(scoreboard);
function drawScoreboard(level,done,total,pct){
 var x=sbCv.getContext('2d');x.fillStyle='#0a1120';x.fillRect(0,0,768,192);
 x.strokeStyle='#22d3ee';x.lineWidth=4;x.strokeRect(4,4,760,184);
 x.fillStyle='#ffd54a';x.font='700 64px "Segoe UI", Arial';x.textAlign='left';
 x.fillText('LV '+(level||0),32,92);
 x.fillStyle='#e2e8f0';x.font='600 44px "Segoe UI", Arial';
 x.fillText('fleet '+done+'/'+total+' goals · '+(pct!=null?pct:0)+'%',32,164);
 x.fillStyle='#7dd3fc';x.font='600 34px "Segoe UI", Arial';x.textAlign='right';
 x.fillText('goal cycles · Lv counter climbing',736,92);x.textAlign='left';
 sbTex.needsUpdate=true;}
drawScoreboard(0,0,0,null);
/* ============ TRADING DESK (SE, by the window): dcabots ============ */
var coin;
(function(){
 var d=new THREE.Mesh(new THREE.BoxGeometry(3.4,.95,1.1),new THREE.MeshStandardMaterial({color:0x1a2338,roughness:.6}));
 d.position.set(12.5,.48,11.6);scene.add(d);
 for(var i=0;i<3;i++){var mon=new THREE.Mesh(new THREE.BoxGeometry(.95,.6,.05),new THREE.MeshStandardMaterial({color:0x0a0f18}));
  mon.position.set(11.4+i*1.1,1.45,11.7);scene.add(mon);
  var sc=document.createElement('canvas');sc.width=128;sc.height=80;var sx=sc.getContext('2d');
  sx.fillStyle='#04140c';sx.fillRect(0,0,128,80);sx.strokeStyle='#4ade80';sx.lineWidth=3;sx.beginPath();
  for(var k=0;k<16;k++){var xx=k*8,yy=40+Math.sin(k*.9+i*2)*14*(sr(i*7+k)-.5)*2;k?sx.lineTo(xx,yy):sx.moveTo(xx,yy);}
  sx.stroke();var st=new THREE.CanvasTexture(sc);st.colorSpace=THREE.SRGBColorSpace;
  var sp=new THREE.Mesh(new THREE.PlaneGeometry(.86,.5),new THREE.MeshBasicMaterial({map:st}));
  sp.position.set(11.4+i*1.1,1.45,11.66);scene.add(sp);}
 var c=document.createElement('canvas');c.width=256;c.height=256;var x=c.getContext('2d');
 x.fillStyle='#f7931a';x.beginPath();x.arc(128,128,124,0,7);x.fill();
 x.strokeStyle='#b45309';x.lineWidth=10;x.beginPath();x.arc(128,128,112,0,7);x.stroke();
 x.fillStyle='#fff';x.font='bold 150px Arial';x.textAlign='center';x.textBaseline='middle';x.fillText('\u20BF',128,134);
 var t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;
 coin=new THREE.Mesh(new THREE.CylinderGeometry(.62,.62,.1,40),new THREE.MeshStandardMaterial({map:t,color:0xffffff,emissive:0x5c3a08,emissiveIntensity:.4}));
 coin.position.set(12.5,2.3,11.2);coin.rotation.z=Math.PI/2;scene.add(coin);
 var l=makeLabel('dcabots — your BTC trading bots (by the market window)','#fbbf24',1.2);l.position.set(12.5,.9,10.6);scene.add(l);
})();
/* ============ FACTS ON THE WALLS (memory/ tree) — pinned where they belong ============ */
var facts=[
 ['github.com/ArnoldPieterse/agent-portal','#93c5fd',-RW+1.2,5.6,6],
 ['you approve the irreversible; we run the rest','#fcd34d',0,5.7,.3],
 ['RESEARCH & RECORD BENCH','#8b96a5',-4.5,.25,-7.3],
 ['BUILD BENCH','#8b96a5',-.5,.25,6.4],
 ['DISPATCH · RECEPTION','#8b96a5',-11.5,.25,3.4]];
facts.forEach(function(f){var l=makeLabel(f[0],f[1],f[2]>10||f[2]<-7?1.1:.8);l.position.set(f[2],f[3],f[4]);scene.add(l);});
/* ============ AGENT PODS: real desks at the registered home cells ============
   The 8 core seats sit exactly on their registered voxel home cells (3 m grid from
   origin -12,-4.5,-12) so clicks still resolve memory/<agent>/ chains. Sub-agents
   (Hermes "community tier") sit at stools beside their lead's desk. */
var SEATS={researcher:[-4.5,-4.5],scribe:[-1.5,-4.5],verifier:[4.5,-4.5],
 orchestrator:[-4.5,1.5],archivist:[4.5,1.5],mechanic:[-4.5,4.5],designer:[1.5,4.5],builder:[4.5,4.5]};
var EXTRA_SEATS={outlet:[-9.5,5.5]};
var SUBS={pixel:[7.0,3.2,'builder'],forge:[7.0,5.8,'builder'],lumen:[-0.9,7.4,'designer'],
 reel:[1.5,7.9,'designer'],splice:[3.9,7.4,'designer']};
var HOST_OF={'127.0.0.1':'WHITE','IP_LAN':'WHITE','IP_LAN':'PALE','IP_LAN':'RED','IP_LAN':'BLACK'};
var podsGroup=new THREE.Group();scene.add(podsGroup);
var agents=[];                 /* {id,name,color,g,orb,pos:Vector3,pill,pillTex,pillCtx,pillS,lightMat,desk} */
var agentHome={};              /* id -> 'V(x,y,z)' for registered seats, null otherwise */
function cellOf(p){var o=[-12,-4.5,-12];return 'V('+[p.x,p.y,p.z].map(function(v,i){
 var m=i===1?3:7;return Math.min(m,Math.max(0,Math.floor((v-o[i])/3)))}).join(',')+')';}
function makeDesk(sub,colorHex){
 var g=new THREE.Group();
 var col=new THREE.Color(colorHex);
 var topM=new THREE.MeshStandardMaterial({color:0x1a2338,roughness:.6});
 var top=new THREE.Mesh(new THREE.BoxGeometry(sub?1.0:1.7,sub?.05:.06,sub?.6:.95),topM);
 top.position.y=sub?.62:.78;g.add(top);
 var base=new THREE.Mesh(new THREE.BoxGeometry(sub?.7:1.4,sub?.55:.72,sub?.4:.7),new THREE.MeshStandardMaterial({color:0x101725}));
 base.position.y=(sub?.31:.38);g.add(base);
 var mw=sub?.55:.9,mh=sub?.34:.55;
 var mon=new THREE.Mesh(new THREE.BoxGeometry(mw,mh,.05),new THREE.MeshStandardMaterial({color:0x0a0f18}));
 mon.position.set(0,sub?1.05:1.28,-(sub?.2:.3));g.add(mon);
 var scr=new THREE.Mesh(new THREE.PlaneGeometry(mw*.9,mh*.85),new THREE.MeshStandardMaterial({color:col,emissive:col,emissiveIntensity:.35}));
 scr.position.set(0,sub?1.05:1.28,-(sub?.2:.3)+.028);g.add(scr);
 var seat=new THREE.Mesh(new THREE.BoxGeometry(sub?.4:.55,sub?.06:.09,sub?.4:.55),new THREE.MeshStandardMaterial({color:0x2a3550}));
 seat.position.set(0,sub?.45:.5,(sub?.45:.75));g.add(seat);
 var back=new THREE.Mesh(new THREE.BoxGeometry(sub?.4:.55,sub?.45:.65,sub?.05:.08),new THREE.MeshStandardMaterial({color:0x2a3550}));
 back.position.set(0,sub?.7:.85,(sub?.68:1.02));g.add(back);
 var post=new THREE.Mesh(new THREE.CylinderGeometry(.04,.04,sub?.35:.4,8),new THREE.MeshStandardMaterial({color:0x101725}));
 post.position.set(0,sub?.24:.24,(sub?.45:.75));g.add(post);
 return g;}
function makePill(){
 var c=document.createElement('canvas');c.width=128;c.height=64;
 var t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;
 var s=new THREE.Sprite(new THREE.SpriteMaterial({map:t,transparent:true,depthWrite:false}));
 s.scale.set(.9,.45,1);return {s:s,t:t,x:c.getContext('2d'),v:''};}
function drawPill(p,txt,color){
 if(p.v===txt)return;p.v=txt;
 var x=p.x;x.clearRect(0,0,128,64);
 x.fillStyle='rgba(7,10,18,.85)';x.beginPath();
 if(x.roundRect)x.roundRect(4,10,120,44,10);else x.rect(4,10,120,44);x.fill();
 x.strokeStyle=color;x.lineWidth=3;x.stroke();
 x.fillStyle=color;x.font='700 30px "Segoe UI", Arial';x.textAlign='center';x.textBaseline='middle';
 x.fillText(txt,64,33);p.t.needsUpdate=true;}
function buildPods(roster){
 while(podsGroup.children.length){var c=podsGroup.children.pop();c.traverse&&c.traverse(function(o){if(o.geometry)o.geometry.dispose();});}
 /* mutate in place: window.__mind (and voxel-ui.js) hold references to these exact objects */
 agents.length=0;for(var k0 in agentHome)delete agentHome[k0];
 roster.forEach(function(a,ai){
  var id=a.id,x,z,sub=null;
  if(SEATS[id]){x=SEATS[id][0];z=SEATS[id][1];}
  else if(EXTRA_SEATS[id]){x=EXTRA_SEATS[id][0];z=EXTRA_SEATS[id][1];}
  else if(SUBS[id]){x=SUBS[id][0];z=SUBS[id][1];sub=SUBS[id][2];}
  else{var ang=ai/roster.length*Math.PI*2;x=Math.cos(ang)*9.5;z=Math.sin(ang)*7+ .3;}
  var color=a.color||'#94a3b8';
  var desk=makeDesk(!!sub,color);
  var dir=new THREE.Vector3(-x,-(z-.3),0).normalize();           /* face the table */
  desk.position.set(x,0,z);desk.rotation.y=Math.atan2(dir.x,dir.z);
  podsGroup.add(desk);
  var g=new THREE.Group();g.position.set(x,0,z);g.userData.podId=id;podsGroup.add(g);
  desk.userData.podId=id;
  var orbM=new THREE.MeshStandardMaterial({color:new THREE.Color(color),emissive:new THREE.Color(color),emissiveIntensity:.9});
var oC=document.createElement('canvas');oC.width=128;oC.height=128;
(function(){var x=oC.getContext('2d');
 x.beginPath();x.arc(64,64,54,0,7);x.fillStyle='#0d1526';x.fill();x.lineWidth=8;x.strokeStyle=color;x.stroke();
 x.beginPath();x.arc(64,64,38,0,7);x.fillStyle=color;x.globalAlpha=.28;x.fill();x.globalAlpha=1;
 x.fillStyle='#fff';x.font='700 62px "Segoe UI", Arial';x.textAlign='center';x.textBaseline='middle';
 x.fillText((a.name||id).slice(0,1).toUpperCase(),64,68);})();
var oTex=new THREE.CanvasTexture(oC);oTex.colorSpace=THREE.SRGBColorSpace;
var orb=new THREE.Sprite(new THREE.SpriteMaterial({map:oTex,transparent:true,depthWrite:false}));orb.scale.set(sub?.5:.72,sub?.5:.72,1);orb.position.y=sub?1.05:1.35;g.add(orb);
  var lightMat=new THREE.MeshStandardMaterial({color:0x334155,emissive:0x475569,emissiveIntensity:.8});
  var lt=new THREE.Mesh(new THREE.SphereGeometry(.05,8,6),lightMat);lt.position.set(sub?.5:-.75,sub?1.28:1.55,sub?.3:-.6);g.add(lt);
  var l=makeLabel(a.name||id,(a.color||'#c8d2e0'),sub?.6:.85);l.position.y=sub?1.4:2.35;g.add(l);
  var pill=makePill();pill.s.position.set(0,sub?1.5:1.72,0);g.add(pill.s);
  agentHome[id]=SEATS[id]?cellOf(new THREE.Vector3(x,2.5,z)):null;
  agents.push({id:id,name:a.name||id,color:color,g:g,orb:orb,pos:new THREE.Vector3(x,sub?1.75:2.5,z),
   pill:pill,lightMat:lightMat,desk:desk,goals:null,host:(function(){try{return HOST_OF[(a.studio||'').replace(/^https?:\/\//,'').split(':')[0]]||'';}catch(e){return '';}})()});
 });}
/* ============ LIVE DATA: roster + goals (5 s) and shelf spines (once) ============ */
var rosterData=[];
function poll(){
 fetch('/api/agents').then(function(r){return r.json();}).then(function(d){
  var ids=(d.agents||[]).map(function(a){return a.id;});
  if(ids.length&&ids.join()!==rosterData.map(function(a){return a.id;}).join()){
   rosterData=d.agents;buildPods(rosterData);}
  return fetch('/api/goals');
 }).then(function(r){return r.json();}).then(function(g){
  drawScoreboard(g.level,g.fleet_done,g.fleet_total,g.fleet_pct);
  (g.agents||[]).forEach(function(s){
   var p=null;for(var i=0;i<agents.length;i++)if(agents[i].id===s.agent)p=agents[i];
   if(!p)return;p.goals=s;
   var txt=(s.done!=null?s.done:0)+'/'+(s.total||10);
   var col='#64748b';
   if(s.blocked>0)col='#f87171';else if(s.total&&s.done>=s.total)col='#4ade80';else if(s.done>0)col='#fbbf24';
   drawPill(p.pill,txt,col);
   p.lightMat.emissive.setHex(col==='#64748b'?0x475569:parseInt(col.slice(1),16));
  });
 }).catch(function(){});}
poll();setInterval(poll,5000);
fetch('/api/memory/file?path=INDEX.md').then(function(r){return r.json();}).then(function(d){
 var lanes=[];(d.text||'').split('\n').forEach(function(line){
  var m=/^-\s+([a-z][\w-]*)\s+(memory\/[\w\/.-]+) - (.+)$/.exec(line);
  if(!m)return;var id=m[1];
  var col='#64748b';for(var i=0;i<agents.length;i++)if(agents[i].id===id)col=agents[i].color;
  lanes.push({id:id,name:m[2].slice(0,34),color:col});});
 if(lanes.length)fillShelves(lanes);
}).catch(function(){/* shelves stay empty-frame */});
/* ============ CAPABILITY CARD (Hermes `plugins info` style) ============ */
var acard=document.getElementById('acard');
function showAgentCard(id){
 var a=null;for(var i=0;i<rosterData.length;i++)if(rosterData[i].id===id)a=rosterData[i];
 if(!a||!acard)return;
 var p=null;for(i=0;i<agents.length;i++)if(agents[i].id===id)p=agents[i];
 var tier=SUBS[id]?'sub · reports to '+((rosterData.filter(function(r){return r.id===SUBS[id][2];})[0]||{}).name||SUBS[id][2]):'official';
 var h='<div style="display:flex;justify-content:space-between;align-items:center">'
  +'<b style="font-size:14px;color:'+a.color+'">'+(a.emoji||'')+' '+(a.name||id)+'</b>'
  +'<button id=aclose style="background:none;border:none;color:#94a3b8;font-size:16px;cursor:pointer">&times;</button></div>';
 h+='<div style="margin:4px 0;display:flex;gap:6px;flex-wrap:wrap">'
  +'<span style="border:1px solid '+(tier==='official'?'#2dd4bf':'#8b96a5')+';color:'+(tier==='official'?'#2dd4bf':'#9fb4cc')+';border-radius:4px;padding:0 6px;font-size:11px">'+tier+'</span>'
  +(p&&p.host?'<span style="border:1px solid #fbbf24;color:#fbbf24;border-radius:4px;padding:0 6px;font-size:11px">host '+p.host+'</span>':'')
  +'</div>';
 h+='<div style="opacity:.8;margin:6px 0">'+(a.blurb||'')+'</div>';
 h+='<div><b style="color:#ffd54a">route (pinned)</b> '+(a.model_id||'?')+'</div>';
 if(a.recommended_models&&a.recommended_models.length){h+='<div style="margin-top:4px"><b style="color:#7dd3fc">routes</b></div>'
  +a.recommended_models.map(function(r){return '<div style="opacity:.75;padding-left:8px">· '+r.id+' — '+(r.why||'')+'</div>';}).join('');}
 if(a.tools&&a.tools.length)h+='<div style="margin-top:6px"><b>tools</b> '+a.tools.map(function(t){return '<span style="border:1px solid #334155;border-radius:4px;padding:0 5px;margin-right:4px;font-size:11px">'+t+'</span>';}).join('')+'</div>';
 h+='<div style="margin-top:6px;opacity:.7">lane <b>memory/'+id+'/</b>'+(agentHome[id]?' · home voxel '+agentHome[id]:' (no registered home cell)')+'</div>';
 if(p&&p.goals){var s=p.goals,pc=s.total?Math.round(100*s.done/s.total):0;
  h+='<div style="margin-top:6px">goals <b>'+s.done+'/'+s.total+'</b> · blocked '+(s.blocked||0)+'<div style="height:5px;background:#1e293b;border-radius:3px;margin-top:3px"><div style="width:'+pc+'%;height:5px;background:'+(s.blocked?'#f87171':(pc>=100?'#4ade80':'#fbbf24'))+';border-radius:3px"></div></div></div>';}
 acard.innerHTML=h;acard.style.display='block';
 var cl=document.getElementById('aclose');if(cl)cl.onclick=function(){acard.style.display='none';};}
/* my own click listener is registered BEFORE voxel-ui.js's, so stopImmediatePropagation
   on unregistered objects keeps the raw-cell panel from clobbering the card */
var rc2=new THREE.Raycaster(),vv2=new THREE.Vector2();
canvas.addEventListener('click',function(ev){
 var r=canvas.getBoundingClientRect();
 vv2.set((ev.clientX-r.left)/r.width*2-1,-(ev.clientY-r.top)/r.height*2+1);
 rc2.setFromCamera(vv2,camera);var hits=rc2.intersectObjects(scene.children,true);
 if(!hits.length)return;
 /* scan hits in distance order for the first interactive object (pod or book);
    particles and stray lines never steal a click */
 var found=null;
 for(var hi=0;hi<hits.length&&!found;hi++){
  if(hits[hi].object.isPoints)continue;
  var o=hits[hi].object;
  while(o){if(o.userData&&o.userData.podId){found=o.userData.podId;break;}
   if(o.userData&&o.userData.lane){found='book:'+o.userData.lane;break;}
   o=o.parent;}}
 if(!found){acard.style.display='none';return;}
 if(found.indexOf('book:')===0){ev.stopImmediatePropagation();showAgentCard(found.slice(5));return;}
 var reg=!!agentHome[found];
 if(!reg)ev.stopImmediatePropagation();
 showAgentCard(found);});
/* ============ CONTROLS (drag orbit, wheel zoom, P / button = floor plan) ============ */
var theta=.95,phi=1.02,dist=30,target=new THREE.Vector3(0,1.8,.3);
var phiGoal=1.02,distGoal=30;
var dragging=false,px=0,py=0;
canvas.addEventListener('pointerdown',function(e){dragging=true;px=e.clientX;py=e.clientY;});
addEventListener('pointerup',function(){dragging=false;});
addEventListener('pointermove',function(e){if(!dragging)return;theta-=(e.clientX-px)*.005;phiGoal=Math.max(.28,Math.min(2.4,phiGoal-(e.clientY-py)*.005));px=e.clientX;py=e.clientY;});
canvas.addEventListener('wheel',function(e){distGoal*=1+Math.sign(e.deltaY)*.08;distGoal=Math.max(9,Math.min(60,distGoal));e.preventDefault();},{passive:false});
addEventListener('resize',function(){camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);});
var planMode=false;
function togglePlan(){planMode=!planMode;phiGoal=planMode?.3:1.02;distGoal=planMode?44:30;
 var b=document.getElementById('plbtn');if(b)b.textContent=planMode?'[ 3D view ]':'[ floor plan ]';}
document.addEventListener('keydown',function(e){if(e.key==='p'||e.key==='P')togglePlan();});
var plb=document.getElementById('plbtn');if(plb)plb.onclick=togglePlan;
/* ============ ANIMATE ============ */
var faceA=Math.atan2(-NPOS.z,NPOS.x);
var clock=new THREE.Clock();
function frame(){
 requestAnimationFrame(frame);
 var dt=Math.min(clock.getDelta(),.05),t=clock.elapsedTime;
 if(!dragging)theta+=dt*.03;
 phi+=(phiGoal-phi)*Math.min(1,dt*4);dist+=(distGoal-dist)*Math.min(1,dt*4);
 camera.position.set(target.x+dist*Math.sin(phi)*Math.sin(theta),target.y+dist*Math.cos(phi),target.z+dist*Math.sin(phi)*Math.cos(theta));
 camera.lookAt(target);
 ssj.position.y=3.1+Math.sin(t*.8)*.2;
 ssj.rotation.y=faceA+Math.sin(t*.25)*.3;
 var pos=ag.attributes.position.array;
 for(var i=0;i<AUR;i++){pos[i*3+1]+=dt*(.6+sr(i)*.9);if(pos[i*3+1]>3.8)pos[i*3+1]=-1;}
 ag.attributes.position.needsUpdate=true;
 auraLight.intensity=26+9*Math.sin(t*6)+4*Math.sin(t*17);
 key.intensity=1.5+.4*Math.sin(t*6);
 nmat.size=.12+.05*Math.sin(t*2.2);
 for(i=0;i<hubs.length;i++)hubs[i].scale.setScalar(1+.35*Math.sin(t*2+i));
 nLight.intensity=16+6*Math.sin(t*2.2+1);
 var hw=handR.clone().applyMatrix4(ssj.matrixWorld);
 for(i=0;i<pulses.length;i++){var p=pulses[i];p.o=(p.o+dt*.25)%1;var e=p.o*p.o*(3-2*p.o);
  p.m.position.lerpVectors(hw,NPOS,e);p.m.scale.setScalar(.6+.8*Math.sin(p.o*Math.PI));}
 for(i=0;i<agents.length;i++){var a=agents[i];
  a.orb.position.y=(a.pos.y)+Math.sin(t*1.4+i)*.07;
  a.orb.rotation.y+=dt*.8;}
 coin.rotation.x+=dt*2;
 helix.rotation.y+=dt*.6;
 ring.material.emissiveIntensity=.3+.15*Math.sin(t*1.3);
 for(i=0;i<leds.length;i++)leds[i].m.material.emissiveIntensity=.3+.7*(0.5+0.5*Math.sin(t*2.2+leds[i].ph));
 renderer.render(scene,camera);}
window.__mind={scene:scene,camera:camera,canvas:renderer.domElement,agents:agents,agentHome:agentHome,
 neuronsPos:NPOS,rigids:{ssj:ssj,neurons:neurons,portal:portal,helix:helix,coin:coin}};
/* ============ HIGH-DETAIL ASSETS (Blender GLBs) ============ */
if(THREE.GLTFLoader){
 var gl=new THREE.GLTFLoader();
 function recenterLater(root,g,anchorLocal){requestAnimationFrame(function(){requestAnimationFrame(function(){
  root.updateMatrixWorld(true);
  var bb=new THREE.Box3();g.scene.traverse(function(o){if(o.isMesh)bb.expandByObject(o);});
  if(bb.isEmpty())return;
  var inv=new THREE.Matrix4().copy(root.matrixWorld).invert();
  var c=bb.getCenter(new THREE.Vector3()).applyMatrix4(inv);
  g.scene.position.x-=(c.x-anchorLocal.x);g.scene.position.z-=(c.z-anchorLocal.z);
 });});}
 gl.load('/ui/assets/models/ssj.glb',function(g){ssjBody.visible=false;ssj.add(g.scene);recenterLater(ssj,g,new THREE.Vector3(0,0,0));},undefined,function(){});
 gl.load('/ui/assets/models/neurons.glb',function(g){neurons.visible=false;g.scene.scale.setScalar(.55);g.scene.position.copy(NPOS);scene.add(g.scene);recenterLater(scene,g,NPOS);},undefined,function(){});
}
/* ============ LIVE VOXEL SUBDIVISION LAYER (mini-voxel clouds, anchored to real positions) ============
   Same machinery as v2/v3: every memory object renders out of thousands of shaded disc
   mini-voxels at its REAL position in the room; drill tip + ghost octants from /api/voxel/all. */
(function(){
 var group=new THREE.Group();scene.add(group);
 var ghosts=[],tips=[];
 var MAXH=9500,MAXR=16000;
 var cv=document.createElement('canvas');cv.width=cv.height=64;var cx2=cv.getContext('2d');
 var grd=cx2.createRadialGradient(25,22,1.5,32,32,31);
 grd.addColorStop(0,'rgba(255,255,255,1)');grd.addColorStop(0.32,'rgba(196,196,196,1)');
 grd.addColorStop(0.66,'rgba(88,88,88,1)');grd.addColorStop(0.9,'rgba(24,24,24,1)');grd.addColorStop(1,'rgba(0,0,0,0)');
 cx2.fillStyle=grd;cx2.beginPath();cx2.arc(32,32,31,0,Math.PI*2);cx2.fill();
 var discTex=new THREE.CanvasTexture(cv);
 var cloudMat=new THREE.ShaderMaterial({
  uniforms:{map:{value:discTex},uScale:{value:425}},
  vertexShader:'uniform float uScale;attribute float aSize;varying vec3 vC;void main(){vC=color;vec4 mv=modelViewMatrix*vec4(position,1.);gl_PointSize=aSize*(uScale/-mv.z);gl_Position=projectionMatrix*mv;}',
  fragmentShader:'uniform sampler2D map;varying vec3 vC;void main(){vec4 t=texture2D(map,gl_PointCoord);if(t.a<0.06)discard;gl_FragColor=vec4(vC*t.rgb,0.96*t.a);}',
  vertexColors:true,transparent:true,depthWrite:true});
 function mkCloud(cap){
  var geo=new THREE.BufferGeometry();
  geo.setAttribute('position',new THREE.BufferAttribute(new Float32Array(cap*3),3).setUsage(THREE.DynamicDrawUsage));
  geo.setAttribute('color',new THREE.BufferAttribute(new Float32Array(cap*3),3).setUsage(THREE.DynamicDrawUsage));
  geo.setAttribute('aSize',new THREE.BufferAttribute(new Float32Array(cap),1).setUsage(THREE.DynamicDrawUsage));
  var pts=new THREE.Points(geo,cloudMat);pts.frustumCulled=false;return pts;}
 var heroMesh=mkCloud(MAXH);
 var heroGroup=new THREE.Group();heroGroup.add(heroMesh);scene.add(heroGroup);
 var restMesh=mkCloud(MAXR);scene.add(restMesh);
 var _col=new THREE.Color();
 function put(pts,slot,px2,py2,pz2,diam,colHex,bright){
  var pa=pts.geometry.attributes.position.array;
  pa[slot*3]=px2;pa[slot*3+1]=py2;pa[slot*3+2]=pz2;
  _col.setHex(colHex).multiplyScalar((0.62+sr(slot*31)*0.6)*(bright||1));
  var ca=pts.geometry.attributes.color.array;
  ca[slot*3]=_col.r;ca[slot*3+1]=_col.g;ca[slot*3+2]=_col.b;
  pts.geometry.attributes.aSize.array[slot]=diam*(0.78+sr(slot*13)*0.5);}
 function flushCloud(pts){
  pts.geometry.setDrawRange(0,pts.userData.n||0);
  ['position','color','aSize'].forEach(function(k){pts.geometry.attributes[k].needsUpdate=true;});}
 function heroMask(px2,py2,pz2){
  if(py2>1.85)return (px2*px2+pz2*pz2)<0.34&&Math.abs(py2-2.35)<0.62;
  if(py2>-1.75){var rad=py2<-0.45?0.4:0.7;return (px2*px2+pz2*pz2)<rad*rad;}
  return false;}
 function anchors(){
  var A={};A.ssj=ssj.position.clone();A.neurons=NPOS.clone();
  A.portal=new THREE.Vector3(-RW+.55,3.4,6);A.helix=helix.position.clone();
  A.coin=coin?coin.position.clone():new THREE.Vector3(12.5,2.3,11.2);
  A.racks=new THREE.Vector3(12.5,1.4,-RD+.6);
  A.reception=new THREE.Vector3(-13.6,1.4,6);A.board=new THREE.Vector3(3.4,2.9,-RD+.12);
  var ags=[];agents.forEach(function(o){ags.push({name:o.id,color:o.color,pos:o.pos.clone()});});
  A.agents=ags;return A;}
 function matchCell(c,A){
  if((c.r||'').indexOf('ssj.glb')>=0)return{key:'ssj',pos:A.ssj,color:0xffc233,kind:'hero'};
  if((c.r||'').indexOf('neurons.glb')>=0)return{key:'neurons',pos:A.neurons,color:0x7fd4ff,kind:'blob'};
  if(/coin/i.test(c.l||''))return{key:'coin',pos:A.coin,color:0xfbbf24,kind:'ring'};
  if(/evolution column/i.test(c.l||''))return{key:'helix',pos:A.helix,color:0x34d399,kind:'blob'};
  if(/^agent portal/i.test(c.l||''))return{key:'portal',pos:A.portal,color:0x22d3ee,kind:'ring'};
  if(/host pillar/i.test(c.l||''))return{key:'racks',pos:A.racks,color:0x9fd0ff,kind:'blob'};
  if(/neuron field/i.test(c.l||''))return{key:'neurons2',pos:A.neurons,color:0x7fd4ff,kind:'pin'};
  if(/wsl-inbox/i.test(c.l||''))return{key:'reception',pos:A.reception,color:0xc4b5fd,kind:'pin'};
  if(/you approve the irreversible/i.test(c.l||''))return{key:'approve',pos:new THREE.Vector3(0,5.6,.3),color:0xfcd34d,kind:'pin'};
  if(/steady state = minimal/i.test(c.l||''))return{key:'board1',pos:new THREE.Vector3(1.6,2.9,-RD+.12),color:0x86efac,kind:'pin'};
  if(/goal cycles/i.test(c.l||''))return{key:'board2',pos:new THREE.Vector3(5.2,4.85,-RD+.12),color:0xe2e8f0,kind:'pin'};
  if(/lm studio :8888/i.test(c.l||''))return{key:'srvwall',pos:new THREE.Vector3(12.7,2.6,-8.6),color:0xfca5a5,kind:'pin'};
  var mm=/^agent (\w+) - home/.exec(c.l||'');
  if(mm){for(var i=0;i<A.agents.length;i++)if(A.agents[i].name===mm[1])
   return{key:'agent:'+mm[1],pos:A.agents[i].pos,color:parseInt(A.agents[i].color.slice(1),16),kind:'blob'};}
  return null;}
 function wireBox(p,s,color,op){
  var g=new THREE.EdgesGeometry(new THREE.BoxGeometry(s,s,s));
  var m=new THREE.LineBasicMaterial({color:color,transparent:true,opacity:op});
  var l=new THREE.LineSegments(g,m);l.position.set(p[0]+s/2,p[1]+s/2,p[2]+s/2);group.add(l);return m;}
 function clearLayer(){
  while(group.children.length){var c=group.children.pop();if(c.geometry)c.geometry.dispose();if(c.material)c.material.dispose();}
  ghosts.length=0;tips.length=0;}
 var lastSig='';
 function build(cells){
  clearLayer();heroMesh.userData.n=0;restMesh.userData.n=0;
  var A=anchors(),byBase={};
  cells.forEach(function(c){var b=c.a.split('/')[0];(byBase[b]=byBase[b]||[]).push(c);});
  var sig='';
  Object.keys(byBase).forEach(function(base){
   var list=byBase[base],top=null;
   list.forEach(function(c){if(c.d===0&&(c.l||c.r))top=c;});
   if(!top)return;
   var tip=top;list.forEach(function(c){if(c.d>tip.d)tip=c;});
   sig+=base+':'+tip.d+';';
   var m=matchCell(top,A);
   var ts=3/Math.pow(2,tip.d);
   var tipC=[tip.p[0]+ts/2,tip.p[1]+ts/2,tip.p[2]+ts/2];
   var cc=[top.p[0]+top.s/2,top.p[1]+top.s/2,top.p[2]+top.s/2];
   if(m&&m.pos){
    var off=new THREE.Vector3(m.pos.x-cc[0],m.pos.y-cc[1],m.pos.z-cc[2]);
    var glow=new THREE.Vector3(tipC[0]-cc[0],tipC[1]-cc[1],tipC[2]-cc[2]);
    if(m.kind==='hero'){
     var slot=0,tries=0;
     while(slot<MAXH&&tries<MAXH*4){tries++;
      var px3=(sr(tries)*2-1)*0.95,py3=sr(tries+70001)*4.7-1.85,pz3=(sr(tries+35000)*2-1)*0.95;
      if(!heroMask(px3,py3,pz3))continue;
      var b=1+(glow.distanceTo(new THREE.Vector3(px3,py3,pz3))<0.5?0.9:0);
      put(heroMesh,slot,px3,py3,pz3,0.11,m.color,b);slot++;}
     heroMesh.userData.n=slot;heroGroup.position.copy(m.pos);
    }else{
     var R=m.kind==='ring'?1.05:m.kind==='blob'?0.8:0.42;
     var n=m.kind==='ring'?900:m.kind==='blob'?1300:420;
     for(var s2=0;s2<n&&restMesh.userData.n<MAXR;s2++){
      var u=sr(s2*3+base.length)*2-1,w=sr(s2*5+7)*2-1,vv3=sr(s2*11+13)*2-1;
      var dl=Math.sqrt(u*u+w*w+vv3*vv3);if(dl>0.98||dl<0.001)continue;
      var fall=1-dl/0.98;if(sr(s2*17)>Math.pow(fall,0.6))continue;
      var wx=m.pos.x+u*R,wy=m.pos.y+w*R*.85,wz=m.pos.z+vv3*R;
      var b=1+(new THREE.Vector3(wx,wy,wz).distanceTo(m.pos.clone().add(glow))<0.4?0.9:0);
      put(restMesh,restMesh.userData.n,wx,wy,wz,m.kind==='ring'?0.12:m.kind==='blob'?0.15:0.09,m.color,b);
      restMesh.userData.n++;}
    }
    if(tip.d>0){
     var dm=new THREE.MeshBasicMaterial({color:0x7fd4ff,transparent:true,opacity:.95,blending:THREE.AdditiveBlending,depthWrite:false});
     var dot=new THREE.Mesh(new THREE.SphereGeometry(.13,10,10),dm);
     dot.position.set(m.pos.x+glow.x,m.pos.y+glow.y,m.pos.z+glow.z);group.add(dot);tips.push(dot);
    }
   }else{
    var col=(top.k==='rigid')?0x2dd4bf:0xfbbf24;
    wireBox(top.p,top.s,col,.13);
    if(tip.d>0){
     var sm=new THREE.MeshBasicMaterial({color:0x7fd4ff,transparent:true,opacity:.95,blending:THREE.AdditiveBlending,depthWrite:false});
     var dot2=new THREE.Mesh(new THREE.SphereGeometry(.16,10,10),sm);
     dot2.position.set(tipC[0],tipC[1],tipC[2]);group.add(dot2);tips.push(dot2);}
    var have={};list.forEach(function(c){if(c.d===1)have[c.a]=1;});
    for(var i=0;i<8;i++){var x=i&1,y=(i>>1)&1,z=(i>>2)&1;
     if(have[base+'/'+x+'/'+y+'/'+z])continue;
     ghosts.push(wireBox([top.p[0]+x*top.s/2,top.p[1]+y*top.s/2,top.p[2]+z*top.s/2],top.s/2,0x22d3ee,.09));}
   }
  });
  flushCloud(heroMesh);flushCloud(restMesh);
  lastSig=sig;}
 function load(){if(document.hidden)return;
  fetch('/api/voxel/all').then(function(r){return r.json();}).then(function(d){
   var cells=d.cells||[];
   var sig='';cells.forEach(function(c){sig+=(c.d>0?c.a+'@'+c.d:'|');});
   if(sig!==lastSig)build(cells);
  }).catch(function(){});}
 load();setInterval(load,2000);
 var t0=performance.now();
 (function anim(){requestAnimationFrame(anim);
  var ph=.5+.5*Math.sin((performance.now()-t0)/350);
  ghosts.forEach(function(m){m.opacity=.05+.11*ph;});
  tips.forEach(function(d){d.scale.setScalar(.7+.6*ph);});
  heroGroup.position.copy(ssj.position);
  cloudMat.uniforms.uScale.value=renderer.domElement.height*0.5;
 })();
})();
frame();
})();
