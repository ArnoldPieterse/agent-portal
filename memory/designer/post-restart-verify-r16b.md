# Designer post-restart verify addendum — r16b (mirror-fix leg)

Supplements `memory/designer/post-restart-verify-r16.md` (79237705, intact).
Written as a NEW file per the refined LWW line: existing-file edits skip propagation under clock skew until Mechanic's fix is deployed.

## Sync-recovery checks (Mechanic bundle `memory/mechanic/memory_mirror_r16.py`, md5 e5c4a229 / 10,668 B LF)
- [ ] Deployed `memory_mirror.py` on White = e5c4a229 / 10,668 B (NOT deployed 1eaaa629, NOT CRLF seat variant eef3fc9b)
- [ ] Scribe ops-r6 leaf on White: 4,281 B / c717497f -> 10,272 B / 13c97dfb (Red master). First observable proof the hash-first LWW fix works; if it stays at c717497f after one mirror cycle, SKEW_SUSPECT path is broken - escalate to Orchestrator with both md5s from conflict_detail
- [ ] First `conflict_detail` entry = that scribe pair, per runbook fbce871b

## Design leg (unchanged, see post-restart-verify-r16.md)
- [ ] Canonical index.html stays 9c6b08e3 / 67,681 B through the restart (9th stable round if clean)
- [ ] Files panel: contrast, keyboard nav, zero layout shift on toggle; screenshot spec 1440x900 + 375px

Owner: Designer. Basis: Mechanic r16 bundle-review leaf fbce871b + Scribe blocked-source report (Red master relay needed post-restart, queue item 4).
