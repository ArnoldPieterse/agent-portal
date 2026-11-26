# Gaussian Splatting for Object Detection from Video + 3D Scan Data
Researcher investigation - 2026-11-26 (user request: "integrate gaussian splatting for object
detection from videos and 3d scanning data investigations")

## TL;DR recommendation
Video/scan -> camera poses (COLMAP or MASt3R) -> train 3D Gaussian Splatting with **gsplat**
(nerfstudio Splatfacto pipeline) -> detect/segment objects ON the splat with a zero-shot
foundation-model method (**Splat Analyzer**-class) or point-cloud-guided segmentation
(**PointGauss**) when scan data is available -> export per-object bounding boxes + splat
clusters -> register each detected object in the voxel registry as `kind: splat` anchored
to its V(x,y,z)/octant address (see memory/archivist/splats.json manifest).

## What 3D Gaussian Splatting gives us (vs NeRF)
- Explicit per-primitive representation: each "Gaussian" carries position, covariance,
  opacity, color/SH coefficients. That makes it a *data structure we can query* -
  grouping, clustering and bounding-boxing individual objects is trivial compared to NeRF's
  implicit MLP (no object identity inside the network).
- Real-time rasterization (CPU/GPU) once trained; .ply/.splat files are portable.
- Trained from ordinary video frames + estimated camera poses - no structured scan needed,
  but LiDAR/photogrammetry scans improve geometry (PointGauss fuses both).

## State of the art for object detection on splats (2025-2026)
1. **Splat Analyzer** (2026) - zero-shot 3D object identification + localization inside
   Gaussian Splat scenes; targets XR / digital twins. No per-scene training: a foundation
   model reasons over the splat -> object boxes/labels directly.
2. **arXiv 2510.23521 - Explicit Memory through Online 3DGS** (Oct 2025) - online 3DGS that
   stores predicted *object-level segments* accumulated over a video; class-aware
   segmentation improves as the video plays. Closest match to "detection from videos".
3. **PointGauss** - point-cloud-guided multi-object segmentation on splats: uses 3D scan
   points to constrain/initialize Gaussian groups -> better object boundaries when a scan
   of the same scene exists (our case: mind-room objects have GLB + voxel anchors).
4. **LabelGS** - label-aware 3DGS for scene segmentation (semantic labels baked into
   training); good when classes are known in advance.
5. **FMGS** - foundation-model-embedded splatting for holistic 3D understanding.
6. **GaussianDet3D** - bridges splats + sparse LiDAR for autonomous-driving detection;
   relevant pattern: fuse cheap geometric scans with learned appearance.

## Tooling (practical)
- **gsplat** (isl-org, `pip install gsplat`) - CUDA rasterizer/library; ~4x less training
  memory than the official 3DGS implementation, ~15% faster convergence. This is the
  backend nerfstudio uses.
- **nerfstudio + Splatfacto** - turnkey video->splat: COLMAP (or MASt3R for sparse/texture-poor
  captures) estimates poses, then trains the splat. CLI-driven, scriptable.
- **SplaTAM** - SLAM variant that emits a splat directly from handheld/robot video
  (no separate pose step) when you don't have COLMAP-quality overlap.
- Hardware: gsplat needs an NVIDIA CUDA GPU for training (inference/rasterization also runs
  on CPU but slowly). Fleet check: BLACK/PALE/RED are LLM hosts (LM Studio/Ollama) -
  whichever exposes a CUDA device can host splat training; otherwise the local White box
  (Blender 5.3 present) if it has an NVIDIA GPU.

## Integration with the Agent Portal voxel system (DONE in this commit)
The 3D world referencing system gets a new object kind:
- `voxel.py set V(x,y,z)/... --kind splat --ref <path/to/object.ply> [--label ...]`
  - a splat-anchored object resolves through the same memory chain as GLB rigid bodies;
  - its bounding box (from detection) is stored in the node's `bounds`, so the ray view
    and mind-room layer render it like any other voxel content.
- **memory/archivist/splats.json** - manifest of splat assets:
  {id, source(video|scan), frames, poses(colmap|mast3r|slamtam), trained_by(host),
   file(.ply/.splat), gaussians(count), objects:[{label, box[6], voxel_addr}]}
- Pipeline (documented for the builder/mechanic to automate on a CUDA host):
  1. ingest video/scan -> extract frames (+LiDAR points if available)
  2. COLMAP/MASt3R camera poses (SplaTAM if handheld, no overlap)
  3. `ns-tracker`/gsplat Splatfacto train -> scene.ply
  4. object pass: Splat Analyzer zero-shot boxes, or PointGauss segmentation when scan
     points exist; optionally LabelGS for known fleet-object classes
  5. export per-object cluster .ply + box6 -> register via voxel.py (kind=splat) and
     append to splats.json manifest
- Render path: voxray.html / mind-room layer already render any content voxel; splat objects
  appear as their bounding cell + drill chain immediately. Full per-Gaussian rendering of a
  .ply is a later upgrade (three.js GS viewer or Blender for offline bakes).

## Risks / open questions
- No confirmed CUDA host in the fleet yet - training box must be identified first.
- Zero-shot detection quality on cluttered indoor scenes untested here; budget one
  validation run on a mind-room capture before relying on it for auto-anchoring.
- Splat file sizes (10-100MB per scene) - keep in memory/archivist/splats/, gitignore the
  binaries, commit only the manifest.
