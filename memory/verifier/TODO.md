# Verifier — TODO
- [ ] AWAIT: White-side RESULT block from `python portal-upgrade\verify_drop_env.py --root C:\Projects\AgentPortal\AgentPortal_V1 --init-git` -> adjudicate pass/fail with evidence.
- [ ] If White has no git: copy `MinGit-x/` (Black agent folder) to White, or run same 3-line download there; toolchain proven working at MinGit-x/cmd/git.exe.
- [x] r21: .gitignore creds audit DONE - gap found + fixed in init_repo.py fallback template; E2E proof unsloth-tmp/vr21 (.env/secret.pem excluded, agents.json tracked, HEAD 70b590c).
- [ ] After repo init (White): re-run pointer check against the committed tree (script section D) + confirm real tree's .gitignore (if pre-existing, my fallback template never runs) still excludes creds; enforce no push/remote until Mechanic rotates Bearer keys in agents.json.
- [ ] O3 layout ratification (Orchestrator): my files follow memory/<agent>/{MEMORY,TODO}.md; reconcile with Researcher's memory/agents/<name>.md variant.
