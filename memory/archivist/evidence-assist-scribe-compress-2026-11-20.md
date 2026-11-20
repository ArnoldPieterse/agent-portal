# Evidence: Assist Scribe Goal 3 (Context Compression) - 2026-11-20

**Assisted by:** Archivist
**Original owner:** Scribe

## Issue Found
`get_gotchas()` in `memory/scribe/compress_context.py` was searching only `memory/scribe/` and picking up INDEX.md / meta-files instead of actual correction content. Result: gotchas section listed file names rather than useful warnings.

## Fix Applied
- Expanded search to `memory/synthesis/`, `memory/ops/`, `memory/scribe/`
- Added skip for INDEX/TODO/MEMORY prefixed files
- Broadened pattern to include `root.cause|405|clobber|revert`
- Added fallback to MEMORY.md hot notes if <3 gotchas found

## Verification
- `python memory/scribe/compress_context.py --agent builder --dry-run`: TOKEN CHECK PASS (362), GOTCHA COUNT 5 PASS
- `python memory/scribe/compress_context.py --agent archivist --dry-run`: TOKEN CHECK PASS (366), GOTCHA COUNT 6 PASS
- Gotchas now contain actual correction/root-cause content from synthesis leaves

## Artifacts
- Fixed file: `memory/scribe/compress_context.py` (get_gotchas function)
