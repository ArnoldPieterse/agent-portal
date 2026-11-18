import os, re, json, time
HERE = os.getcwd()
_ns = {"os": os, "re": re, "json": json, "time": time, "HERE": HERE,
       "load_agents": lambda: json.load(open(os.path.join(HERE, "agents.json"), encoding="utf-8"))}
src = open("agent_portal.py", encoding="utf-8").read()
i = src.index("def _fleet_health_composite")
j = src.index("def _slip_risk_snapshot")
exec(src[i:j], _ns)
r = _ns["_fleet_health_composite"]()
print("ok", r["ok"], "avg", r.get("fleet_avg"), "note:", r.get("note", "")[:60])
for a in r["agents"]:
    print(f"{a['agent']:12} {a['score']:>5} {a['color']:6} r/t={a['goals_reached']}/{a['goals_total']} age={a['evidence_age_days']} excl={a['excluded_factors']}")
