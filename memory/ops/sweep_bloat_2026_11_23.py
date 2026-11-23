#!/usr/bin/env python3
"""One-shot 2026-11-23 (tree bloat): delete host-local bloat from ALL hosts + local.
Bloat = memory/designer/_* browser profile dirs + memory/mechanic/backups/*.tar.gz.
memory_mirror.py now excludes these paths both ways, so they stay gone. Safe to re-run."""
import json, os, shutil, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import memory_mirror as mm

hosts = json.load(open(os.path.join(mm.HERE, "memory_mirror_hosts.json")))
hosts = hosts if isinstance(hosts, list) else hosts.get("hosts", [])

def sweep(memdir):
    removed, freed = 0, 0
    des = os.path.join(memdir, "designer")
    if os.path.isdir(des):
        for e in os.listdir(des):
            p = os.path.join(des, e)
            if e.startswith("_") and os.path.isdir(p):
                try:
                    sz = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(p) for f in fs)
                    shutil.rmtree(p, ignore_errors=True); removed += 1; freed += sz
                except Exception: pass
    bak = os.path.join(memdir, "mechanic", "backups")
    if os.path.isdir(bak):
        for f in os.listdir(bak):
            if f.endswith(".tar.gz"):
                p = os.path.join(bak, f)
                try:
                    sz = os.path.getsize(p); os.remove(p); removed += 1; freed += sz
                except Exception: pass
    return removed, freed

print("== local ==")
r, f = sweep(os.path.join(mm.HERE, "memory"))
print("  removed %d files/dirs, %.1f MB" % (r, f / 1e6))

for h in hosts:
    if h.get("status") != "ok": continue
    name, ip, user = h["name"], h["ip"], h["user"]
    ok, note = mm.ensure_conn(ip, user, h.get("password", ""))
    if not ok:
        print("== %s == CONNECT FAIL: %s" % (name, note)); continue
    memdir = r"\\%s\C$\Users\%s\.unsloth\studio\sandbox\_default\memory" % (ip, user)
    try:
        r, f = sweep(memdir)
        print("== %s == removed %d files/dirs, %.1f MB" % (name, r, f / 1e6))
    except Exception as e:
        print("== %s == SWEEP ERROR: %s" % (name, str(e)[:100]))
