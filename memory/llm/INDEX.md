# LLM INDEX — index of indexes for LLM instances & routing.
Last updated: 2026-11-11. Ground truth = nvidia-smi per-GPU VRAM, never /v1/models alone.

## Entries (keyword -> pointer | use case)
- dual residency / Q4 GPU0 / Q8 GPU1 / aliases atlas-q8|quinn-q4 / engine update kills instances / wedge / thread rebind / memory fit -> memory/llm/instances.md   current layout + durable rules
- Studio API :8888 / load recipe / reload order / recover_all / :3008 dead / stale scripts -> memory/llm/studio-api.md   endpoint map + proven reload recipe (Q8 first)
- serialization / parallel_slots=1 / why rounds never overlap -> memory/portal/architecture.md §serialization   probe verdict + what a fix would require
- remote hosts / Red / Pale / Black / multi-host / 6 more agents / 192.168.1.245 / API key / 401 / per-host routing -> memory/llm/hosts.md   host table + Red recon facts + durable rules
- overnight unload / remotes unloaded / idle TTL / auto-evict / jitModelTTL / why models gone in morning -> memory/llm/overnight-unload.md   hypothesis ranking H1-H4 + pending live checks (opened 11-13, analysis done, confirmation pending)

## Global pointers
- -> agents.json   model_id alias per agent;  -> MEMORY.md hot state;  -> TODO.md plan
