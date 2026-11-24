/* Cycle-15 designer goals 2-9. Same /api/fleet/cockpit feed as cockpit.js;
inserts sections after the mode banner of #ckpPanel.
*/
(function () {
  "use strict";
  var API = "/api/fleet/cockpit";
  var RM = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  var lastHash = '', lastMode = null;
  function esc(s){s=String(s==null?'':s);return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(String.fromCharCode(34),'&quot;');}
  function css(){var s=document.createElement('style');s.textContent=[
    '#ckpPanel .sec15{margin:14px 0 6px;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#9aa3af}',
    '.ckring circle{fill:none;stroke-width:8}',
    '.ckring .bgc{stroke:#2a2f38}',
    '.ckring .fgc{transition:stroke-dashoffset 400ms ease-in-out,stroke 400ms ease-in-out}',
    '.ckbud{height:8px;border-radius:4px;background:#232830;overflow:hidden}',
    '.ckbud i{display:block;height:100%;transition:width 400ms ease-in-out,background 400ms ease-in-out}',
    '.cktl{display:flex;overflow-x:auto;gap:2px;padding:4px 0}',
    '.cktl span{height:14px;border-radius:3px;flex:none;min-width:8px}',
    '.cktl span.cur{box-shadow:0 0 6px 1px currentColor}',
    '.ckcards{display:grid;gap:8px;grid-template-columns:repeat(2,minmax(0,1fr))}',
    '@media(min-width:1440px){.ckcards{grid-template-columns:repeat(4,minmax(0,1fr))}}',
    '.ckcard15{background:#171b22;border:1px solid #2a2f38;border-radius:6px;padding:8px;font-size:12px;transition:transform 400ms ease-in-out}',
    '#ckpModeBanner{transition:background 400ms ease-in-out}',
    '@media(prefers-reduced-motion:reduce){.ckring .fgc,.ckbud i,.ckcard15,#ckpModeBanner{transition:none!important}}',
  ].join('\n');document.head.appendChild(s);
  }
  function sec(label){var d=document.createElement('div');d.className='sec15';d.setAttribute('role','region');d.setAttribute('aria-label',label);d.tabIndex=0;d.textContent=label;return d;}
  function build(p){css();var b=p.querySelector('#ckpModeBanner')||p;
    var lv=document.createElement('span');lv.id='ckp15live';lv.setAttribute('aria-live','polite');lv.style.cssText='position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)';p.appendChild(lv);
    var mk=function(l,id){var s=sec(l);var c=document.createElement('div');c.id=id;s.appendChild(c);return s;};
    [mk('Maintenance tasks','ckp15Cards'),mk('Mode history (24h)','ckp15Tl'),mk('Pass budget','ckp15Bud'),mk('Goal progress','ckp15Ring')].forEach(function(s){b.insertAdjacentElement('afterend',s);});
    p.addEventListener('keydown',function(e){if(e.key!=='ArrowDown'&&e.key!=='ArrowUp')return;var f=Array.prototype.filter.call(p.querySelectorAll('.sec15,.ckcard15'),function(x){return x.tabIndex===0;});if(!f.length)return;var i=f.indexOf(document.activeElement);e.preventDefault();f[e.key==='ArrowDown'?(i+1)%f.length:(i-1+f.length)%f.length].focus();});
  }
  function renderRing(d){var g=d.goals||{};var pct=g.fleet_pct!=null?g.fleet_pct:(g.total?g.done/g.total*100:0);pct=Math.max(0,Math.min(100,pct||0));
    var C=251.33,col=pct>=100?'#8a8f98':'#4a7ddb',el=document.getElementById('ckp15Ring');if(!el)return;
    if(!el.firstChild)el.innerHTML='<svg class=ckring width=96 height=96 viewBox='+String.fromCharCode(34)+'0 0 96 96'+String.fromCharCode(34)+' role=progressbar aria-valuemin=0 aria-valuemax=100><circle class=bgc cx=48 cy=48 r='+String.fromCharCode(34)+'40'+String.fromCharCode(34)+'/><circle class=fgc cx=48 cy=48 r=40 stroke-dasharray=251.33 transform='+String.fromCharCode(34)+'rotate(-90 48 48)'+String.fromCharCode(34)+'/><text x=48 y=52 text-anchor=middle fill=#e8eaed font-size=14></text></svg>';
    var fg=el.querySelector('.fgc'),tx=el.querySelector('text');fg.style.strokeDashoffset=C*(1-pct/100);fg.style.stroke=col;tx.textContent=Math.round(pct)+'%';var sv=el.firstChild;sv.setAttribute('aria-valuenow',Math.round(pct));sv.setAttribute('aria-label','Goal progress '+Math.round(pct)+' percent');
  }
  function renderBudget(d){var el=document.getElementById('ckp15Bud');if(!el)return;var pb=d.pass_budget||{},bud=pb.budget||0,con=pb.consumed||0,p=bud?con/bud*100:0,col=p<50?'#3fb950':(p<80?'#d29922':'#f85149');
    if(!el.firstChild)el.innerHTML='<div style='+String.fromCharCode(39)+'display:flex;align-items:center;gap:10px'+String.fromCharCode(39)+'><div class=ckbud style='+String.fromCharCode(39)+'flex:1'+String.fromCharCode(39)+'><i></i></div><b class=budn style='+String.fromCharCode(39)+'font-size:12px;color:#c7ccd4'+String.fromCharCode(39)+'></b></div>';
    var bar=el.querySelector('i'),n=el.querySelector('.budn');bar.style.width=Math.min(100,p)+'%';bar.style.background=col;n.textContent=con+' / '+bud+' ('+Math.round(p)+'%)';
  }
  var MC={WORK:'#4a7ddb',MAINTENANCE:'#d29922',IDLE:'#6e7681'};
  function tsOf(t){var v=t.ts||t.timestamp||0;return typeof v==='number'?v:(+new Date(v))/1000||0;}
  function renderTl(d){var el=document.getElementById('ckp15Tl');if(!el)return;var tr=(d.mode_transitions||[]).slice().sort(function(a,b){return tsOf(a)-tsOf(b);});
    var key=tr.map(function(t){return t.to_mode+'@'+tsOf(t);}).join('|');if(el.dataset.key===key)return;el.dataset.key=key;
    if(!tr.length){el.innerHTML='<span style='+String.fromCharCode(39)+'color:#8a8f98;font-size:12px'+String.fromCharCode(39)+'>no transitions in the last 24h</span>';return;}
    var h='';tr.forEach(function(t,i){var m=t.to_mode||t.from_mode||'IDLE',c=MC[m]||MC.IDLE,cur=i===tr.length-1;var w=cur?40:18+((tsOf(t)%97)*3);h+='<span class='+String.fromCharCode(39)+'ckseg'+(cur?' cur':'')+String.fromCharCode(39)+' style='+String.fromCharCode(39)+'width:'+w+'px;background:'+c+';color:'+c+String.fromCharCode(39)+' title='+String.fromCharCode(39)+m+' since '+new Date(tsOf(t)*1000).toISOString()+String.fromCharCode(39)+'></span>';});
    el.innerHTML='<div class=cktl>'+h+'</div>';
  }
  function renderCards(d){var el=document.getElementById('ckp15Cards');if(!el)return;var tasks=(d.idle_tasks||[]).slice(-4);
    var old={};Array.prototype.forEach.call(el.querySelectorAll('.ckcard15'),function(c){old[c.dataset.k]=c.offsetTop;});
    var h='';tasks.forEach(function(t){var k=(t.agent||'?')+':'+(t.task||'');h+='<div class=ckcard15 data-k='+String.fromCharCode(39)+esc(k)+String.fromCharCode(39)+' tabindex=0><b>'+esc(t.agent||'?')+'</b><div class=t style='+String.fromCharCode(39)+'color:#c7ccd4;margin:3px 0'+String.fromCharCode(39)+'>'+esc(t.task||'')+'</div><div class=m style='+String.fromCharCode(39)+'color:#8a8f98;font-size:11px;display:flex;justify-content:space-between'+String.fromCharCode(39)+'><span>'+new Date((tsOf(t)||0)*1000).toISOString().slice(5,16).replace('T',' ')+'Z</span><span>'+(t.productive?'\u2713 productive':'\u2717 idle')+'</span></div></div>';});
    if(!tasks.length)h='<div style='+String.fromCharCode(39)+'color:#8a8f98;font-size:12px'+String.fromCharCode(39)+'>no idle tasks logged yet</div>';
    el.innerHTML=h;if(RM)return;Array.prototype.forEach.call(el.querySelectorAll('.ckcard15'),function(c){var o=old[c.dataset.k];if(o==null)return;var dy=o-c.offsetTop;if(!dy)return;c.style.transform='translateY('+dy+'px)';void c.offsetHeight;c.style.transform='';});
  }
  function render(d){var g=d.goals||{};var h=[d.fleet_pct!=null?d.fleet_pct:(g.fleet_pct!=null?g.fleet_pct:g.total),JSON.stringify(d.pass_budget||{}),(d.mode_transitions||[]).length,(d.idle_tasks||[]).length,d.fleet_mode].join('#');if(h===lastHash){return;}lastHash=h;
    renderRing(d);renderBudget(d);renderTl(d);renderCards(d);
    if(lastMode&&d.fleet_mode&&d.fleet_mode!==lastMode){var lv=document.getElementById('ckp15live');if(lv)lv.textContent='Fleet mode changed to '+d.fleet_mode;}lastMode=d.fleet_mode||lastMode;
  }
  function tick(){fetch(API,{cache:'no-store'}).then(function(r){return r.json();}).then(render).catch(function(){});}
  (function(){var n=0;var t=setInterval(function(){var p=document.getElementById('ckpPanel');if(p){clearInterval(t);build(p);tick();setInterval(tick,5000);}else if(++n>100)clearInterval(t);},200);})();
})();
