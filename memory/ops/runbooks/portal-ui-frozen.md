# Portal UI Frozen Runbook

## Trigger
Portal shows empty agent list / dead buttons (JS parse error).

## Steps
1. Check browser console for JS errors (typically core.js parse fail)
2. Identify the offending commit: `git log --oneline -5 -- ui/core.js`
3. Fix: add missing brace / fix syntax; advance pin if index.html affected
4. Verify: hard-refresh (Ctrl+Shift+R); confirm agent list renders
5. Log incident with root cause + fix commit

## SLA
Diagnosis < 5 min; fix < 15 min for simple syntax errors
