"""Voxel reference registry - the 3D world referencing system (2026-11-26).

Each voxel cell addresses a piece of code in the memory tree: a file path,
an M-CODE, or a rigid body object in the mind-room scene. Cells subdivide
recursively into 8 octant sub-voxels - the 3D twin of the tree-leaf memory
system. Level-0 grid covers the room (uniform 3 m^3 cells):
    x: 0..7 (world -12..+12), y: 0..3 (-4.5..+4.5), z: 0..7 (-12..+12)
Address grammar: V(x,y,z) then octant segments, e.g. V(3,3,3)/0/1/1
State: memory/archivist/voxels.json

CLI:
  python voxel.py list [--depth N]
  python voxel.py get V(3,3,3)/0/1/1
  python voxel.py set V(3,3,3) --label L --ref PATH_OR_MCODE [--kind leaf|rigid|anim|space] [--rigid ssj]
  python voxel.py subdivide V(3,3,3)
  python voxel.py resolve V(3,3,3)/0/1/1
"""
import json, os, re, sys, threading, time
HERE = os.path.dirname(os.path.abspath(__file__))          # memory/archivist
ROOT = os.path.dirname(os.path.dirname(HERE))              # project root
DB = os.path.join(HERE, "voxels.json")
GRID = {"x": [0, 7], "y": [0, 3], "z": [0, 7]}
ORIGIN = (-12.0, -4.5, -12.0)
SIZE = (3.0, 3.0, 3.0)
MAX_DEPTH = 11            # 3m / 2^11 = 1.46mm <= 2mm detail floor
MIN_SIZE_M = 0.002        # finest voxel we keep: 2mm
CELL_CAP = 150000         # hard cap on materialized cells (JSON sanity)
MRE = re.compile(r"^[A-Z][a-z]?\d+$")
ARE = re.compile(r"^V\((\d+),(\d+),(\d+)\)(?:/([01])(?:,([01]),?)+)*$", re.S)


def _parse(addr):
    """'V(3,3,3)/0/1/1' -> ('3,3,3', [(0,),(1,),(1,)]) ; None if bad."""
    m = re.match(r"^V\((\d+),(\d+),(\d+)\)", addr or "")
    if not m:
        return None
    base = ",".join(m.groups())
    tail = (addr[m.end():] or "").strip().lstrip("/")
    if not tail:
        return base, []
    digits = tail.split("/")
    if len(digits) % 3 != 0 or any(d not in "01" for d in digits):
        return None
    segs = [tuple(int(digits[i + j]) for j in range(3)) for i in range(0, len(digits), 3)]
    return base, segs


def load():
    if os.path.exists(DB):
        return json.load(open(DB, encoding="utf-8"))
    return {"meta": {"grid": GRID, "origin": ORIGIN, "size": SIZE}, "cells": {}}


def save(db):
    m = db.get("meta") or {}
    m.update({"grid": GRID, "origin": ORIGIN, "size": SIZE})
    db["meta"] = m
    tmp = DB + ".tmp"
    for attempt in range(5):  # Windows can briefly lock the file (AV/indexer)
        try:
            json.dump(db, open(tmp, "w", encoding="utf-8"), indent=1)
            os.replace(tmp, DB)  # atomic: readers never see a half-write
            return
        except PermissionError:
            time.sleep(0.05 * (attempt + 1))
    raise RuntimeError("save blocked after retries")


def node_at(db, addr):
    """Walk to (chain, leaf). chain = list of (addr_str, key, node). None if missing."""
    parsed = _parse(addr)
    if not parsed:
        return None
    base, segs = parsed
    cells, chain = db["cells"], []
    if base not in cells:
        return None
    node, key = cells[base], base
    chain.append((addr[:m_end(addr)] if False else _vstr(base), key, node))
    for s in segs:
        sub = node.get("sub") or {}
        k = ",".join(str(i) for i in s)
        if k not in sub:
            return None
        node = sub[k]
        chain.append((chain[-1][0] + "/" + "/".join(str(i) for i in s), k, node))
    return chain, node


def _vstr(base):
    return "V(" + base + ")"


def m_end(addr):  # kept for clarity; unused branch above
    return 0


