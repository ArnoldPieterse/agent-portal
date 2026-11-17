# Sync-Semantics Implementation Spec (Goal #1, 2026-11-17)

**Consumer:** Mechanic — implement in `memory_mirror.py` + new sidecar files.
**Supersedes:** `sync-semantics-options-2026-11-16.md` (options analysis) — this is the buildable spec for Option A.

---

## 1. Data Model

### 1a. Ownership Map (`memory_mirror_ownership.json`)

JSON file in `HERE/`. Maps path prefixes to owning seat name. Evaluated longest-prefix-first; first match wins.

```json
{
  "version": 1,
  "default_owner": "White",
  "rules": [
    {"prefix": "memory/researcher/", "owner": "Researcher"},
    {"prefix": "memory/designer/",   "owner": "Designer"},
    {"prefix": "memory/mechanic/",   "owner": "Mechanic"},
    {"prefix": "memory/orchestrator/","owner": "Orchestrator"},
    {"prefix": "memory/builder/",    "owner": "Builder"},
    {"prefix": "memory/verifier/",   "owner": "Verifier"},
    {"prefix": "memory/scribe/",     "owner": "Scribe"},
    {"prefix": "memory/archivist/",  "owner": "Archivist"}
  ]
}
```

- `default_owner`: any file not matching a rule is owned by White (root docs, shared files).
- The mirror runs ON White, so "White-owned" means the local copy is authoritative. Remote seats' local copies of White-owned files are read-only mirrors.
- Seat names map to host entries in `memory_mirror_hosts.json` via a `seat_name` field (add this field; values: `Red`, `Pale`, `Black`).

### 1b. Epoch Manifest (`memory_mirror_epoch.json`)

Sidecar file in `HERE/`. Per-path monotonically increasing counter.

```json
{
  "version": 1,
  "entries": {
    "TODO.md":                    {"owner": "White",      "epoch": 42, "last_writer": "White",     "ts": "2026-11-17T12:00:00"},
    "memory/researcher/goal.md":  {"owner": "Researcher", "epoch": 7,  "last_writer": "Researcher","ts": "2026-11-17T11:30:00"}
  }
}
```

- `epoch`: integer, increments by 1 on every successful write that changes the file content.
- `last_writer`: seat name that last bumped the epoch.
- `ts`: ISO-8601 timestamp of the bump (for audit; never used for ordering).
- New files get epoch=1 on first appearance.
- File deletion: entry removed from manifest (logged as `epoch_delete`).

### 1c. Quarantine Inbox (`memory_mirror_quarantine/`)

Directory in `HERE/`. Structure: `quarantine/<timestamp>_<source_seat>/<original_relative_path>`.

```json
// memory_mirror_quarantine/<ts>_<seat>/_meta.json
{
  "source_seat": "Red",
  "original_path": "memory/researcher/some_file.md",
  "detected_at": "2026-11-17T12:05:00",
  "reason": "foreign_write_non_owner",
  "md5": "a1b2c3d4",
  "note": "File owned by Researcher; Red wrote it. Quarantined for review."
}
```

- No silent loss: every foreign write lands here with full provenance.
- Orchestrator (or any human) can review and either discard or manually promote (copy back to correct location + bump epoch).
- Max retention: 30 days; pruned by the scheduled task at start of each run.

---

## 2. Algorithm (Conflict-Resolution Pseudocode)

### 2a. `resolve_owner(rel_path) -> seat_name`

```python
def resolve_owner(rel_path, ownership_map):
    """Longest-prefix match; default_owner if no rule matches."""
    best = None
    for rule in ownership_map["rules"]:
        if rel_path.startswith(rule["prefix"]) and (best is None or len(rule["prefix"]) > len(best["prefix"])):
            best = rule
    return best["owner"] if best else ownership_map["default_owner"]
```

### 2b. `sync_file(sp, dp, rel_path, owner_seat, local_seat, epoch_manifest) -> (action, meta)`

Replaces the current `_decide()` function. Called for both push and pull directions.

