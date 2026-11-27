# GEV security & privacy posture (Phase 8 step 63, 2026-11-27)
<!-- parent: memory/ops/INDEX.md | owner: Verifier + Mechanic -->
Reviewed 2026-11-27 at bring-up. Re-run this review after any GEV upgrade or key addition (see Z8).

## Posture
1. **Loopback-only.** The globe binds `[::1]:4173` / 127.0.0.1 on White; nothing is published to the
   network. Verified at install (`npm run doctor` + live probe); the PortalGEV watchdog restarts it
   with the same binding.
2. **Keyless.** No API keys configured (Esri/OSM/open feeds only) - see memory/world/key-strategy.md (Z8).
3. **No user-location leakage.** All feed queries use coordinates we choose ourselves in
   memory/world/config.json (currently null = no location queries at all). The snapshot job never
   derives a location from user activity, and nothing in the mirror carries device identifiers.
4. **SDR off.** No SDR hardware attached; the layer stays disabled (key-strategy.md keeps it off).
5. **Bundle server scope.** bundle_host.py (:8199 on each host) is read-only over that host's own
   mirrored project copy - no new exposure beyond what the SMB mirror already grants fleet members.
   Paths are root-anchored, dotfiles rejected, reads byte-capped; every request is audited in
   memory/ops/data-requests.jsonl.
6. **Portal stays loopback.** :8099 remains 127.0.0.1-only on White; the LAN-reachable surface is
   only each host's :8199 bundle server (read-only) and Studio :8888 (pre-existing, keyed).

## Residual risks (accepted)
- :8199 has no auth: anyone on the LAN can read the mirrored project state. That equals existing
  SMB C$ access for fleet accounts; if the network perimeter ever widens beyond the home LAN,
  add a bearer token to bundle_host.py before it goes further.
- GEV's public-camera + military-awareness tools exist in the MCP surface; agents are instructed
  (persona note, step 56) to use only the curated query kinds. The full op=call escape hatch stays
  available for explicit human-directed work.
