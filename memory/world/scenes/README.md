# Director scenes as fleet artifacts (Phase 8 step 61, 2026-11-27)
<!-- parent: memory/world/INDEX.md (Z9) | owner: Archivist -->
An agent-authored annotation scene = a saved slice of the shared GEV canvas: the target area,
the findings dropped on it (with share links), and who made it. One example scene per active
goal cycle is the target.

## Format (one JSON file per scene, `scenes/<scene_id>.json`)
```
{
 "scene": "20261127-143000",
 "created": "<ts>",
 "by": "<agent or user>",
 "annotations": [ {"ts","by","target":{"lat","lon","radius_km"}|{"place"},"note","share_url"} ],
 "open_in_gev": "<share-url> | manual fallback note"
}
```

## How they get made
`POST /api/gev {op:"annotate", target:{...}, note:"...", by:"...", save_scene:true, scene_id?}`
- appends the finding to `../annotations.jsonl` (the running log), AND
- writes/updates this scene bundle when `save_scene` is true.

## How the user opens one
Open the `open_in_gev` share link in a browser (it restores camera + tracked target on the local
globe at http://localhost:4173). If no share URL was captured, fly to the annotation's target
manually. Scenes are plain JSON, so agents can also read them back as evidence without the globe.
