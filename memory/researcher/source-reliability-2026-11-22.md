# Source Reliability Scoring Report
Date: 2026-11-22 | Fleet sources scored: 61

## Method
- Citation count across all memory/ leaves (weight 0.5 per citation, capped at 10)
- Positive context mentions (verified/confirmed/success) add 0.3 each (capped 5)
- Negative context mentions (fail/error/contradict) subtract 0.2 each (capped 5)
- Final score clamped to 1-10

## Scoring Rubric
| Score | Meaning |
|-------|---------|
| 8-10 | High reliability: heavily cited, positive context, no contradictions |
| 5-7.9 | Moderate: regularly cited, mixed or neutral context |
| 3-4.9 | Low-moderate: occasionally cited, some negative context |
| 1-2.9 | Low: rarely cited or predominantly negative context |

## Top 3 Most Reliable
1. **3.6/10** (6x cited) - https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict
2. **3.4/10** (5x cited) - https://github.com/ArnoldPieterse/agent-portal
3. **2.9/10** (5x cited) - https://arxiv.org/abs/2311.16542

## Bottom 3 Least Reliable
1. **1/10** (1x cited) - https://learn.microsoft.com/en-us/windows-server/administration/performance-tuni
2. **1/10** (1x cited) - https://pypi.org/simple/playwright/
3. **1/10** (1x cited) - https://playwright.azureedge.net/builds/chromium/

