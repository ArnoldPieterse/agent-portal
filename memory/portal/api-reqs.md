# Portal API request queue - agent file/terminal API (2026-11-25)

Every agent can operate on ANY file the portal lists (the /api/manifest walk of the workspace +
Studio sandbox) plus run terminal commands, via **[[PORTAL-API]] blocks in its chat replies**.
The portal executes them when the turn ends. This is the full reference for the compact block in
the system prompt - read it with your python/terminal tools if you need exact semantics.

## How to call

Emit a fenced block in your reply, ONE JSON object per line:

    [[PORTAL-API]]
    {"call":"requestChange","args":{"file":"agent_portal.py","range":[34,502],"linesToReplace":["new line one","new line two"],"note":"why"}}
    {"call":"viewRequestQueue"}
    [[/PORTAL-API]]

- Max 5 calls per reply. The block is stripped from the displayed/stored message.
- Outcomes arrive on your NEXT turn as a `PORTAL API RESULTS` section (do not re-submit).
- Queued calls return `{ok:true, id:"R0042", queued:true}` - report the reqID to the group/human.

## Calls

Queued (pending until approved by the human in the Requests panel, or a configured approver):
| call | args | effect on approval |
|---|---|---|
| `requestChange` | `file`, `range:[a,b]` 1-based inclusive, `linesToReplace:[...]`, `note?` | splices linesToReplace over lines a..b (a==b==n+1 = append at end) |
| `reqCreateFile` | `file`, `content`, `note?` | writes new file (fails if it exists - use requestChange) |
| `reqDeleteFile` | `file`, `note?` | deletes the file |
| `runCMD` / `runTerminalReq` | `command`, `note?` | runs in the workspace via cmd, 120s timeout, output capped 8KB |

Sync reads (no queue, result straight back):
| call | args | returns |
|---|---|---|
| `reqReadFile` | `file`, `range?` | numbered lines `   34| ...`, 16KB cap - ALWAYS read before crafting a change |
| `listPortalFiles` | - | newest 300 files the portal lists (path + mtime) |
| `viewRequestQueue` | - | pending file requests (id, agent, file, range, note) |
| `viewTerminalQueue` | - | pending terminal requests |
| `getReqInfo` | `reqID` | full record (bodies replaced by lineCount/contentChars) |
| `editReq` | `reqID`, any of `range/linesToReplace/content/note/command/file` | edit YOUR pending request before approval |
| `cancelReq` | `reqID` | withdraw YOUR pending request |
| `getReqHistory` | `n` or `[a..b]` | processed requests, oldest first (default last 30) |
| `viewTerminalOutput` | `reqID` | stdout/stderr/rc of an executed command |
| `getQueueStats` | - | counts by status/kind |

Approver-only (agent must be listed in `memory/ops/api-reqs-config.json` -> `approvers`; humans always can via the UI):
| call | args |
|---|---|
| `approveReq` | `reqID` - applies it now |
| `rejectReq` | `reqID`, `reason?` |

## Rules of the road
1. `reqReadFile` FIRST - ranges must match CURRENT lines; stale ranges fail at apply time.
2. One concern per request; put the WHY in `note` (the human approves from it).
3. Never re-submit a queued call; check `viewRequestQueue` / your PORTAL API RESULTS first.
4. Pinned files (index.html, see memory_mirror.py PIN_FILES) get REVERTED by the mirror -
   changing them through this queue is pointless unless you advance the pin in the same cycle.
5. Terminal commands run on the portal host with full user rights once approved - keep them
   read-only or idempotent; destructive work goes in a file request instead where possible.

## State + REST (for humans / tooling)
- Store: `memory/ops/api-reqs.json` · audit: `memory/ops/api-reqs.jsonl` (append-only events)
- Config: `memory/ops/api-reqs-config.json` `{"approvers":["Verifier"]}`
- GET `/api/reqs?kind=&status=&limit=` · GET `/api/reqs?history=1&limit=N`
- POST `/api/reqs/approve {id,by?}` · POST `/api/reqs/reject {id,reason?,by?}`
- POST `/api/reqs {call,args,agent:"human"}` - humans can queue too (the UI form uses this)