def set_node(db, addr, **fields):
    parsed = _parse(addr)
    if not parsed:
        raise SystemExit("bad address: " + str(addr))
    base, segs = parsed
    node = db["cells"].setdefault(base, {"sub": {}})
    for s in segs:
        k = ",".join(str(i) for i in s)
        node = (node.setdefault("sub", {})).setdefault(k, {"sub": {}})
    for f in ("label", "kind", "ref", "rigid"):
        if fields.get(f) is not None:
            node[f] = fields[f]
    save(db)
    return node


def cell_world(addr):
    """Exact world geometry of any address: (px, py, pz, size_m)."""
    p = _parse(addr)
    if not p:
        return None
    base, segs = p
    x, y, z = (int(v) for v in base.split(","))
    px, py, pz = ORIGIN[0] + x * SIZE[0], ORIGIN[1] + y * SIZE[1], ORIGIN[2] + z * SIZE[2]
    s = SIZE[0]
    for (i, j, k) in segs:
        px += i * s / 2.0; py += j * s / 2.0; pz += k * s / 2.0
        s /= 2.0
    return (px, py, pz, s)

def count_cells(db):
    n = 0
    def walk(node):
        nonlocal n
        n += 1
        for ch in (node.get("sub") or {}).values():
            walk(ch)
    for c in db["cells"].values():
        walk(c)
    return n

def stamp_all(db):
    """Write exact pos/size onto every materialized node (correct locations)."""
    n = 0
    def walk(node, addr):
        nonlocal n
        w = cell_world(addr)
        if not w:
            return
        node["pos"] = [round(w[0], 5), round(w[1], 5), round(w[2], 5)]
        node["size_m"] = round(w[3], 6)
        n += 1
        for k, ch in (node.get("sub") or {}).items():
            walk(ch, addr + "/" + "/".join(k.split(",")))
    for b, c in db["cells"].items():
        walk(c, "V(" + b + ")")
    return n

def subdivide(db, addr, pulse=None):
    """Split one voxel into 8 octant children with exact world pos/size."""
    res = node_at(db, addr)
    if not res:
        raise SystemExit("no such voxel: " + str(addr))
    a, _k, node = res[0][-1]
    subs = node.setdefault("sub", {})
    w = cell_world(a)
    s2 = w[3] / 2.0
    made = 0
    for i in (0, 1):
        for j in (0, 1):
            for k in (0, 1):
                key = str(i) + "," + str(j) + "," + str(k)
                if key not in subs:
                    ch = {"sub": {},
                          "pos": [round(w[0] + i * s2, 5), round(w[1] + j * s2, 5), round(w[2] + k * s2, 5)],
                          "size_m": round(s2, 6)}
                    if pulse:
                        ch["pulse"] = pulse
                    subs[key] = ch
                    made += 1
    return made


def _resolve_ref(ref):
    out = {"ref": ref}
    try:
        sys.path.insert(0, HERE)
        import mcode
    except Exception:
        mcode = None
    if MRE.match(ref or "") and mcode is not None:
        try:
            r = mcode.resolve(ref)
            out.update({"mcode": ref, "path": getattr(r, "path", str(r))})
            return out
        except Exception as e:
            out["error"] = str(e)
            return out
    p = os.path.join(ROOT, (ref or "").replace("/", os.sep))
    if os.path.exists(p):
        out["path"] = os.path.relpath(p, ROOT).replace(os.sep, "/")
        try:
            head = open(p, encoding="utf-8", errors="replace").read(300)
            out["head"] = head
        except Exception as e:
            out["error"] = str(e)
        if mcode is not None:
            try:
                out["mcode"] = mcode.code_for(p)
            except Exception:
                pass
    else:
        out["error"] = "path not found"
    return out


def _nearest(db, addr):
    m = re.match(r"V\((\d+),(\d+),(\d+)\)", addr)
    if not m:
        return None
    t = tuple(int(m.group(i)) for i in (1, 2, 3))
    best, bd = None, None
    for k in (db.get("cells") or {}):
        mk = re.match(r"V\((\d+),(\d+),(\d+)\)", k)
        if not mk:
            continue
        d = sum((int(mk.group(i)) - t[i - 1]) ** 2 for i in (1, 2, 3))
        if bd is None or d < bd:
            best, bd = k, d
    return best


