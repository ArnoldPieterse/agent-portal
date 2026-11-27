# GEV key strategy (Phase 8 step 62, 2026-11-27)
<!-- parent: memory/world/INDEX.md (Z8) | owner: Mechanic -->
**Posture: KEYLESS.** The globe runs on bundled/open feeds only - Esri imagery + OSM fallback base
maps, OpenSky anonymous flights, AIS ships, USGS quakes, NASA FIRMS fires, Launch Library 2,
NOAA cyclones/weather. No API keys configured anywhere in C:\Projects\gods-eye-view.

## If photorealistic Cesium ion terrain is wanted later
1. Add the token via GEV's own POWER UP panel (in-app; it writes .env locally on White).
2. BEFORE adding: document quota/cost - Cesium ion has free-tier limits on terrain + imagery
   asset requests; a 24/7 local globe polling terrain tiles can burn through a free tier.
3. Keep the key OUT of this repo and out of the SMB mirror (it lives only in GEV's .env,
   which is not mirrored - verify that stays true after any GEV upgrade).
4. Re-run the step-63 security review with the new asset in scope.

## What stays off regardless
SDR layer (no hardware attached), public-camera snapshots beyond what agents explicitly request,
military-awareness panel (out of scope for a personal fleet; data exists but we do not surface it).
