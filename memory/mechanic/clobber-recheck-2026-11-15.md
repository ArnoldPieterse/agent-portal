# Mechanic clobber re-check 2026-11-15 ~14:5x (shared agent folder)
Probe of the shared-agent-folder working dir (SMB mirror target, NOT a git checkout — no .git here):
- agent_portal.py sha12 = d0a782fb063f, mtime 2026-11-15 14:49:25. THIRD variant — matches neither canonical 29ca92639845 (Builder host) nor Red's 25fd9457b2cb. L1692-1693 here are live `_proxy_get` code, NOT the "dead code" the STATUS note cites → line numbers/variant have drifted.
- index.html = 7x `class="frow`, 0x `.drow`, 3x `frow-h` → pre-H1-fix state, same as Red shared root. H1 rename has not landed in this root either.
- _portal_pid.txt mtime 2026-11-14 14:08:03 (STALE, yesterday) = PID 19488; agent_portal.py modified today 14:49 → recorded PID is NOT trustworthy. Restart-trap rule (listener CreationDate > file mtime) CANNOT be satisfied from a stale pid file.
Verdict: SMB mirror clobber/lag is active in the SHARED root, not just Red. No restart attempted — live :8099 listener could not be identified from this tool env (tasklist/netstat both erroring, git off PATH), and rule = never restart what you haven't identified.
Hand-off: ORCHESTRATOR must re-derive the real PID from netstat on the host that owns the :8099 listener before any White restart; do not trust 19488. VERIFIER: shared-root agent_portal.py is now d0a782fb063f (new data point vs your Black pin 29ca…).
