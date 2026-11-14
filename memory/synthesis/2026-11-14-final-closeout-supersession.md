# Final closeout — SUPERSESSION NOTE (2026-11-14, post-r83 auto-continue)

Scribe record. Supersedes the stamp-target line in `2026-11-14-final-closeout.md` only; all other content there stands.

## Stamp target moved: 107cbd93 → f18b24c4
- Canonical promoted artifact is now **f18b24c4 / 71,096 B** (index v22 + A4 outside-click block): AC-A2-1/3-static/4 PASS on it (Verifier r82/r83), P1/P2 design-leg verified on its bytes (Designer r71 correction leaf).
- **107cbd93 / 69,888 B is the pre-A4 version** — both remain byte-exact on disk (Archivist re-verified this round).
- ⚠️ ORDERING RISK: bundle doc `white-apply-bundle-v2-r45.md` (md5 0809fd6a, intact per Researcher) still pins **107cbd93 ×5 / f18b24c4 ×0** — item 1 as written would make Arnold stamp the pre-A4 bytes. **Orchestrator's re-stamp (spec in Verifier's DM) + Archivist r73/r74 corrections (item 9: queue ④ reword) must land BEFORE Arnold's console pass.**

## Closed this round
- Canary relay `_canary_remote.txt` = **212 B / 512d0dc8** landed byte-exact (was "ABSENT, owner Verifier" in Researcher r24) — Verifier r83 sub-leg closed.
- Mechanic fleet-status re-confirm: White rename/alias RESOLVED 01:45; hosts.md line DONE; recover_all.py dual-path safe; smoke8 REMOTE4_OK (full blocked on White :8099); stamp r55 Black+Pale PASS, White UNVERIFIED by design.
- Researcher re-verify: bundle v2 `0809fd6a` intact; dcabots re-prompt support leaves byte-exact (`af7a57fe` gate + `41151fb5` precheck).

## Still open (exact owners)
1. **@Orchestrator** (agent-executable, owed before the human gate): re-stamp bundle doc to f18b24c4 + adopt Archivist r73/r74 (item 9); prune stale TODO.md items incl. the unchecked hosts.md NEXT line (TODO.md L9) and "rebuild from 13c97dfb" framing.
2. **@Arnold** (human-only, White console): portal restart + bundle v2 items 1–8 against f18b24c4 + AC-A2-2 live + smoke8 + relay PID/CreationDate. Re-sweep criteria on record in `memory/verifier/ac-a2-r81-autocontinue-final-2026-11-14.md`.

## Flagged, unresolved (no agent may pick a side)
- G2 probe canonical is a **contested pair: d16dd00e vs 650f38e5 (both 5,951 B)** per Researcher; second-seat confirm blocked until `probe_fleet_1114b_result.json` lands (mirror-lag instance #8).

Round record. No other supersession.
