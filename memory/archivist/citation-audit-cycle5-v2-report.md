# Citation Accuracy Audit v2 - Cycle 5 (Builder assist, Archivist goal #2)

Generated: 2026-11-19T00:17:50Z
Method: offline URL classification over memory/**/*.md. EXTERNAL citations inherit
v1's live status; INTERNAL/TEMPLATE/BARE are separated out because they are NOT
broken external citations (v1 miscounted them as dead).

## Classification summary
| Category | Count | Meaning |
|---|---|---|
| PASS | 39 | external citation live |
| FAIL | 11 | external domain dead/unreachable (real broken citation) |
| NOT-RECHECKED | 28 | external, no v1 row matched |
| INTERNAL-MALFORMED | 4 | internal portal URL missing slash after port - FIXABLE DOC BUG |
| TEMPLATE | 3 | placeholder/template token, not a real citation |
| BARE-EMPTY | 2 | bare scheme with no host (placeholder) |
| INTERNAL-OK | 14 | well-formed internal endpoint |

## Key finding (vs v1)
- Total unique URLs: **101**
- Genuinely external citations: **78** (PASS 39, WARN 0, dead 11)
- **True dead-external-citation rate: 14.1%**  (goal target >90% accuracy = <10% dead)
- Malformed internal URLs (fixable doc bugs v1 miscounted as dead): **4**
- Placeholders/templates/bare (not real citations): **5**

## Fixable malformed internal URLs (missing slash after port)
| URL | Suggested fix | File(s) |
| `http://pale:8099api/fleet` | `http://pale:8099/api/fleet` | memory/archivist/citation-audit-cycle5-report.md |
| `http://red:8099api/settings/lan-access/start` | `http://red:8099/api/settings/lan-access/start` | memory/archivist/citation-audit-cycle5-report.md |
| `http://white:8099api/fleet` | `http://white:8099/api/fleet` | memory/archivist/citation-audit-cycle5-report.md |
| `http://white:8099api/todo/prune` | `http://white:8099/api/todo/prune` | memory/archivist/citation-audit-cycle5-report.md |

