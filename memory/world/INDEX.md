# world/ - real-world data layer (M-CODE Z, 2026-11-27)
<!-- parent: memory/INDEX.md | owner: Archivist + Mechanic (snapshot job) | feeds: mind-lab planet cards, host-risk alerts -->
God's Eye View integration state. The globe itself runs on White only (localhost:4173, keyless);
everything here is the data that flows HOME from it and gets mirrored to all hosts.
- -> config.json  user/host location config (null = no location queries; step 63 posture)
- -> gev_snapshot.py  30-min snapshot job (portal _world_watchdog thread): quakes M>4, cyclones, launches, local brief
- -> snapshots.jsonl  one JSON line per 30-min world pass (ts, quakes, cyclones, launches, new_events)
- -> events.jsonl  threshold events (quake M>5 / cyclone / notable launch) - feeds mind-lab planet cards via /api/mind-lab op=planet
- -> annotations.jsonl  agent findings on the shared canvas (POST /api/gev op=annotate), with GEV share links
- -> host-risk.json  last host-risk check result (active alerts; step 58)
- -> planet-acked.json  mind-lab accept/reject ledger for planet events
- -> key-strategy.md  keyless posture + Cesium ion opt-in decision record (step 62)
- -> scenes/README.md  Director annotation scenes as fleet artifacts (step 61)
