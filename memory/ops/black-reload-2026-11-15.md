# OPS NOTE 2026-11-15 ~22:0x - Black re-probe + model reload (non-sandbox seat, White)

## Re-probe of all remotes from White host context (settles Mechanic goal #3 legs)
| Host | TCP :8888 | JWT login | /v1/models loaded | Verdict |
|------|-----------|-----------|-------------------|---------|
| BLACK .99 | PASS 0.2s | OK | 0/5 at 22:0x (all loaded=False) | Studio UP, VRAM empty |
| PALE .39 | PASS 0.2s | OK | 4/6: Q8_0, Q4_K_S, archivist-q8, designer-q4 | healthy |
| RED .245 | PASS 0.2s | OK | 4/5: Q8_0, unsloth GGUF, mechanic-q4, scribe-q8 | **healthy - the WinError 10013 "firewall" was a sandbox artifact, confirmed** |

## Black reload (broken step found + partial fix)
- POST /v1/load Q8_0 {model_path C:\Users\black\models\Qwen3.8-27B-Q8_0, variant Q8_0, gpu 1, ctx 32768, alongside} -> LOADED (verified in /api/inference/loaded-models + /v1/models loaded=True).
- UD-Q4_K_S: BLOCKED - this Studio build rejects raw Windows paths for transformers models ("Repo id must be in the form 'repo_name' or 'namespace/repo_name'"), and a bare id resolves to an HF lookup (unsloth/... not local). black_dual_load2.py's recipe no longer matches this build. Needs folder-scan registration flow (POST /api/hub/scan-folders created folder id 4, status ok) - exact load-by-scanned-id call still to be pinned down.
- Stale tunnel: trycloudflare quick-tunnel URL in tunnel_urls.json no longer resolves (DNS). LAN :8888 works; agents should probe LAN, not the dead hostname.

## Status
Black = Studio UP + Q8_0 resident (Builder/Verifier can generate via it). UD leg pending scan-based load recipe.
