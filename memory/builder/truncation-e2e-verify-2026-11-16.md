# Goal #5 (B5) - truncation detection: _is_truncated refactor + unit fixture

Date: 2026-11-16. Supersedes the earlier text of this leaf (parse_sse/is_failure variant,
test_group_e2e_truncation.py 5/5), which was lost to a mirror clobber and is NOT on disk.
Also supersedes e2e-truncation-integration-2026-11-15.md on test-fixture location (that
fixture never survived the clobber either).

group_e2e.py state (sha12 9e4955611304, 7769B CRLF):
1. `_is_truncated(text, finish)` - module-level pure function before portal_chat:
   True when finish=='length', OR unbalanced `< tool_call>`/`< /tool_call>` counts
   (space-stripped), OR `<function=` present without a closing `< /function>`.
2. portal_chat() calls it: `truncated = _is_truncated(text, finish)` (inline expr removed).
3. Behavior unchanged: truncated field, TRUNCATED tags, truncated_agents/has_truncation in result JSON.

Test fixture: test_truncation_detect.py (project root, beside group_e2e.py)
- AST-extracts ONLY the _is_truncated FunctionDef from group_e2e.py (importing the whole
  script would trigger the live e2e run - no network needed here).
- 6 cases: normal completion / finish_reason=length / unbalanced tool_call tag /
  balanced tags + length / empty text / thinking-only.
- Run 2026-11-16: PASS 6/6 ("PASS: all 6 cases - _is_truncated extracted from group_e2e.py via AST, no network").

Verification: py_compile group_e2e.py OK; python test_truncation_detect.py exit 0.