def resolve_payload(addr):
    db = load()
    res = node_at(db, addr)
    at_addr = addr
    if not res:
        parts = addr.split("/")
        while len(parts) > 1 and not res:
            parts = parts[:-1]
            res = node_at(db, "/".join(parts))
        if res:
            at_addr = "/".join(parts)
        else:
            nb = _nearest(db, addr)
            if nb:
                res = node_at(db, nb)
                at_addr = nb
            else:
                return {"addr": addr, "found": False}
    chain = res[0]
    out = []
    for a, _k, n in chain:
        w = cell_world(a)
        e = {"addr": a, "label": n.get("label", ""), "kind": n.get("kind", "space"),
             "rigid": n.get("rigid"), "has_sub": bool(n.get("sub")),
             "depth": len(_parse(a)[1]) if _parse(a) else 0}
        if w:
            e["pos"] = [round(w[0], 3), round(w[1], 3), round(w[2], 3)]
            e["size_m"] = round(w[3], 4)
            e["cell_size_mm"] = round(w[3] * 1000, 2)
        if e["has_sub"]:
            e["children"] = [a + "/" + k.replace(",", "/") for k in n["sub"].keys()]
        if n.get("ref"):
            e["resolved"] = _resolve_ref(n["ref"])
        out.append(e)
    return {"addr": addr, "found": True, "at": at_addr, "chain": out}


def _walk(node, addr, depth, lines):
    for k in sorted((node.get("sub") or {}).keys()):
        n = node["sub"][k]
        a = addr + "/" + "/".join(k.split(","))
        mark = "*" if (n.get("label") or n.get("ref")) else " "
        lines.append(f"{mark} {a:28s} {n.get('label','')[:34]:34s} {n.get('kind',''):6s} {n.get('ref','')[:30]}")
        if depth > 0:
            _walk(n, a, depth - 1, lines)


def main(argv):
    db = load()
    cmd = argv[1] if len(argv) > 1 else "list"
    if cmd == "list":
        depth = 1
        if "--depth" in argv:
            depth = int(argv[argv.index("--depth") + 1])
        lines = [f"# {len(db['cells'])} level-0 cells, grid {GRID}"]
        root = {"sub": db["cells"]}
        _walk(root, "", depth, lines)
        print("\n".join(lines))
    elif cmd == "get":
        print(json.dumps(resolve_payload(argv[2]), indent=1)[:4000])
    elif cmd == "set":
        kw = {}
        for f in ("label", "kind", "ref", "rigid"):
            if f"--{f}" in argv:
                kw[f] = argv[argv.index(f"--{f}") + 1]
        n = set_node(db, argv[2], **kw)
        print("set", argv[2], "->", json.dumps(n)[:300])
    elif cmd == "subdivide":
        made = subdivide(db, argv[2])
        db.setdefault("meta", {})["cell_count"] = count_cells(db)
        save(db)
        print("made", made, "octants under", argv[2])
    elif cmd == "resolve":
        print(json.dumps(resolve_payload(argv[2]), indent=1)[:4000])
    elif cmd == "stamp":
        n = stamp_all(db)
        db.setdefault("meta", {})["cell_count"] = count_cells(db)
        save(db)
        print("stamped", n, "nodes with exact pos/size")
    elif cmd == "pulse":
        sub = argv[2] if len(argv) > 2 else "status"
        if sub == "arm":
            kw = {}
            for f in ("speed", "max_depth", "every_ms"):
                if "--" + f in argv:
                    kw[f] = int(argv[argv.index("--" + f) + 1])
            if "--to" in argv:
                kw["to"] = argv[argv.index("--to") + 1]
            print("armed", pulse_arm(argv[3], **kw))
        elif sub == "stop":
            print(pulse_stop())
        else:
            print(json.dumps(pulse_status(), indent=1))
    else:
        raise SystemExit(__doc__)


