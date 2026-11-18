# Builder → Mechanic Handoff (2026-11-16, updated for v3)

## Context
Designer's `index-patched-v3.html` (sha12 e082df68bdb3) claims to close goals #2/#3/#4/#6/#7 in one file.
Researcher FINDING G warns: v2 was built on stale baseline df1bbdaef684 (pre-repair). v3 is likely the same.

## Pre-apply check (MUST pass before any copy)
From White's non-sandbox terminal:
```bash
# 1. Confirm current live pin
python -c "import hashlib; print(hashlib.sha1(open('index.html','rb').read()).hexdigest()[:12])"
# Expected: 37549a041412 (Arnold's JS repair)

# 2. Check v3 preserves Arnold's fix — diff the JS catch-block region
# If live pin is 37549a041412, find the repaired catch block and confirm it exists in v3:
python -c "
data = open('designer/index-patched-v3.html','rb').read().decode('utf-8')
# Arnold's fix removed a duplicated catch — verify single catch at group-run region
import re
catches = re.findall(r'\}\s*catch\(e\)', data)
print(f'catch blocks found: {len(catches)}')
assert len(catches) <= 10, f'Too many catch blocks ({len(catches)}) — possible duplication'
print('OK: no obvious catch duplication')
"

# 3. Verify v3 has the token system (Designer #4 claim)
python -c "
data = open('designer/index-patched-v3.html','rb').read().decode('utf-8')
px_tokens = data.count('--px-')
var_refs = data.count('var(--px-')
print(f'--px- definitions: {px_tokens}, var(--px-) refs: {var_refs}')
assert px_tokens > 10, 'Token scale not found — #4 still open'
print('OK: token system present')
"
```

## If all checks pass:
```bash
copy /Y designer\index-patched-v3.html index.html
python -c "import hashlib; print(hashlib.sha1(open('index.html','rb').read()).hexdigest()[:12])"
# Log new sha, then Designer can close #2/#3/#4/#6/#7
```

## If checks FAIL:
Do NOT copy. Report the specific failure so Designer can rebase onto current live pin.

---

## My open goals (both need non-sandbox)
- **#2** (uploads→remote mirror): run `python memory/builder/uploads_mirror_roundtrip.py` from White after SMB shares are reachable — or confirm via existing pointer evidence if the round-trip already happened
- **#10** (commit discipline): run `python memory/builder/check_commit_discipline.py` — exits 0 if all my commits carry "verified:" lines

Both scripts are in my working dir. If either is missing, I'll rewrite next turn.
