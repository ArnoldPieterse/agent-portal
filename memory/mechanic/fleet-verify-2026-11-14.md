# Fleet verify from Red seat - 2026-11-14 03:10 (post 01:45 White rename)

Runbook note: White quant-folder rename + alias re-point (v2, 01:26) worked as designed at 01:45 - the only earlier break was v1's unload body using `{'id':...}` where the endpoint requires `model_path` (422 x11); fixed by unloading on full path first. No further action needed on White from this seat.

## Live probes 03:10:07 (probe_fleet_1114b.py -> ⚠missing:probe_fleet_1114b_result.json)
- BLACK .99 /v1/models 200 (Bearer): Qwen3.8-27B-Q4_K_S loaded ctx 65536 + Qwen3.8-27B-Q8_0 loaded ctx 32768; alias verifier-q4 -> UD-Q4_K_S loaded. DUAL-RESIDENT confirmed.
- PALE .39 /v1/models 200 (Bearer via pale_dl.py token - keyless LAN = 401, same as r20): Qwen3.8-27B-Q8_0 loaded ctx 32768 + Qwen3.8-27B-Q4_K_S loaded ctx 65536; aliases archivist-q8 + designer-q4 both loaded. DUAL-RESIDENT confirmed.
- WHITE .179: :8888 and :8099 both TIMEOUT from Red (matches lan_probe 02:46); SMB C$ with /user:white "" = error 5 access denied (no blank-pw SMB path Red->White, unlike White->seats). White ground truth from this seat = mirror copies only (TODO.md mtime 01:46:28 carries the RESOLVED 01:45 state; MEMORY.md fresh 03:04:46) + indirect proof the White portal is up: this very chat's turns route through it.

## Consequences for open NEXT items (TODO.md top section)
- smoke8 CANNOT run from Red seat: portal :8099 unreachable over LAN (firewall/binding asymmetry - White->Red works, Red->White times out). Needs White console (human leg) or a firewall rule. probe_fleet_1114b.py is the partial replacement already landed (Black+Pale verified live).
- hosts.md White line: ALREADY DONE by Researcher 11-14 ("White model folders -> fleet convention" section, quant-named paths corrected); the TODO checkbox predates that fix - no edit owed from Red seat (existing-file edits do not propagate to White canonical).
