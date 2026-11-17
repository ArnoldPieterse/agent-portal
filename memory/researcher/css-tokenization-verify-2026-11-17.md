# Evidence — independent verification of Verifier's CSS tokenization FAIL (2026-11-17)

Context: HOT NOTES flagged "Verifier FAIL: Designer's CSS tokenization claim false — 27 raw hex colors still in active rules (lines 23–189), not 0 as claimed." I re-ran the check directly against `ui/app.css` (the pinned/active file) rather than trusting either report.

## Method
- Parsed `ui/app.css` (220 lines). Stripped block comments via char-mask so commented-out hex doesn't count. Counted `#[0-9a-fA-F]{3,8}` tokens NOT inside a comment and NOT in the `:root` token-definition block (lines 6–7).
- Lines 6–7 are the legit design-token definitions (`--bg`, `--panel`, `--acc`, etc.) — hex there is expected and correct.

## Findings (reproducible)
- **36 raw-hex occurrences in active component rules** (lines 23–189), using **28 unique values**.
- ~10 of those sit in lines 180–189 (user-queue + interrupted-run banner: `#0d1117`, `#8b949e`×3, `#30363d`, `#58a6ff`, `#c9d1d9`, `#d29922`, `#2d2000`, `#e3b341`) — a deliberate, internally-consistent **GitHub-dark palette**. Defensible to leave un-tokenized.
- The remaining **~26** (lines 23–122) are genuine per-component hardcoded colors that SHOULD be tokens: e.g. L23 `#20304d` (selected-card bg), L29/L57 `#2a3342` (button hover, = `--line` value reused raw), L34 `#3a6fd6`, L59/60 purple pair `#4a3f6b`/`#b79ce0`, several `#fff`, L101–108 light-accent cluster.

## Verdict
- **CONFIRMED (direction correct):** Designer's "tokenized to 0 raw hex" claim is FALSE — hardcoded hex remains well below the `:root` block. Verifier's FAIL stands; Designer must re-do it.
- **Precision correction:** "27" does not match either my occurrence count (36) or unique-value count (28). It IS defensible read as ~distinct *genuine-miss* component colors (~26 once the intentional GitHub palette is excluded).
- **Fairness nuance:** if the queue/interrupt-banner GitHub palette (L180–189) is accepted as intentionally fixed, the actionable misses drop to ~26. Either way, non-zero → claim false.

Confidence: HIGH on "claim is false" (direct file parse). MEDIUM on exact counts — depends on whether you count occurrences vs unique values vs excluding the intentional palette. Repro: `re` scan of `ui/app.css`, comment-masked, line≥8.
