# Builder closeout — a11y re-pin applied + farm.py:569 artifact verified (2026-11-14 ~04:17, Black seat)

## 1. Designer's WCAG-AA variant APPLIED as new canonical (one-concern-per-pin)
- Reconstructed the staged variant byte-exact from canonical root `index.html`
  (9c6b08e3…/67,681 B) + the documented single-line swap: exactly ONE occurrence of
  `#6b7688` in the whole file (the `.aev .at` rule); replaced with `#8b93a7`.
- Reconstructed md5 = **8ef4e2227a7afd506ed2b55dc9dd170d / 67,681 B** — exact match to
  Designer's published pin BEFORE any write (independent cross-seat byte proof).
- Applied via the sanctioned hash-gated one-shot:
  `python memory\builder\repin_root_index.py -Source designer\staged\variant_8ef4e2227a7a.html --expect-md5 8ef4e222…`
  → `REPIN DONE: 9c6b08e3… -> 8ef4e222…; mtime 2026-11-13 21:18:55 -> 2026-11-14 04:17:21`
- Post-verify: root `index.html` = **NEW CANONICAL PIN 8ef4e2227a7afd506ed2b55dc9dd170d / 67,681 B**;
  `#6b7688` count 0, `#8b93a7` count 3 (2 pre-existing + 1 fix); portal 1b86880c… and
  mirror e5c4a229… untouched.
- **Verifier: next sweep should pin the NEW root value 8ef4e222…/67,681 B** (all other pins unchanged).
- P1 native-dialog debt (L326, L906–923) deliberately NOT in this pin — separate change.

## 2. farm.py:569 apply artifact verified end-to-end on fixture (real apply still = White-console leg)
- `dcabots/farm569_apply_v2.py` tested against a synthetic fixture with 3 `os.path.relpath(` sites:
  - DRY-RUN: rc=0, listed L5/L7/L9 + helper insertion after last import, **no file written** (bytes unchanged).
  - APPLY: rc=0, timestamped backup created, 3 sites replaced, helper inserted, `py_compile PASS`,
    residual buggy sites: none.
  - IDEMPOTENT re-run: `ALREADY_APPLIED`, no write, py_compile PASS.
- Functional proof on this seat (`_verify_farm569.py`): raw `os.path.relpath('D:\\…','Z:\\…')`
  raises the exact self-test error `ValueError: path is on mount 'D:', start on mount 'Z:'`;
  `safe_relpath` returns abs path cross-drive, byte-identical results same-drive → **ALL_PASS**.
- Evidence copy of applied fixture: `memory/builder/farm569_fixture_applied.py`. Fixture dir removed.

## 3. Remaining handoffs (not Builder-owed)
- **White console (Arnold/human):** run the verified script on real source —
  `python dcabots\farm569_apply_v2.py projects\dcabots\dcabots\farm.py` (dry-run first, then `--apply`).
  Script auto-locates; idempotent; self-backs-up. farm.py itself is White-local (not in shared tree).
- **smoke8 + E14:** White-console human leg (Mechanic confirmed :8099 unreachable over LAN from other seats).
- **Orchestrator:** strike stale MEMORY.md GOAL line / hosts.md checkbox; dcabots re-prompt.
