"""mindroom_models.py - build detailed GLB assets for the mind room (Blender 5.3 headless).

Outputs:
  ui/assets/models/ssj.glb      high-detail Super Saiyan (floating, right arm to neurons)
  ui/assets/models/neurons.glb  neuron cluster: cell bodies + tapered dendrites + hub branches

Layout matches mind.html local coords: ssj group at (0,3,0), feet ~y=-1, hair top ~y=+3.8.
Run: blender --background --python ui/tools/mindroom_models.py
"""
import math, os
import bpy
from mathutils import Vector

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "models")
os.makedirs(OUT, exist_ok=True)

# same seeded rng as mind.html so neuron layout matches the old point cloud
def sr(i):
    x = math.sin(i * 127.1 + 311.7) * 43758.5453
    return x - int(x)

bpy.ops.wm.read_factory_settings(use_empty=True)

def new_mat(name, color, emissive=(0, 0, 0), ei=0.0, rough=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Emission Color"].default_value = (*emissive, 1)
    b.inputs["Emission Strength"].default_value = ei
    b.inputs["Roughness"].default_value = rough
    return m

def mesh(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj

def sphere(loc, r, mat, seg=24, ring=16, scale=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=ring, radius=r, location=loc)
    o = bpy.context.active_object
    if scale:
        o.scale = scale
    mesh(o, mat)
    return o

def cone_between(a, b, r1, r2, mat, seg=10):
    a, b = Vector(a), Vector(b)
    d = b - a
    L = d.length
    bpy.ops.mesh.primitive_cone_add(vertices=seg, radius1=r1, radius2=r2, depth=L, location=(a + b) / 2)
    o = bpy.context.active_object
    o.rotation_mode = "QUATERNION"
    o.rotation_quaternion = d.to_track_quat("Z", "Y")
    mesh(o, mat)
    return o

def torus(loc, R, r, mat, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(location=loc, major_radius=R, minor_radius=r, major_segments=32, minor_segments=10)
    o = bpy.context.active_object
    o.rotation_euler = rot
    mesh(o, mat)
    return o

def export_sel(path):
    # caller pre-selects; do NOT deselect here
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_apply=True)
    print("WROTE", path, os.path.getsize(path))

# ===================================================================== SSJ
mats = {
    "gold": new_mat("hairGold", (1.0, 0.78, 0.15), emissive=(1.0, 0.62, 0.0), ei=0.55, rough=0.3),
    "suit": new_mat("suitDark", (0.09, 0.12, 0.24), emissive=(0.04, 0.06, 0.18), ei=0.5, rough=0.5),
    "skin": new_mat("skin", (0.92, 0.76, 0.60), rough=0.6),
    "eye":  new_mat("eye", (0.05, 0.10, 0.30), emissive=(0.2, 0.4, 1.0), ei=0.8, rough=0.2),
}
sel = []

head = sphere((0, 2.35, 0), 0.52, mats["skin"]); sel.append(head)
sel.append(sphere((0.40, 2.42, 0.17), 0.055, mats["eye"], seg=12, ring=8))   # eyes face +x
sel.append(sphere((0.40, 2.42, -0.17), 0.055, mats["eye"], seg=12, ring=8))
sel.append(sphere((0.46, 2.18, 0), 0.09, mats["skin"], scale=(0.6, 1, 1)))    # jaw hint
sel.append(cone_between((0, 2.05, 0), (0, 1.75, 0), 0.16, 0.14, mats["skin"]))  # neck

torso = sphere((0, 1.15, 0), 0.5, mats["suit"], scale=(0.95, 1.35, 0.8)); sel.append(torso)
sel.append(sphere((0.12, 1.45, 0), 0.34, mats["suit"], scale=(0.7, 1.0, 0.9)))  # chest plate
sel.append(torus((0, 0.62, 0), 0.34, 0.05, mats["gold"]))                       # belt

# hair: 16 two-stage spikes (base + bent tip)
for i in range(16):
    a = i / 16 * math.tau
    bx, bz = math.cos(a) * 0.34, math.sin(a) * 0.34
    by = 2.72 + sr(i + 80) * 0.18
    # outward-up direction from scalp center (0,2.55,0)
    d = Vector((bx, by + 0.35, bz)) - Vector((0, 2.55, 0))
    h1 = 0.55 + sr(i) * 0.45
    p1 = Vector((bx, by, bz))
    p2 = p1 + d.normalized() * h1
    sel.append(cone_between(p1, p2, 0.16, 0.07, mats["gold"], seg=8))
    # tip: continue with slight outward kick
    k = (Vector((math.cos(a), 0, math.sin(a))) * 0.5 + d.normalized()).normalized()
    h2 = 0.35 + sr(i + 7) * 0.5
    sel.append(cone_between(p2, p2 + k * h2, 0.06, 0.008, mats["gold"], seg=8))

# shoulders + arms (right arm extended toward neurons at +x)
def limb(a, b, r1, r2, mat):
    sel.append(cone_between(a, b, r1, r2, mat, seg=12))

shL, shR = (-0.58, 1.75, 0), (0.58, 1.75, 0)
sel.append(sphere(shL, 0.24, mats["suit"], scale=(1, 1.1, 1)))
sel.append(sphere(shR, 0.24, mats["suit"], scale=(1, 1.1, 1)))
# left arm relaxed
limb(shL, (-1.15, 1.15, 0.30), 0.17, 0.14, mats["suit"])
sel.append(sphere((-1.15, 1.15, 0.30), 0.15, mats["skin"]))
limb((-1.15, 1.15, 0.30), (-1.30, 0.45, 0.42), 0.13, 0.11, mats["suit"])
sel.append(sphere((-1.30, 0.45, 0.42), 0.16, mats["skin"]))
# right arm -> neurons (matches mind.html handR local 2.7,2.05,-.55)
elb = (1.55, 1.95, -0.30)
limb(shR, elb, 0.17, 0.14, mats["suit"])
sel.append(sphere(elb, 0.15, mats["skin"]))
limb(elb, (2.62, 2.05, -0.52), 0.13, 0.10, mats["suit"])
fist = sphere((2.72, 2.05, -0.55), 0.17, mats["skin"]); fist.scale = (1.25, 0.9, 0.9); sel.append(fist)

# legs, floating bent pose
hipL, hipR = (-0.28, 0.45, 0), (0.28, 0.45, 0)
sel.append(sphere(hipL, 0.22, mats["suit"]))
sel.append(sphere(hipR, 0.22, mats["suit"]))
kneeL, kneeR = (-0.52, -0.15, 0.28), (0.46, -0.10, -0.34)
limb(hipL, kneeL, 0.19, 0.16, mats["suit"])
sel.append(sphere(kneeL, 0.17, mats["skin"]))
limb(kneeL, (-0.62, -0.95, 0.42), 0.15, 0.12, mats["suit"])
sel.append(sphere((-0.68, -1.02, 0.48), 0.17, mats["gold"]))   # boots
limb(hipR, kneeR, 0.19, 0.16, mats["suit"])
sel.append(sphere(kneeR, 0.17, mats["skin"]))
limb(kneeR, (0.58, -0.88, -0.42), 0.15, 0.12, mats["suit"])
sel.append(sphere((0.64, -0.95, -0.47), 0.17, mats["gold"]))

for o in sel:
    o.select_set(True)
bpy.context.view_layer.objects.active = sel[0]
export_sel(os.path.join(OUT, "ssj.glb"))

# =================================================================== NEURONS
# clear scene
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
cell_m = new_mat("cellCyan", (0.75, 0.93, 1.0), emissive=(0.22, 0.74, 0.97), ei=1.1, rough=0.25)
ax_m   = new_mat("dendriteTeal", (0.16, 0.48, 0.64), emissive=(0.08, 0.36, 0.55), ei=0.7, rough=0.4)

blobs = [Vector(((sr(i + 200) - .5) * 2.6, (sr(i + 210) - .5) * 1.8, (sr(i + 220) - .5) * 2.6)) for i in range(4)]
N = 48
cells = []
for i in range(N):
    b = blobs[i % 4]
    p = Vector((b.x + (sr(i + 300) - .5) * 1.7, b.y + (sr(i + 310) - .5) * 1.5, b.z + (sr(i + 320) - .5) * 1.7))
    r = 0.05 + sr(i + 400) * 0.11
    cells.append((p, r))
sel = []
for p, r in cells:
    sel.append(sphere(p, r, cell_m, seg=20, ring=14))
# dendrites between near pairs
links = 0
for a in range(N):
    for b in range(a + 1, N):
        if links > 90:
            break
        pa, ra = cells[a]; pb, rb = cells[b]
        d = (pa - pb).length
        if d < 0.72 and d > ra + rb * 0.4:
            sel.append(cone_between(pa, pb, 0.016, 0.008, ax_m, seg=6))
            links += 1
# hub branches: 3 short cones on the 8 biggest cells
big = sorted(range(N), key=lambda i: -cells[i][1])[:8]
for i in big:
    p, r = cells[i]
    for k in range(3):
        a2 = sr(i * 3 + k) * math.tau
        d = Vector((math.cos(a2), sr(i * 3 + k + 9) - .5, math.sin(a2))).normalized()
        sel.append(cone_between(p + d * r * 0.8, p + d * (r + 0.28 + sr(i + k) * 0.15), 0.02, 0.006, ax_m, seg=6))

for o in sel:
    o.select_set(True)
bpy.context.view_layer.objects.active = sel[0]
export_sel(os.path.join(OUT, "neurons.glb"))
print("DONE")
