/* In-process acceptance test for ui/api-client.js (Goal #2). Run: node memory/builder/test_api_client.js */
"use strict";
var ac = require("../../ui/api-client.js"); // UMD -> module.exports in Node

function ok(cond, msg){ if(!cond) throw new Error("FAIL: " + msg); console.log("  PASS " + msg); }

// --- deterministic deps factory ---
function makeDeps(script, opts){
  var calls = [], t = 0;
  opts = opts || {};
  var fetchImpl = function(url, init){
    calls.push({url:url, method:init.method});
    var n = calls.length;
    for (var i=0;i<script.length;i++){ if(script[i].at===n) return Promise.resolve(script[i].res); }
    return Promise.resolve(opts.fallback || { ok:true, status:200, json:function(){return Promise.resolve({fallback:true});} });
  };
  var sleep = function(ms){ t += ms; return Promise.resolve(); };
  return { deps:{ fetchImpl:fetchImpl, sleep:sleep, now:function(){return opts.now||1000;}, rng:function(){return 0;}, cache:new Map() }, calls:calls, sleepMs:function(){return t;} };
}

var core = ac._core;

// T1 backoff monotonic + capped (rng=0 -> jitter 0)
(function(){
  var d0=core.backoffDelay(0,{baseDelayMs:100,maxDelayMs:1000},function(){return 0});
  var d1=core.backoffDelay(1,{baseDelayMs:100,maxDelayMs:1000},function(){return 0});
  var d2=core.backoffDelay(2,{baseDelayMs:100,maxDelayMs:1000},function(){return 0});
  var d9=core.backoffDelay(9,{baseDelayMs:100,maxDelayMs:1000},function(){return 0});
  ok(d0===100 && d1===200 && d2===400, "backoff doubles: "+[d0,d1,d2]);
  ok(d9===1000, "backoff capped at maxDelayMs: "+d9);
})();

// T2 cache TTL semantics
(function(){
  var m=new Map(); core.cacheSet(m,"k",{a:1},30000,1000);
  ok(core.cacheGet(m,"k",15000).a===1, "cache hit within TTL");
  ok(core.cacheGet(m,"k",15001)===null, "cache miss after TTL (30s)");
})();

// T3 GET 500 twice then 200 -> retried, resolved; attempts=3
(async function(){
  var e=makeDeps([{at:1,res:{ok:false,status:500}},{at:2,res:{ok:false,status:500}},{at:3,res:{ok:true,status:200,json:function(){return Promise.resolve({v:1});}}}],{now:1000});
  var r=await core.runWithRetry("/api/x",{method:"GET"},e.deps);
  ok(e.calls.length===3, "T3: fetch called 3x (2 retries) got "+e.calls.length);
  ok(r.data.v===1 && r.cached===false && r.attempts===3, "T3: resolved after retries");
  ok(e.sleepMs()>=300, "T3: exponential backoff slept ("+e.sleepMs()+"ms)");

  // T4 POST not retried by default
  var e2=makeDeps([{at:1,res:{ok:false,status:500}}],{fallback:{ok:false,status:500}});
  var threw=false;
  try{ await core.runWithRetry("/api/merge",{method:"POST"},e2.deps); }catch(err){ threw=(err.name==="ApiError"&&err.kind==="http"&&err.status===500); }
  ok(threw && e2.calls.length===1, "T4: POST not retried by default (1 call, threw ApiError)");

  // T5 cache dedup within TTL
  var e3=makeDeps([{at:1,res:{ok:true,status:200,json:function(){return Promise.resolve({n:1});}}}],{now:1000});
  var a=await core.runWithRetry("/api/agents",{method:"GET"},e3.deps);
  var b=await core.runWithRetry("/api/agents",{method:"GET"},e3.deps);
  ok(e3.calls.length===1 && a.cached===false && b.cached===true, "T5: second GET served from cache (1 fetch)");

  // T6 non-2xx JSON attached to error
  var e4=makeDeps([{at:1,res:{ok:false,status:404,json:function(){return Promise.resolve({msg:"nope"});}}}]);
  var t4=false; try{ await core.runWithRetry("/api/agents/9",{method:"GET"},e4.deps); }catch(err){ t4=(err.status===404 && err.data&&err.data.msg==="nope"); }
  ok(t4, "T6: error carries status + parsed body");

  console.log("\nALL TESTS PASSED");
})();
