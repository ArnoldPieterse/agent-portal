#!/usr/bin/env python3
"""DNA rebuild - reassemble the portal core from memory/dna build functions (2026-11-25).

One regex finds every build function in builds/*.py; chain order comes from deps/id;
each blob decompresses to a byte-identical artifact (sha256-verified both ways).
Usage:
  python memory/dna/rebuild.py             DRY-RUN: verify blobs, report drift vs live files
  python memory/dna/rebuild.py --out DIR   pure reassembly into DIR (the replication proof)
  python memory/dna/rebuild.py --apply     back up current targets, then rewrite them
  python memory/dna/rebuild.py --mint bNN  refresh build NN from its live file (keeps DNA in sync)
"""
import ast, base64, gzip, hashlib, json, os, re, shutil, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))          # memory/dna
ROOT = os.path.dirname(os.path.dirname(HERE))              # project root
BUILDS = os.path.join(HERE, "builds")
MANIFEST = os.path.join(HERE, "manifest.json")
# THE scan regex (see dna-spec.md) - single source of truth for what counts as a build.
BUILD_RE = re.compile(r"^#\s*DNA-BUILD\s+id=(\d+)\s+name=(\S+)\s+target=(\S+)\s+"
                      r"date=(\d{4}-\d{2}-\d{2})\s+deps=([\w,\-]*)\s*$", re.M)

def scan_builds():
    out = []
    for fn in sorted(os.listdir(BUILDS)):
        if not fn.endswith(".py"):
            continue
        src = open(os.path.join(BUILDS, fn), encoding="utf-8").read()
        m = BUILD_RE.search(src)
        if not m:
            print("  ! skipped (no DNA-BUILD header):", fn)
            continue
        consts = {}
        for node in ast.parse(src).body:
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id in ("BLOB", "SHA256")
                    and isinstance(node.value, ast.Constant)):
                consts[node.targets[0].id] = node.value.value
        out.append({"file": fn, "id": int(m.group(1)), "name": m.group(2), "target": m.group(3),
                    "date": m.group(4),
                    "deps": [d for d in m.group(5).split(",") if d and d != "-"],
                    "blob": consts.get("BLOB"), "sha256": consts.get("SHA256")})
    return out

def topo(builds):
    by_id = {b["id"]: b for b in builds}
    order, done = [], set()
    def visit(b, stack):
        if b["id"] in done:
            return
        if b["id"] in stack:
            raise SystemExit("DNA dependency cycle at build " + str(b["id"]))
        for d in b["deps"]:
            if d in by_id:
                visit(by_id[d], stack | {b["id"]})
        done.add(b["id"])
        order.append(b)
    for b in sorted(builds, key=lambda x: x["id"]):
        visit(b, frozenset())
    return order

def h(path):
    try:
        return hashlib.sha256(open(path, "rb").read()).hexdigest()
    except OSError:
        return None

def run(mode, outdir=None):
    builds = scan_builds()
    if not builds:
        print("DNA: no build functions found in", BUILDS)
        return 1
    order = topo(builds)
    entries, ok_all = [], True
    for b in order:
        tgt_rel = b["target"].replace("/", os.sep)
        live = os.path.join(ROOT, tgt_rel)
        try:
            data = gzip.decompress(base64.b64decode(b["blob"] or ""))
        except Exception as e:
            entries.append({**_meta(b), "status": "BLOB-DECODE-FAIL", "detail": str(e)[:80]})
            ok_all = False
            continue
        blob_sha = hashlib.sha256(data).hexdigest()
        if b["sha256"] and blob_sha != b["sha256"]:
            entries.append({**_meta(b), "status": "BLOB-INTEGRITY-FAIL",
                            "detail": blob_sha[:12] + " != " + b["sha256"][:12]})
            ok_all = False
            continue
        disk = h(live)
        if mode == "dry":
            status = "in-sync" if disk == b["sha256"] else ("missing-live" if not disk else "drift")
            entries.append({**_meta(b), "status": status, "live_sha": (disk or "")[:12]})
        elif mode == "out":
            dst = os.path.join(outdir, tgt_rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            open(dst, "wb").write(data)
            good = h(dst) == b["sha256"]
            ok_all &= good
            entries.append({**_meta(b), "status": "rebuilt" if good else "VERIFY-FAIL", "path": dst})
        elif mode == "apply":
            bak = os.path.join(HERE, "backup-" + time.strftime("%Y%m%d-%H%M%S"))
            os.makedirs(bak, exist_ok=True)
            if os.path.isfile(live):
                shutil.copy2(live, os.path.join(bak, os.path.basename(live)))
            os.makedirs(os.path.dirname(live), exist_ok=True)
            open(live, "wb").write(data)
            good = h(live) == b["sha256"]
            ok_all &= good
            entries.append({**_meta(b), "status": "applied" if good else "VERIFY-FAIL",
                            "backup": os.path.basename(bak)})
    manifest = {"built": time.strftime("%Y-%m-%dT%H:%M:%S"), "mode": mode,
                "ok": ok_all, "entries": entries}
    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), indent=1)
    for e in entries:
        print("  b%02d %-16s %-28s %s %s" % (e["id"], e["name"], e["target"], e["status"],
                                            e.get("detail") or e.get("live_sha") or ""))
    print("DNA %s: %d builds, ok=%s | manifest -> memory/dna/manifest.json"
          % (mode, len(entries), ok_all))
    return 0 if ok_all else 1

def _meta(b):
    return {"id": b["id"], "name": b["name"], "target": b["target"],
            "date": b["date"], "sha256": (b["sha256"] or "")[:12]}

def mint(bid):
    builds = {b["id"]: b for b in scan_builds()}
    if bid not in builds:
        print("no build id", bid); return 1
    b = builds[bid]
    live = os.path.join(ROOT, b["target"].replace("/", os.sep))
    data = open(live, "rb").read()
    blob = base64.b64encode(gzip.compress(data, 9)).decode()
    sha = hashlib.sha256(data).hexdigest()
    p = os.path.join(BUILDS, b["file"])
    src = open(p, encoding="utf-8").read()
    today = time.strftime("%Y-%m-%d")
    src = re.sub(r"(#\s*DNA-BUILD\s+id=%d\s+name=\S+\s+target=\S+\s+)date=\d{4}-\d{2}-\d{2}" % bid,
                 r"\1date=" + today, src)
    src = re.sub(r'BLOB\s*=\s*"[^"]*"', 'BLOB = "' + blob + '"', src)
    src = re.sub(r'SHA256\s*=\s*"[^"]*"', 'SHA256 = "' + sha + '"', src)
    open(p, "w", encoding="utf-8").write(src)
    print("minted b%02d %s from live file (%d bytes -> blob %d chars)" % (bid, b["target"], len(data), len(blob)))
    return 0

def main():
    args = sys.argv[1:]
    if args and args[0] == "--out":
        return run("out", os.path.abspath(args[1]))
    if args and args[0] == "--apply":
        return run("apply")
    if args and args[0] == "--mint":
        m = re.match(r"b?(\d+)$", args[1])
        return mint(int(m.group(1)) if m else 0)
    return run("dry")

if __name__ == "__main__":
    sys.exit(main())
