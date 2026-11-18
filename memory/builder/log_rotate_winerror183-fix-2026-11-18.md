# log_rotate.py WinError 183 fix — 2026-11-18 (Builder, cross-assist owner: Mechanic)

## Bug
`memory/mechanic/log_rotate.py`, `rotate_file()` shift loop:
```python
for i in range(KEEP_ROTATIONS - 1, 0, -1):
    src = f"{base}{ext}.{i}"
    dst = f"{base}{ext}.{i+1}"
    if os.path.exists(src):
        if i + 1 > KEEP_ROTATIONS:
            os.remove(src)
        else:
            os.rename(src, dst)   # <-- WinError 183 on Windows if dst exists
```
Two defects:
1. `os.rename(src, dst)` raises **WinError 183** ("Cannot create a file when that file
   already exists") whenever `dst` is present. In steady state `.log.5` is normally the
   compressed `.log.5.gz`, so it only fires when a prior run died between the shift and
   the compress step, leaving a plain `.log.5` behind — exactly the reported trigger.
2. The `if i + 1 > KEEP_ROTATIONS: os.remove(src)` branch is **dead code**: with
   `KEEP_ROTATIONS=5` the loop's max `i+1` is 5, so it never fires; nothing ever evicted
   an over-retention file.

## Fix (minimal — preserve retention semantics)
Clear the rename target before renaming:
```python
    if os.path.exists(src):
        # Clear the target first: Windows os.rename() raises WinError 183
        # if dst already exists (e.g. a prior run crashed mid-rotation).
        if os.path.exists(dst):
            os.remove(dst)
        os.rename(src, dst)
```
No change to the compress-oldest / keep-5 behavior; only makes the rename idempotent.

## Verification (repro + regression)
Test built a temp dir with `app.log` (>10MB) **plus plain `.log.1`–`.log.5` all present**
(the exact crash trigger), imported the real module, and ran `rotate_file()`:
- `rotate_file()` returned True, no exception (pre-fix this raised WinError 183 at the
  `.log.4 -> .log.5` rename).
- Fresh empty `app.log` recreated; `app.log.1` == the rotated big file.
- Steady state = `['app.log.1','app.log.2','app.log.3','app.log.4','app.log.5.gz']`
  → exactly 5 generations, oldest compressed, no `.log.6*` over-retention.
- 5 further big-fill rotations all returned True, no crash, no over-retention.

Result: **PASS**

## Status
Closed for Mechanic's pending bug note ("log_rotate.py shift loop crashes with WinError
183 when .log.5 already exists; fix pending"). Evidence leaf + INDEX line added; end-of-run
sweep auto-links.