## All URLs (classified)
| URL | Category | Status | Detail | File(s) |
| `http://` | BARE-EMPTY | n/a | bare scheme, no host (placeholder) | memory/portal/architecture.md |
| `http://127.0.0.1:8099` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/designer/baseline/README.md, memory/designer/baseline/progress- |
| `http://127.0.0.1:8099/` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/ops/blockers.md |
| `http://127.0.0.1:8099/`` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/designer/ac-a2-design-leg-r30.md |
| `http://127.0.0.1:8099/api/decisions?agent=Scribe` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/mechanic/assist-scribe-goal1-decisions-v2-reland-2026-11-18.md |
| `http://127.0.0.1:8099/api/file/raw?path=flowmap/index.html` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/portal/system-map.md |
| `http://127.0.0.1:8099/api/fleet` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/ops/probes.md |
| `http://127.0.0.1:8099/api/git` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/builder/curl-examples-prune-git-2026-11-15.md, memory/portal/ar |
| `http://127.0.0.1:8099/api/goals` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/ops/boot-deployment-runbook.md |
| `http://127.0.0.1:8099/api/goals`` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/ops/portal-down-2026-11-15.md |
| `http://127.0.0.1:8099/api/health` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/ops/cycle-transition-checklist.md |
| `http://127.0.0.1:8099/api/health/fleet` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/mechanic/goal7-fleet-health-v2-2026-11-18.md |
| `http://127.0.0.1:8099/api/memory`` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/ops/portal-outage-2026-11-15-1825.md |
| `http://127.0.0.1:8099/api/todo/prune` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/builder/curl-examples-prune-git-2026-11-15.md, memory/portal/ar |
| `http://127.0.0.1:8099/index.html` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/designer/post-restart-verify-r16.md |
| `http://127.0.0.1:8099`` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/designer/goal10-cdp-capture-2026-11-18.md, memory/verifier/ac-a |
| `http://127.0.0.1:8888` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/llm/studio-api.md, memory/mechanic/portal-startup-fix-2026-11-1 |
| `http://127.0.0.1:8888/api/health` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/ops/remote-host-metrics-probe-spec.md |
| `http://127.0.0.1:8888/api/settings/lan-access/start` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/llm/hosts.md |
| `http://127.0.0.1:8888/api/settings/model-aliases`` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/llm/model-id-check-2026-11-15.md |
| `http://127.0.0.1:8888/models` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/ops/blockers.md |
| `http://127.0.0.1:8888/models`` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/llm/model-id-check-2026-11-15.md |
| `http://127.0.0.1:8888/v1/models`` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/ops/mechanic-researcher-alias-diagnosis-2026-11-16.md |
| `http://[LAN-IP]:8099` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/portal/ui-upgrades-r4.md |
| `http://[LAN-IP]:8099/api/file/raw?path=TODO.md`` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/mechanic/red-white-reachability-2026-11-14.md |
| `http://IP_RED:8888` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/archivist/REPAIR_2026-11-13.md |
| `http://IP_BLACK:8888` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/llm/hosts.md, memory/ops/black-studio-failover-2026-11-16.md, m |
| `http://[redacted-lan-template]`` | TEMPLATE | n/a | placeholder/template token, not a real citation | memory/researcher/ip-scrub-gate-reconcile-2026-11-15.md |
| `http://[redacted-lan-template`` | TEMPLATE | n/a | placeholder/template token, not a real citation | memory/researcher/citation-manifest-2026-11-15.md |
| `http://host:port/` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/archivist/citation-audit-cycle5-report.md |
| `http://host:port/api/host-metrics` | EXTERNAL | NOT-RECHECKED | (not in v1 sample; live-check on a net seat) | memory/archivist/citation-audit-cycle5-report.md, memory/ops/remote-ho |
| `http://localhost:1235`` | INTERNAL-OK | n/a | internal portal endpoint (localhost) | memory/projects/dcabots.md, memory/researcher/dcabots-reprompt-prechec |
| `http://localhost:8099` | INTERNAL-OK | n/a | internal portal endpoint (localhost) | memory/designer/goal10-cdp-script-2026-11-18.md, memory/goals/designer |
| `http://localhost:8099/`` | INTERNAL-OK | n/a | internal portal endpoint (localhost) | memory/designer/ac-a2-2-console-clean-criteria.md |
| `http://localhost:8099/api/file/raw?path=agent_portal.py`` | INTERNAL-OK | n/a | internal portal endpoint (localhost) | memory/mechanic/ops_r6_red_probe.md |
| `http://localhost:8099/api/fleet/overview` | INTERNAL-OK | n/a | internal portal endpoint (localhost) | memory/verifier/concurrency-stress-report.md |
| `http://localhost:8099/api/goals` | INTERNAL-OK | n/a | internal portal endpoint (localhost) | memory/goals/mechanic-forecast-recovery-matrix.md, memory/verifier/con |
| `http://localhost:8099/api/goals`` | INTERNAL-OK | n/a | internal portal endpoint (localhost) | memory/goals/mechanic-forecast-recovery-matrix.md, memory/mechanic/rec |
| `http://localhost:8099/api/health/fleet`` | INTERNAL-OK | n/a | internal portal endpoint (localhost) | memory/mechanic/goal7-fleet-health-v2-fields-added-2026-11-18.md |
| `http://localhost:8099/api/kb/search?q=test`` | INTERNAL-OK | n/a | internal portal endpoint (localhost) | memory/mechanic/recovery-matrix.md |
| `http://localhost:8099`` | INTERNAL-OK | n/a | internal portal endpoint (localhost) | memory/designer/goal2-fleet-matrix-responsive-verify-2026-11-18.md, me |
| `http://pale:8099/api/fleet`` | INTERNAL-OK | n/a | internal portal endpoint (pale) | memory/ops/host-consistency-report.md |
| `http://pale:8099api/fleet` | INTERNAL-MALFORMED | n/a | missing slash after port -> pale:8099/api | memory/archivist/citation-audit-cycle5-report.md |
| `http://red:8099/api/settings/lan-access/start`` | INTERNAL-OK | n/a | internal portal endpoint (red) | memory/ops/host-consistency-report.md |
| `http://red:8099api/settings/lan-access/start` | INTERNAL-MALFORMED | n/a | missing slash after port -> red:8099/api | memory/archivist/citation-audit-cycle5-report.md |
| `http://white:8099/api/fleet`` | INTERNAL-OK | n/a | internal portal endpoint (white) | memory/ops/host-consistency-report.md |
| `http://white:8099/api/todo/prune`` | INTERNAL-OK | n/a | internal portal endpoint (white) | memory/ops/host-consistency-report.md |
| `http://white:8099api/fleet` | INTERNAL-MALFORMED | n/a | missing slash after port -> white:8099/api | memory/archivist/citation-audit-cycle5-report.md |
| `http://white:8099api/todo/prune` | INTERNAL-MALFORMED | n/a | missing slash after port -> white:8099/api | memory/archivist/citation-audit-cycle5-report.md |
| `http://{host}:{port}/api/host-metrics` | TEMPLATE | n/a | placeholder/template token, not a real citation | memory/archivist/citation-audit-cycle5-report.md, memory/ops/remote-ho |
| `https://` | BARE-EMPTY | n/a | bare scheme, no host (placeholder) | memory/archivist/citation-audit-cycle5-report.md, memory/ops/ingestion |
| `https://arxiv.org/abs/2311.16542` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/ci |
| `https://arxiv.org/abs/2608.06867` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/llm/hotload-s |
| `https://blog.crewai.com/crewai-amp-the-agent-management-plat` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md |
| `https://blog.crewai.com/crewai-amp-the-agent-management-platform/` | EXTERNAL | PASS | HTTP 200 | memory/researcher/competitive-scan-2026-11.md |
| `https://crewai.com/agent-management-platform` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/co |
| `https://deepwiki.com/crewAIInc/crewAI/10-enterprise-features` | EXTERNAL | FAIL | HTTP 429 | memory/archivist/citation-audit-cycle5-report.md |
| `https://deepwiki.com/crewAIInc/crewAI/10-enterprise-features-(crewai-amp` | EXTERNAL | FAIL | HTTP 429 | memory/researcher/competitive-scan-2026-11.md |
| `https://devblogs.microsoft.com/agent-framework/microsoft-age` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md |
| `https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version` | EXTERNAL | PASS | HTTP 200 | memory/researcher/competitive-scan-2026-11.md |
| `https://developer.mozilla.org/en-US/docs/Web/HTTP/Status` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://docs-platform.crewai.com/platform/en/introduction` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/co |
| `https://docs.pytest.org/en/stable/how-to/cache.html` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md |
| `https://docs.python.org/3/library/datetime.html` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://docs.python.org/3/library/json.html` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://docs.python.org/3/library/os.html` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://docs.python.org/3/library/subprocess.html` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://en.wikipedia.org/wiki/Data_migration` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://en.wikipedia.org/wiki/Hash_function` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://en.wikipedia.org/wiki/Queue_(data_structure` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://en.wikipedia.org/wiki/Version_control` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://example.com/elev-helper-docs` | EXTERNAL | FAIL | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] ce | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://example.com/fleet-mirror-notes` | EXTERNAL | FAIL | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] ce | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://example.com/only-one-source` | EXTERNAL | FAIL | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] ce | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://example.com/single-source` | EXTERNAL | FAIL | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] ce | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://example.com/verification-pipelines` | EXTERNAL | FAIL | URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] ce | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://flask.palletsprojects.com/en/2.0.x/api/` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://github.com/ArnoldPieterse/agent-portal` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/ops/public-re |
| `https://github.com/anthropics/claude-code/blob/main/docs/mir` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md |
| `https://github.com/anthropics/claude-code/blob/main/docs/mirror-sync.md` | EXTERNAL | PASS | HTTP 200 | memory/researcher/tests/evidence_good_A.md |
| `https://github.com/lmstudio-ai/lmstudio-bug-tracker/issues/2` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md |
| `https://github.com/lmstudio-ai/lmstudio-bug-tracker/issues/2423` | EXTERNAL | PASS | HTTP 200 | memory/llm/overnight-unload.md, memory/researcher/citation-audit-2026- |
| `https://github.com/rst0git/SwapServeLLM` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/llm/hotload-s |
| `https://github.com/samuelcolvin/watchfiles` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/to |
| `https://horejsek.github.io/python-fastjsonschema/` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/to |
| `https://learn.microsoft.com/en-us/agent-framework/migration-` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md |
| `https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/` | EXTERNAL | PASS | HTTP 200 | memory/researcher/competitive-scan-2026-11.md |
| `https://learn.microsoft.com/en-us/windows-server/administrat` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md |
| `https://learn.microsoft.com/en-us/windows-server/administration/performance-tuni` | EXTERNAL | PASS | HTTP 200 | memory/researcher/citation-audit-2026-11-15.md, memory/researcher/cita |
| `https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/llm/overnight |
| `https://numpy.org/doc/stable/reference/generated/numpy.datet` | EXTERNAL | FAIL | HTTP 404 | memory/archivist/citation-audit-cycle5-report.md |
| `https://numpy.org/doc/stable/reference/generated/numpy.datetime64.html` | EXTERNAL | FAIL | HTTP 404 | memory/researcher/tests/evidence_good_B.md |
| ` [redacted-tunnel-url]` | EXTERNAL | FAIL | URLError: <urlopen error [Errno 11001] getaddrinfo failed> | memory/archivist/citation-audit-cycle5-report.md, memory/llm/hosts.md, |
| `https://realpython.com/python-date-time/` | EXTERNAL | FAIL | HTTP 404 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/te |
| `https://turion.ai/blog/langgraph-vs-crewai-vs-autogen-compar` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md |
| `https://turion.ai/blog/langgraph-vs-crewai-vs-autogen-comparison-2026/` | EXTERNAL | PASS | HTTP 200 | memory/researcher/competitive-scan-2026-11.md |
| `https://uptrace.dev/tools/distributed-tracing-tools` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/to |
| `https://vllm-sr.ai/docs/intro/` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/llm/hotload-s |
| `https://www.langchain.com/blog/langgraph-platform-ga` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/co |
| `https://www.langchain.com/langsmith/deployment` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/co |
| `https://www.langchain.com/langsmith/observability` | EXTERNAL | PASS | HTTP 200 | memory/archivist/citation-audit-cycle5-report.md, memory/researcher/co |
