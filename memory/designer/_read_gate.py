
import json
d = json.load(open("memory/designer/_gate_live.json"))
js = [c for c in d["checks"] if c.get("check") == "js_syntax"][0]
fails = [(r["file"], r["issues"]) for r in js["results"] if not r["pass"]]
print("JS files checked:", js["files_checked"])
print("JS pass overall :", js["pass"])
print("Failing files   :", len(fails))
for f, iss in fails:
    print("   ", f, iss)
# summary of all checks
for c in d["checks"]:
    name = c.get("check")
    print("  check %-20s pass=%s" % (name, c.get("pass")))
print("OVERALL_PASS:", d["overall_pass"])
