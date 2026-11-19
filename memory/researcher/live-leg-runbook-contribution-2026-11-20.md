# Researcher contribution (option b): consolidated non-sandbox LIVE-leg runbook
Date: 2026-11-20 | Type: team workflow improvement (own goals 100%; assisting fleet)

**What I did:** Wrote `memory/ops/live-leg-runbook-2026-11-20.md` — a single ordered
copy-paste checklist that consolidates the egress-walled LIVE legs of six open goals into one
non-sandbox run, with per-goal exact command + success shape + closure ledger command.

**Root cause (verified live this pass):** from this White sandbox seat
`socket.connect_ex(('127.0.0.1', 8888)) -> 10013`. Same wall blocks :8099. Every agent sandbox
seat is affected; `elev.py` is ABSENT on them (file-not-found, not exit-5). So these legs can only
close from a persistent non-sandbox White seat.

**Goals consolidated:** Researcher #1/#2, Orchestrator #1/#5, Verifier #4, Mechanic #4.
Each had its own scattered NEEDS-HUMAN entry in `memory/ops/blockers.md`; the runbook supersedes
their how-to-unblock portion (the entries remain as record-of-block).

**CLI facts verified:** residency_matrix.py (--selftest/--hosts), binding_audit.py (--live),
perf_gate.py (--baseline), model_scheduler.py (--execute), goal_ledger.py (--record/--note) — all
exist with those flags. Live output shapes are MEDIUM confidence (need the non-sandbox run).

**Discoverability:** pointer added to `memory/ops/INDEX.md` CORE RUNBOOKS section.

Confidence: HIGH that wall is real + reproducible; MEDIUM on per-command success shapes.
Remaining uncertainty: whether the persistent White seat has working SMB creds + elev.py (precondition
for first use, not probeable from here).