```python
def sync_file(sp, dp, rel_path, owner_seat, local_seat, epoch_manifest):
    """
    sp  = source path
    dp  = dest path
    rel_path = relative path (e.g. 'memory/researcher/x.md')
    owner_seat = who owns this file per ownership map
    local_seat = which seat is running the mirror right now (always 'White' for push;
                 varies for pull - actually we're always ON White, so local_seat='White'
                 and we compare against what's on remote)
    epoch_manifest = dict loaded from memory_mirror_epoch.json
    """
    entry = epoch_manifest.get(rel_path)
    owner_epoch = entry["epoch"] if entry else 0

    # Case 1: dest doesn't exist -> copy (new file), bump epoch to 1
    if not os.path.exists(dp):
        return "copy", {"reason": "new", "new_epoch": owner_epoch + 1}

    # Case 2: hashes equal -> no-op, skip
    hs, hd = _md5(sp), _md5(dp)
    if hs == hd:
        return "skip_same", {}

    # Case 3: foreign write to non-owned file -> quarantine (NEW BEHAVIOUR)
    # This happens on PULL when a remote seat has modified a file it doesn't own.
    if owner_seat != local_seat and not _is_owned_by(owner_seat, rel_path):
        # Actually the check is simpler: if the REMOTE modified this file
        # (i.e., remote hash differs from what we pushed last time), quarantine it.
        pass  # handled in direction-specific logic below

    # Case 4: epoch comparison (replaces mtime LWW entirely)
    # On PUSH (White -> remote): White is always the authority for its owned files.
    #   If sp hash != dp hash and owner is local_seat (or default=White):
    #     -> copy + bump epoch
    #   If owner is a REMOTE seat:
    #     -> do NOT push; skip (the remote seat will pull its own files)
    #
    # On PULL (remote -> White): Remote sends back its owned files.
    #   If owner_seat == remote's seat:  accept pull, bump epoch
    #   If owner_seat != remote's seat:  QUARANTINE (foreign write)

    if _direction == "push":
        if owner_seat == local_seat:
            return "copy", {"reason": "owner_push", "new_epoch": owner_epoch + 1}
        else:
            return "skip_foreign", {"reason": f"owned by {owner_seat}, not pushing from White"}

    else:  # pull (remote -> White)
        remote_seat = _current_remote_host_seat  # set per mirror_host() call
        if owner_seat == remote_seat:
            return "copy", {"reason": "owner_pull", "new_epoch": owner_epoch + 1}
        elif owner_seat == local_seat:  # White-owned file on remote is stale/different
            # Remote modified a White-owned file -> quarantine
            return "quarantine", {"reason": f"remote {remote_seat} modified White-owned file"}
        else:
            # Third-party file (shouldn't happen in practice) -> quarantine
            return "quarantine", {"reason": f"ambiguous ownership: owner={owner_seat}, remote={remote_seat}"}
```

### 2c. Epoch Bump + Persist

```python
def bump_epoch(manifest, rel_path, seat, new_epoch):
    manifest["entries"][rel_path] = {
        "owner": resolve_owner(rel_path),
        "epoch": new_epoch,
        "last_writer": seat,
        "ts": datetime.datetime.now().isoformat(timespec="seconds")
    }
    # Write atomically: tmp file + rename
    tmp = CFG_EPOCH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(manifest, f, indent=2)
    os.replace(tmp, CFG_EPOCH)
```

### 2d. Quarantine Action

```python
def quarantine_file(sp, rel_path, source_seat, reason):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    qdir = os.path.join(HERE, "memory_mirror_quarantine", f"{ts}_{source_seat}")
    os.makedirs(qdir, exist_ok=True)
    dest = os.path.join(qdir, rel_path.replace("/", os.sep))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copy2(sp, dest)
    meta = {"source_seat": source_seat, "original_path": rel_path,
            "detected_at": datetime.datetime.now().isoformat(),
            "reason": reason, "md5": _md5(sp)}
    with open(os.path.join(qdir, "_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    log({"t": now_str(), "quarantine": {"path": rel_path, **meta}})
```

