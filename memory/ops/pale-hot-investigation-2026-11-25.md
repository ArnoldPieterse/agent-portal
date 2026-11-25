# Pale hot investigation - 2026-11-25 (VERDICT: NOT a breach)
Facts: GPU1 89C / 87-100% util / 254W, llama-server.exe PID7776 serving Qwen3.8-27B-Q8_0 on :61800 (MTP spec decode + reasoning on). GPU0 idle 43C. CPU load 73%.
Security checks ALL CLEAN: no miners/unknown procs; net conns = White(IP_LAN WinRM/SMB/Studio) + Cloudflare + Defender + MS + Red(:7680).
4624 logons = our own WinRM probes (pale, NTLM, type3, from IP_LAN).
4625 failed 'White' logons every 30min FROM 2406:2d40:2466:7f10:7006:8809:a1:82d6 = WHITE'S OWN temp IPv6 (verified via ipconfig) = our SMB mirror sync failing on empty password over IPv6 path. FIX: force mirror to use 192.168.1.x or set SMB creds.
Heat cause: sustained archivist-q8 inference load on GPU1; Studio shows 0 active generations between requests, backend python idle (0 CPU-s/10s) - heat tracks agent RAG cycles, not a runaway local loop at probe time.
Recs: nvidia-smi -pl 450 cap on Pale GPU1; review RAG call frequency per message; fix mirror IPv6 auth failures.
Probes: pale_hot_investigate*.py (1-9), output in pale_probe9_out.txt.
