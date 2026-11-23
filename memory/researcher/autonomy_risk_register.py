#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""autonomy_risk_register.py - Researcher Goal 7 (cycle-11): Autonomy Risk Register.

Scans memory/**/*.md for risk markers (OPS-NOTE, RISK, WARNING, HOLD,
BLOCKED, DOWNGRADE) and builds a deduplicated register: id + one-line risk +
source file + mitigation status (mitigated when the same file carries a
nearby fixed/verified/resolved marker). JSON output is valid and stable.

Usage:
  python autonomy_risk_register.py            # rebuild -> memory/researcher/risk-register.json
  python autonomy_risk_register.py selftest   # includes negative test: plant a risk, re-scan
"""
import hashlib, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
MEMORY = os.path.join(ROOT, "memory")
OUT = os.path.join(HERE, "risk-register.json")
RISK_RE = re.compile(r"\b(OPS-NOTE|RISK|WARNING|HOLD|BLOCKED|DOWNGRADE)\b", re.IGNORECASE)
MITIGATED_RE = re.compile(r"\b(fixed|verified|resolved|mitigated|closed|PASS)\b", re.IGNORECASE)


def scan():
    risks = {}
    for dirpath, _, filenames in os.walk(MEMORY):
        for fn in sorted(filenames):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            try:
                lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                continue
            for i, line in enumerate(lines):
                if not RISK_RE.search(line):
                    continue
                text = " ".join(line.split())[:160]
                rid = hashlib.sha256((rel + "::" + text).encode()).hexdigest()[:10]
                window = "\n".join(lines[max(0, i - 3):i + 4])
                mitigated = bool(MITIGATED_RE.search(window))
                risks[rid] = {
                    "id": rid,
                    "risk": text,
                    "source": rel,
                    "line": i + 1,
                    "mitigated": mitigated,
                    "status": "mitigated" if mitigated else "open",
                }
    return risks


def build():
    t0 = time.time()
    risks = scan()
    reg = {
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total": len(risks),
        "open": sum(1 for r in risks.values() if not r["mitigated"]),
        "mitigated": sum(1 for r in risks.values() if r["mitigated"]),
        "build_s": round(time.time() - t0, 2),
        "risks": sorted(risks.values(), key=lambda r: (r["status"], r["source"])),
    }
    json.dump(reg, open(OUT, "w", encoding="utf-8"), indent=1)
    return reg


def selftest():
    reg = build()
    assert reg["total"] >= 5, "expected >=5 risks in a live tree, got %d" % reg["total"]
    assert reg["open"] + reg["mitigated"] == reg["total"]
    for r in reg["risks"][:20]:
        assert set(r) >= {"id", "risk", "source", "status"}
        assert os.path.exists(os.path.join(ROOT, r["source"].replace("/", os.sep)))
    # determinism: second scan (ignoring generated timestamp) identical
    a = json.dumps([r for r in reg["risks"]], sort_keys=True)
    reg2 = build()
    b = json.dumps([r for r in reg2["risks"]], sort_keys=True)
    assert a == b, "register not deterministic"
    # negative test: plant a fresh risk, re-scan must pick it up, then clean up
    plant = os.path.join(HERE, "_risk_plant_test.md")
    marker = "RISK planted-selftest-%d unique-token-xyzzy" % int(time.time())
    open(plant, "w", encoding="utf-8").write("# t\n\n" + marker + "\n")
    try:
        reg3 = build()
        assert any(marker in r["risk"] for r in reg3["risks"]), "planted risk not detected"
    finally:
        os.remove(plant)
    # rebuild clean state after cleanup
    build()
    print("register: total=%d open=%d mitigated=%d (%.2fs); planted-risk negative test PASS"
          % (reg["total"], reg["open"], reg["mitigated"], reg["build_s"]))
    print("SELFTEST PASS")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "selftest":
        selftest()
    else:
        r = build()
        print("total=%d open=%d mitigated=%d -> %s" % (r["total"], r["open"], r["mitigated"], OUT))

