# Portal - file-link layer (agent-built files -> clickable chips)
Last updated: 2026-11-12 (written + reviewed by maintainer chat; supersedes the "Archivist draft" note).

ONE-SENTENCE SPEC: path-like tokens in an agent's FINAL reply that resolve inside the workspace become clickable `.flink` chips — hover peeks the first lines, click opens the file with its real MIME type.

## Provenance (read before trusting)
The 6-agent roster converged on this feature during the 2026-11-11 group e2e. Archivist announced "Drafted and written: memory/portal/file-links.md" in cross-talk round 2 — **the file never existed** (checked project root, Studio sandbox, AgentPortal_V1; no tool trace in portal logs). Lesson: an agent's "I wrote X" claim is a CLAIM; verify on disk before recording it as done. This leaf was written and code-verified by the maintainer chat instead.

## Backend contract (agent_portal.py)
- `_safe_workspace_file(rel)` (line ~527): dual-root resolver — tries `HERE` (project root) then `SANDBOX_DIR` (Studio sandbox `_default`, found via `_find_sandbox_dir()`). Traversal-safe: realpath must stay under a base; files AND folders resolve (folder refs get a listing peek).
- `GET /api/file?path=<rel>`: existence probe + hover peek. 200 = {path (echoes the REQUESTED rel path — frontend string-matches it exactly), name, size, head (first 40 lines / 8 KB), binary flag}; folder -> `<folder> ... (N entries)` listing; 404 otherwise. Frontend probes every candidate; only 200s become links.
- `GET /api/file/raw?path=<rel>`: click target, opens in new tab. Serves the REAL Content-Type via `mimetypes.guess_type` (.html renders as a website, not source; unknown -> text/plain). >32 MB -> 413. Folder click -> plain-text listing.
- Why dual-root: agent tools execute in the Studio sandbox, so their files land there, not in HERE; the old ~-based SANDBOX_DIR broke when the portal inherited a different USERPROFILE (see bugs/file-links-sandbox.md).

## Frontend contract (index.html `linkifyFiles`, line ~367)
- Runs on FINAL bubbles only. File tokens: `/[\w./\\-]+\.[A-Za-z0-9]{1,8}/g` (must end in an extension); folder tokens: `(?:[\w-]+\/)+` (trailing slash). Max 12 candidates; URLs/www and space-containing tokens skipped.
- Candidates are probed via /api/file in parallel; longest-match-wins replaces exact strings with `.flink` anchors (`/api/file/raw?path=...`, target=_blank noopener). If the bubble text changed meanwhile, the pass is skipped.
- RENDER-TIME PATH RULE (the rule agents must follow): only RELATIVE paths from the agent's working directory can ever link. Absolute/drive-letter paths (C:\..., /Users/...) are 404 by construction — so an agent that reports a file by absolute path gets NO chip and must restate the relative path.

## Known limits (no action queued)
- HTML pages referencing RELATIVE assets (css/js/img) still 404 those assets via /api/file/raw — single-file apps are fine; multi-file apps need a virtual directory or `<base>` injection later.
- Linkification is per-bubble text matching; a path split across stream chunks is fine (runs after final), but a path with spaces never links.
