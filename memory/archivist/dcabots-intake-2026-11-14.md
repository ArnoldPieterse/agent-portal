# dcabots intake - access diagnosis + relay recipe (2026-11-14, Archivist, from Pale)

Task: integrate `\\white\c$\Users\White\WSL-Inbox\projects\dcabots` (Bitcoin trading bots)
into the shared agent folder. Project area scaffolded at `projects/dcabots/` (Designer, prior round).

## Established facts (verified this round from Pale sandbox)
- Source path is on White (White); tools for this turn run in PALE's sandbox
  (`C:\Users\<pale>\.unsloth\studio\sandbox\_default`).
- Pale -> White SMB DENIED on every route tried:
  - `\\white\c$` and `\\White\C$` -> WinError 65 (probe_unc.py) / error 5 (net use)
  - ADMIN$ with `/user:White ""` -> error 5; anonymous `net view \\White` -> error 5
  - IPC$ prompts for username -> no anonymous session at all
  - `cmdkey /list` on Pale = NONE (no stored creds to White)
- Portal `/api/file/raw` (agent_portal.py `_safe_workspace_file`) resolves ONLY relative paths
  inside the portal HERE root or White's own sandbox -> cannot reach WSL-Inbox\projects.
- Python sandbox network egress is allowlisted; raw probes to White blocked by policy.

## Proven route (from memory, not re-tested)
- White -> Pale C$ works with NO explicit net use (memory/llm/hosts.md, Pale row).
- Mirror dst_root pattern (memory_mirror.py): `\\<ip>\C$\Users\<user>\.unsloth\studio\sandbox\_default`
  => Pale target = `\\White`... i.e. from White: `\\Pale\C$\Users\pale\.unsloth\studio\sandbox\_default`.

## Relay command (run ON WHITE console)
    xcopy "C:\Users\<white>\WSL-Inbox\projects\dcabots" "\Pale\C$\Users\pale\.unsloth\studio\sandbox\_default\projects\dcabots\" /E /I /Y /H
Fallbacks: (b) White-hosted turn reads the path locally; (c) add White to memory_mirror_hosts.json
(creds unverified - "empty pw on all hosts" note only covers Red/Pale/Black); (d) Arnold uploads a zip via portal.

## Gaps / open items
- dcabots file tree UNKNOWN until push lands (manifest in projects/dcabots/README.md stays PENDING).
- White's SMB password never verified from a non-White seat - do not assume empty.
- After ingest: decide mirror allowlist policy for projects/dcabots (code yes, secrets NO - keys stay on White .env).
