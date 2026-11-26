"""Voxel pulse engine (2026-11-26) - code that jumps between voxels.

A pulse is a wavefront that starts at an object's top-level voxel and expands
one ring per tick (default 10 ms). Every tick it:
  * updates all level-0 cells on the current ring (correct bounds recorded),
  * re-pulses every content cell within reach - cascading through its whole
    sub-voxel tree, running any code attached to a voxel,
  * follows `jump` links: a voxel may carry jump -> V(...)/... and the pulse
    teleports there, continuing from that voxel (hops are logged),
  * drills: a content cell grows one octant level per tick toward its focus
    point until cells reach the 2 mm detail floor (depth 11 = 1.46 mm).

State: memory/archivist/pulse_state.json   (voxels themselves stay in voxels.json)

CLI:
  python voxel_pulse.py status
  python voxel_pulse.py tick [N]            # run N ticks synchronously
  python voxel_pulse.py seed --id P-x --origin V(4,2,4) --radius 3
  python voxel_pulse.py jump V(4,2,4) V(3,3,3)
  python voxel_pulse.py code V(2,2,4) memory/archivist/pulse_heartbeat.py [--run]
  python voxel_pulse.py verify              # recompute + fix every node's bounds
"""
import json, math, os, sys, time, threading

HERE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(HERE, "voxels.json")
STATE = os.path.join(HERE, "pulse_state.json")
ORIGIN = (-12.0, -4.5, -12.0)
CELL = 3.0
GRID = (8, 4, 8)
FLOOR_MM = 2.0
FLOOR_DEPTH = max(1, math.ceil(math.log2(CELL * 1000.0 / FLOOR_MM)))   # 11 -> 1.46 mm
TICK_S = 0.01

def size_mm(d): return CELL * 1000.0 / (2 ** d)

def _parse(addr):
    m = __import__("re").match(r"^V\((\d+),(\d+),(\d+)\)", addr or "")
    if not m: return None
    base, tail = ",".join(m.groups()), (addr[m.end():] or "").strip().lstrip("/")
    segs = []
    if tail:
        dg = tail.split("/")
        if len(dg) % 3 or any(c not in "01" for c in dg): return None
        segs = [tuple(int(dg[i + j]) for j in range(3)) for i in range(0, len(dg), 3)]
    return base, segs

def _vstr(base): return "V(" + base + ")"

def bounds_of(addr):
    p = _parse(addr)
    if not p: return None
    base, segs = p
    x, y, z = (int(v) for v in base.split(","))
    mn = [ORIGIN[0] + x * CELL, ORIGIN[1] + y * CELL, ORIGIN[2] + z * CELL]
    sz = CELL
    for s in segs:
        mn = [mn[i] + (sz / 2) * s[i] for i in range(3)]
        sz /= 2
    return [round(v, 4) for v in mn] + [round(v + sz, 4) for v in mn]

def load_db():
    if os.path.exists(DB): return json.load(open(DB, encoding="utf-8"))
    return {"meta": {}, "cells": {}}

def save_db(db): json.dump(db, open(DB, "w", encoding="utf-8"), indent=1)

def has_content(n):
    return any(n.get(k) for k in ("label", "ref", "rigid", "code", "jump"))

def cheb(a, b): return max(abs(a[i] - b[i]) for i in range(3))

