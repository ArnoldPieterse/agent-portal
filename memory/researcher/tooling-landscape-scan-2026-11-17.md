# External tooling landscape scan (cycle-3) — 2026-11-17
Owner: Researcher (goal #7). All citations fetched live 2026-11-17.
Scope: tools relevant to the fleet's ops stack (4-host Python, mirror sync, JSON manifests, file-watch).

## Verdict summary
| Category | Pick | Decision | One-line reason |
|---|---|---|---|
| File watching (Windows) | `watchfiles` | **ADOPT** | Rust notify-rs backend, native Windows wheels, faster than watchdog; drop-in for mirror-sync file-watch. |
| JSON Schema validation | `fastjsonschema` (hot path) + `jsonschema` (correctness) | **ADOPT (dual)** | Compiled validator ~25ms vs jsonschema ~5s on valid input; keep jsonschema where draft-2019/2020 compliance matters. |
| Distributed tracing | OpenTelemetry SDK w/ file/OTLP exporter | **MONITOR** | Standard is right for the long run, but full backends (Jaeger/Uptrace/SigNoz + ClickHouse) are overkill at 4 hosts; instrument now with structured spans in existing jsonl. |

## 1. File watching — `watchfiles` (ADOPT)
- Source: https://github.com/samuelcolvin/watchfiles (fetched live).
- Backed by Rust `notify-rs/notify`; prebuilt wheels for Windows/Linux/macOS; Py3.10–3.15.
- API: sync `watch()`, async `awatch()`, plus `run_process()`/`arun_process()` and a CLI (`watchfiles "cmd" src`).
- Formerly `watchgod` (migration guide exists).
- Why over incumbent `watchdog`: watchdog is pure-Python per-backend (ReadDirectoryChangesW on Windows) and fine, but watchfiles batches/dedupes via Rust and is the maintained modern choice; watchdog's known memory-leak is Linux-inotify-specific (a patched fork even exists), not a Windows concern — so this is a perf/maintenance win, not a bug fix.
- Fleet use: mirror-sync instrumentation (goal #3) file-watch + portal auto-reload. Drop-in: `for changes in watch(dir): ...`.
- Caveat: requires Py>=3.10; if any host runs 3.9, pin watchdog there.

## 2. JSON Schema validation — `fastjsonschema` (ADOPT dual)
- Source: https://horejsek.github.io/python-fastjsonschema/ (fetched live) + libhunt compare.
- Benchmarks (from project docs): fastjsonschema compiled ≈0.1s valid / 0.004s invalid on a large schema; plain `jsonschema` ≈5.2s valid / 1.3s invalid; `jsonschema_compiled` ≈0.44s/0.02s. (i.e. ~20–50x faster than uncompiled jsonschema.)
- How: compiles schema -> generated Python function, best when compiled once + used many times (like a regex). `compile_to_code()` can emit to file for marginal extra speed.
- Drafts supported: 04/06/07 only. NOT draft-2019-09/2020-12.
- Gotchas (documented): uses full Python regexes (not the JSON-Schema-limited subset) and rewrites `$` to `\Z`; supports `default` and RETURNS transformed data (use_default=True default).
- Fleet use: validate `agents.json`, manifests, ledger payloads on hot path with fastjsonschema; keep `jsonschema` for any schema needing latest drafts or strict-standard edge cases. Low risk, high win.

## 3. Distributed tracing — OpenTelemetry (MONITOR)
- Source: https://uptrace.dev/tools/distributed-tracing-tools (fetched live, Dec 2025) + CNCF status.
- Landscape: Jaeger v2 (CNCF graduated, OTel-native, v1 deprecates Jan 2026), Uptrace & SigNoz (Go+ClickHouse, native OTel), Zipkin (volunteer-maintained, adapter-only OTel), Grafana Tempo (object-storage, Grafana-integrated).
- Common thread: every serious option now converges on **OpenTelemetry/OTLP as the ingestion standard**; the backends differ mainly in storage (ClickHouse vs object-store vs multi-DBMS).
- Recommendation for THIS fleet: adopt the OTel SDK instrumentation pattern now (it structures goal #3's mirror-sync trace events cleanly), but export to a file/collector, NOT a ClickHouse-backed APM — at 4 hosts that infra is net-negative. Revisit Jaeger/Tempo only if span volume or multi-team debugging demand grows.
- Adopt/reject: **MONITOR** OTel as standard; **REJECT (for now)** heavyweight backends (ClickHouse opex) at current scale.

## Actionable handoffs
- Mechanic: watchfiles is the file-watch primitive for goal #3 instrumentation window (11-17→11-24).
- Builder/Archivist: fastjsonschema for manifest/agents.json validation on hot path; keep jsonschema fallback.
- Scribe: add these 3 to the fleet ops-stack shortlist in next synthesis.

## Confidence
HIGH on file-watch + JSON schema picks (primary sources, concrete numbers). MEDIUM-HIGH on tracing (scale judgment is inference from fleet size; the OTel-is-standard claim is well-supported across sources). Citations: watchfiles GitHub README, fastjsonschema docs, uptrace.dev comparison — all fetched 2026-11-17.
