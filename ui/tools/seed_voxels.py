"""Seed the voxel registry with the mind-room's known anchors (2026-11-26).

Each seeded cell points at real code in the memory tree; refs are encoded to
M-CODEs where possible so the 3D world and the leaf memory system share one
address space. Idempotent: re-running refreshes labels/refs, keeps sub-cells.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "memory", "archivist"))
import voxel  # noqa: E402

db = voxel.load()

# (addr, label, kind, ref, rigid)
SEEDS = [
    ("V(4,2,4)",   "The Reach - you",        "rigid", "agent_portal.py",            "ssj"),
    ("V(6,2,3)",   "Neuron field",           "rigid", "memory/llm/hosts.md",        "neurons"),
    ("V(7,2,7)",   "Host pillar A",          "rigid", "memory/llm/instances.md",    "pillar"),
    ("V(0,2,0)",   "Host pillar B",          "rigid", "memory/llm/hosts.md",        "pillar"),
    ("V(1,2,5)",   "The coin - dcabots",     "rigid", "MEMORY.md",                  "coin"),
    ("V(6,2,6)",   "Evolution column",       "rigid", "ui/pages/evolve.html",       "helix"),
    ("V(4,0,4)",   "Ground-truth floor",     "leaf",  "llm_selector.py",            None),
    ("V(2,1,4)",   "The room you built us",  "leaf",  "ui/pages/mind.html",         None),
]

made = 0
for addr, label, kind, ref, rigid in SEEDS:
    n = voxel.set_node(db, addr, label=label, kind=kind, ref=ref,
                       rigid=rigid if rigid else None)
    made += 1

# drill one level into the two richest cells
for a in ("V(4,2,4)", "V(6,2,3)"):
    voxel.subdivide(db, a)

# sub-voxel anchors (octant coords are local: x,y,z each 0|1)
SUBS = [
    ("V(4,2,4)/0/1/1", "mind - the orchestrator", "leaf", "memory/orchestrator/convergence_api.py", None),
    ("V(4,2,4)/1/1/1", "fist - pointing at you",  "space", None, None),
    ("V(6,2,3)/1/1/0", "portal ring - the door",  "leaf", "agent_portal.py", None),
    ("V(6,2,3)/0/0/1", "fleet spine - llm fleet", "leaf", "memory/llm/hosts.md", None),
]
for addr, label, kind, ref, rigid in SUBS:
    voxel.set_node(db, addr, label=label, kind=kind,
                   ref=ref if ref else None, rigid=rigid if rigid else None)

print(f"seeded {made} level-0 + {len(SUBS)} sub cells; db -> {voxel.DB}")
for a in ("V(4,2,4)/0/1/1",):
    r = voxel.resolve_payload(a)
    print("check", a, "found=", r.get("found"),
          [c.get("resolved", {}).get("mcode") or c.get("resolved", {}).get("error") for c in r.get("chain", [])])
