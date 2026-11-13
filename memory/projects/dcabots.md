# DCABOTS (DCA Bots) — project state
*Updated 2026-11-14 by Researcher. Project area: `projects/dcabots/` (moved from uploads/dcabots; source on White: C:\projects\dcabots, snapshot 2026-11-14 ~01:35).*

- **What**: self-hosted DCA bot, Binance USDT spot. Local LLM proposes strategy cards; deterministic engine validates/backtests/executes. Main strategy v2 = daily top-5 most-volatile + LLM-configured DCA cards (DRAFTS only, never auto-executed).
- **Verified**: engine 29/29 self-tests (re-run on this host 2026-11-14); E13 PASS (risk-reduction: DD 3.23% vs 9.14% fixed); E4 verdict = ship deterministic gate, LLM stance out of trade path; E5: LLM≈default → value=safety/UX; E12 drill 4/4; farm 38,880 backtests done.
- **In flight**: E14 STALLED **89/440** (cache `results/e14/caches/llm_responses.jsonl`, resumable via `python -m dcabots e14`; needs LM Studio :1235). Stage 3 final-report + stage 4 E15 (H15.1) never ran.
- **Bugs/gaps**: farm.py:569 cross-drive os.path.relpath crash on self-test (→ Builder); mirror MISSING webapp.py (:8790 dashboard) + requirements.txt (re-fetch from White). No API keys in mirror (scanned clean). .venv/uv/models excluded as machine-specific; system py3.13+numpy+pandas works here.
- **Open**: resume E14 → stage 3 → E15 verdict; E9 user-arm recruitment; live trading = explicit human action only (`keys set` + `live --i-understand-live-trading`).
- **Detail**: projects/dcabots/PROJECT.md (brief) · README.md (commands) · STATUS.md (project's own 2026-10-14 status) · design/03 (operational truth).
