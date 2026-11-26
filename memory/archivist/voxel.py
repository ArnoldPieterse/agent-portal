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
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))          # memory/archivist
ROOT = os.path.dirname(os.path.dirname(HERE))              # project root
DB = os.path.join(HERE, "voxels.json")
GRID = {"x": [0, 7], "y": [0, 3], "z": [0, 7]}
ORIGIN = (-12.0, -4.5, -12.0)
SIZE = (3.0, 3.0, 3.0)
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
    db["meta"] = {"grid": GRID, "origin": ORIGIN, "size": SIZE}
    json.dump(db, open(DB, "w", encoding="utf-8"), indent=1)


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


def subdivide(db, addr):
    chain = node_at(db, addr)
    if not chain:
        raise SystemExit("no such voxel: " + str(addr))
    node = chain[1]
    subs = node.setdefault("sub", {})
    made = 0
    for i in ("0", "1"):
        for j in ("0", "1"):
            for k in ("0", "1"):
                key = i + "," + j + "," + k
                if key not in subs:
                    subs[key] = {"sub": {}}
                    made += 1
    save(db)
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
        e = {"addr": a, "label": n.get("label", ""), "kind": n.get("kind", "space"),
             "rigid": n.get("rigid"), "has_sub": bool(n.get("sub"))}
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
        print("made", subdivide(db, argv[2]), "octants under", argv[2])
    elif cmd == "resolve":
        print(json.dumps(resolve_payload(argv[2]), indent=1)[:4000])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