## Full Table
| URL | Score | Citations | Negative ctx | Files |
|-----|-------|-----------|--------------|-------|
| https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict | 3.6 | 6 | 0 | memory/llm/overnight-unload.md, memory/r |
| https://github.com/ArnoldPieterse/agent-portal | 3.4 | 5 | 0 | memory/ops/public-repo-agent-portal-2026 |
| https://arxiv.org/abs/2311.16542 | 2.9 | 5 | 1 | memory/archivist/citation-audit-cycle5-r |
| https://github.com/lmstudio-ai/lmstudio-bug-tracker/issues/2 | 2.9 | 4 | 0 | memory/llm/overnight-unload.md, memory/r |
| https://docs-platform.crewai.com/platform/en/introduction | 2.6 | 4 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://crewai.com/agent-management-platform | 2.6 | 4 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://www.langchain.com/blog/langgraph-platform-ga | 2.6 | 4 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://en.wikipedia.org/wiki/Version_control | 2.6 | 4 | 0 | memory/researcher/tests/evidence_good_A. |
| https://docs.python.org/3/library/json.html | 2.6 | 4 | 0 | memory/archivist/citation-audit-cycle5-r |
|  [redacted-tunnel-url] | 2.4 | 5 | 2 | memory/researcher/citation-manifest-2026 |
| https://github.com/rst0git/SwapServeLLM | 2.1 | 3 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://vllm-sr.ai/docs/intro/ | 2.1 | 3 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://arxiv.org/abs/2608.06867 | 2.1 | 3 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://www.langchain.com/langsmith/deployment | 2.1 | 3 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://www.langchain.com/langsmith/observability | 2.1 | 3 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://github.com/samuelcolvin/watchfiles | 2.1 | 3 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://horejsek.github.io/python-fastjsonschema/ | 2.1 | 3 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://uptrace.dev/tools/distributed-tracing-tools | 2.1 | 3 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://docs.python.org/3/library/subprocess.html | 2.1 | 3 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://en.wikipedia.org/wiki/Hash_function | 2.1 | 3 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://docs.python.org/3/library/os.html | 2.1 | 3 | 0 | memory/researcher/tests/evidence_good_A. |
| https://developer.mozilla.org/en-US/docs/Web/HTTP/Status | 2.1 | 3 | 0 | memory/researcher/tests/evidence_good_A. |
| https://flask.palletsprojects.com/en/2.0.x/api/ | 2.1 | 3 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://en.wikipedia.org/wiki/Data_migration | 2.1 | 3 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://docs.python.org/3/library/datetime.html | 2.1 | 3 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://blog.crewai.com/crewai-amp-the-agent-management-plat | 1.8 | 3 | 0 | memory/researcher/competitive-scan-2026- |
| https://turion.ai/blog/langgraph-vs-crewai-vs-autogen-compar | 1.8 | 3 | 0 | memory/researcher/competitive-scan-2026- |
| https://learn.microsoft.com/en-us/windows-server/administrat | 1.8 | 3 | 0 | memory/researcher/sync-clobber-analysis- |
| https://en.wikipedia.org/wiki/Queue_(data_structure | 1.6 | 3 | 1 | memory/archivist/citation-audit-cycle5-r |
| http://IP_BLACK:8888 | 1.6 | 3 | 1 | memory/llm/hosts.md |
| https://github.com/lmstudio-ai/lmstudio-bug-tracker/issues/2 | 1.6 | 2 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://docs.pytest.org/en/stable/how-to/cache.html | 1.6 | 2 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://learn.microsoft.com/en-us/windows-server/administrat | 1.6 | 2 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://blog.crewai.com/crewai-amp-the-agent-management-plat | 1.6 | 2 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://devblogs.microsoft.com/agent-framework/microsoft-age | 1.6 | 2 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://learn.microsoft.com/en-us/agent-framework/migration- | 1.6 | 2 | 0 | memory/archivist/citation-audit-cycle5-r |
| https://turion.ai/blog/langgraph-vs-crewai-vs-autogen-compar | 1.6 | 2 | 0 | memory/archivist/citation-audit-cycle5-r |
| http://{host}:{port}/api/host-metrics | 1.5 | 3 | 0 | memory/ops/remote-host-metrics-probe-spe |
| http://Red:8888 | 1.5 | 3 | 0 | memory/archivist/REPAIR_2026-11-13.md, m |
| http://[redacted-lan-template] | 1.3 | 2 | 0 | memory/researcher/ip-scrub-gate-reconcil |
| https://github.com/anthropics/claude-code/blob/main/docs/mir | 1.3 | 2 | 0 | memory/researcher/tests/evidence_good_A. |
| https://learn.microsoft.com/en-us/agent-framework/migration- | 1.3 | 2 | 0 | memory/researcher/competitive-scan-2026- |
| https://example.com/fleet-mirror-notes | 1.1 | 3 | 2 | memory/archivist/citation-audit-cycle5-r |
| https://example.com/elev-helper-docs | 1.1 | 3 | 2 | memory/archivist/citation-audit-cycle5-r |
| https://example.com/verification-pipelines | 1.1 | 3 | 2 | memory/archivist/citation-audit-cycle5-r |
| https://example.com/only-one-source | 1.1 | 3 | 2 | memory/archivist/citation-audit-cycle5-r |
| https://example.com/single-source | 1.1 | 3 | 2 | memory/archivist/citation-audit-cycle5-r |
| https://realpython.com/python-date-time/ | 1.1 | 3 | 2 | memory/archivist/citation-audit-cycle5-r |
| https://github.com/anthropics/claude-code/blob/main/docs/mir | 1.1 | 2 | 1 | memory/archivist/citation-audit-cycle5-r |
| https://deepwiki.com/crewAIInc/crewAI/10-enterprise-features | 1 | 2 | 2 | memory/archivist/citation-audit-cycle5-r |
| https://numpy.org/doc/stable/reference/generated/numpy.datet | 1 | 2 | 2 | memory/archivist/citation-audit-cycle5-r |
| https:// | 1 | 2 | 0 | memory/archivist/citation-audit-cycle5-r |
| http://[redacted-lan-template | 1 | 2 | 0 | memory/archivist/citation-audit-cycle5-v |
| https://deepwiki.com/crewAIInc/crewAI/10-enterprise-features | 1 | 2 | 1 | memory/researcher/competitive-scan-2026- |
| https://numpy.org/doc/stable/reference/generated/numpy.datet | 1 | 2 | 1 | memory/researcher/tests/evidence_good_B. |
| http:// | 1 | 2 | 1 | memory/portal/architecture.md, memory/ar |
| https://devblogs.microsoft.com/agent-framework/microsoft-age | 1 | 2 | 0 | memory/researcher/competitive-scan-2026- |
| https://devblogs.microsoft.com/agent-framework/microsoft-age | 1 | 1 | 0 | memory/archivist/citation-audit-cycle5-v |
| https://learn.microsoft.com/en-us/windows-server/administrat | 1 | 1 | 0 | memory/archivist/citation-audit-cycle5-v |
| https://pypi.org/simple/playwright/ | 1 | 1 | 0 | memory/researcher/browser-blocker-correc |
| https://playwright.azureedge.net/builds/chromium/ | 1 | 1 | 0 | memory/researcher/browser-blocker-correc |