class PulseEngine:
    def __init__(self):
        self.db = load_db()
        self.st = self._load_state()
        self.lock = threading.Lock()
        self.running = False
        self.thread = None
        self._dirty = False

    # ---------- state ----------
    def _load_state(self):
        if os.path.exists(STATE):
            st = json.load(open(STATE, encoding="utf-8"))
            for P in st.get("pulses", {}).values(): P.pop("_frontier", None)
            return st
        return {"tick": 0, "started": None, "pulses": {}, "last_hops": [], "stats": {}}

    def save(self):
        self.st["saved_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        json.dump(self.st, open(STATE, "w", encoding="utf-8"), indent=1)
        if self._dirty:
            save_db(self.db); self._dirty = False

    # ---------- pulse ops ----------
    def seed(self, pid, origin, radius):
        self.st["pulses"][pid] = {"origin": origin, "radius": int(radius), "ring": 0,
                                  "done": False, "hops": []}
        self.save()

    def _touch(self, base, tick, hops_left=8, jumped=None):
        """Materialize level-0 cell + cascade its sub-tree. Returns node."""
        cells = self.db["cells"]
        n = cells.setdefault(base, {"sub": {}})
        self._cascade(n, _vstr(base), 0, tick, hops_left, jumped or set())
        return n

    def _cascade(self, n, addr, depth, tick, hops_left, jumped):
        b = bounds_of(addr)
        if b and n.get("bounds") != b: n["bounds"] = b
        n["last_tick"] = tick
        self._dirty = True
        # drill one level per tick toward focus (content cells only, stop at 2 mm floor)
        if depth < FLOOR_DEPTH and has_content(n) and not n.get("sub"):
            c = [ (n["bounds"][0]+n["bounds"][3])/2, (n["bounds"][1]+n["bounds"][4])/2, (n["bounds"][2]+n["bounds"][5])/2 ]
            f = n.get("focus") or c
            s = tuple(1 if f[i] > c[i] + 1e-9 else 0 for i in range(3))
            key = ",".join(str(i) for i in s)
            child = {"kind": "drill", "label": "drill d%d %.2fmm" % (depth+1, size_mm(depth+1)), "sub": {}}
            n["sub"] = n.get("sub") or {}
            n["sub"][key] = child
        # jump links - the pulse teleports and continues from the target voxel
        j = n.get("jump")
        if j and hops_left > 0:
            pj = _parse(j)
            if pj and addr not in jumped:
                jumped.add(addr)
                hop = {"tick": tick, "from": addr, "to": j}
                self.st["last_hops"].append(hop); self.st["last_hops"] = self.st["last_hops"][-12:]
                for P in self.st["pulses"].values():
                    _h = P.setdefault("hops", [])
                    _h.append(hop)
                    if len(_h) > 200: del _h[:-200]   # cap: log, not history
                base_j, _segs = pj
                self._touch(base_j, tick, hops_left - 1, jumped)
        # run attached code (throttled per node, default once per second)
        if n.get("code") and n.get("run"):
            every = int(n.get("code_every", 100))
            if tick - int(n.get("last_code_tick", 0)) >= every:
                n["last_code_tick"] = tick
                res = self._run_code(n, addr, tick)
                n["last_code"] = (res or "")[:200]
        for k, ch in (n.get("sub") or {}).items():
            self._cascade(ch, addr + "/" + "/".join(k.split(",")), depth + 1, tick, hops_left, jumped)

    def _run_code(self, n, addr, tick):
        try:
            import importlib.util
            p = os.path.join(os.path.dirname(HERE), "..", n["code"].replace("/", os.sep))
            p = os.path.normpath(p)
            spec = importlib.util.spec_from_file_location("voxel_code_" + str(tick), p)
            mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
            r = mod.on_pulse({"tick": tick, "addr": addr, "db": self.db, "state": self.st})
            return str(r) if r is not None else "ok"
        except Exception as e:
            return "ERR " + str(e)[:120]

    # ---------- the 10 ms tick ----------
    def tick(self):
        with self.lock:
            self.st["tick"] += 1; tick = self.st["tick"]
            if not self.st.get("started"): self.st["started"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            for pid, P in list(self.st["pulses"].items()):
                o = _parse(P["origin"])
                if not o: continue
                obase = tuple(int(v) for v in o[0].split(","))
                if P["ring"] < P["radius"]:
                    P["ring"] += 1; ring = P["ring"]
                    for x in range(GRID[0]):
                        for y in range(GRID[1]):
                            for z in range(GRID[2]):
                                if cheb((x, y, z), obase) == ring:
                                    self._touch("%d,%d,%d" % (x, y, z), tick)
                reach = max(P["ring"], 1)
                seen = set()
                for base in list(self.db["cells"].keys()):
                    t = tuple(int(v) for v in base.split(","))
                    if cheb(t, obase) <= reach:
                        n = self.db["cells"][base]
                        if has_content(n) or n.get("sub"):
                            key = (pid, base, P["ring"])
                            if key not in seen:
                                seen.add(key)
                                self._cascade(n, _vstr(base), 0, tick, 8, set())
                if P["ring"] >= P["radius"]: P["done"] = True
            self.st["stats"] = {"cells": sum(self._count(v) for v in self.db["cells"].values()),
                                "hops_total": len(self.st["last_hops"])}
            if tick % 100 == 0: self.save()

    def _count(self, n):
        return 1 + sum(self._count(c) for c in (n.get("sub") or {}).values())

    # ---------- thread ----------
    def start(self):
        if self.thread and self.thread.is_alive(): return "already running"
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True, name="voxel-pulse")
        self.thread.start()
        return "started @ %d ms/tick" % int(TICK_S * 1000)

    def stop(self):
        self.running = False; self.save(); return "stopped at tick %d" % self.st["tick"]

    def _loop(self):
        next_t = time.perf_counter() + TICK_S
        while self.running:
            t0 = time.perf_counter()
            try: self.tick()
            except Exception as e: self.st["last_error"] = str(e)[:200]
            next_t += TICK_S
            delay = next_t - time.perf_counter()
            if delay > 0: time.sleep(delay)
            else: next_t = time.perf_counter()   # fell behind; resync

    def status(self):
        return {"tick": self.st["tick"], "started": self.st.get("started"),
                "running": bool(self.thread and self.thread.is_alive()),
                "floor_mm": FLOOR_MM, "floor_depth": FLOOR_DEPTH,
                "cell_size_at_floor_mm": round(size_mm(FLOOR_DEPTH), 3),
                "pulses": {k: {kk: vv for kk, vv in v.items() if kk != "hops"} | {"hops": len(v.get("hops", []))} for k, v in self.st["pulses"].items()},
                "last_hops": self.st["last_hops"][-6:],
                "stats": self.st.get("stats", {}), "last_error": self.st.get("last_error")}

# ---------- module-level singleton (used by the portal) ----------
_ENGINE = None
def engine():
    global _ENGINE
    if _ENGINE is None: _ENGINE = PulseEngine()
    return _ENGINE

def default_seeds():
    st = engine().st
    if not st["pulses"]:
        for pid, o, r in (("P-ssj", "V(4,2,4)", 3), ("P-portal", "V(1,2,3)", 3), ("P-neurons", "V(6,2,3)", 3)):
            st["pulses"][pid] = {"origin": o, "radius": r, "ring": 0, "done": False, "hops": []}
        engine().save()

def main(argv):
    e = engine(); cmd = argv[1] if len(argv) > 1 else "status"
    if cmd == "status": print(json.dumps(e.status(), indent=1))
    elif cmd == "tick":
        default_seeds()
        for _ in range(int(argv[2]) if len(argv) > 2 else 1): e.tick()
        e.save(); print("tick", e.st["tick"], json.dumps(e.status()["stats"]))
    elif cmd == "seed":
        a = dict(zip(["--id", "--origin", "--radius"], argv[2:]))
        e.seed(a["--id"], a["--origin"], a.get("--radius", 3)); print("seeded", a)
    elif cmd == "jump":
        db = e.db; p = _parse(argv[2])
        n = db["cells"].get(p[0]) if p else None
        if not n: raise SystemExit("no such cell " + argv[2])
        n["jump"] = argv[3]; save_db(db); print("jump", argv[2], "->", argv[3])
    elif cmd == "code":
        db = e.db; p = _parse(argv[2])
        n = db["cells"].get(p[0]) if p else None
        if not n: raise SystemExit("no such cell " + argv[2])
        n["code"] = argv[3]
        if "--run" in argv: n["run"] = True
        save_db(db); print("code", argv[2], "->", argv[3], "run=%s" % n.get("run"))
    elif cmd == "verify":
        fixed = 0
        def walk(n, addr):
            nonlocal fixed
            b = bounds_of(addr)
            if b and n.get("bounds") != b: n["bounds"] = b; fixed += 1
            for k, ch in (n.get("sub") or {}).items(): walk(ch, addr + "/" + "/".join(k.split(",")))
        for base, n in db_items(e.db): walk(n, _vstr(base))
        save_db(e.db); print("verified, fixed", fixed)
    elif cmd == "start": default_seeds(); print(e.start())
    else: raise SystemExit(__doc__)

def db_items(db): return db["cells"].items()

if __name__ == "__main__": main(sys.argv)
