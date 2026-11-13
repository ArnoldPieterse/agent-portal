# Designer r28 — A5 send-button contrast: ready hunk + record correction (NEW file, 2026-11-14)

Auto-continue round. New file per transport line (existing-file edits LWW-skip under skew). Supplements `post-restart-verify-r19.md` (FAIL #5 origin) and `a4-dual-base-verify-r27.md`. Apply = Builder via hash-gated one-shot; acceptance = Verifier. No index.html writes from me (r16 ruling stands).

## 0. Record correction (first-party, both staged variants)
`panel-discipline-r20.md` inferred the 8ef4e222 "WCAG-AA stamp" differed from 9c6b08e3 by one line in :root = "the contrast swap = r19 FAIL #5." FIRST-PARTY DIFF OF BOTH STAGED VARIANTS REFUTES THAT: the only differing line is `.aev .at{color:#…}` (#6b7688 → #8b93a7), an a11y-check timestamp color. `--acc` is **#4f8cff in BOTH bases** and the three white-text-on-accent fills are byte-identical in both. **FAIL #5 is open on both candidate bases; the 8ef4e222 stamp did not fix it.** Consequence: whichever base wins, A5 (below) is still owed. This corrects the r20 inference only — the A4 dual-base verdict in r27 is unaffected.

## 1. Defect + why a global --acc darken is WRONG (computed)
`--acc:#4f8cff` serves two roles across 14 `var(--acc)` uses with MUTUALLY EXCLUSIVE AA constraints:
- Role F (fill, white text on top — needs token DARK): `#send`, `.seg button.on`, `.btn.pri` → all at **3.22:1 now** (FAIL; r19 sheet named only send, but the other two carry the identical latent defect).
- Role L (line/border/icon/text on panel — needs token LIGHT): `#attach` icon, `.chipfile .st`, hover/focus/dragover borders → all at **5.43:1 now** (PASS).

No single hex satisfies both on this hue:
| candidate | white-on-token (Role F) | token-on-panel (Role L) |
|---|---|---|
| #4f8cff (current) | 3.22 ✗ | 5.43 ✓ |
| #3d7ce6 | 4.02 ✗ | 4.34 ✗ |
| #3570da | 4.69 ✓ | 3.73 ✗ |

Darken enough to pass Role F and Role L breaks; lighten to keep Role L and Role F stays at 3.22. **Correct fix = split the token**, not move it.

## 2. Fix (A5): new fill-only token, applied to the 3 Role-F contexts only
Add `--acc-strong:#2f6fe0` (white-on = **4.70:1 ✓ AA**); repoint ONLY `#send`, `.seg button.on`, `.btn.pri` to it. The 11 Role-L uses keep `--acc` at 5.43 — zero regression. Hue stays in the same blue family (no visual break).

## 3. Hunk — 4 anchors, each verified UNIQUE in BOTH bases this round
Base-agnostic: A5 touches only L10 (`:root` token line), L37, L69, L102 — none of which A4 (JS insert @ `filesRefresh` anchor + panel-div move into #modeBar + one new CSS rule) modifies. Anchor STRINGS remain unique pre- or post-A4; hash gate matches strings, not line numbers → A5 applies independently of, or stacked after, A4.

```
A (token):  --acc:#4f8cff;--ok:#3ddc84
          -> --acc:#4f8cff;--acc-strong:#2f6fe0;--ok:#3ddc84
B (seg):    .seg button.on{background:var(--acc);color:#fff}
          -> .seg button.on{background:var(--acc-strong);color:#fff}
C (send):   #send{background:var(--acc);border:none;color:#fff;border-radius:10px;padding:0 18px;cursor:pointer;font-size:14px}
          -> #send{background:var(--acc-strong);border:none;color:#fff;border-radius:10px;padding:0 18px;cursor:pointer;font-size:14px}
D (pri):    .btn.pri{background:var(--acc);border-color:var(--acc);color:#fff}
          -> .btn.pri{background:var(--acc-strong);border-color:var(--acc-strong);color:#fff}
```
Anchor uniqueness (first-party, both staged variants): A=1/1, B=1/1, C=1/1, D=1/1.
Post-apply simulation fingerprint (LF-normalized, RELATIVE comparison only — Builder's gate must hash actual CRLF disk bytes):
| base | post-A5 LF md5 | --acc-strong count |
|---|---|---|
| 9c6b08e3 | 473f4e925e63759d7d8291c4215f8e69 | 5 (1 def + 3 fills, .btn.pri counts 2) |
| 8ef4e222 | 28278850d219164a2024e40c036f7efe | 5 |

## 4. AC-A5 (functional acceptance — Verifier, post-apply)
- A5-1: computed contrast of `#send`, `.seg button.on`, `.btn.pri` (white on #2f6fe0) = **4.70 ≥ 4.5** AA normal text.
- A5-2: Role-L sample unchanged — `#attach` icon + `.chipfile .st` still on `--acc` #4f8cff → 5.43 (no regression).
- A5-3: no other rule references `--acc-strong` (exactly 5 occurrences file-wide); `--acc` count unchanged at its pre-A5 value.

## Lane state (designer)
DESIGN DELIVERABLES COMPLETE + A5 hunk ready. r19 sheet roll-forward: #1 CLOSED (Orchestrator opt-b), #3/#4 = A4 hunks ready (apply=Builder), **#5 = A5 hunk ready this leaf (apply=Builder)**, #2 alert()/confirm() + #6 360px media-query still open (Builder / needs one visual capture on a :8099-reachable seat). Next Designer action only if: A4 or A5 lands (I re-run the r19 sheet + support AC-A4/AC-A5), or base stamp changes. No index.html writes owed from me since r16.

Owner: Designer. Evidence: first-party diff of both staged variants (`designer/staged/variant_9c6b08e3….html`, `variant_8ef4e2227a7a.html`) + WCAG relative-luminance computation this round; anchors re-grepped in both bases.
