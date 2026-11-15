# Agent Portal

A local multi-agent group-chat portal backed by the [Unsloth Studio](https://unsloth.ai) desktop harness. Multiple AI agents converse with you and with each other — and **each agent is served by its own LLM instance**, not a persona mask over one shared model. The portal itself loads nothing: it is a thin web UI + proxy in front of Unsloth Studio, so every agent gets the full desktop harness (reasoning, skills, RAG, tool execution).

Built and operated on a small local fleet of Windows machines ("White", "Red", "Black", "Pale"), each hosting one or more model instances.

## What's in this repo

| Path | What it is |
|---|---|
| `agent_portal.py` | The portal server: chat API, agent routing, file/folder uploads, DM redaction, workspace↔sandbox sync, git hooks. Single-file Python (stdlib + local LLM APIs). |
| `index.html` | The whole UI — one self-contained HTML page (chat threads, files panel, settings, fleet status). |
| `agents.json` | Agent roster: personas, model bindings, per-agent config. (API keys redacted in this copy.) |
| `memory/` | The agents' modular memory system: a pointer index (`memory/INDEX.md`) over per-role modules (orchestrator, builder, designer, mechanic, researcher, verifier, scribe, archivist, ops, llm, portal, synthesis…). This is the durable project state. |
| `MEMORY.md` | Hot file — newest-first working state for the host seat ("White"). Kept small on purpose. |
| `TODO.md` / `TODO_completed.md` | Live plan + completed work log. |
| `DESIGN.md` | Original design plan and vision. |
| `SETUP_HISTORY.md` | How the fleet got set up, step by step. |
| `docs_chat.md` | Reference copy of the Unsloth Studio chat docs the build was based on. |
| `memory_mirror.py`, `host_api.py`, `fleet_reload.py`, `recover_all.py/.bat`, `reboot_launchers.py`, `reboot_recover.py`, `smoke8.py`, `group_e2e.py`, `e2e_test.py`, `verify_e2e.py`, `red_chain.py`, `pale_dl.py`, `black_dual_load2.py`, `white_load_q8.py`, `portal_start.bat`, `fleet_reload.bat` | Fleet ops scripts: cross-host memory mirroring, host API probes, model load/reload, boot recovery, and end-to-end test suites. |

## How it runs (short version)

1. Each fleet machine runs Unsloth Studio with one or more local model instances (LM Studio / Ollama style backends).
2. `pythonw agent_portal.py` on the host seat serves the UI + API on a LAN port; every agent's messages are proxied to that agent's own model instance.
3. Agents work in parallel seats with their own memory modules under `memory/`; a mirror script keeps the shared state files (`TODO.md`, `MEMORY.md`, `memory/` leaves) in sync across hosts (last-writer-wins, size+md5 guarded).
4. A post-turn git hook auto-commits the curated file allowlist (see `.gitignore`) after every agent turn — that is where this repo's commit history comes from.

## Notes for anyone reading this publicly

- This is a snapshot of a working local system, uploaded as-is: the memory tree contains round logs, incident notes, and design decisions from real operation.
- All API keys / tokens in `agents.json` and the ops scripts are redacted. LAN hostnames/IPs appear in some notes; they are internal to the original network only.
- The portal is intentionally single-file + one HTML page; there is no build step. Python 3 stdlib is enough for the server.
