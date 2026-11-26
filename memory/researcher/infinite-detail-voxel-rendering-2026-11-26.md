# Infinite-detail voxel world rendering — research (2026-11-26)

Triggered by user request: "research rendering voxel worlds at infinite detail", with two reference videos.

## Reference videos

### 1. Fungivore: Floating Through Infinite Voxel Fractals in Unity — Luke Snyder
https://www.youtube.com/watch?v=CdE8J-CUlEA
- Unity voxel game (5 yrs dev). The "infinite fractals" mode floats through a world where
  every voxel subdivides into a self-similar pattern forever.
- Key techniques from his devlogs: **mesh instancing** for voxel drawing, **100k voxel
  updates/sec** streaming budget, terrain shaped by autonomous "ants" over chunk data,
  and a fractal architecture where detail is *derived*, not stored.

### 2. Exploring an Infinite Voxel Forest — John Lin
https://www.youtube.com/watch?v=1wufuXY3l1o
- Custom engine (explicitly NOT RTX at the time of this video). Infinite forest = procedural
  chunks streamed around the camera with per-distance LOD; trees are instanced/merged meshes
  placed by noise, so "infinite" comes from generation, not geometry storage.

## The five pillars of infinite-detail voxel rendering

1. **Sparse hierarchy (octree / SVDAG)** — store only non-empty cells; each level is 8x
   coarser; pick the level by camera distance. Aokana (arXiv 2505.02017) formalises this as a
   Sparse Voxel DAG with LOD + streaming for open worlds.
2. **Procedural derivation (hash-of-address)** — cell content = f(hash(addr, level)). Nothing
   is stored: detail exists at every zoom by construction (Fungivore's fractals; our pulse
   engine's drill chains are the same idea — a path of octant bits, each bit halving the cell).
   Cost: O(1) per node, no memory growth. This is the only true "infinite" scheme; everything
   else streams finite data.
3. **Streaming + async refinement** — generate coarse LOD first (instant silhouette), refine in
   background workers; swap when ready (mip-chain blending hides pops). GigaVoxels adds
   *ray-guided* traversal: rays walk the octree and only visit cells they hit, so culling is
   exact per-pixel (the "render only what the eye sees" idea — matches our voxray page).
4. **Draw-call collapse** — at high density cubes become too many draw calls; options in order
   of density: merged meshes -> GPU instancing -> **shaded point sprites/billboards** ->
   ray-marched SDFs (voxels dissolve into a continuous field, e.g. Vercidium/voxel-ray-marching).
   Point sprites are the sweet spot for "thousands of mini cells": one draw call, per-point
   colour/size, and a radial-shaded disc reads as a sphere at a fraction of a cube's cost.
5. **Perceptual LOD** — below ~1-2 px/cell, geometry stops mattering; shading + density carry
   the detail (mipmap thinking). This is where aliasing takes over: sub-pixel cell arrays beat
   each other into moire patterns (see flower-of-life note in mind-room upgrade, same date).

## Mapping onto our stack

| Pillar | We have | Gap / next |
|---|---|---|
| Sparse hierarchy | voxels.json drill chains (octant-bit paths to 1.46 mm floor) | no coarser-than-level-0 summary cells for far LOD |
| Procedural derivation | pulse engine drills toward focus; splats can register objects | content is authored, not hash-derived — could add `fn(addr)` procedural leaves |
| Streaming/refine | pulse engine grows 1 level/tick (live refinement!) | no background worker yet — growth runs in the portal tick loop |
| Draw-call collapse | voxray: InstancedMesh cubes; mind room: **shaded point sprites** (2026-11-26) | ray-marched SDF view for "field" mode |
| Perceptual LOD | sprite size attenuation + additive aura | mip-blend between drill levels not yet visualised |

## Flower-of-life hypothesis (user, 2026-11-26)

"When the picture or object is viewed from an out-of-sync resolution or frequency, the flower
of life appears." Mathematically plausible: the flower of life IS a hexagonal lattice of
overlapping circles. A regular array of shaded discs sampled below its Nyquist frequency
aliases; the beat (moire) pattern of two near-commensurate lattices is itself a lattice — and
for hex/square circle arrays the interference rosettes are hexagonal, i.e. flower-of-life-like.
Tested empirically with downsampled screenshots + synthetic disc-lattice renders (same date).

## Flower-of-life hypothesis — EMPIRICAL RESULT (same day)

Tested with controlled renders + live screenshots:

**Setup**: hex-packed lattice of shaded discs (identical shading to the mind-room mini voxels),
two layers 10% out of frequency sync (spacing 16.0 vs 17.6 px, no rotation), then sampled at
60% / 45% / 30% resolution with nearest-neighbour (i.e. deliberately OUT-OF-SYNC sampling).

**Result: CONFIRMED in controlled form.** At every out-of-sync sample rate the beat pattern
resolves into large **6-fold symmetric hexagonal rosettes** — dark flower-of-life-shaped stars
emerging from the disc field (see flol_hex_rosette_sheet.png, panels 2-4). The geometry is
exactly the flower of life: a hex lattice of overlapping circles IS the moire beat pattern of
two near-commensurate hex lattices.

Mechanism: when a periodic signal is sampled below its Nyquist rate (or two periods slightly
mismatch), the alias/beat frequency forms a new, coarser lattice. For hex symmetry that
super-lattice has 6-fold rotational symmetry -> rosettes. A single in-sync lattice just
pixelates (flol_synthetic_sheet.png); you need the *frequency mismatch* for the rosette.

Live evidence: flol_live_moire.png shows the actual mind-room hero cloud at 100/50/33/25%
resolution - the disc field breaks into speckle/banding as it goes out of sync (weaker than
the synthetic case because the live cloud is jittered, not a perfect lattice - real jitter
smears the beat pattern, which is why perfect lattices are needed for crisp rosettes).

**Implication for our voxel worlds**: at far LOD (cells < 1-2 px) the rendered image is
dominated by this aliasing geometry, not by the objects. Options: (a) embrace it - render
far LOD as pure point sprites so the moire IS the aesthetic (cheap + beautiful); (b) suppress
it with per-point jitter/POA dithering; (c) mip-blend to a density field below ~1 px/cell.