class PulseEngine:
    """10ms voxel pulse (2026-11-26): code that jumps between voxels.
    From an object's top-level voxel a wavefront expands every `every_ms`
    (default 10), visiting each neighbour and generating sub-voxels one level
    deeper per pass, down to the 2mm floor (MAX_DEPTH). A jump target (`to`)
    teleports the wavefront when its region is exhausted."""

    def __init__(self):
        self.lock = threading.Lock()
        self.jumps = {}
        self.ticks = 0
        self.running = False

    def _ensure(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self._loop, daemon=True).start()

    def arm(self, addr, speed=8, max_depth=MAX_DEPTH, every_ms=10, to=None):
        with self.lock:
            jid = addr + ("->" + to if to else "")
            self.jumps[jid] = {"addr": addr, "to": to, "speed": int(speed),
                               "max_depth": min(int(max_depth), MAX_DEPTH),
                               "every_ms": max(1, int(every_ms)),
                               "frontier": [addr], "ring": 0, "ticks": 0,
                               "made": 0, "hops": 0, "done": False, "next_at": 0.0}
            self._ensure()
        return jid

    def stop(self):
        with self.lock:
            self.jumps = {}
            self.running = False
        return {"stopped": True}

    def status(self):
        with self.lock:
            out = {"running": any(not j["done"] for j in self.jumps.values()),
                   "ticks": self.ticks, "jumps": []}
            for jid, j in self.jumps.items():
                out["jumps"].append({"id": jid, "addr": j["addr"], "to": j["to"],
                                     "every_ms": j["every_ms"], "max_depth": j["max_depth"],
                                     "ring": j["ring"], "ticks": j["ticks"], "made": j["made"],
                                     "hops": j["hops"], "frontier": len(j["frontier"]),
                                     "done": j["done"]})
        return out

    def _loop(self):
        last_flush = 0.0
        db = None  # persistent across ticks: a failed flush must not lose progress
        try:
            while True:
                time.sleep(0.01)  # base tick: 10ms
                now = time.time()
                with self.lock:
                    if not self.jumps:
                        db = None
                        continue
                    if db is None:
                        db = load()
                    self.ticks += 1
                    changed = False
                    for j in self.jumps.values():
                        if j["done"] or now < j["next_at"]:
                            continue
                        j["next_at"] = now + j["every_ms"] / 1000.0
                        j["ticks"] += 1
                        total = db.get("meta", {}).get("cell_count")
                        if total is None:
                            total = count_cells(db)
                            db.setdefault("meta", {})["cell_count"] = total
                        before = total
                        steps = 0
                        while j["frontier"] and steps < j["speed"]:
                            a = j["frontier"].pop(0)
                            parsed = _parse(a)
                            if not parsed or len(parsed[1]) >= j["max_depth"]:
                                continue
                            if total >= CELL_CAP:
                                break
                            made = subdivide(db, a, pulse={"ring": j["ring"], "tick": self.ticks})
                            steps += 1
                            if made:
                                total += made
                                db["meta"]["cell_count"] = total
                                changed = True
                                for c in ("0", "1"):
                                    for d2 in ("0", "1"):
                                        for e2 in ("0", "1"):
                                            j["frontier"].append(a + "/" + c + "/" + d2 + "/" + e2)
                        j["made"] += total - before
                        if not j["frontier"] and j.get("to"):
                            j["hops"] += 1
                            j["addr"], j["to"] = j["to"], None
                            j["frontier"] = [j["addr"]]
                            j["ring"] = 0
                        elif not j["frontier"]:
                            j["done"] = True
                    all_done = all(j["done"] for j in self.jumps.values())
                    if changed and (now - last_flush >= 0.5 or all_done):
                        try:
                            save(db)
                            last_flush = now
                        except Exception:
                            pass  # transient lock; state kept in memory, retried next window
                    if all_done:
                        try:
                            save(db)
                        except Exception:
                            pass
                        self.running = False
                        db = None
                        break
        except Exception:
            self.running = False


ENGINE = PulseEngine()


def pulse_arm(addr, **kw):
    return ENGINE.arm(addr, **kw)


def pulse_stop():
    return ENGINE.stop()


def pulse_status():
    return ENGINE.status()


if __name__ == "__main__":
    main(sys.argv)