### 2e. Modified `mirror_host()` Flow

```python
def mirror_host(h):
    # ... connection setup unchanged ...
    remote_seat = h["seat_name"]  # NEW field in hosts.json
    epoch_manifest = _load_epoch_manifest()

    # PUSH: only push files owned by White (local seat)
    for rel in _allowlist() + memory_tree:
        owner = resolve_owner(rel, ownership_map)
        if owner != "White":
            continue  # don't push files owned by other seats
        action, meta = sync_file(sp, dp, rel, owner, "White", epoch_manifest, direction="push")
        # handle copy / skip_same as before; log skip_foreign for audit

    # PULL: only pull files owned by the remote seat
    for rel in remote_memory_tree:
        owner = resolve_owner(rel, ownership_map)
        if owner == remote_seat:
            action, meta = sync_file(sp, dp, rel, owner, "White", epoch_manifest, direction="pull")
            if action == "copy":
                copy + bump_epoch
        else:
            # Foreign write -> quarantine
            quarantine_file(sp, rel, remote_seat, f"owned by {owner}")

    _save_epoch_manifest(epoch_manifest)
```

---

## 3. Migration Path from Current LWW

### Phase 0: Add `seat_name` to hosts (no behaviour change)
- Edit `memory_mirror_hosts.json`: add `"seat_name": "Red"|"Pale"|"Black"` per host.
- No code change needed yet; just data prep. **Risk: none.**

### Phase 1: Ship ownership map + epoch manifest (passive, no enforcement)
- Create `memory_mirror_ownership.json` with the rules above.
- Create `memory_mirror_epoch.json` empty (`{"version":1,"entries":{}}`).
- Modify `mirror_host()` to:
  - Load both files at start.
  - Call `resolve_owner()` for each file.
  - **Log** ownership decisions but DO NOT change sync behaviour yet (still use `_decide()` LWW).
  - On push/pull copy, record the epoch in the manifest (bump on content change) but don't gate on it.
- Run for 1–2 days. Verify: epoch manifest is populating correctly; ownership map resolves all files; no crashes.

### Phase 2: Enforce ownership on PUSH (White stops pushing foreign files)
- Gate the push loop: `if owner != "White": continue` (skip, log as `skip_foreign`).
- Epoch comparison replaces mtime for White-owned files: if source hash differs from dest, always copy (White is authoritative).
- **Risk:** If a remote seat has a newer version of a file that's actually White-owned but was edited there in error, it won't get pushed back. Mitigation: the pull side will quarantine it (Phase 3).

### Phase 3: Enforce ownership on PULL + activate quarantine
- Gate the pull loop: only accept files owned by the remote seat.
- Foreign writes go to quarantine inbox.
- Epoch bump on accepted pulls.
- **Risk:** First run may flood quarantine if stale foreign edits exist. Mitigation: dry-run mode (`--dry-run` flag logs what WOULD be quarantined without moving files); run once, review, then enable for real.

### Phase 4: Remove mtime logic (full cutover)
- Delete `_decide()` function.
- Remove `SKEW_TOL`, `MTOL` constants.
- Epoch is the sole ordering mechanism.
- Keep the JSON audit log (every decision still logged).
- **Risk:** If epoch manifest is lost/corrupted, fall back to hash-equality (skip same) and quarantine everything else until manually re-baselined. Add a `--rebaseline` flag: scan all files, set epoch=1 for each, clear conflicts.

### Rollback Plan
Each phase is independently rollback-able:
- Phase 1 rollback: delete the two JSON files; mirror reverts to pure LWW (existing code path).
- Phase 2 rollback: remove the `if owner != "White": continue` gate.
- Phase 3 rollback: set quarantine action to `skip_stale` instead of `quarantine` (foreign writes silently dropped, logged).
- Phase 4 rollback: restore `_decide()` from git history; epoch manifest becomes informational-only again.

Git history is the ultimate safety net — all changes are committed per phase.

