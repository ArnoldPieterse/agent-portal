import json,pathlib,datetime
from collections import defaultdict
POS={"r":1,"s":2,"a":3,"f":4,"n":5}
def sc(o):
 o=o.lower()
 if o in POS: return POS[o]
 if "fail" in o or "abort" in o or "reject" in o: return 0
 if "pass" in o or "success" in o or "ratif" in o: return 4
 if "review" in o or "pending" in o: return 2
 return 3
def cyc(d):
 if not d or d=="unknown": return 0
 dt=datetime.date.fromisoformat(d)
 if dt<=datetime.date(2026,11,14): return 1
 if dt<=datetime.date(2026,11,16): return 2
 if dt<=datetime.date(2026,11,18): return 3
 if dt<=datetime.date(2026,11,20): return 4
 if dt<=datetime.date(2026,11,22): return 5
 return 6
A=pathlib.Path("memory/archivist")
R=pathlib.Path("memory/researcher")
recs=[json.loads(l) for l in (A/"decision-archive-data.jsonl").read_text().splitlines() if l.strip()]
for r in recs: r["cycle"]=cyc(r.get("date","")); r["score"]=sc(r.get("outcome",""))
def norm_owner(o):
 o=o.lower().strip()
 return o if o in ("archivist","builder","designer","mechanic","orchestrator","scribe","verifier") else "other"
agent_cyc=defaultdict(lambda: defaultdict(list))
domain_cyc=defaultdict(lambda: defaultdict(list))
for r in recs:
 if r["cycle"]==0: continue
 ag=norm_owner(r.get("owner","?"))
 agent_cyc[ag][r["cycle"]].append(r["score"])
 domain_cyc[r.get("category","other")][r["cycle"]].append(r["score"])
def trend(d):
 series=[]
 for c in range(1,7):
  v=d.get(c,[])
  series.append({"cycle":c,"n":len(v),"mean":round(sum(v)/len(v),3) if v else None})
 return series
agent_trend={a: trend(d) for a,d in agent_cyc.items()}
domain_trend={d2: trend(d3) for d2,d3 in domain_cyc.items()}
def detect_reg(trend_data):
 regs=[]
 for a,series in trend_data.items():
  prev=None
  for pt in series:
   if pt["mean"] is None: continue
   if prev is not None and pt["mean"]<prev-1.0:
    regs.append({"agent":a,"from_cycle":pt["cycle"]-1,"to_cycle":pt["cycle"],"drop":round(prev-pt["mean"],2)})
   prev=pt["mean"]
 return regs
regs=detect_reg(agent_trend)
