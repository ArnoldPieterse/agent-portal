# Portal bugs — file links & sandbox resolution
Last updated: 2026-11-11 (stale-process incident + live verification). Newest first.
## [DONE] MIME fix not live - schtasks /run no-op on a Running task (FIXED 2026-11-11)
Symptom: after the MIME fix + memory-tree edits (agent_portal.py last write 00:56), the RUNNING portal
(PID 23544, created 00:45 - BEFORE the edit) still served timer-app/index.html as text/plain; user
screenshot showed raw HTML source at /api/file/raw. The earlier "smoke green" had never been checked
against the live process's start time.
Root cause: `schtasks /run /tn PortalRun` reports SUCCESS but NO-OPS while the task Status is Running
(the portal runs indefinitely AS the task's own process, so the task is always Running). The old listener
kept :8099; no new instance ever started.
Fix/verify: taskkill the PID from _portal_pid.txt FIRST, then schtasks /run -> NEW PID 13184 (CreationDate
AFTER agent_portal.py LastWriteTime). Live smoke all green: timer-app/index.html + calculator-app/index.html
-> text/html; charset=utf-8 (RENDERED as website); model_list_now.json -> application/json; TODO.md ->
text/markdown; timer-app/ folder 200; traversal 404; missing 404; /api/memory 200. _portal_pid.txt updated.
Rule: after ANY agent_portal.py edit, prove the live process postdates the file (CreationDate vs
LastWriteTime) - a smoke that passed at some point proves nothing about the current listener.
Detail: memory/ops/windows-runbook.md §Portal lifecycle.
## [DONE] Raw links showed source - HTML not rendered, wrong file type (FIXED 2026-11-11)
Symptom: clicking a file link opened /api/file/raw?path=calculator.html and displayed the RAW
HTML SOURCE instead of rendering the page (user screenshot: squashed <style> text). Links resolved
fine (200) but "do not seem to render as a website or file type".
Root cause (agent_portal.py /api/file/raw): `if ctype is None or ctype.startswith("text/"): ctype =
text/plain` - the handler DELIBERATELY forced every text/* type to text/plain, so .html (text/html)
could never render. Same line flattened .md/.js/.css into plain text.
Fix: serve the REAL mimetypes.guess_type result; only unknown types fall back to text/plain;
text-family + application/json get "; charset=utf-8" appended. Now .html -> text/html (browser renders
the page), .json -> application/json, .md -> text/markdown, .js/.css keep their types.
Restart: schtasks /run /tn PortalRun. Smoke: /api/file/raw?path=calculator.html -> Content-Type
text/html; charset=utf-8; workspace TODO.md still 200 (text/plain fallback unchanged).
Known limit (noted, no action): HTML pages that reference RELATIVE assets (icons/, other .js) will
404 those assets via /api/file/raw - single-file apps (calculator.html) are unaffected. If needed
later: serve a virtual directory or inject <base href="/api/file/raw?path=<dir>/">.
## [DONE] Sandbox refs still 404 after dual-root fix; folder refs + link matching broken (FIXED 2026-11-11)
Symptom: with the dual-root resolver in place, workspace files (TODO.md) resolved but sandbox refs
(timer-app/index.html) still 404'd. Two more latent bugs found while fixing it: (a) /api/file echoed
relpath-from-HERE ('../../Users/...') so the frontend's exact-string match against reply text never hit ->
no link rendered even when the file resolved; (b) _safe_workspace_file accepted files only, so folder refs
(timer-app/) were rejected.
Root cause of (a)-adjacent 404s: SANDBOX_DIR = expanduser("~")/... - the portal instance I launched inherited
my tool shell's environment where USERPROFILE=C:\Projects\AgentPortal, so ~ resolved to a nonexistent dir. The
old instance worked only because it was launched from a session with USERPROFILE=C:\Users\<white> (schtasks
interactive). Env-dependent paths must not be assumed from the launcher shell.
Fix (agent_portal.py): _find_sandbox_dir() - if the ~-based dir is missing, scan C:\Users\*\.unsloth\studio\
sandbox\_default (found C:\Users\<white>\...); /api/file now echoes the REQUESTED rel path verbatim; new folder
branch in /api/file (directory-listing peek for hover popup) and /api/file/raw (plain-text listing on click);
_safe_workspace_file accepts files AND directories. Fix (index.html): linkifyFiles also collects folder tokens
via /(?<![\w./\\-])(?:[\w-]+\/)+/g - unit-tested against Quinn's actual bubble text (candidates: timer-app/,
timer-app/index.html, sandbox/timer-app/sw.js; URLs correctly excluded).
Restart: schtasks /run /tn PortalRun -> PID 23544 (killed direct-launch instance 24980 first). Smoke all green:
TODO.md 200 (workspace); timer-app/index.html 200 (sandbox, was 404); timer-app/ folder peek 200 (5 entries);
raw folder listing 200; raw sandbox file 200; traversal ..\\..\\Windows 404; missing 404. Unit test confirmed
SANDBOX_DIR resolves to the real sandbox even from the USERPROFILE=C:\Projects\AgentPortal shell.

## [DONE] Agent files landed in Studio sandbox, not workspace (FIXED 2026-11-11)
Symptom: user got a link to Quinn's calculator app that 404'd; the path "Z:\calculator-app\index.html" was a
hallucination (no Z: drive on this host - wmic verified). The real build (7,200 B, 11/11 00:02) sat in
C:\Users\<white>\.unsloth\studio\sandbox\_default\calculator-app\index.html next to Atlas's calculator.html and
the two news reports.
Mechanism: portal calls Studio /v1/chat/completions with local tool execution and passes NO session_id; per the
OpenAPI spec session_id "scopes the tool execution sandbox" -> every agent tool writes into the "_default"
sandbox, not the project workspace (HERE). Meanwhile /api/file + /api/file/raw were hard-guarded to HERE only,
and the frontend only linkifies path tokens the backend confirms exist -> every agent-reported path 404'd
silently; even a correct absolute sandbox path would have been rejected by the traversal guard.
Fix (agent_portal.py): (1) SANDBOX_DIR constant = ~/.unsloth/studio/sandbox/_default; (2) _safe_workspace_file()
now resolves against BOTH roots (workspace first, then sandbox), same no-traversal guard per root; (3) TOOLS
prompt block corrected: tools run in a shared agent folder, report created files by RELATIVE path exactly as
shown in tool results, never invent drive letters/absolute paths. Restart PID 10628 -> 24148. Smoke all green:
/api/memory 200; /api/file?path=calculator-app/index.html 200 (served from sandbox); /api/file/raw 200;
TODO.md still resolves from workspace root.
Self-correction loop (added same day): file-access instructions now live in SHARED memory so agents fix their
own links: FILE ACCESS block at the TOP of memory/INDEX.md - inside the first 1600 chars that _index_block()
injects into every group prompt (the old "Rules for agents with tools" section sat BELOW that cut and never
reached any agent) + self-correction clause in build_system_prompt TOOLS ("if you ever reported an absolute
path or a drive letter, it was wrong: restate it relative now") + MEMORY.md hot note.
Probe note: non-streaming /v1/chat/completions with enable_tools hung >300 s without creating a session sandbox
dir; the portal's streaming mode works fine -> keep stream: True in probes.