---

## 4. Test Plan

### Unit Tests (run on White, no network)
| # | Test | Input | Expected |
|---|------|-------|----------|
| T1 | `resolve_owner` default | path="TODO.md" | returns "White" |
| T2 | `resolve_owner` lane | path="memory/researcher/x.md" | returns "Researcher" |
| T3 | `resolve_owner` longest-prefix | path="memory/researcher/sub/y.md" with rules for both prefixes | returns longest match |
| T4 | New file push | dp doesn't exist, owner=White | action=copy, new_epoch=1 |
| T5 | Same hash skip | hs==hd | action=skip_same |
| T6 | White-owned push | owner=White, direction=push | action=copy (always, hash diff) |
| T7 | Foreign push skipped | owner=Researcher, direction=push from White | action=skip_foreign |
| T8 | Owner pull accepted | owner=Red, remote_seat=Red, direction=pull | action=copy |
| T9 | Foreign pull quarantined | owner=White, remote_seat=Red, direction=pull | action=quarantine |
| T10 | Epoch monotonicity | bump same file 3x | epochs are 1,2,3 (strictly increasing) |
| T11 | Quarantine file lands | foreign write detected | file exists in quarantine dir with correct _meta.json |
| T12 | Epoch manifest atomic write | concurrent read during write | no partial JSON (tmp+rename) |

### Integration Tests (require at least 1 live remote, e.g. Red)
| # | Test | Steps | Expected |
|---|------|-------|----------|
| I1 | Steady-state no-op | Run mirror with no changes | pushed=0, pulled=0, all skip_same |
| I2 | White edits TODO.md, push | Edit locally, run mirror | Red's copy updated; epoch bumped; log shows owner_push |
| I3 | Researcher edits own file on remote, pull back | Edit on Red, run mirror | White's copy updated; epoch bumped; log shows owner_pull |
| I4 | Red edits TODO.md (foreign), pull | Edit TODO.md on Red, run mirror | Red's edit quarantined; White's TODO.md unchanged; quarantine dir has the file + meta |
| I5 | Quarantine pruning | Create quarantine entry >30 days old, run mirror | Entry deleted |
| I6 | Rebaseline after manifest loss | Delete epoch.json, run `--rebaseline` | All files get epoch=1; no conflicts logged |

### Acceptance Criteria for Goal Closure
- [ ] Unit tests T1–T12 all pass (run via `python -m pytest memory/researcher/test_sync_spec.py` or equivalent).
- [ ] Integration test I4 specifically demonstrates the quarantine path working end-to-end.
- [ ] Epoch manifest is valid JSON after 5 consecutive mirror runs.
- [ ] No mtime-based decisions remain in the code (grep for `st_mtime` in memory_mirror.py returns 0 hits outside comments).

---

## Appendix: Files Changed / Created
| File | Action |
|------|--------|
| `memory_mirror_ownership.json` | NEW |
| `memory_mirror_epoch.json` | NEW (created empty, populated on first run) |
| `memory_mirror_quarantine/` | NEW directory (git-ignored) |
| `memory_mirror_hosts.json` | ADD `seat_name` field per host |
| `memory_mirror.py` | MODIFIED: replace `_decide()` with ownership+epoch logic; add quarantine, epoch bump, rebaseline flag |
| `.gitignore` | ADD `memory_mirror_quarantine/` and `memory_mirror_epoch.json.tmp` |

## Open Questions for Mechanic
1. Where do we store the epoch manifest if White's disk fills / is wiped? Answer: it's reconstructable via `--rebaseline`; treat as cache, not source of truth. The source of truth is the file content + ownership map.
2. Should quarantine entries be visible in the portal UI? Nice-to-have; not blocking. Suggest a `/api/quarantine` endpoint in a later cycle.
3. Multi-remote concurrency: if two remotes both pull at the same moment, is there a race on epoch bump? Answer: no — each remote's mirror runs independently and only White writes the epoch manifest (remotes get it via push). Single-writer on the manifest itself.
