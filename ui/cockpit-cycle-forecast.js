/* cockpit-cycle-forecast.js — Cycle Duration Forecast Widget (Designer goal #3, cycle-17)
   SVG chart: actual cycle durations (solid line + dots) vs predicted next cycle (dotted).
   Gap highlighted if >20%. Data from /api/convergence.
*/
(function(){"use strict";
var API="/api/convergence",MAX=5,THRESHOLD=0.20,W=380,H=130,P={t:24,r:16,b:26,l:44};
function esc(s){return String(s==null?"":s).replace(/[&<>\"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]});}
function css(){var s=document.createElement("style");s.textContent=[
".ckcf{margin:4px 0 12px;padding:10px 12px;background:var(--bg-2,#171b22);border:1px solid var(--line,#2a2f38);border-radius:8px;min-height:150px}",
".ckcf-hd{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:#8a8f98;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center}",
".ckcf-legend{display:flex;gap:12px;font-size:10px;color:#aab2bf;text-transform:none;letter-spacing:0}",
".ckcf-legend .dot{width:8px;height:3px;border-radius:2px;display:inline-block;margin-right:4px;vertical-align:middle}",
".ckcf-empty{font-size:12px;color:#8a8f98;font-style:italic;padding:20px 0;text-align:center}",
".ckcf-gap-warn{color:var(--warn,#d4a017);font-weight:600;margin-top:4px;font-size:11px}"
].join("\n");document.head.appendChild(s);}
function linearPredict(vals){if(vals.length<2)return null;var n=vals.length,sm=n,sxm=0,SYM=0,sxy=0;
for(var i=0;i<n;i++){sxm+=i;SYM+=vals[i];sxy+=i*vals[i];}
var denom=n*sxm-sxm*sxm;if(Math.abs(denom)<1e-9)return null;
var slope=(n*sxy-sxm*SYM)/denom,icpt=(SYM-slope*sxm)/n;
return icpt+slope*n;}
function chart(cycles,pred){
if(!cycles||cycles.length===0)return"";
var vals=cycles.map(function(c){return c.duration_h||0});
var allVals=vals.slice();if(pred!=null)allVals.push(pred);
var mn=Math.min.apply(null,allVals),mx=Math.max.apply(null,allVals);
if(mx-mn<0.1){mn-=0.5;mx+=0.5;}
var range=mx-mn,pad=range*0.12;
function x(i){return P.l+(i/Math.max(1,cycles.length-1))*(W-P.l-P.r);}
function y(v){return P.t+(1-(v-mn+pad)/(range+2*pad))*(H-P.t-P.b);}
var s='<svg width="100%" viewBox="0 0 '+W+' '+H+'" style="display:block">';
for(var gi=0;gi<=3;gi++){var gv=mn+pad+(range+2*pad)*gi/4,gy=y(gv);
s+='<line x1="'+P.l+'" y1="'+gy.toFixed(1)+'" x2="'+(W-P.r)+'" y2="'+gy.toFixed(1)+'" stroke="#2a2f38" stroke-width="0.5"/>';
s+='<text x="'+(P.l-6)+'" y="'+(gy+4).toFixed(1)+'" text-anchor="end" fill="#8a8f98" font-size="9">'+gv.toFixed(1)+'</text>';}
if(cycles.length>=2){var pts=vals.map(function(v,i){return x(i).toFixed(1)+","+y(v).toFixed(1)}).join(" ");
s+='<polyline fill="none" stroke="#4a7ddb" stroke-width="2" points="'+pts+'"/>';}
vals.forEach(function(v,i){s+='<circle cx="'+x(i).toFixed(1)+'" cy="'+y(v).toFixed(1)+'" r="3.5" fill="#4a7ddb"/>'
s+='<text x="'+x(i).toFixed(1)+'" y="'+(H-P.b+14)+'" text-anchor="middle" fill="#8a8f98" font-size="9">'+esc(cycles[i].cycle)+'</text>';});
if(pred!=null){var px=x(vals.length),py=y(pred);
s+='<line x1="'+x(vals.length-1).toFixed(1)+'" y1="'+y(vals[vals.length-1]).toFixed(1)+'" x2="'+px.toFixed(1)+'" y2="'+py.toFixed(1)+'" stroke="#d4a017" stroke-width="1.5" stroke-dasharray="5,3"/>';
s+='<circle cx="'+px.toFixed(1)+'" cy="'+py.toFixed(1)+'" r="3.5" fill="#d4a017"/>';
s+='<text x="'+px.toFixed(1)+'" y="'+(H-P.b+14)+'" text-anchor="middle" fill="#d4a017" font-size="9">next</text>';}
var gapHtml="";
if(pred!=null&&vals.length>0){var last=vals[vals.length-1];if(last>0){var gap=Math.abs(pred-last)/last;if(gap>THRESHOLD)gapHtml='<div class="ckcf-gap-warn">\u26A0 Gap '+Math.round(gap*100)+'% vs previous cycle</div>';}}
s+='</svg>'+gapHtml;return s;}
function render(data){var el=document.getElementById("ckpCfChart");if(!el)return;
var cycles=(data.cycle_duration_trend&&data.cycle_duration_trend.cycles)||[];
var last5=cycles.slice(-MAX);
if(last5.length===0){el.innerHTML='<div class="ckcf-empty">No cycle duration data yet</div>';return;}
var allVals=last5.map(function(c){return c.duration_h||0});
var pred=linearPredict(allVals);
el.innerHTML=chart(last5,pred);}
function build(){var panel=document.getElementById("ckpPanel");if(!panel){setTimeout(build,400);return;}
css();var sec=document.createElement("div");sec.className="sec";sec.textContent="Cycle Duration Forecast";
var box=document.createElement("div");box.id="ckpCfChart";box.className="ckcf";box.setAttribute("data-testid","cycle-forecast-widget");
box.innerHTML='<div class="ckcf-hd"><span>Cycle Duration (h)</span><span class="ckcf-legend"><span><span class="dot" style="background:#4a7ddb"></span>actual</span><span><span class="dot" style="background:#d4a017;border-top:2px dotted #d4a017;height:0"></span>predicted</span></span></div>';
var health=panel.querySelector("#ckpHealth");
if(health&&health.parentNode){var risks=panel.querySelector('[id*="Risks"]')||null;if(risks)risks.parentNode.insertBefore(sec,risks);else panel.appendChild(sec);risks=panel.querySelector('[id*="Risks"]');if(risks)risks.parentNode.insertBefore(box,risks);else panel.appendChild(box);}
else{panel.appendChild(sec);panel.appendChild(box);}}
async function refresh(){try{var r=await fetch(API,{cache:"no-store"});render(await r.json());}catch(e){}}
function init(){build();refresh();setInterval(refresh,60000);}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
window.CKP_CYCLE_FORECAST={refresh:refresh};
})();