import json, datetime
entry = {
    "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "host": "Red (sandbox seat)",
    "type": "goal4_dryrun_reconfirm",
    "results": {
        "recover_dryrun": "PASS (clean boot, NO-OP)",
        "recover_dryrun_force": "PASS (portal down, would start)",
        "deploy_verify_only": "0/1 (schtasks COM unavailable in sandbox - known blocker)"
    },
    "note": "Re-confirmed same state as prior pass. Schtask registration requires non-sandbox admin seat."
}
with open("memory/mechanic/reboot-recovery.jsonl", "a") as f:
    f.write(json.dumps(entry) + "\n")
print("logged")